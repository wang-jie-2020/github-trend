import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from fetch_trending import TRENDING_URL, fetch_html, parse_trending_html
from trending_html_contracts import COLLECTION_FILENAME, validate_collection


class ApiUnavailableError(RuntimeError):
    pass


def build_collection(
    top: int,
    *,
    fetch_trending_html: Callable[[], str] = fetch_html,
    fetch_repo_metadata: Callable[[str], Mapping[str, Any]] = None,
    now: str | None = None,
) -> dict[str, Any]:
    if top <= 0:
        raise ValueError("top must be positive")

    metadata_fetcher = fetch_repo_metadata or globals()["fetch_repo_metadata"]
    html = fetch_trending_html()
    trending_items = parse_trending_html(html)[:top]
    collected_at = now or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    repositories = []
    for rank, item in enumerate(trending_items, start=1):
        repo = item["repo"]
        metadata = metadata_fetcher(repo)
        trending_description = item.get("description") or metadata.get("api_description") or "No description provided."
        api_description = metadata.get("api_description") or trending_description
        language = item.get("language") or "Unknown"

        repositories.append(
            {
                "rank": rank,
                "repo": repo,
                "url": f"https://github.com/{repo}",
                "trending_description": trending_description,
                "api_description": api_description,
                "language": language,
                "stars": int(item.get("stars", 0)),
                "forks": int(item.get("forks", 0)),
                "topics": list(metadata.get("topics") or []),
                "license": metadata.get("license"),
                "homepage": metadata.get("homepage"),
                "pushed_timestamp": metadata.get("pushed_timestamp") or "Unknown",
                "latest_release": metadata.get("latest_release"),
            }
        )

    collection = {
        "source_url": TRENDING_URL,
        "since": "weekly",
        "collected_at": collected_at,
        "top": top,
        "repositories": repositories,
    }
    validate_collection(collection)
    return collection


def write_collection(collection: Mapping[str, Any], output_dir: Path) -> Path:
    collection = validate_collection(collection)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / COLLECTION_FILENAME
    output_path.write_text(json.dumps(collection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def fetch_repo_metadata(
    repo: str,
    *,
    env: Mapping[str, str] | None = None,
    run_command: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    urlopen_func: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    env = os.environ if env is None else env
    gh_metadata = _fetch_repo_metadata_with_gh(repo, run_command)
    if gh_metadata is not None:
        return gh_metadata

    token = env.get("GITHUB_TOKEN") or env.get("DEPLOY_TOKEN")
    if token:
        try:
            return _fetch_repo_metadata_with_token(repo, token, urlopen_func)
        except Exception as exc:  # noqa: BLE001 - surfaced as a clear route-level failure
            raise ApiUnavailableError(f"GitHub metadata unavailable for {repo}: token REST API failed ({exc})") from exc

    raise ApiUnavailableError(
        f"GitHub metadata unavailable for {repo}: gh api failed and no GITHUB_TOKEN or DEPLOY_TOKEN is set"
    )


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)

    collection = build_collection(args.top)
    output_path = write_collection(collection, Path(args.out_dir))
    print(output_path)
    return 0


def _fetch_repo_metadata_with_gh(
    repo: str, run_command: Callable[..., subprocess.CompletedProcess]
) -> dict[str, Any] | None:
    repo_data = _run_gh_json(["gh", "api", f"repos/{repo}"], run_command)
    if repo_data is None:
        return None

    release_data = _run_gh_json(["gh", "api", f"repos/{repo}/releases/latest"], run_command, optional_not_found=True)
    return _metadata_from_api_payload(repo_data, release_data)


def _run_gh_json(
    args: list[str],
    run_command: Callable[..., subprocess.CompletedProcess],
    *,
    optional_not_found: bool = False,
) -> Mapping[str, Any] | None:
    try:
        result = run_command(args, capture_output=True, text=True, encoding="utf-8", check=False)
    except FileNotFoundError:
        return None

    if result.returncode != 0:
        if optional_not_found and _looks_like_not_found(result.stderr):
            return None
        if optional_not_found:
            raise ApiUnavailableError(f"GitHub latest release metadata unavailable: gh api failed ({result.stderr.strip()})")
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, Mapping):
        return None
    return data


def _looks_like_not_found(stderr: str) -> bool:
    text = stderr.lower()
    return "not found" in text or "http 404" in text or "404" in text


def _fetch_repo_metadata_with_token(
    repo: str, token: str, urlopen_func: Callable[..., Any]
) -> dict[str, Any]:
    repo_data = _github_get_json(f"https://api.github.com/repos/{repo}", token, urlopen_func)
    release_data = None
    try:
        release_data = _github_get_json(f"https://api.github.com/repos/{repo}/releases/latest", token, urlopen_func)
    except HTTPError as exc:
        if exc.code != 404:
            raise
    return _metadata_from_api_payload(repo_data, release_data)


def _github_get_json(url: str, token: str, urlopen_func: Callable[..., Any]) -> Mapping[str, Any]:
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "weekly-trending-html-reader",
        },
        method="GET",
    )
    try:
        with urlopen_func(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError):
        raise
    if not isinstance(data, Mapping):
        raise ApiUnavailableError(f"GitHub API returned non-object JSON for {url}")
    return data


def _metadata_from_api_payload(
    repo_data: Mapping[str, Any], release_data: Mapping[str, Any] | None
) -> dict[str, Any]:
    return {
        "api_description": repo_data.get("description") or "No API description provided.",
        "topics": [str(topic) for topic in repo_data.get("topics") or []],
        "license": _license_name(repo_data.get("license")),
        "homepage": repo_data.get("homepage") or None,
        "pushed_timestamp": repo_data.get("pushed_at") or "Unknown",
        "latest_release": _release_metadata(release_data),
    }


def _license_name(license_data: Any) -> str | None:
    if not isinstance(license_data, Mapping):
        return None
    return license_data.get("spdx_id") or license_data.get("name")


def _release_metadata(release_data: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not release_data:
        return None
    return {
        "name": release_data.get("name") or release_data.get("tag_name") or "Unnamed release",
        "tag_name": release_data.get("tag_name") or "",
        "url": release_data.get("html_url") or "",
        "published_at": release_data.get("published_at") or "",
    }


if __name__ == "__main__":
    raise SystemExit(main())

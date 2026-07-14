import json
from pathlib import Path
from typing import Any, Mapping


COLLECTION_FILENAME = "collection.json"
SUMMARIES_FILENAME = "summaries.json"

COLLECTION_REQUIRED_FIELDS = {
    "rank",
    "repo",
    "url",
    "trending_description",
    "api_description",
    "language",
    "stars",
    "forks",
    "topics",
    "license",
    "homepage",
    "pushed_timestamp",
    "latest_release",
}

SUMMARY_REQUIRED_FIELDS = {
    "repo",
    "readme_status",
    "readme_error",
    "summary",
    "why_it_matters",
    "best_for",
    "key_points",
}

EXCLUDED_COLLECTION_FIELDS = {
    "readme",
    "readme_text",
    "readme_source",
    "readme_path",
    "readme_paths",
    "open_issues",
    "open_issues_count",
    "owner_type",
}

EXCLUDED_SUMMARY_FIELDS = {
    "readme",
    "readme_text",
    "readme_source",
    "readme_content",
}

README_STATUSES = {"ok", "missing", "unreadable"}


class ContractError(ValueError):
    pass


def validate_collection(data: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise ContractError("collection must be a JSON object")

    repositories = data.get("repositories")
    if not isinstance(repositories, list):
        raise ContractError("collection.repositories must be a list")

    seen = set()
    for index, repository in enumerate(repositories, start=1):
        if not isinstance(repository, Mapping):
            raise ContractError(f"repository #{index} must be an object")

        excluded = EXCLUDED_COLLECTION_FIELDS.intersection(repository)
        if excluded:
            names = ", ".join(sorted(excluded))
            raise ContractError(f"collection repository {repository.get('repo', index)} contains excluded field: {names}")

        missing = COLLECTION_REQUIRED_FIELDS.difference(repository)
        if missing:
            names = ", ".join(sorted(missing))
            raise ContractError(f"collection repository {repository.get('repo', index)} missing fields: {names}")

        repo = _required_string(repository, "repo", f"repository #{index}")
        if "/" not in repo:
            raise ContractError(f"repository #{index} repo must be owner/name")
        if repo in seen:
            raise ContractError(f"duplicate repo in collection: {repo}")
        seen.add(repo)

        rank = repository["rank"]
        if not isinstance(rank, int) or rank < 1:
            raise ContractError(f"{repo} rank must be a positive integer")

        for field in ["url", "trending_description", "api_description", "language", "pushed_timestamp"]:
            _required_string(repository, field, repo)

        for field in ["stars", "forks"]:
            value = repository[field]
            if not isinstance(value, int) or value < 0:
                raise ContractError(f"{repo} {field} must be a non-negative integer")

        topics = repository["topics"]
        if not isinstance(topics, list) or not all(isinstance(topic, str) for topic in topics):
            raise ContractError(f"{repo} topics must be a list of strings")

        for field in ["license", "homepage"]:
            value = repository[field]
            if value is not None and not isinstance(value, str):
                raise ContractError(f"{repo} {field} must be a string or null")

        latest_release = repository["latest_release"]
        if latest_release is not None and not isinstance(latest_release, Mapping):
            raise ContractError(f"{repo} latest_release must be an object or null")

    return dict(data)


def validate_summaries(data: Mapping[str, Any], collection: Mapping[str, Any]) -> dict[str, Any]:
    collection = validate_collection(collection)
    if not isinstance(data, Mapping):
        raise ContractError("summaries must be a JSON object")

    summaries = data.get("summaries")
    if not isinstance(summaries, list):
        raise ContractError("summaries.summaries must be a list")

    collection_repos = [repository["repo"] for repository in collection["repositories"]]
    collection_repo_set = set(collection_repos)
    summary_repo_set = set()

    for index, summary in enumerate(summaries, start=1):
        if not isinstance(summary, Mapping):
            raise ContractError(f"summary #{index} must be an object")

        excluded = EXCLUDED_SUMMARY_FIELDS.intersection(summary)
        if excluded:
            names = ", ".join(sorted(excluded))
            raise ContractError(f"summary {summary.get('repo', index)} contains excluded field: {names}")

        missing = SUMMARY_REQUIRED_FIELDS.difference(summary)
        if missing:
            names = ", ".join(sorted(missing))
            raise ContractError(f"summary #{index} missing fields: {names}")

        repo = _required_string(summary, "repo", f"summary #{index}")
        if repo in summary_repo_set:
            raise ContractError(f"duplicate repo in summaries: {repo}")
        summary_repo_set.add(repo)

        status = summary["readme_status"]
        if status not in README_STATUSES:
            raise ContractError(f"{repo} readme_status must be one of: {', '.join(sorted(README_STATUSES))}")
        if status in {"missing", "unreadable"} and not _is_non_empty_string(summary["readme_error"]):
            raise ContractError(f"{repo} readme_error is required when README is {status}")
        if status == "ok" and summary["readme_error"] not in (None, ""):
            raise ContractError(f"{repo} readme_error must be empty when README status is ok")

        for field in ["summary", "why_it_matters", "best_for"]:
            _required_string(summary, field, repo)

        key_points = summary["key_points"]
        if not isinstance(key_points, list) or len(key_points) != 3:
            raise ContractError(f"{repo} must have exactly three key_points")
        if not all(_is_non_empty_string(point) for point in key_points):
            raise ContractError(f"{repo} key_points must be non-empty strings")

    missing = [repo for repo in collection_repos if repo not in summary_repo_set]
    if missing:
        raise ContractError(f"missing summaries for repositories: {', '.join(missing)}")

    extras = sorted(summary_repo_set.difference(collection_repo_set))
    if extras:
        raise ContractError(f"summaries contain unknown repositories: {', '.join(extras)}")

    return dict(data)


def load_reader_inputs(input_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    collection = json.loads((input_dir / COLLECTION_FILENAME).read_text(encoding="utf-8"))
    summaries = json.loads((input_dir / SUMMARIES_FILENAME).read_text(encoding="utf-8"))
    collection = validate_collection(collection)
    summaries = validate_summaries(summaries, collection)
    return collection, summaries


def _required_string(data: Mapping[str, Any], field: str, label: str) -> str:
    value = data[field]
    if not _is_non_empty_string(value):
        raise ContractError(f"{label} {field} must be a non-empty string")
    return value


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

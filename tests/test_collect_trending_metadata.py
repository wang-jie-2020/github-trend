import json
import subprocess
from pathlib import Path
from urllib.error import HTTPError

import pytest

from scripts.collect_trending_metadata import ApiUnavailableError, build_collection, fetch_repo_metadata, write_collection
from scripts.trending_html_contracts import validate_collection


TRENDING_HTML = Path("tests/fixtures/trending_sample.html").read_text(encoding="utf-8")


def metadata_for(repo):
    return {
        "api_description": f"API description for {repo}",
        "topics": ["topic-a", "topic-b"],
        "license": "MIT",
        "homepage": f"https://example.com/{repo.split('/')[-1]}",
        "pushed_timestamp": "2026-07-13T12:00:00Z",
        "latest_release": {
            "name": "v1.0.0",
            "tag_name": "v1.0.0",
            "url": f"https://github.com/{repo}/releases/tag/v1.0.0",
            "published_at": "2026-07-12T12:00:00Z",
        },
    }


def test_build_collection_preserves_trending_rank_order_and_contract():
    collection = build_collection(
        2,
        fetch_trending_html=lambda: TRENDING_HTML,
        fetch_repo_metadata=metadata_for,
        now="2026-07-14T00:00:00Z",
    )

    validate_collection(collection)
    assert collection["top"] == 2
    assert [repo["repo"] for repo in collection["repositories"]] == ["owner1/repo1", "owner2/repo2"]
    assert collection["repositories"][0]["rank"] == 1
    assert collection["repositories"][0]["trending_description"] == "first repo description"
    assert collection["repositories"][0]["api_description"] == "API description for owner1/repo1"
    assert "readme_path" not in collection["repositories"][0]
    assert "open_issues_count" not in collection["repositories"][0]
    assert "owner_type" not in collection["repositories"][0]


def test_build_collection_respects_top_n():
    collection = build_collection(
        1,
        fetch_trending_html=lambda: TRENDING_HTML,
        fetch_repo_metadata=metadata_for,
        now="2026-07-14T00:00:00Z",
    )

    assert [repo["repo"] for repo in collection["repositories"]] == ["owner1/repo1"]


def test_write_collection_creates_output_directory(tmp_path):
    collection = build_collection(
        1,
        fetch_trending_html=lambda: TRENDING_HTML,
        fetch_repo_metadata=metadata_for,
        now="2026-07-14T00:00:00Z",
    )

    output_path = write_collection(collection, tmp_path / "dated-output")

    assert output_path == tmp_path / "dated-output" / "collection.json"
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["repositories"][0]["repo"] == "owner1/repo1"


def test_fetch_repo_metadata_prefers_gh_api_when_available():
    calls = []

    def run_command(args, **kwargs):
        calls.append(args)
        if args[-1] == "repos/owner/repo":
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps({
                "description": "from gh",
                "topics": ["gh-topic"],
                "license": {"spdx_id": "Apache-2.0"},
                "homepage": "https://example.com",
                "pushed_at": "2026-07-13T12:00:00Z",
            }), stderr="")
        return subprocess.CompletedProcess(args, 0, stdout=json.dumps({
            "name": "release one",
            "tag_name": "v1",
            "html_url": "https://github.com/owner/repo/releases/tag/v1",
            "published_at": "2026-07-12T12:00:00Z",
        }), stderr="")

    metadata = fetch_repo_metadata("owner/repo", env={"GITHUB_TOKEN": "should-not-be-used"}, run_command=run_command)

    assert metadata == {
        "api_description": "from gh",
        "topics": ["gh-topic"],
        "license": "Apache-2.0",
        "homepage": "https://example.com",
        "pushed_timestamp": "2026-07-13T12:00:00Z",
        "latest_release": {
            "name": "release one",
            "tag_name": "v1",
            "url": "https://github.com/owner/repo/releases/tag/v1",
            "published_at": "2026-07-12T12:00:00Z",
        },
    }
    assert calls == [
        ["gh", "api", "repos/owner/repo"],
        ["gh", "api", "repos/owner/repo/releases/latest"],
    ]


def test_fetch_repo_metadata_falls_back_to_token_rest_when_gh_fails():
    requested_urls = []

    def run_command(args, **kwargs):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="not authenticated")

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    def urlopen_func(request, timeout):
        requested_urls.append(request.full_url)
        if request.full_url.endswith("/releases/latest"):
            raise HTTPError(request.full_url, 404, "Not Found", hdrs=None, fp=None)
        return Response({
            "description": "from token",
            "topics": ["rest-topic"],
            "license": None,
            "homepage": None,
            "pushed_at": "2026-07-11T12:00:00Z",
        })

    metadata = fetch_repo_metadata(
        "owner/repo",
        env={"GITHUB_TOKEN": "token-value"},
        run_command=run_command,
        urlopen_func=urlopen_func,
    )

    assert metadata["api_description"] == "from token"
    assert metadata["latest_release"] is None
    assert requested_urls == [
        "https://api.github.com/repos/owner/repo",
        "https://api.github.com/repos/owner/repo/releases/latest",
    ]


def test_fetch_repo_metadata_fails_when_gh_release_lookup_errors_without_token():
    def run_command(args, **kwargs):
        if args[-1] == "repos/owner/repo":
            return subprocess.CompletedProcess(args, 0, stdout=json.dumps({
                "description": "from gh",
                "topics": [],
                "license": None,
                "homepage": None,
                "pushed_at": "2026-07-13T12:00:00Z",
            }), stderr="")
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="rate limit exceeded")

    with pytest.raises(ApiUnavailableError, match="latest release"):
        fetch_repo_metadata("owner/repo", env={}, run_command=run_command)


def test_fetch_repo_metadata_fails_clearly_without_api_route():
    def run_command(args, **kwargs):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="not authenticated")

    with pytest.raises(ApiUnavailableError, match="GitHub metadata unavailable"):
        fetch_repo_metadata("owner/repo", env={}, run_command=run_command)


def test_build_collection_rejects_non_positive_top():
    with pytest.raises(ValueError, match="top must be positive"):
        build_collection(0, fetch_trending_html=lambda: TRENDING_HTML, fetch_repo_metadata=metadata_for)

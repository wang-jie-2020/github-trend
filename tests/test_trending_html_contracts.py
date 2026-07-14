import copy
import json
from pathlib import Path

import pytest

from scripts.trending_html_contracts import ContractError, load_reader_inputs, validate_collection, validate_summaries


FIXTURE_DIR = Path("tests/fixtures/github_weekly_trending")


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_collection_and_summaries_match_contract():
    collection = validate_collection(load_fixture("collection.json"))
    summaries = validate_summaries(load_fixture("summaries.json"), collection)

    assert collection["repositories"][0]["repo"] == "owner1/repo1"
    assert summaries["summaries"][0]["key_points"] == [
        "Provides a simple command-line workflow.",
        "Integrates with common developer tooling.",
        "Has clear metadata for quick evaluation.",
    ]


def test_collection_rejects_excluded_fields():
    collection = load_fixture("collection.json")
    collection["repositories"][0]["readme_path"] = "README.md"

    with pytest.raises(ContractError, match="readme_path"):
        validate_collection(collection)


def test_collection_rejects_duplicate_repositories():
    collection = load_fixture("collection.json")
    collection["repositories"][1]["repo"] = "owner1/repo1"

    with pytest.raises(ContractError, match="duplicate repo"):
        validate_collection(collection)


def test_summaries_reject_readme_source_fields():
    collection = validate_collection(load_fixture("collection.json"))
    summaries = load_fixture("summaries.json")
    summaries["summaries"][0]["readme_text"] = "# full README"

    with pytest.raises(ContractError, match="readme_text"):
        validate_summaries(summaries, collection)


def test_summaries_require_exactly_three_key_points():
    collection = validate_collection(load_fixture("collection.json"))
    summaries = load_fixture("summaries.json")
    summaries["summaries"][0]["key_points"] = ["one", "two"]

    with pytest.raises(ContractError, match="exactly three key_points"):
        validate_summaries(summaries, collection)


def test_summaries_must_cover_collection_without_extras():
    collection = validate_collection(load_fixture("collection.json"))
    summaries = load_fixture("summaries.json")
    summaries["summaries"] = summaries["summaries"][:1]

    with pytest.raises(ContractError, match="missing summaries"):
        validate_summaries(summaries, collection)

    summaries = load_fixture("summaries.json")
    extra = copy.deepcopy(summaries["summaries"][0])
    extra["repo"] = "unknown/repo"
    summaries["summaries"].append(extra)

    with pytest.raises(ContractError, match="unknown repositories"):
        validate_summaries(summaries, collection)


def test_missing_or_unreadable_readme_requires_explicit_error():
    collection = validate_collection(load_fixture("collection.json"))
    summaries = load_fixture("summaries.json")
    summaries["summaries"][1]["readme_error"] = ""

    with pytest.raises(ContractError, match="readme_error"):
        validate_summaries(summaries, collection)


def test_load_reader_inputs_reads_known_artifacts(tmp_path):
    (tmp_path / "collection.json").write_text(
        (FIXTURE_DIR / "collection.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "summaries.json").write_text(
        (FIXTURE_DIR / "summaries.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    collection, summaries = load_reader_inputs(tmp_path)

    assert [repo["repo"] for repo in collection["repositories"]] == ["owner1/repo1", "owner2/repo2"]
    assert [summary["repo"] for summary in summaries["summaries"]] == ["owner1/repo1", "owner2/repo2"]

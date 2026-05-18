import json
from pathlib import Path

from scripts.fetch_trending import normalize_items, parse_trending_html


def test_parse_trending_html_extracts_repositories():
    html = Path("tests/fixtures/trending_sample.html").read_text(encoding="utf-8")
    parsed = parse_trending_html(html)

    assert len(parsed) == 2
    assert parsed[0]["repo"] == "owner1/repo1"
    assert parsed[1]["repo"] == "owner2/repo2"


def test_normalize_items_matches_expected_fixture():
    html = Path("tests/fixtures/trending_sample.html").read_text(encoding="utf-8")
    parsed = parse_trending_html(html)
    normalized = normalize_items(parsed)

    expected = json.loads(Path("tests/fixtures/trending_expected.json").read_text(encoding="utf-8"))
    assert normalized == expected

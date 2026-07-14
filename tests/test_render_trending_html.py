import json
from pathlib import Path

import pytest

from scripts.render_trending_html import render_html, render_trending_html
from scripts.trending_html_contracts import ContractError


FIXTURE_DIR = Path("tests/fixtures/github_weekly_trending")


def load_fixture(name):
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_render_html_contains_split_cards_and_reader_content():
    html = render_html(load_fixture("collection.json"), load_fixture("summaries.json"))

    assert html.count('class="reader-card"') == 2
    assert "#1" in html
    assert "owner1/repo1" in html
    assert "https://github.com/owner1/repo1" in html
    assert "Python" in html
    assert "1,234" in html
    assert "56 forks" in html
    assert "Repo one automates a focused development workflow." in html
    assert "Why it matters" in html
    assert "Best for" in html
    assert "Provides a simple command-line workflow." in html
    assert "MIT" in html
    assert "v1.0.0" in html
    assert "README returned 404 during dry run." in html


def test_render_html_includes_keyboard_navigation_and_responsive_css():
    html = render_html(load_fixture("collection.json"), load_fixture("summaries.json"))

    assert "keydown" in html
    assert "ArrowRight" in html
    assert "ArrowLeft" in html
    assert "PageDown" in html
    assert "Home" in html
    assert "End" in html
    assert "@media (max-width: 760px)" in html


def test_render_html_is_deterministic():
    collection = load_fixture("collection.json")
    summaries = load_fixture("summaries.json")

    assert render_html(collection, summaries) == render_html(collection, summaries)


def test_render_html_escapes_dynamic_content():
    collection = load_fixture("collection.json")
    summaries = load_fixture("summaries.json")
    collection["repositories"][0]["api_description"] = "<script>alert('x')</script>"
    summaries["summaries"][0]["summary"] = "Uses <strong>markup</strong> safely."

    html = render_html(collection, summaries)

    assert "<script>alert" not in html
    assert "&lt;script&gt;alert" in html
    assert "Uses &lt;strong&gt;markup&lt;/strong&gt; safely." in html


def test_render_html_fails_when_summary_is_missing():
    collection = load_fixture("collection.json")
    summaries = load_fixture("summaries.json")
    summaries["summaries"] = summaries["summaries"][:1]

    with pytest.raises(ContractError, match="missing summaries"):
        render_html(collection, summaries)


def test_render_trending_html_writes_to_input_directory(tmp_path):
    for name in ["collection.json", "summaries.json"]:
        (tmp_path / name).write_text((FIXTURE_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")

    output_path = render_trending_html(tmp_path)
    first_render = output_path.read_text(encoding="utf-8")
    second_path = render_trending_html(tmp_path)
    second_render = second_path.read_text(encoding="utf-8")

    assert output_path == tmp_path / "trending.html"
    assert first_render == second_render
    assert "owner2/repo2" in first_render

from datetime import date

from scripts.create_issue import build_search_query, build_weekly_title
from scripts.render_markdown import render_issue_body


def test_render_issue_body_contains_header_and_rows():
    items = [
        {
            "source": "trending",
            "rank": 1,
            "repo": "owner1/repo1",
            "url": "https://github.com/owner1/repo1",
            "summary": "desc 1",
            "language": "Python",
            "stars": 1234,
            "forks": 56,
        }
    ]

    body = render_issue_body(items=items, top=20, generated_at="2026-05-11T01:00:00Z")

    assert "# Weekly GitHub Trending" in body
    assert "owner1/repo1" in body
    assert "https://github.com/owner1/repo1" in body
    assert "Top 20" in body


def test_build_weekly_title_uses_iso_week():
    assert build_weekly_title(date(2026, 5, 11)) == "Weekly GitHub Trending - 2026-W20"


def test_build_search_query_targets_open_issues_by_exact_title():
    q = build_search_query("owner/repo", "Weekly GitHub Trending - 2026-W20")
    assert q == 'repo:owner/repo is:issue is:open in:title "Weekly GitHub Trending - 2026-W20"'

# GitHub Weekly Trending MVP A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated weekly GitHub Trending report that runs every Monday 09:00 Asia/Shanghai and creates one deduplicated GitHub Issue per ISO week.

**Architecture:** A GitHub Actions workflow invokes a Python fetch script to pull and parse the weekly Trending page into JSON, then invokes a publish script to render markdown and create an issue via GitHub REST API. Idempotency is enforced by ISO-week title lookup before issue creation. Manual dispatch is included for verification.

**Tech Stack:** GitHub Actions, Python 3 stdlib (`urllib`, `html.parser`, `json`, `datetime`), GitHub REST API

---

## File Structure

- Create: `.github/workflows/weekly-trending.yml` — weekly schedule + manual dispatch workflow
- Create: `scripts/fetch_trending.py` — fetch and parse trending weekly page into normalized JSON
- Create: `scripts/create_issue.py` — dedupe by weekly issue title, render markdown, and create issue
- Create: `scripts/render_markdown.py` — pure markdown rendering helper for reuse/testing
- Create: `tests/test_fetch_trending.py` — parser and normalization tests using saved HTML fixture
- Create: `tests/test_render_markdown.py` — markdown rendering tests
- Create: `tests/fixtures/trending_sample.html` — deterministic fixture for parser test
- Create: `tests/fixtures/trending_expected.json` — expected normalized output fixture
- Modify: `docs/superpowers/specs/2026-05-11-github-trending-design.md` — append plan linkage note

## Task 1: Scaffold workflow contract

**Files:**
- Create: `.github/workflows/weekly-trending.yml`
- Test: `gh workflow view "weekly-trending"` (after push)

- [ ] **Step 1: Write the failing static contract check**

Create `.github/workflows/weekly-trending.yml` with intentionally missing `workflow_dispatch`:

```yaml
name: weekly-trending

on:
  schedule:
    - cron: "0 1 * * 1"

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - uses: actions/checkout@v4
```

- [ ] **Step 2: Run YAML check to verify contract is incomplete**

Run: `python - <<'PY'\nimport yaml,sys\nobj=yaml.safe_load(open('.github/workflows/weekly-trending.yml','r',encoding='utf-8'))\nassert 'workflow_dispatch' in obj['on']\nPY`
Expected: FAIL with `AssertionError`

- [ ] **Step 3: Write minimal complete workflow trigger and execution steps**

Replace file with:

```yaml
name: weekly-trending

on:
  schedule:
    - cron: "0 1 * * 1"
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Fetch weekly trending
        run: python scripts/fetch_trending.py --top 20 --out /tmp/trending.json

      - name: Create weekly issue
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: python scripts/create_issue.py --input /tmp/trending.json --top 20
```

- [ ] **Step 4: Run YAML parse check to verify it passes**

Run: `python - <<'PY'\nimport yaml\nobj=yaml.safe_load(open('.github/workflows/weekly-trending.yml','r',encoding='utf-8'))\nassert 'workflow_dispatch' in obj['on']\nassert obj['jobs']['generate']['permissions']['issues']=='write'\nprint('ok')\nPY`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/weekly-trending.yml
git commit -m "feat: add weekly trending workflow scaffold"
```

## Task 2: Implement and test Trending parser (TDD)

**Files:**
- Create: `scripts/fetch_trending.py`
- Create: `tests/test_fetch_trending.py`
- Create: `tests/fixtures/trending_sample.html`
- Create: `tests/fixtures/trending_expected.json`

- [ ] **Step 1: Write failing parser tests**

Create `tests/test_fetch_trending.py`:

```python
import json
from pathlib import Path

from scripts.fetch_trending import parse_trending_html, normalize_items


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
```

Create `tests/fixtures/trending_sample.html`:

```html
<article class="Box-row">
  <h2><a href="/owner1/repo1"> owner1 / repo1 </a></h2>
  <p>first repo description</p>
  <span itemprop="programmingLanguage">Python</span>
  <a href="/owner1/repo1/stargazers">1,234</a>
  <a href="/owner1/repo1/forks">56</a>
</article>
<article class="Box-row">
  <h2><a href="/owner2/repo2"> owner2 / repo2 </a></h2>
  <p>second repo description</p>
  <span itemprop="programmingLanguage">Go</span>
  <a href="/owner2/repo2/stargazers">987</a>
  <a href="/owner2/repo2/forks">12</a>
</article>
```

Create `tests/fixtures/trending_expected.json`:

```json
[
  {
    "source": "trending",
    "rank": 1,
    "repo": "owner1/repo1",
    "url": "https://github.com/owner1/repo1",
    "summary": "first repo description",
    "language": "Python",
    "stars": 1234,
    "forks": 56
  },
  {
    "source": "trending",
    "rank": 2,
    "repo": "owner2/repo2",
    "url": "https://github.com/owner2/repo2",
    "summary": "second repo description",
    "language": "Go",
    "stars": 987,
    "forks": 12
  }
]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_fetch_trending.py -q`
Expected: FAIL with `ModuleNotFoundError` or missing symbol for `parse_trending_html`

- [ ] **Step 3: Write minimal parser implementation**

Create `scripts/fetch_trending.py`:

```python
import argparse
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.request import Request, urlopen

TRENDING_URL = "https://github.com/trending?since=weekly"


@dataclass
class RepoItem:
    repo: str = ""
    description: str = ""
    language: str = ""
    stars: int = 0
    forks: int = 0


class TrendingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self._in_article = False
        self._in_h2 = False
        self._in_description = False
        self._in_language = False
        self._capture_stars = False
        self._capture_forks = False
        self._current = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "Box-row" in attrs.get("class", ""):
            self._in_article = True
            self._current = RepoItem()
        if not self._in_article:
            return
        if tag == "h2":
            self._in_h2 = True
        elif tag == "p":
            self._in_description = True
        elif tag == "span" and attrs.get("itemprop") == "programmingLanguage":
            self._in_language = True
        elif tag == "a":
            href = attrs.get("href", "")
            if self._in_h2 and href.count("/") >= 2:
                self._current.repo = href.strip("/")
            elif href.endswith("/stargazers"):
                self._capture_stars = True
            elif href.endswith("/forks"):
                self._capture_forks = True

    def handle_endtag(self, tag):
        if tag == "article" and self._in_article:
            self._in_article = False
            self._in_h2 = False
            self._in_description = False
            self._in_language = False
            self._capture_stars = False
            self._capture_forks = False
            self.items.append(self._current)
            self._current = None
        elif tag == "h2":
            self._in_h2 = False
        elif tag == "p":
            self._in_description = False
        elif tag == "span":
            self._in_language = False
        elif tag == "a":
            self._capture_stars = False
            self._capture_forks = False

    def handle_data(self, data):
        if not self._in_article or self._current is None:
            return
        text = data.strip()
        if not text:
            return
        if self._in_description:
            self._current.description = text
        elif self._in_language:
            self._current.language = text
        elif self._capture_stars:
            self._current.stars = int(re.sub(r"[^0-9]", "", text) or 0)
        elif self._capture_forks:
            self._current.forks = int(re.sub(r"[^0-9]", "", text) or 0)


def parse_trending_html(html: str):
    parser = TrendingParser()
    parser.feed(html)
    return [
        {
            "repo": item.repo,
            "description": item.description,
            "language": item.language,
            "stars": item.stars,
            "forks": item.forks,
        }
        for item in parser.items
        if item.repo
    ]


def normalize_items(items):
    normalized = []
    for idx, item in enumerate(items, start=1):
        normalized.append(
            {
                "source": "trending",
                "rank": idx,
                "repo": item["repo"],
                "url": f"https://github.com/{item['repo']}",
                "summary": item.get("description", ""),
                "language": item.get("language", ""),
                "stars": int(item.get("stars", 0)),
                "forks": int(item.get("forks", 0)),
            }
        )
    return normalized


def fetch_html():
    request = Request(TRENDING_URL, headers={"User-Agent": "weekly-trending-bot"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    html = fetch_html()
    parsed = parse_trending_html(html)
    normalized = normalize_items(parsed)[: args.top]

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_fetch_trending.py -q`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_trending.py tests/test_fetch_trending.py tests/fixtures/trending_sample.html tests/fixtures/trending_expected.json
git commit -m "feat: add trending parser and normalization"
```

## Task 3: Implement markdown renderer (TDD)

**Files:**
- Create: `scripts/render_markdown.py`
- Create: `tests/test_render_markdown.py`

- [ ] **Step 1: Write failing renderer test**

Create `tests/test_render_markdown.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_render_markdown.py -q`
Expected: FAIL with missing `render_issue_body`

- [ ] **Step 3: Write minimal renderer implementation**

Create `scripts/render_markdown.py`:

```python
def render_issue_body(items, top, generated_at):
    lines = [
        "# Weekly GitHub Trending",
        "",
        f"- Generated at: {generated_at}",
        "- Source: GitHub Trending (weekly)",
        f"- Top {top}",
        "",
        "| # | Repository | Language | Stars | Forks | Summary |",
        "|---|---|---|---:|---:|---|",
    ]

    for item in items:
        repo_link = f"[{item['repo']}]({item['url']})"
        lines.append(
            f"| {item['rank']} | {repo_link} | {item['language'] or '-'} | {item['stars']} | {item['forks']} | {item['summary'] or '-'} |"
        )

    lines.extend(["", "_This issue is generated automatically._"])
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/test_render_markdown.py -q`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/render_markdown.py tests/test_render_markdown.py
git commit -m "feat: add markdown renderer for weekly issue"
```

## Task 4: Implement issue creation with idempotency (TDD)

**Files:**
- Create: `scripts/create_issue.py`
- Modify: `tests/test_render_markdown.py`

- [ ] **Step 1: Write failing unit test for title format and dedupe query helper**

Append to `tests/test_render_markdown.py`:

```python
from datetime import date

from scripts.create_issue import build_weekly_title, build_search_query


def test_build_weekly_title_uses_iso_week():
    assert build_weekly_title(date(2026, 5, 11)) == "Weekly GitHub Trending - 2026-W20"


def test_build_search_query_targets_open_issues_by_exact_title():
    q = build_search_query("owner/repo", "Weekly GitHub Trending - 2026-W20")
    assert q == 'repo:owner/repo is:issue is:open in:title "Weekly GitHub Trending - 2026-W20"'
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_render_markdown.py -q`
Expected: FAIL with missing functions in `scripts.create_issue`

- [ ] **Step 3: Write minimal issue publisher implementation**

Create `scripts/create_issue.py`:

```python
import argparse
import json
import os
from datetime import datetime, timezone, date
from urllib.parse import quote
from urllib.request import Request, urlopen

from scripts.render_markdown import render_issue_body


def build_weekly_title(d: date) -> str:
    iso_year, iso_week, _ = d.isocalendar()
    return f"Weekly GitHub Trending - {iso_year}-W{iso_week:02d}"


def build_search_query(repo: str, title: str) -> str:
    return f'repo:{repo} is:issue is:open in:title "{title}"'


def github_api_request(method: str, url: str, token: str, payload=None):
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def issue_exists(repo: str, token: str, title: str) -> bool:
    q = build_search_query(repo, title)
    url = f"https://api.github.com/search/issues?q={quote(q)}"
    data = github_api_request("GET", url, token)
    return data.get("total_count", 0) > 0


def create_issue(repo: str, token: str, title: str, body: str):
    url = f"https://api.github.com/repos/{repo}/issues"
    payload = {"title": title, "body": body, "labels": ["github-trending", "weekly-report"]}
    return github_api_request("POST", url, token, payload)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]

    items = json.loads(open(args.input, "r", encoding="utf-8").read())
    now = datetime.now(timezone.utc)
    title = build_weekly_title(now.date())

    if issue_exists(repo, token, title):
        print("Issue already exists for this ISO week; skipping.")
        return

    body = render_issue_body(items=items, top=args.top, generated_at=now.isoformat())

    try:
        create_issue(repo, token, title, body)
    except Exception:
        create_issue(repo, token, title, body)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/test_render_markdown.py -q`
Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add scripts/create_issue.py tests/test_render_markdown.py
git commit -m "feat: add weekly issue creation with dedupe"
```

## Task 5: End-to-end local verification and workflow wiring check

**Files:**
- Modify: `.github/workflows/weekly-trending.yml`
- Modify: `docs/superpowers/specs/2026-05-11-github-trending-design.md`

- [ ] **Step 1: Add explicit script path assumptions to workflow comments**

Update `.github/workflows/weekly-trending.yml` job steps to keep exact command lines:

```yaml
      - name: Fetch weekly trending
        run: python scripts/fetch_trending.py --top 20 --out /tmp/trending.json

      - name: Create weekly issue
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
        run: python scripts/create_issue.py --input /tmp/trending.json --top 20
```

- [ ] **Step 2: Run full local test suite for this feature**

Run: `pytest tests/test_fetch_trending.py tests/test_render_markdown.py -q`
Expected: `5 passed`

- [ ] **Step 3: Run local dry-run rendering check**

Run: `python scripts/fetch_trending.py --top 5 --out /tmp/trending.json && python - <<'PY'\nimport json\nfrom scripts.render_markdown import render_issue_body\nitems=json.load(open('/tmp/trending.json','r',encoding='utf-8'))\nprint(render_issue_body(items,5,'2026-05-11T01:00:00Z')[:300])\nPY`
Expected: output starts with `# Weekly GitHub Trending`

- [ ] **Step 4: Append implementation linkage note to spec**

Append to `docs/superpowers/specs/2026-05-11-github-trending-design.md`:

```markdown
## 11. 实施计划
- 实施计划文件：`docs/superpowers/plans/2026-05-11-github-trending-mvp-a-implementation-plan.md`
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/weekly-trending.yml docs/superpowers/specs/2026-05-11-github-trending-design.md
git commit -m "chore: finalize workflow verification and spec linkage"
```

## Task 6: Manual GitHub Actions verification checklist

**Files:**
- Modify: `docs/superpowers/specs/2026-05-11-github-trending-design.md`

- [ ] **Step 1: Push branch and trigger workflow dispatch**

Run:

```bash
git push -u origin <feature-branch>
gh workflow run weekly-trending.yml
```

Expected: workflow run is created successfully.

- [ ] **Step 2: Verify workflow run success**

Run: `gh run list --workflow weekly-trending.yml --limit 1`
Expected: latest run status `completed` and conclusion `success`

- [ ] **Step 3: Verify issue was created once**

Run: `gh issue list --search "Weekly GitHub Trending - 2026-W20" --limit 5`
Expected: exactly 1 open issue

- [ ] **Step 4: Re-run workflow and verify idempotency**

Run:

```bash
gh workflow run weekly-trending.yml
gh run list --workflow weekly-trending.yml --limit 1
```

Expected: run succeeds and issue count remains 1.

- [ ] **Step 5: Commit verification note**

Append to spec under 验证章节:

```markdown
- 已通过 workflow_dispatch 触发验证，重复触发未创建重复周报 Issue。
```

Then run:

```bash
git add docs/superpowers/specs/2026-05-11-github-trending-design.md
git commit -m "docs: record manual workflow verification results"
```

## Self-Review Checklist Results

- Spec coverage: covered scheduling, Trending parsing, issue generation, idempotency, error handling (single retry), permissions, and validation path.
- Placeholder scan: no TBD/TODO/placeholders in tasks.
- Type consistency: `parse_trending_html`, `normalize_items`, `render_issue_body`, `build_weekly_title`, and `build_search_query` are consistent across tasks.

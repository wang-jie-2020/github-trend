# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project goal
- Automate a weekly GitHub Trending report and publish it as a deduplicated GitHub Issue.

## Common commands

### Run the weekly pipeline locally
```bash
uv sync --dev
uv run python scripts/fetch_trending.py --top 20 --out /tmp/trending.json
GITHUB_TOKEN=<token> GITHUB_REPOSITORY=<owner/repo> uv run python scripts/create_issue.py --input /tmp/trending.json --top 20
```

### Run tests
```bash
uv run pytest -q
uv run pytest tests/test_fetch_trending.py -q
uv run pytest tests/test_render_markdown.py -q
uv run pytest tests/test_render_markdown.py::test_build_weekly_title_uses_iso_week -q
```

### Build / lint
- No dedicated build or lint command is configured in this repository yet.
- Primary verification is test execution (`pytest`).
- Dependency management uses `uv` (`uv.lock`, `uv sync`).

## Architecture overview

### 1) Workflow orchestration
- `.github/workflows/weekly-trending.yml` schedules execution at `0 1 * * 1` (UTC Monday) and supports `workflow_dispatch`.
- The workflow runs two scripts in order: fetch trending data, then create/publish the issue.

### 2) Data acquisition and normalization
- `scripts/fetch_trending.py` fetches `https://github.com/trending?since=weekly` and parses HTML using `html.parser.HTMLParser`.
- `TrendingParser` extracts repository metadata from `article.Box-row` blocks.
- `normalize_items()` converts parsed rows to a stable schema used downstream:
  - `source`, `rank`, `repo`, `url`, `summary`, `language`, `stars`, `forks`
- Output is written as JSON (`--out`) for the publisher step.

### 3) Rendering and publishing
- `scripts/render_markdown.py` is a pure renderer that builds the final issue markdown table/body.
- `scripts/create_issue.py`:
  - builds ISO-week title via `build_weekly_title()`
  - checks for existing open weekly issue via GitHub Search API (`issue_exists`) to ensure idempotency
  - creates issue via GitHub REST API with labels `github-trending` and `weekly-report`
- Required environment variables for publishing:
  - `GITHUB_TOKEN`
  - `GITHUB_REPOSITORY`

### 4) Tests and fixtures
- `tests/test_fetch_trending.py` validates parser extraction and normalization against fixtures.
- `tests/test_render_markdown.py` validates markdown output and weekly title/search-query helpers.
- `tests/fixtures/trending_sample.html` and `tests/fixtures/trending_expected.json` provide deterministic parser expectations.

## Design references
- `docs/superpowers/specs/2026-05-11-github-trending-design.md`
- `docs/superpowers/plans/2026-05-11-github-trending-mvp-a-implementation-plan.md`

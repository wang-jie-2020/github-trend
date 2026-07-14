---
name: github-weekly-trending
description: Generate a dated local split-card HTML reader for weekly GitHub Trending repositories using collection JSON, Claude-driven README summaries, and a deterministic renderer.
---

# GitHub Weekly Trending HTML Reader

Generate a standalone local HTML reader for weekly GitHub Trending repositories.

This skill is separate from the repository's existing GitHub Issue publishing pipeline. It does not publish, host, archive, or create Issues. Its only final artifact is a local `trending.html` file.

## Workflow

The workflow has three stages:

1. **Collect** weekly GitHub Trending repositories and GitHub API metadata into `collection.json`.
2. **Summarize** each repository README in the current Claude Code session and write structured summaries to `summaries.json`.
3. **Render** deterministic standalone HTML from `collection.json` and `summaries.json`.

Use a dated output directory:

```text
htmls/github-weekly-trending-YYYYMMDD/
```

Same-day reruns reuse and overwrite the same dated directory. The directory contains:

```text
collection.json
summaries.json
trending.html
```

## Collection stage

Run collection into the dated output directory:

```bash
uv run python -m scripts.collect_trending_metadata --top 20 --out-dir htmls/github-weekly-trending-YYYYMMDD
```

Use a smaller Top N for manual smoke tests, for example `--top 3`.

The collector:

- Discovers repositories from `https://github.com/trending?since=weekly` in rank order.
- Enriches each repository with GitHub repository metadata.
- Prefers locally authenticated `gh api`.
- Falls back to token REST API access using `GITHUB_TOKEN`, then `DEPLOY_TOKEN`.
- Fails clearly if neither GitHub API route works.
- Does not write README source text, README paths, open issue data, or owner type.

### `collection.json` contract

Top-level object:

```json
{
  "source_url": "https://github.com/trending?since=weekly",
  "since": "weekly",
  "collected_at": "2026-07-14T00:00:00Z",
  "top": 20,
  "repositories": []
}
```

Each repository record must contain:

- `rank`
- `repo`
- `url`
- `trending_description`
- `api_description`
- `language`
- `stars`
- `forks`
- `topics`
- `license`
- `homepage`
- `pushed_timestamp`
- `latest_release`

The collection contract explicitly excludes:

- README source text
- README paths
- open issues / open issue counts
- owner type

## Summarization stage

Read `collection.json`, then fetch each repository README on demand in the current Claude Code session. Summarize the README content, discard the source text, and write only `summaries.json` into the same dated output directory.

Do not implement or call a Python script that uses the Claude API for summarization. The current Claude Code session performs the reading and summarization.

### `summaries.json` contract

Top-level object:

```json
{
  "summaries": [
    {
      "repo": "owner/name",
      "readme_status": "ok",
      "readme_error": null,
      "summary": "One sentence explaining what the project is.",
      "why_it_matters": "Why this repository is worth attention this week.",
      "best_for": "Who should look at or use the project.",
      "key_points": [
        "First concise point.",
        "Second concise point.",
        "Third concise point."
      ]
    }
  ]
}
```

Rules:

- There must be exactly one summary record per collected repository.
- No summary records should exist for repositories outside `collection.json`.
- `key_points` must contain exactly three non-empty concise bullets.
- README source text is never stored in `summaries.json`.
- Missing README content must be represented explicitly with `readme_status: "missing"` and a non-empty `readme_error`.
- Unreadable README content must be represented explicitly with `readme_status: "unreadable"` and a non-empty `readme_error`.

## Render stage

Run the renderer from the dated output directory:

```bash
uv run python -m scripts.render_trending_html --input-dir htmls/github-weekly-trending-YYYYMMDD
```

The renderer reads `collection.json` and `summaries.json`, validates both contracts, and writes:

```text
htmls/github-weekly-trending-YYYYMMDD/trending.html
```

Report the final path clearly. When appropriate, suggest opening the file in a browser to manually verify keyboard navigation, single-card readability, and responsive layout.

## Visual spec

The confirmed visual direction is a full-screen split-card reader:

- One repository per full-screen card/slide.
- Two-column desktop layout.
- Left side: rank, repository link/name, language, stars, forks.
- Right side: README-derived summary, why-it-matters, best-for, three key points, topics, license, homepage, pushed timestamp, and latest release metadata when available.
- Keyboard navigation between cards.
- Responsive stacked layout on narrow screens.
- Light, low-saturation page palette.
- White card surface.
- Subtle hairline borders.
- Rounded corners.
- Restrained system typography.

The visual direction explicitly rejects:

- Flat list layouts.
- Dense table layouts.
- Dark terminal styling.
- Generic Bento grids.
- Warm editorial serif styling.
- AI-gradient visual clichés.

Use `htmls/v4-split-card-mock.html` only as a design reference. It is not the production schema and may contain fields that are excluded from this skill's contracts.

## Verification

Run focused tests after changing each seam:

```bash
uv run python -m pytest tests/test_trending_html_contracts.py -q
uv run python -m pytest tests/test_collect_trending_metadata.py -q
uv run python -m pytest tests/test_render_trending_html.py -q
```

Then run the full suite:

```bash
uv run python -m pytest -q
```

Unit tests must not call the live GitHub API. Use fixtures or injected fakes for collector behavior.

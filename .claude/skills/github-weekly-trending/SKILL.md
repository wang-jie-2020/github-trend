---
name: github-weekly-trending
description: Use when the user wants a weekly GitHub Trending HTML reader/report: collect Trending metadata, summarize READMEs in-session, and render dated split-card `trending.html`.
---

# GitHub Weekly Trending HTML Reader

Generate a standalone local HTML reader for weekly GitHub Trending repositories.
Does not publish, host, create Issues, or interact with the existing Issue pipeline.
Sole artifact: a local `trending.html`.

Full contracts live in [`references/schema.md`](references/schema.md).

## Steps

### 1. Pick output directory

Use a dated directory:

```
htmls/github-weekly-trending-YYYYMMDD/
```

Same-day reruns reuse and overwrite the same directory.

**Completion:** the output directory exists and is empty, or contains artifacts from a prior same-day run.

### 2. Collect metadata

```bash
uv run python scripts/collect_trending_metadata.py --top 20 --out-dir htmls/github-weekly-trending-YYYYMMDD
```

Use `--top 3` for smoke tests. The collector discovers Trending repos, enriches with GitHub API metadata, prefers `gh api` over token REST, and fails clearly if no route works.

**Completion:** `collection.json` exists in the output directory and its `repositories` array has exactly the expected top-N count.

### 3. Summarize READMEs

Read `collection.json`. Fetch each repository README on demand in this Claude Code session.
Summarize each, discard source text, write `summaries.json`.

Do not call an external Claude API script — this session does the reading and summarization.

**Completion:** `summaries.json` has exactly one summary record per collected repository, every `key_points` array has three non-empty bullets, and no summary exists for a repo outside `collection.json`.

### 4. Render HTML

```bash
uv run python scripts/render_trending_html.py --input-dir htmls/github-weekly-trending-YYYYMMDD
```

**Completion:** `trending.html` exists and was generated without contract validation errors.

### 5. Report

**Completion:** Report the final `trending.html` path. When appropriate, suggest opening the file in a browser.

## Visual spec

Full-screen split-card reader. One repo per card.

- Two-column desktop; left: rank, repo, language, stars, forks; right: summary, why-it-matters, best-for, key points, metadata.
- Keyboard navigation.
- Responsive stacked layout on narrow screens.
- Light low-saturation palette, white card surface, subtle hairline borders, rounded corners, restrained system typography.

Rejects: flat lists, dense tables, dark terminal styling, Bento grids, warm editorial serif, AI-gradient clichés.

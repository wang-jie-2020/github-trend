# GitHub Weekly Trending HTML Reader contract

This reference is the single source of truth for the local HTML reader data contracts. The active workflow is three-stage:

1. Collect weekly Trending metadata into `collection.json`.
2. Summarize READMEs in the current Claude Code session into `summaries.json`.
3. Render deterministic standalone HTML into `trending.html`.

The skill does not use a one-pass script that fetches Trending HTML and renders cards directly.

## Output directory

Use one dated directory per run date:

```text
htmls/github-weekly-trending-YYYYMMDD/
```

Same-day reruns reuse and overwrite the same directory. The directory contains:

```text
collection.json
summaries.json
trending.html
```

## `collection.json`

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

| Field | Meaning |
|---|---|
| `rank` | Rank from weekly Trending order. |
| `repo` | Repository full name, `owner/name`. |
| `url` | Repository URL. |
| `trending_description` | Description shown on GitHub Trending. |
| `api_description` | Description from the GitHub repository API. |
| `language` | Primary language, or null when unavailable. |
| `stars` | Stargazer count. |
| `forks` | Fork count. |
| `topics` | Repository topics array. |
| `license` | License name or null. |
| `homepage` | Homepage URL or null. |
| `pushed_timestamp` | Latest pushed timestamp from the repository API. |
| `latest_release` | Latest release metadata or null. |

The collection contract explicitly excludes:

- README source text
- README paths
- open issues / open issue counts
- owner type

## `summaries.json`

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

## `trending.html`

The renderer reads `collection.json` and `summaries.json`, validates both contracts, and writes:

```text
htmls/github-weekly-trending-YYYYMMDD/trending.html
```

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

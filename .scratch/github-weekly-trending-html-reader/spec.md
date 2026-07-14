Status: ready-for-agent

# GitHub Weekly Trending HTML Reader Skill

## Problem Statement

The current GitHub Trending weekly data is hard to read in depth. The raw Trending Page is optimized for scanning a list, while this project needs a generated HTML artifact that helps a reader understand each repository one at a time, with enough context to decide whether it is worth opening.

A simple visual conversion of Trending rows into HTML is not valuable. Without additional repository metadata and README-derived explanation, the result is only a restyled list. The user wants a polished, readable HTML output where each repository becomes a focused card with general metrics on one side and AI-distilled context on the other.

## Solution

Create a `github-weekly-trending` skill workflow that generates a standalone HTML reader for GitHub Trending weekly repositories.

The workflow has three distinct responsibilities:

1. Collect Trending repositories and GitHub API metadata into structured data.
2. Use the current Claude Code session to read repository READMEs and produce structured summaries.
3. Render the confirmed split-card visual direction into a stable HTML artifact from structured data and summaries.

The generated HTML is a local artifact. The skill does not publish, host, archive, or create Issues. Any later use of the HTML is outside this skill's responsibility.

## User Stories

1. As a developer, I want GitHub Trending converted into a readable HTML artifact, so that I can review weekly repositories without scanning the raw Trending Page.
2. As a developer, I want one repository shown per card, so that I can focus on understanding one project at a time.
3. As a developer, I want the card split into general information and detailed reading content, so that I can separate quick facts from deeper context.
4. As a developer, I want each card to show rank, repository name, language, stars, and forks, so that I can orient myself quickly.
5. As a developer, I want the card to include AI-distilled README content, so that I can understand what the repository does without opening GitHub.
6. As a developer, I want the README summary to be structured, so that every card is consistent and easy to compare.
7. As a developer, I want repository topics, license, homepage, update time, and latest release metadata when available, so that I can understand maturity and relevance.
8. As a developer, I want the HTML to be visually polished, so that reading the weekly report feels intentional rather than like a data dump.
9. As a developer, I want to navigate between repositories with keyboard controls, so that I can read the report efficiently.
10. As a developer, I want output artifacts grouped by run date, so that each day's generated report is easy to find.
11. As a developer, I want same-day reruns to overwrite the same dated output directory, so that iteration does not create noisy duplicate folders.
12. As a maintainer, I want metadata collection separated from rendering, so that API behavior and visual output can be changed independently.
13. As a maintainer, I want AI summarization separated from rendering, so that the template stays deterministic while README interpretation remains flexible.
14. As a maintainer, I want the visual style captured as a written visual spec, so that future agents can preserve the confirmed direction instead of re-inventing the UI.
15. As a maintainer, I want the renderer to consume structured JSON files, so that visual output is repeatable and testable.
16. As a maintainer, I want the skill to prefer the locally authenticated GitHub CLI, so that it can use existing local credentials without extra token setup.
17. As a maintainer, I want token fallback for GitHub API calls, so that the skill can still run in environments without an authenticated GitHub CLI.
18. As a maintainer, I want the workflow to fail clearly if GitHub metadata cannot be fetched, so that it does not produce a misleading incomplete report.
19. As a maintainer, I want README source text not to be stored by default, so that large READMEs do not create noisy artifacts or context-heavy JSON files.
20. As a maintainer, I want only AI summaries persisted, so that styling can be rerun without repeating every README summarization.
21. As a future agent, I want explicit schemas for collection data and summaries, so that I can implement without reinterpreting conversation history.
22. As a future agent, I want the confirmed visual direction documented separately from implementation code, so that I can update the renderer while preserving design intent.

## Implementation Decisions

- The feature is implemented as a project skill named `github-weekly-trending`.
- The skill is scoped to generating a standalone HTML file. It does not publish, host, archive, or create GitHub Issues.
- The existing repository weekly Issue pipeline remains separate from this skill.
- The skill workflow is split into three stages: collect, summarize, render.
- The collection stage discovers repositories from the GitHub Trending weekly page and enriches them with GitHub repository metadata.
- GitHub API access prefers the local `gh` CLI when available and authenticated.
- If `gh` cannot be used, GitHub API access falls back to environment tokens such as `GITHUB_TOKEN` or `DEPLOY_TOKEN`.
- If neither GitHub API route is available, the workflow fails clearly rather than generating a fake complete HTML artifact.
- Repository README content is not stored in the collection JSON and is not persisted by default.
- README content is fetched during the summarization stage, handed to the current Claude Code session, summarized, and discarded.
- AI summarization is a required step. The HTML reader is not considered useful without README-derived context.
- The summarization stage is performed by Claude Code in the current session, not by a Python script calling the Claude API.
- The collection stage produces repository metadata only.
- The summarization stage produces one structured summary per repository.
- The render stage reads repository metadata and structured summaries, then emits a deterministic HTML file.
- The visual style description is separated from the renderer implementation. The renderer executes a confirmed visual spec instead of letting Claude freely generate HTML each time.
- The confirmed visual direction is a full-screen card reader with one repository per slide.
- Each card uses a two-column layout: general facts on the left, detailed context on the right.
- The left side contains rank, repository link, language, stars, and forks.
- The right side contains AI summary content plus selected GitHub metadata.
- The visual direction uses a light, low-saturation palette, a white card surface, subtle hairline borders, rounded corners, and restrained typography.
- The visual direction avoids flat list layouts, dense table layouts, dark terminal styling, generic Bento grids, warm editorial serif styling, and AI-gradient visual clichés.
- Output directories are date-based and use `YYYYMMDD` granularity.
- Same-day reruns overwrite the same dated output directory.
- The dated output directory contains the collection JSON, summary JSON, and final HTML file.
- The collection script receives an explicit output directory from the skill workflow instead of deciding naming policy itself.
- The render script receives an explicit input directory and reads the known JSON artifacts from that directory.

### Collection Data Shape

The collection artifact contains one record per repository with these fields:

- rank
- repo
- url
- trending description
- API description
- language
- stars
- forks
- topics
- license
- homepage
- pushed timestamp
- latest release metadata

It does not contain README text, README paths, open issues, or owner type.

### Summary Data Shape

The summary artifact contains one record per repository with these fields:

- repo
- summary: one sentence explaining what the project is
- why it matters: why this repository is worth attention this week
- best for: who should look at or use the project
- key points: three concise bullets

### Visual Prototype Decision

A prototype established the accepted visual direction: a full-screen split-card reader with keyboard navigation. The prototype is a reference artifact for design intent, not production code. The production renderer should implement the same direction with structured data.

## Testing Decisions

Tests should validate external behavior and stable artifact contracts, not internal implementation details.

Primary test seams:

1. Collection seam: given representative Trending and GitHub API responses, the collector writes valid metadata JSON.
2. Summary seam: given repository README content, the summarization output conforms to the agreed summary schema.
3. Render seam: given metadata JSON and summaries JSON, the renderer produces an HTML file containing the expected repository cards, navigation elements, and summary sections.

The highest-value seam is the render seam because the user's confirmed goal is the final readable HTML artifact.

Testing decisions:

- Use fixtures for collected metadata and summary JSON.
- Test that rendered HTML contains repository links, rank, language, stars, forks, summary, why-it-matters, best-for, key points, and metadata fields.
- Test that the renderer does not require network access.
- Test that the renderer is deterministic for the same input files.
- Test that missing summaries fail clearly rather than silently omitting AI content.
- Test that missing optional metadata renders a clear placeholder or omitted detail according to the visual spec.
- Test that the collector can be exercised with mocked GitHub API responses.
- Do not test live GitHub API behavior in unit tests.
- Manual verification should open the generated HTML in a browser and check keyboard navigation, single-card readability, and responsive layout.

Existing prior art in the repository:

- Parser and normalization tests use fixtures for GitHub Trending HTML.
- Markdown rendering tests validate output text from structured input.
- The new renderer should follow the same pattern: fixture input, deterministic output assertions.

## Out of Scope

- Publishing or hosting the generated HTML.
- Creating GitHub Issues from the generated HTML.
- Replacing the existing weekly Issue workflow.
- Storing README source text by default.
- Calling the Claude API directly from Python.
- Fully automated unattended README summarization.
- Historical analytics, charts, trend deltas, or star-growth analysis.
- GitHub owner type and open issue count.
- Multi-source aggregation beyond GitHub Trending weekly.
- Dark terminal, dense leaderboard, Bento grid, or magazine-style visual alternatives.

## Further Notes

- Existing domain glossary: `CONTEXT.md`
- Existing architecture decisions: `docs/adr/`
- Existing weekly report spec: `docs/specs/weekly-trending-report.md`
- Current project skill folder: `.claude/skills/github-weekly-trending/`
- Confirmed visual prototype: `htmls/v4-split-card-mock.html`
- Local issue tracker convention: `docs/agents/issue-tracker.md`

## Comments

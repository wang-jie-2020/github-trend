# 02 — Render fixture data into the split-card HTML reader

**What to build:** Given fixture collection data and fixture README summaries, generate a standalone `trending.html` that implements the confirmed split-card reader: one repository per full-screen card, left-side general facts, right-side AI summary and repository metadata, keyboard navigation, and readable responsive layout.

**Blocked by:** 01 — Lock the HTML reader contracts and visual spec.

**Status:** ready-for-agent

- [ ] The renderer reads collection data and summary data from a supplied input directory.
- [ ] The renderer writes a standalone HTML file into the same input directory.
- [ ] The rendered HTML contains one full-screen card per repository.
- [ ] Each card shows rank, repository link, language, stars, and forks on the general-information side.
- [ ] Each card shows summary, why-it-matters, best-for, key points, and selected metadata on the detail side.
- [ ] The HTML includes keyboard navigation between cards.
- [ ] The renderer is deterministic for the same input files.
- [ ] Tests or fixture-based verification cover the rendered output without network access.

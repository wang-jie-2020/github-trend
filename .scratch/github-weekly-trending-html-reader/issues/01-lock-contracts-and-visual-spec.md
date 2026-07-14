# 01 — Lock the HTML reader contracts and visual spec

**What to build:** Capture the agreed contracts for the GitHub Weekly Trending HTML reader so future implementation agents can work from stable written agreements instead of conversation history. This includes the collection data contract, summary contract, dated output directory convention, split-card visual direction, and the three-stage skill workflow.

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] The skill documentation describes the collect → summarize → render workflow.
- [ ] The collection data contract is documented and excludes README source text, README paths, open issues, and owner type.
- [ ] The summary contract is documented with `repo`, `summary`, `why_it_matters`, `best_for`, and three `key_points`.
- [ ] The output directory convention is documented as `htmls/github-weekly-trending-YYYYMMDD/`, with same-day reruns overwriting the same directory.
- [ ] The confirmed split-card visual direction is documented separately from renderer implementation.
- [ ] The visual direction explicitly rules out the rejected flat list, dense table, dark terminal, generic Bento, warm editorial serif, and AI-gradient styles.

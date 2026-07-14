# 04 — Produce summaries.json with Claude-driven README summarization

**What to build:** From a collected repository metadata file, use the current Claude Code session to fetch each repository README on demand, produce structured summaries, and write a summary data file. README source text is not stored by default; only the distilled summaries are persisted.

**Blocked by:** 01 — Lock the HTML reader contracts and visual spec; 03 — Collect Trending repository metadata into a dated output directory.

**Status:** ready-for-agent

- [ ] The skill workflow instructs Claude to fetch README content for each collected repository on demand.
- [ ] README source text is summarized and then discarded rather than stored as an artifact.
- [ ] The generated summary data matches the documented summary contract.
- [ ] Each repository summary includes `summary`, `why_it_matters`, `best_for`, and exactly three `key_points`.
- [ ] Missing or unreadable README content is handled explicitly rather than silently omitted.
- [ ] The summary data is written into the same dated output directory as the collection data.
- [ ] The summarization workflow does not require a Python script to call the Claude API.
- [ ] A fixture or dry-run example demonstrates the expected summary data shape.

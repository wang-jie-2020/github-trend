# 05 — Wire the full github-weekly-trending skill workflow

**What to build:** Connect the documentation and scripts into a complete `/github-weekly-trending` workflow that creates a dated output directory, collects repository metadata, produces Claude-driven README summaries, renders the final split-card HTML reader, and opens or reports the final artifact path.

**Blocked by:** 02 — Render fixture data into the split-card HTML reader; 03 — Collect Trending repository metadata into a dated output directory; 04 — Produce summaries.json with Claude-driven README summarization.

**Status:** ready-for-agent

- [ ] The skill documentation describes the complete user-facing workflow from invocation to final HTML artifact.
- [ ] The workflow creates or selects `htmls/github-weekly-trending-YYYYMMDD/` before running scripts.
- [ ] The workflow runs collection into the dated output directory.
- [ ] The workflow produces summary data in the same dated output directory.
- [ ] The workflow runs rendering from the dated output directory.
- [ ] The final HTML matches the confirmed split-card visual direction.
- [ ] The workflow reports the final HTML path clearly.
- [ ] The workflow can be manually verified end-to-end with a small Top N value.

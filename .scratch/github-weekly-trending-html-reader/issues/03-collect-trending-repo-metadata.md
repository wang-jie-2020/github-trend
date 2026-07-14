# 03 — Collect Trending repository metadata into a dated output directory

**What to build:** Collect the weekly GitHub Trending repositories and enrich each repository with GitHub API metadata, producing a collection data file in a caller-supplied output directory. The collector should prefer the locally authenticated GitHub CLI and fall back to token-based REST API access.

**Blocked by:** 01 — Lock the HTML reader contracts and visual spec.

**Status:** ready-for-agent

- [ ] The collector accepts a Top N value and an explicit output directory.
- [ ] The collector creates the output directory if it does not exist.
- [ ] The collector discovers repositories from GitHub Trending weekly in rank order.
- [ ] The collector enriches each repository with API description, topics, license, homepage, pushed timestamp, and latest release metadata when available.
- [ ] The collector writes collection data matching the documented contract.
- [ ] The collector does not write README source text or README paths into the collection data.
- [ ] GitHub API access prefers `gh api` when available and authenticated.
- [ ] GitHub API access falls back to environment token-based REST API access.
- [ ] If neither API route is available, the collector fails clearly instead of producing incomplete data.
- [ ] Tests or fixture-based verification cover successful collection and API unavailability behavior without requiring live GitHub API calls.

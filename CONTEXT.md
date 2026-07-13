# GitHub Trend

This context defines the language for collecting GitHub Trending entries and turning them into lightweight internal distribution artifacts.

## Language

**Weekly GitHub Trending**:
The weekly GitHub Trending source this project collects and reports on.
_Avoid_: GitHub search results, repository discovery feed

**Trending Item**:
A normalized repository entry from Weekly GitHub Trending, including its rank, repository name, URL, summary, language, stars, and forks.
_Avoid_: Raw HTML row, repo blob

**Attention Signal**:
The assumption that a repository's appearance and rank in Weekly GitHub Trending is enough to justify lightweight internal attention.
_Avoid_: Expert recommendation, technical due diligence

**Weekly Issue**:
A GitHub Issue that publishes one week's Trending Items as a Markdown report.
_Avoid_: Ticket, task, discussion thread

**ISO Week Deduplication**:
The rule that prevents more than one Weekly Issue from being created for the same ISO week.
_Avoid_: Duplicate check, retry protection

**Trending HTML Snapshot**:
A lightweight, standalone HTML artifact that presents GitHub Trend materials outside the GitHub repository and issue-reading experience.
_Avoid_: Expert report, recommendation memo, reporting system

**GitHub Trend HTML Snapshot Skill**:
A Codex skill dedicated to producing Trending HTML Snapshots from GitHub Trend materials.
_Avoid_: Generic HTML generator, trend analysis agent

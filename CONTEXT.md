# CONTEXT.md

GitHub Trending 周报自动化项目的领域模型与统一语言。

## 术语表 (Ubiquitous Language)

| 术语 | 定义 |
|---|---|
| **Trending Page** | GitHub 的 `https://github.com/trending?since=weekly` 页面，整个 pipeline 的唯一数据源 |
| **RepoItem** | HTML 解析器从 Trending Page 提取的原始仓库条目：`repo`, `description`, `language`, `stars`, `forks` |
| **Normalized Item** | 标准化后的仓库条目，供下游消费：`source`, `rank`, `repo`, `url`, `summary`, `language`, `stars`, `forks` |
| **Source** | 数据来源标识。当前固定为 `"trending"`；预留给 Search API 扩展（B 阶段）时新增 `"search_api"` 源 |
| **ISO Week** | Issue 去重的边界单位：同一 ISO 周只保留一条周报 Issue，通过标题精确匹配实现 |
| **Weekly Report** | 最终产物——一条带 `github-trending`、`weekly-report` 标签的 GitHub Issue，包含该周 Top N 仓库的 Markdown 表格 |

## 架构

```
GitHub Actions (cron / workflow_dispatch)
  └─ fetch_trending.py  →  拉取并解析 Trending Page → JSON
  └─ create_issue.py    →  查重 + 渲染 Markdown + 创建 Issue
       └─ render_markdown.py  →  纯 Markdown 渲染
```

## 参考

- Spec：`docs/specs/weekly-trending-report.md`
- ADR：`docs/adr/`

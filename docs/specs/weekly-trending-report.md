# Weekly GitHub Trending 周报自动化

## Problem Statement

团队需要每周了解 GitHub 上哪些仓库在社区里上升最快。手动刷 `github.com/trending` 既费时间又不留档——每次看的结果无法回溯。

## Solution

全自动周报系统：每周一早上 9:00（Asia/Shanghai）抓取 GitHub Trending 周榜，生成去重后的 GitHub Issue，包含 Top N 仓库的 Markdown 表格（仓库名、语言、stars、forks、简介）。团队直接在 Issue 里浏览和回溯。

## User Stories

1. As a 团队成员, I want 每周一早上自动收到一条 Trending 周报 Issue, so that 无需手动刷新 GitHub Trending 页面。
2. As a 团队成员, I want 周报 Issue 包含仓库名、语言、stars、forks 和简介的表格, so that 能快速判断哪些仓库值得关注。
3. As a 维护者, I want 同一周重复触发不会创建重复 Issue, so that 无需手动清理。
4. As a 维护者, I want 能手动触发 workflow 来调试或补发周报, so that 不依赖 cron 也能验证 pipeline。
5. As a 维护者, I want 解析失败时 workflow 明确报错, so that 第一时间知道 GitHub 页面结构变了。
6. As a 开发者, I want 渲染逻辑独立于发布逻辑, so that 可单独测试 Markdown 输出。
7. As a 开发者, I want 解析逻辑有 fixture 测试覆盖, so that 修改解析器时不会引入回归。

## Implementation Decisions

### 数据获取：HTML 解析

GitHub 不提供 Trending 官方 API。用 `html.parser.HTMLParser` 解析 `github.com/trending?since=weekly` 页面的 `<article class="Box-row">` 块。解析失败直接让 workflow 失败——不静默降级。（见 ADR-0001）

### 去重策略：ISO Week 标题匹配

去重以 ISO Week 为边界，不引入外部存储。Issue 标题 `Weekly GitHub Trending - <ISO_YEAR>-W<ISO_WEEK>`，创建前通过 GitHub Search API 查询同标题 open Issue。（见 ADR-0002）

### 认证：DEPLOY_TOKEN

用 `DEPLOY_TOKEN` secret 而非内置 `GITHUB_TOKEN`——Search API 对后者有速率限制。

### 依赖管理：uv + python-dotenv

`uv` 管理依赖和 lockfile。唯一第三方依赖 `python-dotenv` 用于本地开发加载 `.env`。

### 模块划分

- **采集层** (`fetch_trending`): HTML 拉取 → `TrendingParser` 解析 → `normalize_items()` 标准化 → JSON
- **渲染层** (`render_markdown`): 纯函数，条目列表入，Markdown 出
- **发布层** (`create_issue`): ISO 周标题 → 去重检查 → 渲染 → Issue 创建
- **调度层** (`.github/workflows/weekly-trending.yml`): cron 周一 01:00 UTC = 09:00 Asia/Shanghai + `workflow_dispatch`

### 数据结构

Normalized Item（采集层与渲染层之间的 JSON 桥接）:
```json
{
  "source": "trending",
  "rank": 1,
  "repo": "owner/name",
  "url": "https://github.com/owner/name",
  "summary": "...",
  "language": "Python",
  "stars": 1234,
  "forks": 56
}
```
`source` 留给 Search API 扩展（B 阶段）时用 `"search_api"` 区分。

## Testing Decisions

**只测试外部行为，不测试实现细节。** 测试挂在模块入口函数上，不 mock 内部状态。

已有测试接缝：
- `parse_trending_html()` + `normalize_items()` — HTML fixture → JSON 输出
- `render_issue_body()` — 条目列表 → Markdown 文本
- `build_weekly_title()` — 日期 → ISO 周标题
- `build_search_query()` — repo + title → GitHub Search 查询语法

不测试 HTTP 请求或 GitHub API 调用——这些由 workflow dispatch 手动验证。

## Out of Scope

- 飞书/钉钉/Slack 推送
- 历史统计与可视化
- 多仓库聚合
- Search API 自定义榜单（B 阶段）
- Issue 中嵌入图表

## References

- 领域模型：`CONTEXT.md`
- ADR：`docs/adr/0001-html-parsing-for-trending-data.md`、`docs/adr/0002-iso-week-issue-deduplication.md`

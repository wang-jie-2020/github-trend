# ADR-0001: HTML 解析获取 Trending 数据

**日期**：2026-05-11  
**状态**：已采纳

## 背景

GitHub 不提供 Trending 页面的官方 API。需要一种方式获取 `github.com/trending?since=weekly` 页面的仓库列表数据。

## 决策

使用 Python stdlib 的 `html.parser.HTMLParser` 直接解析 Trending 页面的 HTML。

```python
# scripts/fetch_trending.py:22
class TrendingParser(HTMLParser):
    ...
```

解析目标为 `<article class="Box-row">` 块，从中提取 repo 路径、description、language、stars、forks。

## 后果

- **正面**：无外部依赖，不依赖第三方 API，维护成本低
- **负面**：依赖 GitHub 页面 DOM 结构，结构变化会导致解析失败；需提供 HTML fixture 测试覆盖
- **缓解**：`tests/fixtures/trending_sample.html` 提供可更新的 fixture；解析失败时任务直接报错，不静默降级

# ADR-0002: ISO Week 作为 Issue 去重依据

**日期**：2026-05-11  
**状态**：已采纳

## 背景

每周一自动创建周报 Issue。需要确保同一周重复触发不会产生重复 Issue。

## 决策

以 ISO Week 作为去重边界：Issue 标题固定为 `Weekly GitHub Trending - <ISO_YEAR>-W<ISO_WEEK>`，创建前通过 GitHub Search API 检索是否存在同标题的 open Issue。

```python
# scripts/create_issue.py:16-18
def build_weekly_title(d: date) -> str:
    iso_year, iso_week, _ = d.isocalendar()
    return f"Weekly GitHub Trending - {iso_year}-W{iso_week:02d}"

# scripts/create_issue.py:41-45
def issue_exists(repo: str, token: str, title: str) -> bool:
    q = build_search_query(repo, title)
    url = f"https://api.github.com/search/issues?q={quote(q)}"
    data = github_api_request("GET", url, token)
    return data.get("total_count", 0) > 0
```

## 后果

- **正面**：无需外部存储或状态记录，GitHub Search API 本身就是 truth source
- **正面**：属人可读——通过 Issue 标题即可识别归属周
- **负面**：如果手动修改过 Issue 标题，则无法幂等保护
- **约定**：周报 Issue 标题不可手动修改

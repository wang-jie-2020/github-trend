# GitHub Trending Weekly Report

自动抓取 GitHub Trending（weekly），渲染为 Markdown，并以“按 ISO 周去重”的方式发布为 GitHub Issue。

## 功能

- 抓取 `https://github.com/trending?since=weekly`
- 解析并标准化仓库信息（repo、language、stars、forks、summary）
- 生成周报 Issue 内容（Markdown 表格）
- 按 ISO 周标题去重，避免重复创建同周 Issue
- GitHub Actions 每周自动执行（支持手动触发）

## 项目结构

- `scripts/fetch_trending.py`：抓取与解析 Trending 页面，输出标准 JSON
- `scripts/render_markdown.py`：将标准数据渲染为 Issue Markdown
- `scripts/create_issue.py`：检查是否已存在本周 Issue，不存在则创建
- `.github/workflows/weekly-trending.yml`：每周调度入口
- `tests/`：解析、标准化、渲染与标题/查询逻辑测试

## 环境要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## 快速开始（uv）

```bash
uv sync --dev
```

### 本地执行完整流程

```bash
uv run python scripts/fetch_trending.py --top 20 --out /tmp/trending.json
GITHUB_TOKEN=<token> GITHUB_REPOSITORY=<owner/repo> uv run python scripts/create_issue.py --input /tmp/trending.json --top 20
```

> `GITHUB_TOKEN` 需要具备创建 issue 权限；`GITHUB_REPOSITORY` 形如 `owner/repo`。

## 测试

```bash
uv run pytest -q
uv run pytest tests/test_fetch_trending.py -q
uv run pytest tests/test_render_markdown.py -q
```

## GitHub Actions

工作流文件：`.github/workflows/weekly-trending.yml`

- 定时：每周一 UTC 01:00（`0 1 * * 1`）
- 也支持 `workflow_dispatch` 手动触发

默认使用 `secrets.GITHUB_TOKEN` 和 `${{ github.repository }}` 创建 issue。

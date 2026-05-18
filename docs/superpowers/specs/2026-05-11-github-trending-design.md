# GitHub 每周趋势榜自动化设计（先 A 后 B）

## 1. 背景
需要在仓库内实现一个每周自动任务：抓取 GitHub Trending 周榜（A），并自动发布为 GitHub Issue。第一阶段优先跑通闭环；第二阶段再加入 GitHub Search API 自定义榜单（B）。

## 2. 目标与成功标准
### 目标
- 每周一 09:00（Asia/Shanghai）自动执行。
- 抓取 GitHub Trending 的 weekly 榜单并生成可读周报。
- 自动创建一条周报 Issue，便于团队查看和留档。

### 成功标准
- 手动触发 workflow 能稳定创建 Issue。
- 定时触发后可自动生成当周 Issue。
- 同一周不会重复创建 Issue。

## 3. 范围
### 本期范围（A）
- GitHub Actions 定时执行。
- 抓取并解析 GitHub Trending weekly 页面。
- 生成 Markdown 榜单内容（Top N，默认 20）。
- 创建 Issue（含标题、正文、labels）。

### 暂不做
- 飞书/钉钉/Slack 推送。
- 复杂历史统计与可视化。
- 多仓库聚合。

## 4. 总体架构
- 调度层：`.github/workflows/weekly-trending.yml`
- 采集层：`scripts/fetch_trending.py`
- 发布层：`scripts/create_issue.py`
- 可选配置层：`config/trending.yml`

数据流：
1. workflow 在 cron 或手动触发时启动。
2. `fetch_trending.py` 拉取并解析 weekly 榜单。
3. 生成 Markdown 报告文本。
4. `create_issue.py` 检查是否已有当周 Issue；若无则创建。

## 5. 关键设计
### 5.1 调度
- GitHub Actions `schedule` 使用 UTC：`0 1 * * 1`（对应 Asia/Shanghai 周一 09:00）。
- 同时保留 `workflow_dispatch` 用于调试和回归验证。

### 5.2 抓取与解析（A）
- 目标页面：`https://github.com/trending?since=weekly`
- 解析字段（尽量提取，缺失时留空）：
  - `rank`
  - `repo`（owner/name）
  - `url`
  - `description`
  - `language`
  - `stars`
  - `forks`
- 统一输出结构（为 B 扩展预留）：
  - `source`（固定为 `trending`）
  - `rank`
  - `repo`
  - `url`
  - `summary`
  - `language`
  - `stars`
  - `forks`

### 5.3 Issue 生成
- 标题格式：`Weekly GitHub Trending - YYYY-Www`
- 正文结构：
  - 统计头（生成时间、来源、Top N）
  - 表格或列表（repo、语言、stars、链接、简介）
  - 备注（自动生成说明）
- labels：默认 `github-trending`、`weekly-report`（可配置）

### 5.4 幂等与去重
- 创建前按标题检索当周 Issue。
- 如果已存在则结束任务（成功退出，不重复创建）。

## 6. 错误处理与可靠性
- 抓取失败：任务直接失败并输出错误日志。
- 解析失败：任务失败并记录关键片段，便于修复解析器。
- Issue 创建失败：重试 1 次，失败则任务失败。
- 不中断策略：不做静默降级，优先暴露失败信号。

## 7. 权限与安全
- 使用 GitHub Actions 内置 `GITHUB_TOKEN`，不引入个人 PAT。
- workflow 最小权限：
  - `contents: read`
  - `issues: write`
- 不在仓库中存储任何密钥或令牌。

## 8. 验证方案
1. 手动触发 workflow，确认创建 Issue 成功。
2. 校验 Issue 内容完整性与可读性（字段齐全、链接可点开）。
3. 验证幂等：同一周再次触发不会创建重复 Issue。
4. 临时短周期验证调度后，恢复为每周 cron。

## 9. 对 B（Search API）的扩展位
- 在采集层新增 `fetch_search_api.py`，输出同一统一结构，`source=search_api`。
- 在渲染层按来源分节展示：
  - Section A：Trending 周榜（主榜）
  - Section B：Search API 自定义榜（补充榜）
- 现有 workflow 与发布流程不变，只扩展数据源与渲染逻辑。

## 10. 落地顺序（MVP）
1. 建 workflow（cron + dispatch）。
2. 实现 Trending 抓取解析。
3. 实现 Markdown 生成与 Issue 发布。
4. 做手动触发验证与幂等验证。
5. 稳定后再接入 B。

## 11. 实施计划
- 实施计划文件：`docs/superpowers/plans/2026-05-11-github-trending-mvp-a-implementation-plan.md`
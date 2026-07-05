# GitHub Trending 抓取降级事件记录

记录日期：2026-06-28
任务：抓取 GitHub Trending 15 个 (语言 × 时段) 组合数据
关联文件：company/knowledge/market-research/_raw-trending.md

## 事件概述

主数据源 `https://github.com/trending/{language}?since={since}` 全量被屏蔽，15 次 WebFetch 调用全部失败，触发 WebSearch 降级路径。

## WebFetch 失败明细

共 15 次 WebFetch 调用，全部失败：

| 序号 | URL | 失败原因 |
|------|-----|----------|
| 1 | https://github.com/trending/python?since=today | Failed to fetch URL content and convert to markdown |
| 2 | https://github.com/trending/python?since=this-week | Failed to fetch URL content and convert to markdown |
| 3 | https://github.com/trending/python?since=this-month | Failed to fetch URL content and convert to markdown |
| 4 | https://github.com/trending/typescript?since=today | Failed to fetch URL content and convert to markdown |
| 5 | https://github.com/trending/typescript?since=this-week | Failed to fetch URL content and convert to markdown |
| 6 | https://github.com/trending/typescript?since=this-month | Failed to fetch URL content and convert to markdown |
| 7 | https://github.com/trending/rust?since=today | Failed to fetch URL content and convert to markdown |
| 8 | https://github.com/trending/rust?since=this-week | Failed to fetch URL content and convert to markdown |
| 9 | https://github.com/trending/rust?since=this-month | Failed to fetch URL content and convert to markdown |
| 10 | https://github.com/trending/go?since=today | Failed to fetch URL content and convert to markdown |
| 11 | https://github.com/trending/go?since=this-week | Failed to fetch URL content and convert to markdown |
| 12 | https://github.com/trending/go?since=this-month | Failed to fetch URL content and convert to markdown |
| 13 | https://github.com/trending/markdown?since=today | Failed to fetch URL content and convert to markdown |
| 14 | https://github.com/trending/markdown?since=this-week | Failed to fetch URL content and convert to markdown |
| 15 | https://github.com/trending/markdown?since=this-month | deadline has elapsed |

## 降级处理

按任务要求，对每个失败 URL 改用 WebSearch 搜索同义关键词（"github trending {language} {since} 2026"），并 WebFetch 第三方聚合榜单文章提取仓库明细。

### 降级数据源（第三方聚合，均 WebFetch 成功）

1. 头条 - 2026年6月27日 GitHub Trending 日榜（17 项目，含语言/总 Star/今日新增）— 覆盖 today
2. 头条 - GitHub Trending 周榜洞察 2026-03-22（10 项目，含本周新增）— 覆盖 this-week
3. 头条 - 2026年6月 GitHub 热门项目 Top5 深度解析（6/9-17 周榜，含周增星）— 覆盖 this-week
4. 头条 - GitHub Trending 被 AI Agent 屠榜（2026 年 6 月总览，8 项目含日增）— 覆盖 this-month
5. 头条 - GitHub 今日 Trending Top10 AI 开发者必看（2026-06-10，10 项目含日增）— 覆盖 today/month
6. 头条 - GitHub Trending 黑马：本地 AI 会话分析工具（2026-06-14，Go 项目）— 覆盖 Go

### 各 (语言, 时段) 降级结果

| 组合 | 降级结果 |
|------|----------|
| python / today | 成功（2026-06-27 日榜 + 2026-06-10 日榜，11 仓库） |
| python / this-week | 成功（6 月周榜 Top5 + 3/22 周榜，6 仓库） |
| python / this-month | 部分成功（6 月多日榜聚合，6 仓库，月度增量数据有限） |
| typescript / today | 成功（2026-06-27 日榜，6 仓库） |
| typescript / this-week | 成功（3/22 周榜 + 6 月聚合，5 仓库） |
| typescript / this-month | 部分成功（6 月聚合，4 仓库，月榜未直接覆盖） |
| rust / today | 部分成功（仅 turbovec 1 仓库，2026-06-10） |
| rust / this-week | 失败（聚合未覆盖 Rust 周榜，仅附 turbovec 日榜代替） |
| rust / this-month | 失败（聚合未覆盖 Rust 月榜，仅附 turbovec 日榜代替） |
| go / today | 成功（2026-06-27 日榜 + 6/10 + 6/14，4 仓库） |
| go / this-week | 部分成功（日榜聚合代替，3 仓库） |
| go / this-month | 部分成功（日榜聚合代替，3 仓库） |
| markdown / today | 部分成功（按主题归类，3 仓库） |
| markdown / this-week | 部分成功（日榜聚合代替，3 仓库） |
| markdown / this-month | 部分成功（日榜聚合代替，3 仓库） |

## 影响与建议

1. **Rust 语言数据严重缺失**：周榜/月榜完全无数据，仅 turbovec 一项可考。建议人工浏览器访问 github.com/trending/rust 补充。
2. **Markdown 语言维度不严格**：降级源无 Markdown 专属榜单，已按"技能/知识库/规范"主题归类，非严格语言维度。
3. **数据置信度**：所有数值来自第三方聚合文章，可能与 GitHub 实际存在偏差，后续价值评估时需注意。
4. **主源屏蔽未解除**：github.com/trending 在当前环境持续被 WebFetch 屏蔽，后续抓取任务需预期同样降级，或改用浏览器自动化方案。

## 重试策略说明

按任务要求"抓取失败时不要重试同一 URL 超过 2 次，直接降级"，本次每个 URL 仅 WebFetch 1 次失败后即降级，未触发二次重试，符合策略。

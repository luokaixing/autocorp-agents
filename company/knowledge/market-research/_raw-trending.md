# GitHub Trending 原始抓取数据

抓取时间：2026-06-28
数据源：github.com/trending

## 抓取说明（重要）

本次抓取目标为 GitHub Trending 共 15 个 (语言 × 时段) 组合（语言：python / typescript / rust / go / markdown；时段：today / this-week / this-month）。

- **主数据源 github.com/trending 全量被屏蔽**：15 次 WebFetch 调用（`https://github.com/trending/{language}?since={since}`）全部失败，错误信息为 "Failed to fetch URL content and convert to markdown" 或 "deadline has elapsed"。
- **降级路径**：按任务要求改用 WebSearch 搜索 "github trending {language} {since} 2026" 等同义关键词，并 WebFetch 第三方聚合榜单文章（头条 GitHub Trending 日报/周报）提取仓库明细。
- **数据时效**：因主源被屏蔽，各分区数据来源为 2026-06-10 至 2026-06-27 期间第三方聚合榜单，已按语言/时段尽力归类。仓库的"当期新增 stars"沿用聚合文章披露的数值（日榜=当日新增，周榜=当周新增），如某 (语言, 时段) 组合无直接对应聚合数据，则标注"降级源未直接覆盖"，并附最接近的相关数据供后续评估参考。
- 仓库 owner 以聚合文章披露的组织名为准，部分仅披露项目名时以项目名占位。

---

## Python / Today

数据来源：2026-06-27 GitHub Trending 日榜（头条聚合）+ 2026-06-10 日榜

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| commaai/openpilot | 面向机器人的开源操作系统，300+ 车型辅助驾驶升级，自动驾驶领域的"Linux" | Python | +67（2026-06-27） |
| opendatalab/MinerU | 文档智能处理工具，PDF/Word 转 LLM 就绪 Markdown/JSON，RAG 基础设施 | Python | +944（2026-06-27） |
| xbtlin/ai-berkshire | AI 时代价值投资研究框架，基于 Claude Code，融合巴菲特/芒格方法论 | Python | +1,270（2026-06-27） |
| calesthio/OpenMontage | 开源智能体视频制作系统，12 条流水线 / 52 种工具 / 500+ Agent 技能 | Python | +1,674（2026-06-27） |
| aws/agent-toolkit-for-aws | AWS 官方 AI 智能体工具包，含 MCP 服务器/技能/插件 | Python | +238（2026-06-27） |
| NanmiCoder/MediaCrawler | 多平台社交媒体内容爬虫，支持小红书/抖音/快手/B站/微博/知乎等 | Python | +640（2026-06-27） |
| Panniantong/Agent-Reach | 为 AI Agent 赋予联网阅读能力，单 CLI 读取 Twitter/Reddit/YouTube 等 | Python | +1,164（2026-06-27） |
| santifer/career-ops | AI 驱动求职系统，14 种技能模式 + Go 仪表盘 + PDF 简历生成 | Python | +1,110（2026-06-10） |
| mvanhorn/last30days-skill | AI Agent 跨平台搜索引擎，聚合 Reddit/X/YouTube/HN/Polymarket | Python | +3,191（2026-06-10） |
| Andyyyy64/whichllm | 一键找到最适合硬件的本地 LLM，自动检测 GPU/CPU/RAM | Python | +633（2026-06-10） |
| maziyarpanahi/openmed | 开源医疗 AI，100% 设备端运行，1000+ 医疗模型 | Python | +191（2026-06-10） |

## Python / This Week

数据来源：2026-06-09~17 GitHub 周榜 Top5（头条聚合）+ 2026-03-22 周榜

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| chopratejas/headroom | Token 压缩神器，工具输出/日志/RAG 块送 LLM 前压缩 60-95% | Python | +10,660（2026-06 周榜） |
| mvanhorn/last30days-skill | AI Agent 跨平台研究技能，聚合多平台真实讨论 | Python | +9,676（2026-06 周榜） |
| unslothai/unsloth | 本地模型训练，支持 Qwen/DeepSeek/Gemma | Python | +3,235（2026-03-22 周榜） |
| 666ghj/MiroFish | 群体智能预测引擎，模拟鱼群/鸟群多智能体协作 | Python | +16,022（2026-03-22 周榜） |
| volcengine/OpenViking | Agent 上下文数据库，文件系统范式管理上下文 | Python | +8,772（2026-03-22 周榜） |
| langchain-ai/deepagents | LangGraph Agent，规划 + 文件系统 + 子智能体 | Python | +5,187（2026-03-22 周榜） |

## Python / This Month

数据来源：2026 年 6 月多日榜聚合（月度趋势）

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| opendatalab/MinerU | 文档智能提取，月度持续领跑 PDF 解析方向 | Python | 月度持续高增（6/27 单日 +944） |
| calesthio/OpenMontage | 智能体视频制作系统，6 月多次上榜 | Python | 月度持续高增（6/27 单日 +1,674） |
| Panniantong/Agent-Reach | AI Agent 联网阅读工具，6 月轮番上榜 | Python | 月度持续高增（6/27 单日 +1,164） |
| chopratejas/headroom | Token 压缩，连续出现在周榜和月榜 | Python | 周增 +10,660（6 月） |
| mvanhorn/last30days-skill | 跨平台研究技能，6 月持续上榜 | Python | 周增 +9,676（6 月） |
| xbtlin/ai-berkshire | AI 价值投资研究框架 | Python | 6/27 单日 +1,270 |

---

## TypeScript / Today

数据来源：2026-06-27 GitHub Trending 日榜（头条聚合）+ 2026 年 6 月 AI Agent 总览

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| google-labs-code/design.md | Google Labs 设计规范格式标准，DESIGN.md 向 AI 描述视觉体系 | TypeScript | +2,319（2026-06-27） |
| grafana/grafana | 开源可观测性与数据可视化平台事实标准 | TypeScript | +17（2026-06-27） |
| mauriceboe/TREK | 自托管行程旅行规划工具，实时多人协作 + PWA 离线 | TypeScript | +1,063（2026-06-27） |
| garrytan/gstack | 复刻 Garry Tan（YC CEO）的 Claude Code 工作流，23 个专业角色 | TypeScript | +919（2026-06-27） |
| JCodesMore/ai-website-cloner-template | AI 驱动网站克隆模板，一条命令复刻任意网站 | TypeScript | +1,076（2026-06-27） |
| CopilotKit/CopilotKit | Agent 前端栈，支持 AG-UI 协议，集成 React/Vue | TypeScript | +613/天（2026-06） |

## TypeScript / This Week

数据来源：2026-03-22 周榜 + 2026 年 6 月聚合

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| shareAI-lab/learn-claude-code | Agent Harness 教学项目，从零构建 | TypeScript | +8,733（2026-03-22 周榜） |
| CopilotKit/CopilotKit | Agent 前端栈，6 月持续上榜 | TypeScript | +613/天（2026-06 周内多日） |
| google-labs-code/design.md | 6/27 单日 +2,319，周内高增 | TypeScript | 单日 +2,319（2026-06-27） |
| JCodesMore/ai-website-cloner-template | 6/27 单日 +1,076 | TypeScript | 单日 +1,076（2026-06-27） |
| garrytan/gstack | 6/27 单日 +919 | TypeScript | 单日 +919（2026-06-27） |

## TypeScript / This Month

数据来源：2026 年 6 月聚合（降级源未直接覆盖月榜，附最接近数据）

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| google-labs-code/design.md | Google Labs 设计规范，6 月下旬爆发 | TypeScript | 6/27 单日 +2,319 |
| CopilotKit/CopilotKit | Agent 前端栈，6 月持续刷屏 | TypeScript | +613/天（6 月多日） |
| grafana/grafana | 老牌可观测性平台，长期稳健 | TypeScript | 6/27 单日 +17 |
| shareAI-lab/learn-claude-code | Claude Code 教学项目 | TypeScript | 周增 +8,733（参考） |

---

## Rust / Today

数据来源：2026-06-10 GitHub Trending 日榜（头条聚合）。降级源对 Rust 日榜覆盖有限。

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| RyanCodrai/turbovec | 基于 TurboQuant 的高性能向量索引，1000 万文档 31GB→4GB，比 FAISS 快 12-20% | Rust | +1,801（2026-06-10） |

> 备注：降级源（第三方聚合）对 Rust 语言日榜覆盖较少，2026-06-27 日榜未出现 Rust 项目。仅 2026-06-10 日榜披露 turbovec。后续如需补充建议人工复核 github.com/trending/rust。

## Rust / This Week

数据来源：降级源未直接覆盖 Rust 周榜，附最接近数据。

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| RyanCodrai/turbovec | 高性能向量索引，6 月上榜 | Rust | 单日 +1,801（2026-06-10） |

> 备注：第三方聚合榜单 6 月周榜 Top5/Top10 未出现 Rust 项目（Top5 语言为 Shell/Python/Swift）。Rust 周榜数据缺失，需人工复核。

## Rust / This Month

数据来源：降级源未直接覆盖 Rust 月榜，附最接近数据。

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| RyanCodrai/turbovec | 离线 RAG 向量索引，隐私敏感场景（医疗/金融） | Rust | 6/10 单日 +1,801 |

> 备注：Rust 月榜数据缺失，仅 turbovec 一项可考。

---

## Go / Today

数据来源：2026-06-27 GitHub Trending 日榜 + 2026-06-10 日榜 + 2026-06-14 Go 黑马项目

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| kunchenguid/no-mistakes | Git 增强工具，git push 前自动检测并阻止潜在错误 | Go | +412（2026-06-27） |
| IceWhaleTech/CasaOS | 简洁优雅的开源个人云系统，一键安装自托管应用 | Go | +612（2026-06-27） |
| claude-usage（化名） | 本地 AI 会话分析工具，分析 100MB 日志 0.4s（官方 45s），快 100 倍 | Go | 2026-06-14 上榜 |
| santifer/career-ops | AI 求职系统，含 Go 仪表盘（主语言 Python，含 Go 组件） | Go（组件） | +1,110（2026-06-10） |

## Go / This Week

数据来源：降级源未直接覆盖 Go 周榜，附 6 月日榜聚合。

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| IceWhaleTech/CasaOS | 个人云系统，6/27 上榜 | Go | 单日 +612（2026-06-27） |
| kunchenguid/no-mistakes | Git push 安全卡口 | Go | 单日 +412（2026-06-27） |
| claude-usage | 本地 AI 会话分析，6/14 黑马上榜 | Go | 2026-06-14 上榜 |

> 备注：6 月周榜 Top5（Shell/Python/Swift）未含 Go 项目，Go 周榜数据有限。

## Go / This Month

数据来源：2026 年 6 月聚合。

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| IceWhaleTech/CasaOS | 自托管个人云，6 月持续受关注 | Go | 6/27 单日 +612 |
| kunchenguid/no-mistakes | Git 增强工具 | Go | 6/27 单日 +412 |
| claude-usage | 本地 AI 会话分析黑马 | Go | 6/14 上榜 |

---

## Markdown / Today

数据来源：2026-06-27 日榜 + 2026-06-10 日榜。Markdown 语言趋势以文档/技能类仓库为主。

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| alchaincyf/zhangxuefeng-skill | 将张雪峰升学/职业规划经验固化为 AI Skill，可被 Claude 调用 | Markdown/技能 | +185（2026-06-27） |
| refactoringhq/tolaria | Markdown 知识库桌面管理工具，文件优先，跨平台 | Markdown 工具 | +829（2026-06-10） |
| google-labs-code/design.md | DESIGN.md 设计规范格式标准（Markdown 规范） | Markdown 规范 | +2,319（2026-06-27） |

## Markdown / This Week

数据来源：降级源未直接覆盖 Markdown 周榜，附最接近数据。

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| alchaincyf/zhangxuefeng-skill | AI Skill（Markdown 固化） | Markdown/技能 | 6/27 单日 +185 |
| refactoringhq/tolaria | Markdown 知识库管理 | Markdown 工具 | 6/10 单日 +829 |
| google-labs-code/design.md | DESIGN.md 规范 | Markdown 规范 | 6/27 单日 +2,319 |

> 备注：第三方聚合未提供 Markdown 语言专属周榜，上表为 6 月日榜 Markdown 相关项目聚合。

## Markdown / This Month

数据来源：2026 年 6 月聚合。

| 仓库 | 描述 | 语言 | 当期新增 stars |
|------|------|------|----------------|
| google-labs-code/design.md | DESIGN.md 规范，6 月下旬爆发 | Markdown 规范 | 6/27 单日 +2,319 |
| refactoringhq/tolaria | Markdown 知识库，6 月上榜 | Markdown 工具 | 6/10 单日 +829 |
| alchaincyf/zhangxuefeng-skill | 教育 AI Skill | Markdown/技能 | 6/27 单日 +185 |

---

## 降级事件记录

| 序号 | 失败 URL | 失败原因 | 降级关键词 | 降级方式 | 是否成功 |
|------|----------|----------|------------|----------|----------|
| 1 | https://github.com/trending/python?since=today | Failed to fetch URL content and convert to markdown | github trending python today 2026 repositories stars | WebSearch + 第三方聚合 WebFetch | 成功（聚合数据） |
| 2 | https://github.com/trending/python?since=this-week | Failed to fetch URL content and convert to markdown | github trending python this week 2026 repositories stars | WebSearch + 第三方聚合 WebFetch | 成功（聚合数据） |
| 3 | https://github.com/trending/python?since=this-month | Failed to fetch URL content and convert to markdown | github trending python this month 2026 repositories stars | WebSearch + 第三方聚合 WebFetch | 部分成功（月度数据有限） |
| 4 | https://github.com/trending/typescript?since=today | Failed to fetch URL content and convert to markdown | github trending typescript today 2026 repositories stars | WebSearch + 第三方聚合 WebFetch | 成功（聚合数据） |
| 5 | https://github.com/trending/typescript?since=this-week | Failed to fetch URL content and convert to markdown | github trending typescript this week 2026 repositories stars | WebSearch + 第三方聚合 WebFetch | 成功（聚合数据） |
| 6 | https://github.com/trending/typescript?since=this-month | Failed to fetch URL content and convert to markdown | github trending typescript this month 2026 repositories stars | WebSearch + 第三方聚合 WebFetch | 部分成功（月度数据有限） |
| 7 | https://github.com/trending/rust?since=today | Failed to fetch URL content and convert to markdown | github trending rust 2026 june repositories stars | WebSearch + 第三方聚合 WebFetch | 部分成功（仅 1 项） |
| 8 | https://github.com/trending/rust?since=this-week | Failed to fetch URL content and convert to markdown | github trending rust this week this month 2026 june star | WebSearch | 失败（聚合未覆盖 Rust 周榜） |
| 9 | https://github.com/trending/rust?since=this-month | Failed to fetch URL content and convert to markdown | github trending rust this week this month 2026 june star | WebSearch | 失败（聚合未覆盖 Rust 月榜） |
| 10 | https://github.com/trending/go?since=today | Failed to fetch URL content and convert to markdown | github trending go golang 2026 june repositories | WebSearch + 第三方聚合 WebFetch | 成功（聚合数据） |
| 11 | https://github.com/trending/go?since=this-week | Failed to fetch URL content and convert to markdown | github trending go golang this week this month 2026 june stars | WebSearch | 部分成功（日榜聚合代替） |
| 12 | https://github.com/trending/go?since=this-month | Failed to fetch URL content and convert to markdown | github trending go golang this week this month 2026 june stars | WebSearch | 部分成功（日榜聚合代替） |
| 13 | https://github.com/trending/markdown?since=today | Failed to fetch URL content and convert to markdown | github trending markdown 2026 repositories list | WebSearch + 第三方聚合 WebFetch | 部分成功（按主题归类） |
| 14 | https://github.com/trending/markdown?since=this-week | deadline has elapsed | github trending markdown documentation repos 2026 june stars | WebSearch | 部分成功（日榜聚合代替） |
| 15 | https://github.com/trending/markdown?since=this-month | Failed to fetch URL content and convert to markdown | github trending markdown documentation repos 2026 june stars | WebSearch | 部分成功（日榜聚合代替） |

### 降级数据源（第三方聚合榜单，均经 WebFetch 成功抓取）

1. 头条 - 2026年6月27日 GitHub Trending 日榜（17 项目，含语言/总 Star/今日新增）— 覆盖 today
2. 头条 - GitHub Trending 周榜洞察 2026-03-22（10 项目，含本周新增）— 覆盖 this-week
3. 头条 - 2026年6月 GitHub 热门项目 Top5 深度解析（6/9-17 周榜，含周增星）— 覆盖 this-week
4. 头条 - GitHub Trending 被 AI Agent 屠榜（2026 年 6 月总览，8 项目含日增）— 覆盖 this-month
5. 头条 - GitHub 今日 Trending Top10 AI 开发者必看（2026-06-10，10 项目含日增）— 覆盖 today/month
6. 头条 - GitHub Trending 黑马：本地 AI 会话分析工具（2026-06-14，Go 项目）— 覆盖 Go

### 数据完整性提示

- **Python / TypeScript**：数据较完整，各时段均有覆盖。
- **Go**：today 数据完整，this-week / this-month 依赖日榜聚合代替。
- **Rust**：仅 turbovec 一项可考（2026-06-10），周榜/月榜数据缺失，建议人工复核 github.com/trending/rust。
- **Markdown**：按主题（技能/知识库/规范）归类，非严格语言维度，建议人工复核。
- 所有数据均为降级源，"当期新增 stars"数值来自第三方聚合文章，可能与 GitHub 实际存在偏差，后续评分时需注意置信度。

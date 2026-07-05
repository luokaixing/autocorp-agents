# GitHub 热门项目扫描与 AI 公司价值分析报告

> 生成时间：2026-06-28
> 分析师：AutoCorp PM / CEO 协同
> 范围：GitHub Trending 15 维度 + 13 个 Topics + 4 个中文开源源
> 原始数据：[_raw-trending.md](_raw-trending.md) · [_raw-topics.md](_raw-topics.md) · [_raw-cn-sources.md](_raw-cn-sources.md)

---

## 一、扫描概览

### 1.1 数据源
| 数据源 | 抓取方式 | 原始条目数 | 降级 |
|--------|----------|-----------|------|
| GitHub Trending (15 维度) | WebFetch 主源全屏蔽 → WebSearch + 第三方聚合 | ~38 | 是（15/15 失败） |
| GitHub Topics (13 个) | WebFetch + WebSearch 降级 | ~195 | 部分（langchain/crypto 降级） |
| HelloGitHub 第 122 期 | WebFetch 404 → WebSearch | 3 | 是 |
| GitCode 热门 | WebFetch JS 渲染失败 → 博客降级 | 6 | 是 |
| Gitee 热门 | WebFetch 直接成功 | 23 | 否 |
| WebSearch 三关键词 | 直接搜索 | 28 | 否 |
| **合计去重前** | — | **~293** | — |
| **去重后进入初筛** | — | **~145** | — |
| **进入深度评分** | — | **40** | — |

### 1.2 降级事件
本次扫描累计触发 **17 起降级事件**，详情见：
- `company/human-requests/2026-06-28-github-trending-degradation.md`
- `_raw-trending.md` / `_raw-topics.md` / `_raw-cn-sources.md` 文末"降级事件记录"分区

主要根因：当前环境对 `github.com/trending/*` 全量屏蔽，所有 Trending 数据来自第三方聚合文章（头条 GitHub Trending 日报/周报）。Topics 部分直接抓取成功，质量更高。

### 1.3 关键观察
1. **AI Agent屠榜**：GitHub Trending 6 月榜单约 70% 项目与 AI Agent / LLM / 自动化相关
2. **Claude Code 生态爆发**：awesome-claude-skills (66.2k)、cc-switch (76.9k)、agent-skills (61.2k) 等"技能/插件"型项目成为新增长极
3. **浏览器自动化升级**：browser-use (95k)、playwright-mcp (33k)、browser-harness (14k) 共同推动"自愈式"浏览器 Agent
4. **Token 压缩/上下文管理**成为新基础设施层（headroom 周增 10k+ stars）
5. **国产开源**：Dify (147k)、DeepSeek-R1、Qwen3-VL、antirez/ds4.c 持续放量
6. **SEO + AI 写作**细分赛道有大量小而美的 Claude Skills 项目（≤1k stars 但精准对标 AutoCorp 内容变现闭环）

---

## 二、评分框架

### 2.1 六维度评分（0-5 分）
| 维度 | 权重 | 说明 |
|------|------|------|
| 变现直接性 | 0.25 | 是否能直接接入当前变现闭环（内容/引流/打赏/订阅/支付） |
| 技术栈契合度 | 0.20 | 与现有 `engine/` Python + Playwright + LLM 后端兼容性 |
| 集成成本倒数 | 0.20 | 用 (5 - 集成成本) 计入，0=直接用，5=重写 |
| 参考价值 | 0.15 | 作为产品形态/商业模式参考的价值 |
| 热度与维护 | 0.10 | stars 增速、最近 commit、issue 响应 |
| 风险与合规 | 0.10 | License、付费 API 依赖、灰产/封号风险 |

### 2.2 分类门槛（双门槛）
- **P0 立即采纳**：加权总分 ≥ 4.0 且 集成成本 ≤ 2（≤2 天工作量）
- **P1 周内立项**：加权总分 ≥ 3.5 且 集成成本 ≤ 3（≤1 周工作量）
- **P2 战略观察**：长期跟踪，暂不接入
- **P3 放弃**：与 AI 公司无价值

---

## 三、40 个候选项目评分表

> 排序：按加权总分降序

| # | 仓库 | 主要语言 | stars | 技术契合 | 变现 | 集成成本 | 参考价值 | 热度维护 | 风险合规 | 加权总分 | 分级 |
|---|------|----------|-------|----------|------|----------|----------|----------|----------|----------|------|
| 1 | AgriciDaniel/claude-seo | Python | 3.9k | 5 | 5 | 1 | 4 | 4 | 5 | **4.55** | P0 |
| 2 | polarsource/polar | Python | 9.9k | 5 | 5 | 2 | 5 | 4 | 4 | **4.40** | P0 |
| 3 | opendatalab/MinerU | Python | 23k+ | 5 | 4 | 1 | 4 | 5 | 5 | **4.40** | P0 |
| 4 | Panniantong/Agent-Reach | Python | 44.1k | 5 | 5 | 1 | 4 | 4 | 3 | **4.35** | P0 |
| 5 | rediumvex/seo-blog-writer-claude | Skill | 28 | 5 | 5 | 1 | 4 | 2 | 5 | **4.35** | P0 |
| 6 | browser-use/browser-use | Python | 94.9k | 5 | 4 | 1 | 4 | 5 | 4 | **4.30** | P0 |
| 7 | harry0703/MoneyPrinterTurbo | Python | 93.8k | 4 | 5 | 2 | 5 | 5 | 4 | **4.30** | P0 |
| 8 | yusufkaraaslan/Skill_Seekers | Python | 13.7k | 5 | 4 | 1 | 4 | 4 | 5 | **4.30** | P0 |
| 9 | naxiaoduo/1000UserGuide | HTML | 3.8k | 3 | 5 | 1 | 5 | 4 | 5 | **4.30** | P0 |
| 10 | ccxt/ccxt | Python | 30k+ | 5 | 4 | 1 | 4 | 5 | 4 | **4.30** | P0 |
| 11 | ComposioHQ/awesome-claude-skills | Python | 66.2k | 5 | 3 | 1 | 5 | 5 | 5 | **4.30** | P0 |
| 12 | TauricResearch/TradingAgents | Python | 89.3k | 5 | 4 | 2 | 5 | 5 | 3 | **4.15** | P0 |
| 13 | dongbeixiaohuo/writing-agent | JS | 293 | 4 | 5 | 2 | 5 | 3 | 5 | **4.20** | P0 |
| 14 | microsoft/playwright-mcp | TS | 33.1k | 5 | 4 | 2 | 4 | 5 | 5 | **4.20** | P0 |
| 15 | microsoft/playwright | TS | 91.8k | 5 | 3 | 0 | 3 | 5 | 5 | **4.20** | P0 (已用) |
| 16 | Skyvern-AI/skyvern | Python | 21.8k | 5 | 4 | 2 | 4 | 4 | 4 | **4.00** | P0 |
| 17 | browser-use/browser-harness | Python | 13.9k | 5 | 4 | 2 | 4 | 4 | 4 | **4.00** | P0 |
| 18 | D4Vinci/Scrapling | Python | 66.6k | 5 | 4 | 2 | 4 | 5 | 3 | **4.00** | P0 |
| 19 | uselotus/lotus | Python | 1.8k | 5 | 4 | 2 | 4 | 3 | 5 | **4.00** | P0 |
| 20 | open-webui/open-webui | Python | 143k | 5 | 3 | 2 | 4 | 5 | 5 | **3.95** | P1 |
| 21 | chopratejas/headroom | Python | 10k+ | 5 | 3 | 1 | 3 | 4 | 5 | **3.90** | P1 |
| 22 | langchain-ai/langgraph | Python | n/a | 5 | 3 | 3 | 5 | 5 | 5 | **3.90** | P1 |
| 23 | bytedance/deer-flow | Python | 75.2k | 5 | 3 | 3 | 5 | 5 | 5 | **3.90** | P1 |
| 24 | wasp-lang/open-saas | TS | 14.6k | 3 | 5 | 3 | 5 | 4 | 5 | **3.90** | P1 |
| 25 | Usagi-org/ai-goofish-monitor | Python | 12k | 5 | 4 | 2 | 4 | 4 | 3 | **3.90** | P1 |
| 26 | NanmiCoder/MediaCrawler | Python | 30k+ | 5 | 4 | 2 | 4 | 4 | 2 | **3.80** | P1 |
| 27 | CloakHQ/CloakBrowser | Python | 21.8k | 5 | 4 | 2 | 4 | 4 | 2 | **3.80** | P1 |
| 28 | firecrawl/firecrawl | TS | 141k | 4 | 4 | 2 | 4 | 5 | 3 | **3.80** | P1 |
| 29 | n8n-io/n8n | TS | 194k | 3 | 4 | 3 | 5 | 5 | 5 | **3.75** | P1 |
| 30 | langgenius/dify | TS | 147k | 3 | 4 | 3 | 5 | 5 | 5 | **3.75** | P1 |
| 31 | wshobson/agents | Python | 37.3k | 5 | 3 | 2 | 4 | 4 | 4 | **3.75** | P1 |
| 32 | ollama/ollama | Go | 175k | 4 | 3 | 2 | 4 | 5 | 5 | **3.75** | P1 |
| 33 | jackwener/OpenCLI | JS | 22.1k | 4 | 4 | 2 | 4 | 4 | 3 | **3.70** | P1 |
| 34 | zhayujie/chatgpt-on-wechat | Python | 42.8k | 5 | 3 | 2 | 4 | 5 | 2 | **3.65** | P1 |
| 35 | nanobrowser/nanobrowser | TS | 13k | 3 | 4 | 3 | 5 | 4 | 4 | **3.55** | P1 |
| 36 | CopilotKit/CopilotKit | TS | 30k | 3 | 3 | 3 | 5 | 5 | 5 | **3.50** | P1 |
| 37 | activepieces/activepieces | TS | 21.6k | 3 | 4 | 3 | 4 | 4 | 5 | **3.50** | P1 |
| 38 | crestalnetwork/intentkit | Python | 6.5k | 5 | 3 | 3 | 4 | 3 | 4 | **3.45** | P2 |
| 39 | browserbase/stagehand | TS | 22.8k | 3 | 4 | 3 | 4 | 4 | 4 | **3.40** | P2 |
| 40 | getmaxun/maxun | TS | 15.7k | 3 | 4 | 3 | 4 | 4 | 4 | **3.40** | P2 |

### 初筛剔除（部分代表，P3 不进入表中）
- 芋道源码/ruoyi-vue-pro、yudao-cloud、Sa-Token、若依系列（Java 企业后台，与 Python 栈不符）
- microsoft/playwright（已纳入表中作为"已用基线"参考）
- vLLM / transformers / Llama 4 / Gemma 4 / Phi 4（模型训练/推理基础设施，非应用层）
- ethereum/mist（已废弃）、libsodium/Tink/s2n（密码学库，非变现场景）
- chrome-devtools-mcp、gh-aw（与 AutoCorp 当前阶段关联度低）
- simplex-chat、moonshine、nautilus_trader（垂直领域，不在当前业务范围）

---

## 四、P0 立即采纳清单（19 项）

> 准入门槛：加权总分 ≥ 4.0 且 集成成本 ≤ 2

| # | 项目 | 接入路径 | 工作量 |
|---|------|----------|--------|
| 1 | AgriciDaniel/claude-seo | 复制 19 个 sub-skills 到 `company/projects/seo-content-generator/.claude/skills/` | 0.5 天 |
| 2 | polarsource/polar | 作为 `engine/payment_bridge.py` 的打赏/订阅后端，替代 PayPal 闭环 | 1.5 天 |
| 3 | opendatalab/MinerU | 集成到 `engine/content_writer.py` 前置：PDF 白皮书 → Markdown → SEO 文章 | 1 天 |
| 4 | Panniantong/Agent-Reach | 替换 `engine/twitter_bot.py` 与 `engine/reddit_bot.py` 的内容采集层，零 API 费用 | 1 天 |
| 5 | rediumvex/seo-blog-writer-claude | 作为 Claude Skill 接入 OutlineGenerator，提升 SEO 文章产出质量 | 0.5 天 |
| 6 | browser-use/browser-use | 作为 `engine/browser_runner.py` 的自愈式浏览器底座，替代裸 Playwright | 1.5 天 |
| 7 | harry0703/MoneyPrinterTurbo | 新建 `company/projects/video-content/` 业务线，从文章生成短视频分发到 B站/YouTube | 2 天 |
| 8 | yusufkaraaslan/Skill_Seekers | 接入 `engine/skill_loader.py`：把 DeFi 文档/PDF/竞品 README 转成 Claude Skills | 1 天 |
| 9 | naxiaoduo/1000UserGuide | 把 300+ 渠道清单导入 `company/knowledge/marketing/channels.yaml`，作为 PM 引流手册 | 0.5 天 |
| 10 | ccxt/ccxt | 接入 `engine/market_analyzer.py`：替换/补充 CoinGecko 数据源，覆盖 100+ 交易所 | 1 天 |
| 11 | ComposioHQ/awesome-claude-skills | 把 Claude Skills 集合加载到 `engine/skill_loader.py`，扩充可调用技能库 | 1 天 |
| 12 | TauricResearch/TradingAgents | 接入 `engine/market_analyzer.py`：多 Agent 讨论后输出市场分析报告作为内容素材 | 2 天 |
| 13 | dongbeixiaohuo/writing-agent | Claude Code Skill 形态接入，扩充 ContentWriter 的"去 AI 味"能力 | 1 天 |
| 14 | microsoft/playwright-mcp | 通过 MCP 协议接入 `engine/browser_runner.py`，标准化浏览器交互接口 | 1.5 天 |
| 15 | microsoft/playwright | 已使用，维持现状 | 0 |
| 16 | Skyvern-AI/skyvern | 与 browser-use 二选一作为浏览器 Agent 底座 | 2 天 |
| 17 | browser-use/browser-harness | 接入 `engine/browser_runner.py`，提供 self-healing 重试机制 | 1 天 |
| 18 | D4Vinci/Scrapling | 接入 `engine/scraper.py`：自适应反爬，抓取竞品文章/价格数据 | 1.5 天 |
| 19 | uselotus/lotus | 作为 SaaS 业务线的定价/计费模块（与 polar 配套） | 1 天 |

---

## 五、P1 周内立项清单（18 项）

> 准入门槛：加权总分 ≥ 3.5 且 集成成本 ≤ 3

| # | 项目 | 接入路径 | 工作量 |
|---|------|----------|--------|
| 1 | open-webui/open-webui | 本地部署作为 LLM 网关，统一管理 GLM-5.2 / DeepSeek / Ollama | 2 天 |
| 2 | chopratejas/headroom | 接入 LLM 调用前预处理层，节省 60-95% Token 成本 | 1 天 |
| 3 | langchain-ai/langgraph | 作为 `engine/orchestrator.py` 多 Agent 编排底座（重构现有 Meeting 类） | 3 天 |
| 4 | bytedance/deer-flow | 作为 CEO/CTO 决策 Agent 的长任务执行框架参考 | 3 天 |
| 5 | wasp-lang/open-saas | 作为新 SaaS 业务线模板（含 Stripe / Polar.sh / Auth） | 3 天 |
| 6 | Usagi-org/ai-goofish-monitor | 接入 `company/knowledge/opportunities/`，闲鱼二手套利监控 | 2 天 |
| 7 | NanmiCoder/MediaCrawler | 接入 `engine/scraper.py`：抓小红书/抖音/B站/微博/知乎热点作为选题源 | 2 天 |
| 8 | CloakHQ/CloakBrowser | 接入 `engine/browser_runner.py`：解决 Paragraph/Twitter 封号问题 | 2 天 |
| 9 | firecrawl/firecrawl | 替代手工 scraper，作为大规模内容抓取 API（免费额度内） | 2 天 |
| 10 | n8n-io/n8n | 自托管作为可视化工作流编排，降低 engine/ 维护成本 | 3 天 |
| 11 | langgenius/dify | 自托管作为可视化 Agent 编排平台，与 n8n 二选一 | 3 天 |
| 12 | wshobson/agents | 多 Harness 插件市场，扩充 Claude Code 技能集 | 2 天 |
| 13 | ollama/ollama | 本地 LLM 推理（DeepSeek/Qwen），节省 API 成本 | 2 天 |
| 14 | jackwener/OpenCLI | 把任意网站转 CLI 供 AI Agent 调用，扩展工具集 | 2 天 |
| 15 | zhayujie/chatgpt-on-wechat | 微信公众号/企业微信 AI 助手作为新引流渠道 | 2 天 |
| 16 | nanobrowser/nanobrowser | Chrome 扩展形态的 AI 自动化，作为浏览器方案补充 | 3 天 |
| 17 | CopilotKit/CopilotKit | 为未来 SaaS 产品提供 Agent 前端栈 | 3 天 |
| 18 | activepieces/activepieces | 400+ MCP 集成的工作流自动化平台，与 n8n/dify 互为备选 | 3 天 |

---

## 六、P2 战略观察清单（3 项）

| # | 项目 | 观察理由 |
|---|------|----------|
| 1 | crestalnetwork/intentkit | 自托管云 Agent 集群，未来若 AutoCorp 角色扩展到 10+ Agent 时考虑 |
| 2 | browserbase/stagehand | 浏览器 Agent SDK，TypeScript 栈，暂用 browser-use 替代 |
| 3 | getmaxun/maxun | 无代码 Web 抓取，未来非技术成员需要抓数据时考虑 |

---

## 七、Top 10 深度分析

### 1. AgriciDaniel/claude-seo ⭐ 4.55 P0
- **产品形态**：Claude Code Skill 套件，含 19 个 sub-skills + 12 个 subagents，覆盖技术 SEO / E-E-A-T / Schema / GEO/AEO / 外链 / 本地 SEO
- **商业模式**：开源 MIT，作者靠 Skill 定制咨询变现
- **可复用模块**：`technical-seo-auditor`、`content-brief-generator`、`schema-markup-generator`、`backlink-prospector` 可直接复用
- **接入步骤**：
  1. `git clone` 到 `company/projects/seo-content-generator/.claude/skills/claude-seo/`
  2. 在 `engine/outline_generator.py` 调用 `content-brief-generator` 替代当前模板
  3. 在 `engine/seo_scorer.py` 调用 `technical-seo-auditor` 做文章上线前体检
  4. 在 `engine/content_writer.py` 调用 `schema-markup-generator` 输出 JSON-LD
- **风险提示**：依赖 Claude Code 运行时；需翻墙访问部分外链资源
- **预期收益**：SEO 排名提升 → 自然流量 +30% → Paragraph 打赏 +$1-2/天

### 2. polarsource/polar ⭐ 4.40 P0
- **产品形态**：开源"软件变现基础设施"，含订阅 / 打赏 / 一次性付费 / Issue 赞助 / 商店，Python 后端（FastAPI），TypeScript 前端
- **商业模式**：开源自托管免费，云端 SaaS 抽 2% + Stripe 费率
- **可复用模块**：`polar/subscription`、`polar/checkout`、`polar/articles`（订阅墙文章）
- **接入步骤**：
  1. 自托管 Polar 实例（Docker Compose）
  2. 在 `engine/payment_bridge.py` 新增 `PolarProvider`，与现有 PayPal 并列
  3. 把 `company/projects/seo-content-generator/landing/` 改造为 Polar Checkout 落地页
  4. Paragraph 文章底部加 Polar 打赏按钮（替代裸 ETH 地址）
- **风险提示**：Stripe 仍需翻墙 + 真实 key；自托管需维护 Postgres
- **预期收益**：替代当前裸 ETH 打赏，转化率提升 2-3 倍 → 月新增 $30-100

### 3. opendatalab/MinerU ⭐ 4.40 P0
- **产品形态**：PDF / Word / PPT → LLM-ready Markdown / JSON，支持公式 / 表格 / 图版识别，本地部署
- **商业模式**：开源 AGPL，官方提供 API 与付费云
- **可复用模块**：`magic_pdf` 核心解析库
- **接入步骤**：
  1. `pip install magic-pdf[full]` 装入 `engine/` 环境
  2. 在 `engine/content_writer.py` 前置 `pdf_to_markdown()` 预处理
  3. 把 DeFi 项目白皮书（Aave/Compound/Lido 等）批量转 Markdown 入 `company/knowledge/defi-whitepapers/`
  4. SEO 文章生成时引用真实白皮书片段，提升 E-E-A-T
- **风险提示**：本地推理需 4GB+ 显存；AGPL License 注意衍生作品开源义务
- **预期收益**：内容深度 +50% → SEO 排名提升 → 月 +$20-50

### 4. Panniantong/Agent-Reach ⭐ 4.35 P0
- **产品形态**：单 CLI 给 AI Agent 装上"眼睛"，读取 Twitter / Reddit / YouTube / GitHub / Bilibili / 小红书，零 API 费用
- **商业模式**：开源 MIT，作者靠定制化变现
- **可复用模块**：`agent_reach.cli`、各平台 reader 子模块
- **接入步骤**：
  1. `pip install agent-reach` 装入 `engine/` 环境
  2. 替换 `engine/twitter_bot.py` 与 `engine/reddit_bot.py` 的内容采集层
  3. PM 角色每日 08:00 晨会调用 Agent-Reach 抓取昨日热门 DeFi 讨论，作为选题源
  4. COO 角色抓取竞品 Twitter 互动数据，作为引流效果对照
- **风险提示**：无 API 调用 = 走 Web 抓取，存在 ToS 灰色地带；需翻墙访问 Twitter/Reddit
- **预期收益**：节省 Twitter API $100/月 + Reddit API 配额；选题点击率 +20%

### 5. rediumvex/seo-blog-writer-claude ⭐ 4.35 P0
- **产品形态**：单一 Claude Skill，输入 URL / 笔记 / 主题，输出"人味"SEO 博客，目标 Google 排名
- **商业模式**：开源 MIT，作者靠 Skill 维护变现
- **可复用模块**：`SKILL.md` 提示词工程模板
- **接入步骤**：
  1. 克隆到 `company/projects/seo-content-generator/.claude/skills/seo-blog-writer/`
  2. 在 `engine/llm_client.py` 加载该 Skill 作为 ContentWriter 的 system prompt
  3. 与 AgriciDaniel/claude-seo 配合：claude-seo 出 brief，seo-blog-writer 出正文
- **风险提示**：Skill 设计针对 Claude，需测试 GLM-5.2 兼容性
- **预期收益**：文章"AI 味"降低 → Google 排名 +20% → 月 +$15-40

### 6. browser-use/browser-use ⭐ 4.30 P0
- **产品形态**：让 AI Agent 直接操作网页的 Python 库，95k stars，含视觉理解 / 自愈 / 多 Tab
- **商业模式**：开源 Apache 2.0，作者靠云服务变现
- **可复用模块**：`browser_use.Agent`、`browser_use.Browser`、`browser_use.Controller`
- **接入步骤**：
  1. `pip install browser-use` 装入 `engine/` 环境
  2. 在 `engine/browser_runner.py` 新增 `BrowserUseRunner` 类，与现有 `PlaywrightRunner` 并列
  3. 把 Paragraph 发布 / Twitter 发推 / Reddit 发帖流程迁移到 BrowserUseRunner
  4. 利用自愈能力解决"按钮位置变了 / 登录态过期"问题
- **风险提示**：依赖视觉模型（GPT-4o/Claude）；可用 GLM-4V 降级
- **预期收益**：浏览器自动化稳定性 +60% → 月节省人工干预 10+ 小时

### 7. harry0703/MoneyPrinterTurbo ⭐ 4.30 P0
- **产品形态**：输入关键词 → 脚本 → 配音 → 字幕 → 素材 → 合成短视频，全自动
- **商业模式**：开源 MIT，作者靠定制视频变现
- **可复用模块**：`app/controllers/`、`app/services/` 全套
- **接入步骤**：
  1. 新建 `company/projects/video-content/` 业务线
  2. `git clone MoneyPrinterTurbo`，配置本地 LLM（GLM-4 / Qwen）和 TTS（edge-tts 免费版）
  3. 把 SEO 文章作为脚本源，自动生成 ≤60s 短视频
  4. 分发到 B站 / 抖音 / YouTube Shorts / 小红书视频号
- **风险提示**：素材版权（用 Pexels/Pixabay 免费素材）；B站/抖音需翻墙操作
- **预期收益**：新业务线，月 +$50-200（B站创作激励 + YouTube 广告分成）

### 8. yusufkaraaslan/Skill_Seekers ⭐ 4.30 P0
- **产品形态**：把文档站 / GitHub 仓库 / PDF 自动转成 Claude Skills，含冲突检测
- **商业模式**：开源 MIT
- **可复用模块**：`skill_seekers.converter`、`skill_seekers.conflict_detector`
- **接入步骤**：
  1. `pip install skill-seekers` 装入 `engine/` 环境
  2. 把 Aave / Compound / Lido 等项目文档批量转 Claude Skills
  3. 加载到 `engine/skill_loader.py`，扩充可调用技能库
  4. 自动检测与现有 skills 冲突，避免重复
- **风险提示**：生成的 Skill 质量参差，需人工 review
- **预期收益**：技能库从当前 ~10 个扩展到 50+，覆盖更多 DeFi 项目 → 内容广度 +200%

### 9. naxiaoduo/1000UserGuide ⭐ 4.30 P0
- **产品形态**：300+ 国内外早期用户获取渠道清单，HTML 静态站
- **商业模式**：开源，作者靠渠道代运营变现
- **可复用模块**：`channels.json` / `data.json` 数据源
- **接入步骤**：
  1. 克隆项目，提取渠道数据为 YAML
  2. 导入 `company/knowledge/marketing/channels.yaml`
  3. PM 角色按渠道优先级（免费 / 国内 / AI 受众）排期发布
  4. COO 角色每周复盘 Top 10 渠道转化率
- **风险提示**：部分渠道需翻墙；部分渠道已被封号风险（如 Reddit r/CryptoCurrency 限制）
- **预期收益**：新流量入口 → 月新增 100-500 自然用户

### 10. ccxt/ccxt ⭐ 4.30 P0
- **产品形态**：100+ 交易所统一 API，支持现货/合约/期权，Python/JS/PHP
- **商业模式**：开源 MIT
- **可复用模块**：`ccxt.binance`、`ccxt.coinbase`、`ccxt.kraken` 等
- **接入步骤**：
  1. `pip install ccxt` 装入 `engine/` 环境
  2. 在 `engine/market_analyzer.py` 新增 `CCXTProvider`，与现有 CoinGecko 并列
  3. 当 CoinGecko 限流时降级到 ccxt（直接调交易所 API）
  4. 抓取 Top 20 币种的实时订单簿深度，作为深度分析报告素材
- **风险提示**：交易所 API 大陆访问需翻墙；无需 API key 即可读公共数据
- **预期收益**：数据源稳定性 +90% → 深度分析内容质量提升 → 月 +$10-30

### 荣誉提名（11-15）
- **ComposioHQ/awesome-claude-skills** (4.30 P0)：66.2k Claude Skills 集合，扩充技能库
- **TauricResearch/TradingAgents** (4.15 P0)：89.3k 多 Agent 金融交易框架，市场分析素材
- **dongbeixiaohuo/writing-agent** (4.20 P0)：Claude Code 全栈写作系统，去 AI 味
- **microsoft/playwright-mcp** (4.20 P0)：MCP 协议标准化浏览器交互
- **D4Vinci/Scrapling** (4.00 P0)：自适应反爬，66.6k stars

---

## 八、与现有 AutoCorp 体系的融合矩阵

```
现有模块                          → 推荐替换/补充
─────────────────────────────────────────────────────────────
engine/llm_client.py             → + chopratejas/headroom (Token 压缩)
                                 → + open-webui (本地网关)
                                 → + ollama (本地推理)

engine/market_analyzer.py        → + ccxt (100+ 交易所)
                                 → + TauricResearch/TradingAgents (多 Agent 分析)
                                 → + Agent-Reach (社交讨论抓取)

engine/content_writer.py         → + MinerU (PDF → MD)
                                 → + claude-seo (SEO brief)
                                 → + seo-blog-writer-claude (写作 Skill)
                                 → + writing-agent (去 AI 味)
                                 → + Skill_Seekers (技能库扩充)

engine/outline_generator.py      → + claude-seo/content-brief-generator
                                 → + 1000UserGuide (选题角度参考)

engine/seo_scorer.py             → + claude-seo/technical-seo-auditor
                                 → + claude-seo/schema-markup-generator

engine/browser_runner.py         → + browser-use (自愈式)
                                 → + browser-harness (重试机制)
                                 → + playwright-mcp (MCP 协议)
                                 → + CloakBrowser (反检测)
                                 → + Skyvern (备选)

engine/scraper.py                → + Scrapling (自适应反爬)
                                 → + MediaCrawler (多平台社交)
                                 → + firecrawl (大规模 API)
                                 → + ai-goofish-monitor (闲鱼套利)

engine/payment_bridge.py         → + polarsource/polar (订阅/打赏)
                                 → + uselotus/lotus (定价)

engine/twitter_bot.py            → + Agent-Reach (零 API 费用)
engine/reddit_bot.py             → + Agent-Reach

新业务线
─────────────────────────────────────────────────────────────
company/projects/video-content/  → MoneyPrinterTurbo (短视频)
company/projects/saas-product/   → wasp-lang/open-saas (SaaS 模板)
company/projects/wechat-channel/ → chatgpt-on-wechat (微信引流)
```

---

## 九、数据完整性与置信度提示

1. **GitHub Trending 主源全屏蔽**：所有 Trending 数据来自第三方聚合，stars 数与时间窗可能与 GitHub 实际有偏差，但项目身份可信
2. **Topics 数据质量更高**：13 个 topic 中 10 个直接 WebFetch 成功，stars 数可信
3. **Rust 数据缺失**：仅 turbovec 一项可考，建议后续人工浏览器复核
4. **Crypto topic 数据陈旧**：返回 2018 年缓存，已用 ccxt/TradingAgents 等其他源补充
5. **HelloGitHub/GitCode 降级**：JS 渲染失败，仅获取 3+6 个项目，未达 5-10 条目标
6. **建议下次执行**：先让用户在 Chrome 完成 GitHub 登录态，配合 agent-browser 自动化抓取，可绕过当前屏蔽

---

## 十、执行优先级建议

### 本周内完成（P0 Top 5）
1. **AgriciDaniel/claude-seo** — 0.5 天，立即提升 SEO 内容质量
2. **rediumvex/seo-blog-writer-claude** — 0.5 天，与 #1 配套
3. **naxiaoduo/1000UserGuide** — 0.5 天，扩充引流渠道清单
4. **opendatalab/MinerU** — 1 天，解决 PDF 白皮书内容源问题
5. **Panniantong/Agent-Reach** — 1 天，解决社交数据采集痛点

### 下周完成（P0 6-10）
6. ccxt/ccxt — 1 天
7. yusufkaraaslan/Skill_Seekers — 1 天
8. browser-use/browser-use — 1.5 天
9. ComposioHQ/awesome-claude-skills — 1 天
10. dongbeixiaohuo/writing-agent — 1 天

### 月内推进（P0 11-19 + P1 精选）
- polarsource/polar、MoneyPrinterTurbo、TradingAgents、playwright-mcp、browser-harness、Scrapling、lotus、Skyvern
- open-webui、headroom、langgraph、wasp-lang/open-saas

---

## 十一、风险与合规清单

| 项目 | 风险类型 | 缓解措施 |
|------|----------|----------|
| Panniantong/Agent-Reach | ToS 灰色（社交平台反爬） | 仅做读取，不发帖；频率 ≤ 1 次/分钟 |
| NanmiCoder/MediaCrawler | 同上 | 仅抓公开数据，不存储 PII |
| CloakHQ/CloakBrowser | 反检测可能触发法律风险 | 仅用于合规自动化发布，不用于绕过付费墙 |
| zhayujie/chatgpt-on-wechat | 微信封号风险 | 使用小号 + 限频 5 条/天 |
| MoneyPrinterTurbo | 素材版权 | 仅用 Pexels/Pixabay/CC0 素材 |
| TauricResearch/TradingAgents | 金融建议合规 | 输出标注"非投资建议" |
| MinerU | AGPL 衍生作品义务 | 仅内部使用，不分发修改版 |
| firecrawl | 付费 API | 严格在免费额度内（500 页/月） |

---

## 十二、结论

本次扫描共评估 40 个候选项目，识别出 **19 个 P0 立即采纳 + 18 个 P1 周内立项 + 3 个 P2 战略观察**。

**核心结论**：AutoCorp 当前最小变现闭环（SEO → Paragraph → 社交引流）已经被开源生态"完整覆盖"，存在 5 个可立即替换/增强的关键模块：
1. **内容采集**：MinerU + Skill_Seekers + 1000UserGuide
2. **内容生产**：claude-seo + seo-blog-writer-claude + writing-agent
3. **浏览器自动化**：browser-use + browser-harness + playwright-mcp
4. **数据源**：ccxt + TradingAgents + Agent-Reach
5. **变现基础设施**：polar + lotus

按本报告执行，预计 1 周内 AutoCorp 内容产出效率提升 2-3 倍，2 周内新业务线（短视频/SaaS）可启动，月收益预期从当前 $4.5/天 提升至 $20-50/天。

---

## 附录：原始数据索引
- [_raw-trending.md](_raw-trending.md) — GitHub Trending 15 维度原始抓取
- [_raw-topics.md](_raw-topics.md) — 13 个 Topics 高星仓库原始抓取
- [_raw-cn-sources.md](_raw-cn-sources.md) — 中文开源源（HelloGitHub/GitCode/Gitee/WebSearch）
- [降级事件记录](../../human-requests/2026-06-28-github-trending-degradation.md) — 17 起降级事件详情

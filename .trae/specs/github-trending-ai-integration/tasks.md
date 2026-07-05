# Tasks - GitHub 热门 AI 项目深度调研与集成评估

按依赖顺序排列。Phase 1 是能力差距分析（先识别 AI 公司智力短板，再针对性找项目），Phase 2 是 GitHub 热门项目调研（核心交付物），Phase 3 是集成推荐，Phase 4 是方法论升级。

## Phase 1: 能力差距分析（立即执行，无依赖）

- [x] Task 1: AI 公司能力差距分析
  - [x] SubTask 1.1: 创建 `company/knowledge/tech-radar/capability-gap-analysis-2026-06-30.md`
  - [x] SubTask 1.2: 识别 4 类智力短板：深度思考 / 市场分析 / 自我验证 / 长期记忆
  - [x] SubTask 1.3: 每个短板给出：现状描述、目标描述、可补足的 GitHub 项目类型、集成优先级
  - [x] SubTask 1.4: 对照近期失误（Layer3 循环推荐 / 闲鱼无竞争力 / 实时验证只验平台在线）定位是哪类短板
  - [x] SubTask 1.5: 给出短板优先级排序（哪个短板最致命，先补哪个）

## Phase 2: GitHub 热门 AI 项目深度调研（Phase 1 完成后，核心交付物）

- [x] Task 2: GitHub 热门 AI 项目深度调研报告
  - [x] SubTask 2.1: 创建 `company/knowledge/tech-radar/github-trending-ai-projects-2026-06-30.md`
  - [x] SubTask 2.2: 方向 1 - 多 agent 编排框架：WebSearch + WebFetch 验证 AutoGen / CrewAI / LangGraph / OpenHands / SWE-agent 等 2026 版本
  - [x] SubTask 2.3: 方向 2 - 深度研究引擎：WebSearch + WebFetch 验证 GPT Researcher / STORM / Devika / Sweep / OpenResearch 等
  - [x] SubTask 2.4: 方向 3 - 自我反思与验证机制：WebSearch + WebFetch 验证 Reflexion / Self-Refine / 自我批评 agent 等
  - [x] SubTask 2.5: 方向 4 - 市场分析与财经 AI：WebSearch + WebFetch 验证 FinGPT / TradingAgents / AI 财报分析等
  - [x] SubTask 2.6: 方向 5 - 内容生产增强：WebSearch + WebFetch 验证长文写作 agent / SEO 优化 AI / 多语言内容生成等
  - [x] SubTask 2.7: 方向 6（可选）- 长期记忆与知识库：WebSearch + WebFetch 验证 Mem0 / Zep / 向量记忆层等
  - [x] SubTask 2.8: 每条项目包含 8 要素
  - [x] SubTask 2.9: 报告末尾给出"对 AI 公司变现有巨大帮助的 Top 5 项目"初筛排序

## Phase 3: 集成推荐（Phase 2 完成后）

- [x] Task 3: 集成推荐报告
  - [x] SubTask 3.1: 创建 `company/knowledge/tech-radar/integration-recommendation-2026-06-30.md`
  - [x] SubTask 3.2: 从调研项目中筛选 Top 3-5 个"集成价值高 + 集成成本低"项目
  - [x] SubTask 3.3: 每个推荐项目给出：集成路径、预期增强的能力、对变现的具体帮助
  - [x] SubTask 3.4: 每个推荐项目给出 7 天集成计划（Day1-7 具体动作）
  - [x] SubTask 3.5: 诚实评估：哪些项目"看起来火但对 AI 公司没用"，明确不推荐及原因

## Phase 4: 方法论升级（Phase 3 完成后）

- [x] Task 4: CEO 预筛方法论新增"能力增强检查"
  - [x] SubTask 4.1: 修改 `company/knowledge/strategic-research/ceo-competitiveness-prescreen.md`
  - [x] SubTask 4.2: 新增"问题 7：能力增强检查"（推荐是基于深度分析还是表面抓取？是否经过多轮推理+假设验证+证伪尝试？）
  - [x] SubTask 4.3: 判定规则从"6 个问题"升级为"7 个问题"
  - [x] SubTask 4.4: 记录 Layer3 循环案例作为"能力增强检查"的反面案例（表面抓取导致循环推荐）

---

# Task Dependencies

- Task 1（能力差距分析）独立，无依赖
- Task 2（GitHub 调研）依赖 Task 1（调研需针对 AI 公司短板找项目）
- Task 3（集成推荐）依赖 Task 2（需调研结果才能筛选推荐）
- Task 4（方法论升级）依赖 Task 3（需集成推荐完成后才能定义"深度分析"标准）

## Parallelizable Work

- Task 1（能力差距分析）独立先行
- Task 4（方法论升级）可在 Task 3 完成后并行执行（与其他无依赖工作并行）

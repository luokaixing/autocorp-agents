# GitHub 热门 AI 项目深度调研与集成评估 Spec

## Why

AI 公司当前在变现路径上反复出现"循环推荐已证伪方案""实时验证只验平台可访问不验任务可做"等智力失败。用户判断：这些问题的根因是 AI 公司自身不够智能、不够强、不够稳——缺少真正的深度思考与市场分析能力。GitHub 上 2025-2026 年有大量热门 AI 项目（如多 agent 框架、深度研究引擎、自我反思机制、市场分析工具等），需要实时调研哪些能直接增强 AI 公司的核心能力，从而让变现路径判断更准、产出更稳、最终对变现产生巨大帮助。

## What Changes

- **新增** `company/knowledge/tech-radar/github-trending-ai-projects-2026-06-30.md` —— GitHub 2026 年热门 AI 项目深度调研报告，覆盖至少 5 个方向（多 agent 编排 / 深度研究引擎 / 自我反思与验证 / 市场分析 / 内容生产增强），每条项目实时验证 + 集成价值评估 + 集成成本评估
- **新增** `company/knowledge/tech-radar/integration-recommendation-2026-06-30.md` —— 集成推荐报告，从调研项目中筛选 Top 3-5 个"对 AI 公司变现有巨大帮助"的项目，给出具体集成路径
- **新增** `company/knowledge/tech-radar/capability-gap-analysis-2026-06-30.md` —— AI 公司能力差距分析，对照 GitHub 热门项目能力，识别 AI 公司当前智力短板（深度思考 / 市场分析 / 自我验证 / 长期记忆）
- **修改** `company/knowledge/strategic-research/ceo-competitiveness-prescreen.md` —— 在竞争力预筛方法论中新增"能力增强检查"环节，避免再次出现"智力失败导致推荐失误"

## Impact

- Affected specs:
  - `us-market-revenue-research` —— 美国市场研究的能力基础依赖本次调研的深度研究引擎
  - `strategic-reanalysis-viable-path` —— 战略重分析能力依赖本次调研的自我反思机制
- Affected code:
  - `engine/` 目录可能新增深度研究 / 反思 / 市场分析模块
  - `engine/crypto/realtime_opportunity_scanner.py` —— 可能集成更强的市场分析能力
  - `engine/agents/` —— 多 agent 编排可能升级
- Affected operations:
  - 每日晨会的"机会扫描"环节可能升级为"深度研究 + 自我反思 + 市场分析"三段式
  - 推荐前预筛新增"能力增强检查"——确保推荐基于深度分析而非表面抓取
- Affected user experience: AI 公司从"会抓网页的脚本"升级为"能深度思考 + 自我验证 + 市场分析的智能体"，变现路径判断更准，循环错误减少

## ADDED Requirements

### Requirement: GitHub 热门 AI 项目深度调研

AI 公司 SHALL 进行一次 GitHub 2026 年热门 AI 项目的深度调研，覆盖至少 5 个方向，每条项目实时验证 + 集成价值评估。

#### Scenario: 多方向调研
- **WHEN** 本 spec 实施
- **THEN** 生成 `company/knowledge/tech-radar/github-trending-ai-projects-2026-06-30.md`
- **AND** 报告必须覆盖以下 5 个方向（每条用 WebSearch 2026 年 + WebFetch GitHub 实时验证）：
  - 方向 1：多 agent 编排框架（如 AutoGen / CrewAI / LangGraph / OpenHands / SWE-agent 等的 2026 版本）
  - 方向 2：深度研究引擎（如 GPT Researcher / STORM / Devika / Sweep / OpenResearch 等）
  - 方向 3：自我反思与验证机制（如 Reflexion / Self-Refine / Constitutional AI / 自我批评 agent 等）
  - 方向 4：市场分析与财经 AI（如 FinGPT / TradingAgents / AI 财报分析 / 市场情绪分析等）
  - 方向 5：内容生产增强（如长文写作 agent / SEO 优化 AI / 多语言内容生成等）
  - 方向 6（可选）：长期记忆与知识库（如 Mem0 / Zep / 向量记忆层等）
- **AND** 每条项目必须包含 8 要素：
  1. 项目名 + GitHub URL（实时验证可访问）
  2. Star 数 + 最近活跃度（2026-06-30 实时抓取）
  3. 核心能力描述
  4. 与 AI 公司当前能力的差距（这个项目能补什么短板）
  5. 集成价值评估（对 AI 公司变现有巨大帮助的程度，1-5 星）
  6. 集成成本评估（学习曲线 / 依赖复杂度 / 改造工作量，1-5 星）
  7. 真实案例或文档引用（非记忆，实时抓取 README）
  8. 风险与限制（许可证 / 中文支持 / Windows 兼容 / TRAE IDE 内可用性）

#### Scenario: 实时验证强制
- **WHEN** 推荐任何项目
- **THEN** 必须用 WebSearch（2026 年）+ WebFetch 访问 GitHub 仓库验证当日可访问性与活跃度
- **AND** 验证失败的项目标记为"未验证"，不推荐
- **AND** 禁止凭 AI 记忆推荐（知识截止 2025 年 8 月）

### Requirement: 集成推荐与能力差距分析

AI 公司 SHALL 基于调研结果，筛选 Top 3-5 个"对变现有巨大帮助"的项目并给出集成路径，同时识别 AI 公司当前能力短板。

#### Scenario: 集成推荐
- **WHEN** 调研完成
- **THEN** 生成 `company/knowledge/tech-radar/integration-recommendation-2026-06-30.md`
- **AND** 从调研项目中筛选 Top 3-5 个项目，按"集成价值高 + 集成成本低"排序
- **AND** 每个推荐项目给出：集成路径（哪个引擎模块 / 怎么集成）、预期增强的能力、对变现的具体帮助、7 天集成计划

#### Scenario: 能力差距分析
- **WHEN** 调研完成
- **THEN** 生成 `company/knowledge/tech-radar/capability-gap-analysis-2026-06-30.md`
- **AND** 对照 GitHub 热门项目能力，识别 AI 公司当前 4 类智力短板：
  1. 深度思考能力（当前：表面抓取；目标：多轮推理 + 假设验证）
  2. 市场分析能力（当前：抓平台列表；目标：财报级深度分析 + 趋势预测）
  3. 自我验证能力（当前：把"平台在线"当"任务可做"；目标：反思 + 证伪 + 黑名单自动维护）
  4. 长期记忆能力（当前：每次对话从零开始；目标：跨会话记忆 + 教训积累）
- **AND** 每个短板给出：现状描述、目标描述、可补足的 GitHub 项目、集成优先级

### Requirement: 推荐前能力增强检查

AI 公司 SHALL 在 CEO 竞争力预筛方法论中新增"能力增强检查"环节，确保推荐基于深度分析而非表面抓取。

#### Scenario: 能力增强检查
- **WHEN** AI 公司准备推荐任何变现路径
- **THEN** 虚拟 CEO 必须先回答："这个推荐是基于深度分析还是表面抓取？"
- **AND** 如答"表面抓取"或"不确定"，方案标记为"未通过预筛"
- **AND** 此检查环节记录到 `company/knowledge/strategic-research/ceo-competitiveness-prescreen.md`

## MODIFIED Requirements

### Requirement: CEO 竞争力预筛方法论

原方法论含 6 个问题（壁垒/需求/流量/付费意愿/现有资源匹配/已证伪检查），现新增第 7 个问题"能力增强检查"：

- **问题 7：能力增强检查**
  - 这个推荐是基于深度分析还是表面抓取？
  - 是否经过多轮推理 + 假设验证 + 证伪尝试？
  - 如答"表面抓取"或"未经过多轮推理"，方案标记为"未通过预筛"
- 判定规则从"6 个问题"升级为"7 个问题"

## REMOVED Requirements

无移除。本次为纯增量调研与能力增强。

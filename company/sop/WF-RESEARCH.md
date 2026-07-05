---
id: WF-RESEARCH
name: 市场调研与选题工作流 SOP
trigger: 每日 08:30 Phase-Research 触发（Phase-Morning 完成后自动触发）
owner_role: product_manager
inputs:
  - company/operations/morning-decisions-YYYY-MM-DD.md
  - company/knowledge/market-research/_raw-trending.md
  - company/knowledge/market-research/_raw-topics.md
  - company/knowledge/opportunities/radar-YYYY-MM-DD.md
outputs:
  - company/knowledge/market-research/topics-YYYY-MM-DD.md
  - company/projects/<product>/prd.md
acceptance_criteria:
  - topics-YYYY-MM-DD.md 已产出且含至少 5 个选题
  - 每个选题含痛点/目标用户/竞品/变现路径/预期 ROI 五要素
  - 至少 1 个选题被标记为「推荐立项」并附 ROI 计算明细
  - PRD（若 CEO 已立项）已产出且 MVP 范围 ≤ 4 周
  - 选题清单已 publish topic=research.topics_ready 消息
sla_minutes: 60
fallback: 若 Phase-Morning 未产出 morning-decisions，PM 沿用昨日选题方向自主扫描；若 LLM 后端失败，基于 _raw-trending.md 关键词生成基础选题清单（仅标题），标记 sop_compliance=degraded
---

# 市场调研与选题工作流 SOP

## 工作流概述
本工作流对应 Phase-Research，由 PM 主持。从市场情报出发，识别用户痛点 → 定义目标用户 → 分析竞品 → 设计变现路径 → 产出可立项的选题清单与 PRD。是后续 WF-DESIGN / WF-BUILD 的前置工作流。

## 工作流参与者
- **主责**：PM（product_manager）
- **协作**：CEO（决策立项）、CTO（技术可行性预评估，可选）

## Actions（执行步骤）

### Stage 1：情报聚合（10 分钟内）
1. 读取 `company/operations/morning-decisions-YYYY-MM-DD.md`，了解 CEO 当日战略方向与重点
2. 读取 `company/knowledge/market-research/_raw-trending.md`，获取 CoinGecko 涨幅榜 / Twitter 热点 / Reddit 热帖
3. 读取 `company/knowledge/market-research/_raw-topics.md`，获取近期积累的话题素材
4. 读取 `company/knowledge/opportunities/radar-YYYY-MM-DD.md`，了解机会雷达已识别的候选
5. 聚合去重，形成「候选选题池」（约 15-20 个）

### Stage 2：选题评估与排序（20 分钟内）
1. 对候选选题池逐个评估五要素：
   - **痛点**：用户具体痛点与现有方案不足（必须可量化描述）
   - **目标用户**：画像与付费意愿（含用户规模估算）
   - **竞品**：头部竞品 + 差异化机会
   - **变现路径**：定价模型 + 预期 MRR 区间
   - **预期 ROI**：预期收入 / 预期成本（ROI < 1.5x 淘汰）
2. 按 ROI 排序，取 Top 5-8 写入选题清单
3. 标记至少 1 个「推荐立项」选题，附详细 ROI 计算明细

### Stage 3：产出选题清单（10 分钟内）
1. 写入 `company/knowledge/market-research/topics-YYYY-MM-DD.md`，格式：
   ```markdown
   # YYYY-MM-DD 选题清单

   ## 推荐立项
   - **选题**: Uniswap V4 Hook 机制深度分析
   - **预期 ROI**: 2.5x
   - **预期成本**: $5
   - **预期收入**: $12.5
   - **理由**: DeFi 热度上升 35%，目标渠道转化率 8%

   ## 候选选题（按 ROI 降序）
   ### 1. Uniswap V4 Hook 机制深度分析
   - 痛点: ...
   - 目标用户: ...
   - 竞品: ...
   - 变现路径: ...
   - 预期 ROI: 2.5x

   ### 2. ...
   ```
2. publish `topic=research.topics_ready`，payload 含 `{date, topic_count, recommended_topic, recommended_roi}`
3. 若发现高价值机会（ROI > 3x），额外 publish `topic=research.hot_opportunity` 通知 CEO 立项

### Stage 4：产出 PRD（按需，CEO 立项后触发）（20 分钟内）
1. 等待 CEO 基于 morning-decisions 决定立项后，进入 PRD 撰写
2. PRD 必须包含 7 个章节：
   - 痛点（用户具体痛点 + 现有方案不足）
   - 目标用户（画像 + 付费意愿 + 规模估算）
   - 竞品（头部竞品 + 差异化机会 + 功能对比表）
   - 变现路径（定价模型 + 预期 MRR + 北极星指标）
   - MVP 范围（**≤ 4 周开发量**，按模块拆分）
   - 功能需求清单（按优先级 P0/P1/P2 排序）
   - 验收标准（可量化的成功指标）
3. 写入 `company/projects/<product>/prd.md`
4. publish `topic=research.prd_ready`，payload 含 `{product, mvp_weeks, expected_roi, modules}`

## Notes（注意事项）
- **数据来源**：所有选题必须基于 `_raw-trending.md` / `_raw-topics.md` / `radar-*.md` 中的实际数据，禁止凭空想象
- **变现导向**：所有选题与需求必须能映射到可量化的变现假设，禁止"为了做而做"
- **MVP 约束**：PRD 的 MVP 范围不得超过 4 周开发量，超出则拆分多期
- **Phase 衔接**：本工作流完成后通过 `publish(topic="research.prd_ready")` 触发 WF-DESIGN
- **降级路径**：Phase-Morning 未产出时 PM 自主扫描；LLM 失败时产出标题级清单
- **超时处理**：超过 60 分钟未完成，强制结束当前工作流，已有产出保留，未完成项标记 `phase_timeout`

## Examples（示例）

### 示例：选题清单 publish 消息
```json
{
  "topic": "research.topics_ready",
  "from_role": "product_manager",
  "to_role": null,
  "payload": {
    "date": "2026-06-29",
    "topic_count": 7,
    "recommended_topic": "Uniswap V4 Hook 机制深度分析",
    "recommended_roi": 2.5,
    "topics_path": "company/knowledge/market-research/topics-2026-06-29.md"
  }
}
```

### 示例：PRD 完成消息触发下游
```json
{
  "topic": "research.prd_ready",
  "from_role": "product_manager",
  "to_role": "architect",
  "payload": {
    "product": "seo-content-generator",
    "mvp_weeks": 2,
    "expected_roi": 3.2,
    "modules": ["content_generator", "seo_optimizer", "channel_adapter", "analytics_tracker"],
    "prd_path": "company/projects/seo-content-generator/prd.md"
  }
}
```

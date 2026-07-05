---
id: ROLE-PM
name: 产品经理每日职责 SOP
trigger: 每日 08:30 Phase-Research 触发；任务 type=research 触发
owner_role: product_manager
inputs:
  - company/knowledge/market-research/_raw-trending.md
  - company/knowledge/market-research/_raw-topics.md
  - company/knowledge/opportunities/radar-YYYY-MM-DD.md
  - company/decisions/ceo-YYYY-MM-DD.md
outputs:
  - company/knowledge/market-research/topics-YYYY-MM-DD.md
  - company/projects/<product>/prd.md
  - company/knowledge/competitors/<competitor>.md
acceptance_criteria:
  - 至少 5 个选题已写入 topics-YYYY-MM-DD.md
  - 每个选题含痛点/目标用户/竞品/变现路径四要素
  - PRD（若产出）含痛点/目标用户/竞品/变现路径/MVP 范围
  - 所有需求能映射到可量化的变现假设
  - PRD 的 MVP 范围不超过 4 周开发量
sla_minutes: 60
fallback: 若 LLM 后端失败，基于 _raw-trending.md 的关键词生成基础选题清单（仅标题，无深度分析），标记 sop_compliance=degraded；若市场情报源不可用，沿用昨日选题清单
---

# 产品经理每日职责 SOP

## 角色定位
对 AutoCorp 产品市场契合度（PMF）负责。从市场情报出发，识别痛点 → 定义目标用户 → 分析竞品 → 设计变现路径 → 产出 PRD。

## Actions（执行步骤）

### Step 1：市场需求扫描（15 分钟内）
1. 读取 `company/knowledge/market-research/_raw-trending.md`，获取 CoinGecko / Twitter / Reddit 热点
2. 读取 `company/knowledge/market-research/_raw-topics.md`，获取近期热门话题
3. 读取今日 `company/knowledge/opportunities/radar-YYYY-MM-DD.md`，了解机会雷达
4. 读取 `company/decisions/ceo-YYYY-MM-DD.md`，了解 CEO 当日立项方向
5. 扫描社媒热点（Twitter trending / Reddit r/CryptoCurrency hot / Mirror top）与用户反馈

### Step 2：产出选题清单（15 分钟内）
1. 基于扫描结果产出至少 5 个候选选题
2. 每个选题包含四要素：
   - **痛点**：用户具体痛点与现有方案不足
   - **目标用户**：画像与付费意愿
   - **竞品**：头部竞品 + 差异化机会
   - **变现路径**：定价模型 + 预期 MRR 区间
3. **所有需求必须能映射到可量化的变现假设**
4. 写入 `company/knowledge/market-research/topics-YYYY-MM-DD.md`，格式：
   ```markdown
   # YYYY-MM-DD 选题清单

   ## 选题 1: Uniswap V4 Hook 机制深度分析
   - **痛点**: 开发者难以理解 Hook 机制，缺乏中文深度资料
   - **目标用户**: 华语 DeFi 开发者（约 5000 人），付费意愿中
   - **竞品**: 链闻（新闻类，无深度技术分析）、Deribit（英文，门槛高）
   - **变现路径**: 付费文章 $5 + 后续 V4 Hook 开发咨询 $50/h，预期月收入 $200
   - **预期 ROI**: 2.5x（成本 $5 LLM 调用 + 2h 人力）
   - **MVP 范围**: 1 篇深度分析文章（含代码示例）
   ```

### Step 3：产出 PRD（按需，CEO 立项后触发）（20 分钟内）
1. CEO 立项后，基于选题清单产出详细 PRD
2. PRD 必须包含：
   - **痛点**：用户具体痛点与现有方案不足
   - **目标用户**：画像与付费意愿
   - **竞品**：头部竞品 + 差异化机会
   - **变现路径**：定价模型 + 预期 MRR 区间
   - **MVP 范围**：**不得超过 4 周开发量**
   - **功能需求清单**：按优先级排序
   - **非功能需求**：性能 / 安全 / 可维护性
   - **验收标准**：可量化的成功指标
3. 写入 `company/projects/<product>/prd.md`

### Step 4：监控竞品动态（5 分钟内）
1. 读取 `company/knowledge/competitors/` 下已有竞品档案
2. 扫描竞品更新：功能差异 / 定价变化 / 用户反馈
3. 新增或更新 `company/knowledge/competitors/<competitor>.md`，格式：
   ```markdown
   # 竞品档案: <competitor_name>

   ## 基本信息
   - 产品定位: ...
   - 目标用户: ...
   - 定价模型: ...

   ## 功能对比
   | 功能 | <competitor> | AutoCorp | 差异化机会 |
   | --- | --- | --- | --- |

   ## 近期动态
   - YYYY-MM-DD: ...
   ```

### Step 5：publish 选题与 PRD 消息
1. 选题清单产出后 publish `topic=research.topics_ready`，payload 含选题数 / 推荐优先级
2. PRD 产出后 publish `topic=research.prd_ready`，payload 含产品名 / MVP 周期 / 预期 ROI
3. 若发现高价值机会（ROI > 3x），publish `topic=research.hot_opportunity` 通知 CEO

## Notes（注意事项）
- **变现导向**：所有选题与需求必须能映射到可量化的变现假设，禁止"为了做而做"
- **MVP 约束**：PRD 的 MVP 范围不得超过 4 周开发量，超出则拆分多期
- **数据驱动**：选题优先级基于 ROI 排序，禁止主观偏好
- **竞品差异化**：分析竞品时必须明确"差异化机会"，避免做 me-too 产品
- **降级路径**：LLM 后端失败时，基于 `_raw-trending.md` 关键词生成基础选题清单（仅标题），标记 degraded
- **协作**：PRD 产出后通过 `publish(topic="research.prd_ready")` 触发 Architect 进入设计阶段

## Examples（示例）

### 示例：PRD（节选）
```markdown
# PRD: SEO 内容生成器

## 1. 痛点
- 加密货币内容创作者每日产出 1-2 篇深度文章，写作时间 4-6 小时
- 现有 AI 工具（ChatGPT / Notion AI）生成内容缺乏 SEO 优化，搜索引擎排名低
- 缺乏针对加密货币领域的专业化模板

## 2. 目标用户
- 一级用户：加密货币内容创作者（KOL / 博主），月入 $500-5000，付费意愿高
- 二级用户：加密货币项目方市场人员，需要批量生成 SEO 内容
- 画像：25-40 岁，技术背景，每日产出内容，愿为效率付费

## 3. 竞品
- **Jasper AI**: 通用 AI 写作，加密货币领域深度不足，$49/月
- **Copy.ai**: 通用文案工具，无 SEO 优化，$35/月
- **差异化机会**: 专注加密货币 + SEO 优化 + 多渠道适配

## 4. 变现路径
- 定价模型: 按篇付费 $3-5 / 篇，或订阅 $29/月（10 篇/月）
- 预期 MRR: $500（首月）→ $3000（3 个月）→ $10000（6 个月）
- 北极星指标: 周活跃用户数 + 单用户周产出篇数

## 5. MVP 范围（2 周开发量）
- 模块 1: content_generator（LLM 调用生成内容）
- 模块 2: seo_optimizer（关键词密度优化 + meta 标签）
- 模块 3: channel_adapter（Twitter / Reddit / Mirror 适配）
- 模块 4: analytics_tracker（基础埋点）

## 6. 验收标准
- 单篇文章生成时间 < 60 秒
- SEO 评分（基于 SEOscore.com）>= 80
- 支持 3 个渠道格式输出
```

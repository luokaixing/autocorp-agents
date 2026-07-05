---
id: WF-PROMOTE
name: 内容发布与渠道推广工作流 SOP
trigger: 每日 15:00 Phase-Promote 触发（监听 topic=task.done.test 消息且无 P0/P1 缺陷后启动）
owner_role: coo
inputs:
  - company/projects/<product>/source/
  - company/projects/<product>/delivery-notes.md
  - company/projects/<product>/test-report.md
  - company/knowledge/marketing/channels.yaml
  - company/config/ledger.yaml
outputs:
  - company/marketing/<channel>-posts-YYYY-MM-DD.md
  - company/operations/coo-daily-YYYY-MM-DD.md
  - company/knowledge/marketing/promotion-plan-<product>.md
acceptance_criteria:
  - 至少 1 份推广物料已产出（文案/海报/社媒片段）
  - 推广物料定价不低于变动成本
  - 首次发布到新渠道已触发 DecisionGate 人工确认
  - 渠道预算分配通过 ledger 校验（sum <= balance * 0.3）
  - 运营日报已产出且含关键指标 + 异常告警
  - 发布完成已 publish topic=promotion.published 消息
sla_minutes: 60
fallback: 若 WF-BUILD 产物缺失（source/ 或 test-report.md），跳过本次推广并在运营日报标记 reason=missing_product；若 LLM 后端失败，使用 channels.yaml 标准文案模板生成物料；若 Chrome 自动化失败，物料产出但延迟发布，publish topic=promotion.deferred
---

# 内容发布与渠道推广工作流 SOP

## 工作流概述
本工作流对应 Phase-Promote，由 COO 主持。从 WF-BUILD 产出的内容出发，按渠道适配生成物料 → 决策门禁校验 → 渠道发布 → 追踪转化率 → 产出运营日报，形成"内容 → 渠道 → 收入"的闭环。

## 工作流参与者
- **主责**：COO（首席运营官）
- **协作**：Programmer（提供产品交付物）、CEO（决策门禁确认）

## Actions（执行步骤）

### Stage 1：交付物核验与渠道清单加载（5 分钟内）
1. 读取 `company/projects/<product>/source/` 下当日产出的内容文件
2. 读取 `company/projects/<product>/test-report.md`，确认无 P0/P1 缺陷（有则不进入本工作流）
3. 读取 `company/projects/<product>/delivery-notes.md`，了解交付清单与已知问题
4. 读取 `company/knowledge/marketing/channels.yaml`，获取所有渠道清单与配置
5. 读取 `company/config/ledger.yaml`，确认预算可用余额
6. 若 source/ 或 test-report.md 缺失 → 跳过本次推广，运营日报标记 `reason=missing_product`

### Stage 2：按渠道适配生成推广物料（25 分钟内）
1. 读取当日产出的内容（文章 / 代码 / 工具）
2. 按渠道适配生成物料：
   - **Twitter**：280 字符内，含 1-2 个 hashtag，附图片或 GIF
   - **Reddit**：标题 + 正文，按目标 subreddit 风格调整（如 r/CryptoCurrency 偏深度分析）
   - **Mirror / Medium**：长文格式，含标题/摘要/正文/标签
   - **Twitter Thread**：5-10 条推文串联，适合技术深度内容
3. 定价策略：所有付费内容定价 `>= 变动成本`（LLM API 调用费 + 平台手续费）
4. 写入 `company/marketing/<channel>-posts-YYYY-MM-DD.md`

### Stage 3：决策门禁校验（5 分钟内）
1. 调用 `DecisionGate.check("external_publish", context)`：
   - **首次发布到新渠道** → 触发人工确认
   - 含敏感话题（政治 / 监管 / 争议项目）→ 触发人工确认
2. 调用 `DecisionGate.check("order_quote", context)`（若涉及付费内容）：
   - 定价 > $50 或折扣 > 20% → 触发人工确认
3. 用户拒绝 → publish `topic=promotion.cancelled`，物料归档不发布
4. 用户确认或无需门禁 → 进入 Stage 4

### Stage 4：渠道发布（10 分钟内）
1. 按渠道优先级（ROI 高的先发）依次发布：
   - 调用 `engine/social_reach.py` 或 Chrome 自动化发布到 Twitter / Reddit / Mirror
   - 失败的渠道记录到运营日报，标记 `sop_compliance=degraded`
2. 发布成功后记录：渠道 / 内容 ID / 发布时间 / 预期触达
3. publish `topic=promotion.published`，payload 含：
   ```json
   {
     "product": "<product>",
     "channels": ["twitter", "reddit", "mirror"],
     "content_ids": ["tw-xxx", "rd-yyy", "mr-zzz"],
     "expected_reach": 1500,
     "expected_revenue": 12.5
   }
   ```

### Stage 5：追踪渠道转化率（10 分钟内）
1. 查询昨日已发布内容的数据：阅读量 / 互动数 / 转化数 / 收入
2. 按渠道归因转化：用户从哪个渠道进入 → 完成什么动作 → 产生多少收入
3. 计算每个渠道的 ROI = 渠道收入 / 渠道成本
4. ROI < 1.0x 的渠道标记"暂停投放"，下次循环不再分配预算

### Stage 6：产出运营日报与推广方案（5 分钟内）
1. 写入 `company/operations/coo-daily-YYYY-MM-DD.md`，含：
   - 关键指标表（渠道 / 阅读量 / 互动数 / 转化数 / 转化率 / ROI）
   - 异常告警（🔴 红色 / 🟡 黄色）
   - 明日计划（优先投放 / 暂停投放）
2. 长期推广方案写入 `company/knowledge/marketing/promotion-plan-<product>.md`，含：
   - 渠道：主要获客渠道与预算分配
   - 定价：定价模型与心理锚点
   - 追踪指标：北极星指标 + 关键转化漏斗
   - 时间线：0-30 / 30-60 / 60-90 天里程碑

## Notes（注意事项）
- **预算红线**：所有渠道预算总和不得超过余额 30%，否则触发人工确认
- **定价底线**：定价不得低于变动成本（LLM API 调用费 + 平台手续费）
- **渠道适配**：同一内容在不同渠道需差异化（Twitter 短平快，Mirror 深度长文）
- **决策门禁超时**：超时 60 分钟未回复，按 `timeout_action=cancel` 取消发布
- **降级路径**：Chrome 自动化失败时物料产出但延迟发布，标记 `sop_compliance=degraded`
- **超时处理**：超过 60 分钟未完成，强制结束，已发布渠道保留，未发布标记 `phase_timeout`

## Examples（示例）

### 示例：渠道配置
```yaml
# channels.yaml
channels:
  - name: twitter
    type: social
    auto_publish: true
    daily_budget: $2
    rate_limit: 50 tweets/day
    api: engine/social_reach.py
  - name: reddit
    type: social
    auto_publish: true
    daily_budget: $1
    subreddits: [CryptoCurrency, defi, ethtrader]
  - name: mirror
    type: blog
    auto_publish: true
    daily_budget: $0
    upload_list: company/knowledge/marketing/mirror-upload-list.md
```

### 示例：推广物料
```markdown
# twitter-tweets-2026-06-29.md

## Tweet 1 (主线推广)
🧵 Uniswap V4 的 Hook 机制彻底改变了 DEX 的可组合性。

过去 V3 只能调参数，现在 V4 可以在交易生命周期的每个阶段注入自定义逻辑。

这意味着什么？
1. 自定义预言机
2. 动态手续费
3. MEV 抗性池

完整深度分析 👇 [Mirror 链接]
#DeFi #Uniswap #Web3

## Tweet 2 (Thread 续)
💡 Hook 的 8 个挂载点：
- beforeInitialize / afterInitialize
- beforeSwap / afterSwap
- beforeModify / afterModify
- beforeDonate / afterDonate

每个挂载点都可以注入自定义逻辑，相当于给 DEX 装上了「插件系统」。
```

### 示例：运营日报
```markdown
# coo-daily-2026-06-29.md
## 关键指标
| 渠道 | 阅读量 | 互动数 | 转化数 | 转化率 | ROI | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| Twitter | 1250 | 89 | 12 | 0.96% | 2.3x | 🟢 |
| Reddit | 580 | 34 | 5 | 0.86% | 1.8x | 🟢 |
| Mirror | 230 | 12 | 2 | 0.87% | 1.2x | 🟡 |

## 异常告警
- 🟡 Mirror 阅读量低于均值（历史 350），建议优化标题
- 🟢 Twitter ROI 2.3x 表现优异，建议追加预算

## 明日计划
- 优先投放渠道: Twitter（追加 $1 预算）
- 暂停投放渠道: 无
```

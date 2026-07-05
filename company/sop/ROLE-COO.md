---
id: ROLE-COO
name: 首席运营官每日职责 SOP
trigger: 每日 15:00 Phase-Promote 触发；任务 type=promote 触发
owner_role: coo
inputs:
  - company/projects/<product>/source/
  - company/knowledge/marketing/channels.yaml
  - company/config/ledger.yaml
  - company/operations/morning-decisions-YYYY-MM-DD.md
outputs:
  - company/marketing/<channel>-posts-YYYY-MM-DD.md
  - company/operations/coo-daily-YYYY-MM-DD.md
  - company/knowledge/marketing/promotion-plan-<product>.md
acceptance_criteria:
  - 至少 1 份推广物料已产出（文案/海报/社媒片段）
  - 推广物料定价不低于变动成本
  - 首次发布到新渠道已触发 DecisionGate 人工确认
  - 运营日报含关键指标 + 异常告警
  - 渠道预算分配通过 ledger 校验（余额充足）
sla_minutes: 60
fallback: 若 LLM 后端失败，使用 channels.yaml 中的标准文案模板生成物料，并标记 sop_compliance=degraded；若 Chrome 自动化失败，物料产出但延迟发布，publish task.deferred
---

# 首席运营官每日职责 SOP

## 角色定位
对 AutoCorp 产品推广和收入负责。从渠道、定价、追踪指标、时间线四个维度制定可落地的增长计划。

## Actions（执行步骤）

### Step 1：检查已发布内容数据（10 分钟内）
1. 读取 `company/knowledge/marketing/channels.yaml`，获取所有渠道清单（Twitter / Reddit / Mirror / Medium 等）
2. 对每个渠道查询昨日数据：阅读量、互动数（点赞/评论/转发）、转化数（点击/注册/付费）
3. 计算每个渠道的转化率 = 转化数 / 阅读量
4. 识别异常：转化率 < 历史均值 50% 或阅读量 < 历史均值 30% 标记为红色

### Step 2：生成推广物料（25 分钟内）
1. 读取 `company/projects/<product>/source/` 下当日产出的内容
2. 按渠道适配生成物料：
   - **Twitter**：280 字符内，含 1-2 个 hashtag，附图片或 GIF
   - **Reddit**：标题 + 正文，按目标 subreddit 风格调整（如 r/CryptoCurrency 偏深度分析）
   - **Mirror / Medium**：长文格式，含标题/摘要/正文/标签
3. 定价策略：所有付费内容定价 `>= 变动成本`，参考 `ledger.yaml` 中历史回款数据
4. 调用 `DecisionGate.check("external_publish", context)`：
   - **首次发布到新渠道** → 触发人工确认
   - 含敏感话题（政治/监管/争议项目）→ 触发人工确认

### Step 3：追踪渠道转化率（10 分钟内）
1. 按渠道归因昨日转化：用户从哪个渠道进入、完成什么动作、产生多少收入
2. 计算每个渠道的 ROI = 渠道收入 / 渠道成本
3. ROI < 1.0x 的渠道标记"暂停投放"，下次循环不再分配预算

### Step 4：输出运营日报（10 分钟内）
1. 写入 `company/operations/coo-daily-YYYY-MM-DD.md`，格式：
   ```markdown
   # YYYY-MM-DD 运营日报
   ## 关键指标
   | 渠道 | 阅读量 | 互动数 | 转化数 | 转化率 | ROI |
   | --- | --- | --- | --- | --- | --- |
   ## 异常告警
   - 🔴 <channel> 转化率下降 60%，建议暂停
   - 🟡 <channel> 阅读量低于均值，需调整发布时间
   ## 明日计划
   - 优先投放渠道：<top_channel>
   - 暂停投放渠道：<paused_channel>
   ```
2. 写入推广物料到 `company/marketing/<channel>-posts-YYYY-MM-DD.md`
3. 长期推广方案写入 `company/knowledge/marketing/promotion-plan-<product>.md`，含：
   - 渠道：主要获客渠道与预算分配
   - 定价：定价模型与心理锚点
   - 追踪指标：北极星指标 + 关键转化漏斗
   - 时间线：0-30 / 30-60 / 60-90 天里程碑

### Step 5：预算校验与 publish
1. 所有渠道策略必须通过 `ledger` 中的预算校验：`sum(渠道预算) <= ledger.balance * 0.3`
2. publish `topic=promotion.published`，payload 含渠道 / 物料路径 / 预期 ROI
3. 若 DecisionGate 触发且用户拒绝，publish `topic=promotion.cancelled`

## Notes（注意事项）
- **预算红线**：所有渠道预算总和不得超过余额 30%，否则触发人工确认
- **定价底线**：定价不得低于变动成本（LLM API 调用费 + 平台手续费）
- **渠道适配**：同一内容在不同渠道需差异化（Twitter 短平快，Mirror 深度长文）
- **降级路径**：Chrome 自动化失败时，物料产出但延迟发布，标记 `sop_compliance=degraded`
- **决策门禁超时**：超时 60 分钟未回复，按 `timeout_action=cancel` 取消发布

## Examples（示例）

### 示例：Twitter 推广物料
```markdown
# twitter-tweets-2026-06-29.md

## Tweet 1
🧵 Uniswap V4 的 Hook 机制彻底改变了 DEX 的可组合性。

过去 V3 只能调参数，现在 V4 可以在交易生命周期的每个阶段注入自定义逻辑。

这意味着什么？
1. 自定义预言机
2. 动态手续费
3. MEV 抗性池

完整深度分析 👇 [Mirror 链接]
#DeFi #Uniswap #Web3
```

### 示例：运营日报
```markdown
# coo-daily-2026-06-29.md
## 关键指标
| 渠道 | 阅读量 | 互动数 | 转化数 | 转化率 | ROI |
| --- | --- | --- | --- | --- | --- |
| Twitter | 1250 | 89 | 12 | 0.96% | 2.3x |
| Reddit | 580 | 34 | 5 | 0.86% | 1.8x |
| Mirror | 230 | 12 | 2 | 0.87% | 1.2x |

## 异常告警
- 🟡 Mirror 阅读量低于均值（历史 350），建议优化标题
```

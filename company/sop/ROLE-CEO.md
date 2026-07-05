---
id: ROLE-CEO
name: 首席执行官每日职责 SOP
trigger: 每日 08:00 Phase-Morning 触发；并在 18:00 Phase-Review 主持复盘
owner_role: ceo
inputs:
  - company/config/ledger.yaml
  - company/operations/evening-review-昨日.md
  - company/knowledge/opportunities/radar-今日.md
  - company/config/task_queue.yaml
outputs:
  - company/operations/morning-decisions-YYYY-MM-DD.md
  - company/decisions/ceo-YYYY-MM-DD.md
  - company/config/task_queue.yaml
acceptance_criteria:
  - morning-decisions-YYYY-MM-DD.md 已产出且含立项清单
  - 至少 1 条 decision.initiate 或 decision.kill 或 decision.reprioritize 消息已 publish
  - 当日 P0 任务优先级已写入 task_queue.yaml
  - 单笔支出超余额 30% 已显式标注「需二次审批」
sla_minutes: 30
fallback: 若 LLM 后端失败，沿用昨日立项清单与优先级，并在 morning-decisions 文件中标记 sop_compliance=degraded；若市场情报缺失，仅基于 ledger 余额做防御性决策（默认 reject 新立项）
---

# 首席执行官每日职责 SOP

## 角色定位
对 AutoCorp 的成本、市场与最终决策负责。所有决策必须基于数据（账本余额、市场情报、预期 ROI），拒绝拍脑袋式判断。

## Actions（执行步骤）

### Step 1：读取数据上下文（5 分钟内）
1. 读取 `company/config/ledger.yaml`，记录当前余额、过去 7 天净收入、危机阈值状态
2. 读取昨日 `company/operations/evening-review-YYYY-MM-DD.md`，提取 KPI 完成情况与遗留问题
3. 读取今日 `company/knowledge/opportunities/radar-YYYY-MM-DD.md`，识别候选机会
4. 读取 `company/config/task_queue.yaml`，统计 `pending` / `in_progress` / `failed` 任务数

### Step 2：决策当日立项 / 砍项 / 调优先级（15 分钟内）
1. 对每个候选机会执行 ROI 评估：`预期收入 / 预期成本`，**ROI < 1.5x 默认 reject**
2. 对已有项目评估"砍项信号"：连续 3 天无产出 / 实际成本超预算 50% / 战略方向变化
3. 对新立项调用 `DecisionGate.check("product_initiate", context)`：
   - 预计成本 > $20 或周期 > 3 天 → 触发人工确认
4. **单笔支出超余额 30% 必须显式标注「需二次审批」**
5. 输出格式：
   ```
   决策: approve / reject / revise
   理由: 基于数据的具体理由
   预算影响: 对余额/收入/支出的量化影响
   ```

### Step 3：写入决策产物（5 分钟内）
1. 将当日立项清单写入 `company/operations/morning-decisions-YYYY-MM-DD.md`，格式：
   ```markdown
   # YYYY-MM-DD 晨会决策
   ## 当日立项清单
   - [P0] <task_title> | 预期 ROI: 2.0x | 预算: $X | owner: <role>
   ## 砍项清单
   - <task_title> | reason: <cost_overrun|strategic_shift|...>
   ## 优先级调整
   - <task_id>: P2 → P0 | reason: <client_order|market_hot|...>
   ```
2. 详细决策日志写入 `company/decisions/ceo-YYYY-MM-DD.md`，含每条决策的 ROI 计算与理由
3. 更新 `task_queue.yaml`：新增任务、调整 `priority`、`status=killed` 等

### Step 4：publish 决策消息到消息池（持续）
1. 每条立项决策 → `publish(topic="decision.initiate", payload={task_id, title, owner, priority, expected_roi})`
2. 每条砍项决策 → `publish(topic="decision.kill", payload={task_id, reason})`
3. 每条优先级调整 → `publish(topic="decision.reprioritize", payload={task_id, from_priority, to_priority, reason})`

### Step 5：18:00 Phase-Review 主持复盘
1. 汇总当日 5 类健康指标（任务/角色/财务/协作/服务）
2. 对未达成 KPI 的项目决定"继续 / 调整 / 砍项"
3. 战略方向调整需调用 `DecisionGate.check("strategy_adjust", context)` 触发人工确认
4. 输出 `company/decisions/ceo-review-YYYY-MM-DD.md`

## Notes（注意事项）
- **数据优先**：所有决策必须引用 ledger / radar / task_queue 中的具体数据，禁止"我觉得"式判断
- **风险红线**：余额 < $1000 时禁止新立项，触发财务红色警报
- **降级路径**：LLM 后端失败时，沿用昨日决策清单，并在产物中标记 `sop_compliance=degraded`
- **人工在环**：决策门禁触发后超时 60 分钟未回复，按 `timeout_action=defer` 处理，下次循环再触发

## Examples（示例）

### 示例 1：立项决策
```yaml
# morning-decisions-2026-06-29.md
- task_id: task-2026-06-29-001
  title: "撰写 Uniswap V4 Hook 机制深度分析"
  priority: P0
  owner: product_manager
  expected_roi: 2.5x
  expected_cost: $5
  expected_revenue: $12.5
  decision: approve
  reason: "DeFi 协议热度上升 35%，目标渠道 Twitter 现有 1.2k 粉丝转化率 8%"
  budget_impact: "余额 $8500 → $8495，预期 7 天内回款 $12.5"
```

### 示例 2：砍项决策
```yaml
- task_id: task-2026-06-25-014
  title: "Layer3 自动答题脚本"
  decision: kill
  reason: "连续 3 天无产出，且 Layer3 反作弊升级导致 ROI < 1.0x"
  budget_impact: "已支出 $3 沉没，无后续支出"
```

---
id: WF-REVIEW
name: 日终复盘与战略调整工作流 SOP
trigger: 每日 18:00 Phase-Review 触发
owner_role: ceo
inputs:
  - company/operations/morning-decisions-YYYY-MM-DD.md
  - company/operations/coo-daily-YYYY-MM-DD.md
  - company/config/task_queue.yaml
  - company/config/ledger.yaml
  - company/messages/message-pool-YYYY-MM-DD.jsonl
  - company/health/health-YYYY-MM-DD.md
outputs:
  - company/operations/evening-review-YYYY-MM-DD.md
  - company/operations/decision-trail-YYYY-MM-DD.md
  - company/decisions/ceo-review-YYYY-MM-DD.md
acceptance_criteria:
  - evening-review-YYYY-MM-DD.md 已产出且含 KPI 完成情况与遗留问题
  - decision-trail-YYYY-MM-DD.md 已产出且含当日所有消息按时间排序的清单
  - ceo-review-YYYY-MM-DD.md 已产出且含战略调整决策（继续/调整/砍项）
  - 健康报告已被引用（5 类指标齐全）
  - 任一指标亮红色已触发 human_loop 通知
  - 复盘完成已 publish topic=phase.done.review 消息
sla_minutes: 30
fallback: 若 health 报告缺失，CEO 基于 ledger 与 task_queue 自行估算健康状态；若消息池文件缺失，决策链路审计报告标记 reason=missing_messages；若 LLM 后端失败，沿用昨日复盘模板填充当日数据
---

# 日终复盘与战略调整工作流 SOP

## 工作流概述
本工作流对应 Phase-Review，由 CEO 主持、全员参与。汇总当日 5 类健康指标 → 生成决策链路审计报告 → 对未达成 KPI 的项目决定"继续/调整/砍项" → 战略方向调整（需人工确认），形成"执行 → 复盘 → 调整"的闭环。

## 工作流参与者
- **主责**：CEO（主持复盘）
- **协作**：全员（提供当日产出与 KPI 数据）

## Actions（执行步骤）

### Stage 1：数据汇总（10 分钟内）
1. 读取 `company/operations/morning-decisions-YYYY-MM-DD.md`，提取当日立项清单与优先级
2. 读取 `company/operations/coo-daily-YYYY-MM-DD.md`，提取运营日报与异常告警
3. 读取 `company/config/task_queue.yaml`，统计当日任务：
   - 新增任务数 / 完成数 / 失败数 / 重试数 / 阻塞数
   - 平均完成时长 = sum(completed_at - claimed_at) / 完成数
   - 失败率 = 失败数 / (完成数 + 失败数)
   - 重试率 = 重试数 / 总任务数
4. 读取 `company/config/ledger.yaml`，提取：
   - 当日真实收入 / 虚拟收入 / 支出 / 净额
   - 钱包余额 / 危机警报阈值状态
5. 读取 `company/health/health-YYYY-MM-DD.md`，提取 5 类健康指标状态（🟢/🟡/🔴）
6. 读取 `company/messages/message-pool-YYYY-MM-DD.jsonl`，统计消息池活跃度

### Stage 2：健康指标核验（5 分钟内）
1. 核验 5 类健康指标：
   - **任务健康**：pending 数 / 平均完成时长 / 失败率 / 重试率
   - **角色健康**：每角色激活状态 / 产出文件数 / KPI 达成率
   - **财务健康**：钱包余额 / 当日真实收入 / 危机警报
   - **协作健康**：消息池活跃度 / 跨角色转交次数 / Phase 完整执行率
   - **服务健康**：未完成订单数 / 订单平均交付周期 / 一次验收通过率
2. 任一指标亮红色时：
   - publish `topic=health.alert.red`，payload 含 `{indicator, value, threshold, detail}`
   - 调用 `human_loop` 通知用户"<indicator> 红色警报：<detail>"
   - 在次日 Phase-Morning 把对应问题列为 P0 优先级

### Stage 3：生成决策链路审计报告（5 分钟内）
1. 读取当日消息池 `message-pool-YYYY-MM-DD.jsonl`，按时间排序所有消息
2. 为每条消息标注：
   - `from_role` / `topic` / `created_at`
   - `triggered_actions`：后续触发的任务 ID（通过 topic 关联 task_queue）
3. 写入 `company/operations/decision-trail-YYYY-MM-DD.md`，格式：
   ```markdown
   # YYYY-MM-DD 决策链路审计报告

   ## 消息流（按时间排序）
   | 时间 | from_role | topic | triggered_actions |
   | --- | --- | --- | --- |
   | 08:00:15 | ceo | decision.initiate | task-001, task-002 |
   | 08:30:22 | product_manager | research.topics_ready | task-003 |
   | 10:00:18 | architect | design.completed | task-004 |
   | 12:00:05 | programmer | build.module_done | - |
   | 14:30:42 | tester | task.blocked | task-004 (重开) |
   | 15:00:10 | coo | promotion.published | - |

   ## 关键决策点
   - 08:00 CEO 立项 task-001（基于 ROI 2.5x）
   - 14:30 Tester 阻断 task-004（P1 缺陷 DEF-001）
   - 18:00 CEO 复盘决定 task-005 砍项（连续 3 天无产出）
   ```

### Stage 4：KPI 复盘与战略调整（5 分钟内）
1. 对每个项目评估 KPI 完成情况：
   - CEO KPI: `wallet_balance_weekly_growth >= 5%`
   - CTO KPI: `tech_debt_resolution_rate >= 80%`
   - COO KPI: `weekly_tips_total >= $10`
   - Architect KPI: `weekly_design_docs >= 2`
   - Programmer KPI: `weekly_delivery_count >= 5` / `first_pass_rate >= 80%`
   - Tester KPI: `weekly_test_count >= 5` / `defect_miss_rate <= 10%`
   - PM KPI: `weekly_topics >= 5` / `adoption_rate >= 50%`
2. 对未达成 KPI 的项目决定"继续 / 调整 / 砍项"
3. 战略方向调整需调用 `DecisionGate.check("strategy_adjust", context)` 触发人工确认
4. 写入 `company/decisions/ceo-review-YYYY-MM-DD.md`，含：
   ```markdown
   # YYYY-MM-DD CEO 复盘决策

   ## KPI 完成情况
   | 角色 | KPI | 目标 | 实际 | 状态 |
   | --- | --- | --- | --- | --- |
   | CEO | wallet_balance_weekly_growth | >=5% | 3.2% | 🟡 |
   | COO | weekly_tips_total | >=$10 | $7.5 | 🟡 |
   | Programmer | weekly_delivery_count | >=5 | 7 | 🟢 |

   ## 战略调整决策
   - 决策: continue / adjust / kill
   - 项目: <project_name>
   - 理由: ...
   - 行动项: ...
   ```

### Stage 5：产出复盘报告与 publish（5 分钟内）
1. 写入 `company/operations/evening-review-YYYY-MM-DD.md`，含：
   - 当日 KPI 完成情况
   - 任务统计（新增 / 完成 / 失败 / 阻塞）
   - 财务状况（收入 / 支出 / 净额 / 余额）
   - 健康指标仪表盘（5 类指标 🟢/🟡/🔴）
   - 遗留问题与次日计划
2. publish `topic=phase.done.review`，payload 含：
   ```json
   {
     "date": "YYYY-MM-DD",
     "tasks_completed": <N>,
     "tasks_failed": <N>,
     "real_income": <N>,
     "health_status": {
       "task": "green",
       "role": "yellow",
       "finance": "red",
       "collab": "green",
       "service": "green"
     },
     "review_path": "company/operations/evening-review-YYYY-MM-DD.md"
   }
   ```
3. 若任一指标亮红色，额外 publish `topic=health.alert.red` 并调用 `human_loop`

## Notes（注意事项）
- **数据完整性**：所有复盘必须基于实际数据（ledger / task_queue / health / messages），禁止主观判断
- **红色警报**：任一指标亮红色必须触发 human_loop 通知用户，不得"静默处理"
- **战略调整门禁**：战略方向调整必须通过 `DecisionGate.check("strategy_adjust")` 触发人工确认
- **决策链路**：所有决策必须有迹可循，记录在 `decision-trail-YYYY-MM-DD.md`
- **降级路径**：health 报告缺失时 CEO 基于 ledger 与 task_queue 自行估算；消息池缺失时审计报告标记 `reason=missing_messages`
- **超时处理**：超过 30 分钟未完成，强制结束，已有产出保留，未完成项标记 `phase_timeout`

## Examples（示例）

### 示例：健康仪表盘
```markdown
## 健康指标仪表盘

| 指标类别 | 状态 | 关键值 | 阈值 | 详情 |
| --- | --- | --- | --- | --- |
| 任务健康 | 🟢 | pending=3, 失败率=5% | 失败率<10% | 平均完成时长 45min |
| 角色健康 | 🟡 | 6/7 角色激活 | 全部激活 | Tester 今日未激活 |
| 财务健康 | 🔴 | 余额 $50, 真实收入 $0 | 余额>$100 | 连续 3 天无真实收入 |
| 协作健康 | 🟢 | 消息 42 条, 转交 8 次 | 消息>20 | Phase 完整执行率 100% |
| 服务健康 | 🟢 | 未完成订单 0 | <3 | 无活跃订单 |
```

### 示例：红色警报通知
```json
{
  "topic": "health.alert.red",
  "from_role": "ceo",
  "to_role": null,
  "payload": {
    "indicator": "finance",
    "value": {"balance": 50, "real_income_today": 0, "consecutive_zero_days": 3},
    "threshold": {"min_balance": 100, "max_zero_days": 2},
    "detail": "财务健康红色警报：连续 3 天无真实收入，余额 $50 低于阈值 $100",
    "action": "次日 Phase-Morning 把「变现突破」列为 P0 优先级"
  }
}
```

### 示例：复盘报告（节选）
```markdown
# 2026-06-29 日终复盘

## KPI 完成情况
| 角色 | KPI | 目标 | 实际 | 状态 |
| --- | --- | --- | --- | --- |
| CEO | wallet_balance_weekly_growth | >=5% | 3.2% | 🟡 |
| Programmer | weekly_delivery_count | >=5 | 7 | 🟢 |
| Tester | defect_miss_rate | <=10% | 8% | 🟢 |

## 任务统计
- 新增: 8 | 完成: 6 | 失败: 1 | 阻塞: 1
- 平均完成时长: 45 min
- 失败率: 14.3%（高于阈值 10%，标记 🟡）

## 财务状况
- 真实收入: $0 | 虚拟收入: $5 | 支出: $3 | 净额: +$2
- 余额: $50（低于阈值 $100，触发 🔴 红色警报）

## 遗留问题
1. task-004 因 P1 缺陷阻塞，需 Programmer 明日修复
2. 财务红色警报：连续 3 天无真实收入，需在次日 Phase-Morning 列为 P0

## 次日计划
- [P0] 变现突破：评估 3 个新变现机会
- [P1] 修复 DEF-001：content_generator 异常路径
- [P2] Mirror 渠道优化：调整发布时间
```

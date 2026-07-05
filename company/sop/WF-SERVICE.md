---
id: WF-SERVICE
name: 外部客户订单交付工作流 SOP
trigger: 订单状态流转到 confirmed 后触发 Phase-Service（独立于日常 Phase 链）
owner_role: product_manager
inputs:
  - company/orders/confirmed/<order_id>.yaml
  - company/config/decision-gates.yaml
  - company/templates/prd-template.md
  - company/templates/architecture-template.md
  - company/templates/test-report-template.md
  - company/templates/acceptance-template.md
outputs:
  - company/orders/delivered/<order_id>/README.md
  - company/orders/delivered/<order_id>/prd.md
  - company/orders/delivered/<order_id>/source/
  - company/orders/delivered/<order_id>/test-report.md
  - company/orders/delivered/<order_id>/acceptance.md
acceptance_criteria:
  - 交付目录 company/orders/delivered/<order_id>/ 已创建
  - README.md / prd.md / source/ / test-report.md / acceptance.md 五份产物齐全
  - prd.md 基于 prd-template.md 模板且必填字段已填
  - test-report.md 无 P0/P1 缺陷
  - acceptance.md 含验收标准与签字位
  - 订单状态已流转到 delivered 并 publish topic=order.delivered 消息
sla_minutes: 240
fallback: 若客户需求模糊，PM 通过 human_loop 向客户澄清；若 LLM 后端失败，复用模板产出骨架文档并标记 sop_compliance=degraded；若超时，已完成的产物保留，未完成项标记 phase_timeout，订单状态保持 in_progress
---

# 外部客户订单交付工作流 SOP

## 工作流概述
本工作流对应 Phase-Service，是独立于日常 Phase 链的订单驱动工作流。从客户订单确认出发，按"调研 → 设计 → 实现 → 测试 → 交付"五阶段编排角色协作，产出标准化交付包，客户验收后流转到收款环节。

## 工作流参与者
- **主责**：PM（订单需求转化）、Architect（设计）、Programmer（实现）、Tester（测试）
- **协作**：CEO（报价与决策门禁）、COO（交付包打包）

## Actions（执行步骤）

### Stage 1：订单解析与需求澄清（30 分钟内，PM 主导）
1. 读取 `company/orders/confirmed/<order_id>.yaml`，提取：
   - `client_name` / `client_contact` / `requirement` / `quoted_price` / `expected_delivery`
   - `assigned_roles[]` / `sop_id`（默认 WF-SERVICE）
2. 基于 `company/templates/prd-template.md` 产出 `prd.md`，必填字段：
   - 客户需求摘要
   - 功能需求清单（按 P0/P1/P2 优先级）
   - 验收标准（可量化）
   - 交付时间线
3. 若客户需求模糊 → 通过 `human_loop` 向客户澄清，记录到 `events[]`
4. 写入 `company/orders/in_progress/<order_id>/prd.md`
5. publish `topic=order.prd_ready`，payload 含 `{order_id, prd_path, mvp_weeks}`

### Stage 2：架构设计（45 分钟内，Architect 主导）
1. Architect 读取 `prd.md`，按 `WF-DESIGN` 工作流的 Stage 2-5 执行
2. 产出 `architecture.md`（基于 `architecture-template.md` 模板）
3. 产出 `modules.yaml` 与 `interfaces.yaml`
4. CTO 评审（可简化为 fast-track：MVP < 1 周可跳过 CTO 评审）
5. 写入 `company/orders/in_progress/<order_id>/architecture.md`
6. publish `topic=order.design_ready`，payload 含 `{order_id, modules_count}`

### Stage 3：编码实现（90 分钟内，Programmer 主导）
1. Programmer 按 `WF-BUILD` 工作流的 Stage 1-3 执行
2. 按 modules.yaml 依赖顺序编码，严格遵循 interfaces.yaml
3. 产出 `source/<module>.py` 与 `source/<module>_test.py`
4. 写入 `company/orders/in_progress/<order_id>/source/`
5. publish `topic=order.code_ready`，payload 含 `{order_id, modules_count, loc}`

### Stage 4：测试与质量把关（45 分钟内，Tester 主导）
1. Tester 按 `WF-BUILD` 工作流的 Stage 4-5 执行
2. 生成测试用例（正常/边界/异常三类场景）
3. 执行测试与回归测试
4. 产出 `test-report.md`（基于 `test-report-template.md` 模板）与 `defects.yaml`
5. **任何 P0/P1 缺陷必须阻断交付**：publish `topic=task.blocked` reason=`defect_p1`
6. 写入 `company/orders/in_progress/<order_id>/test-report.md`
7. publish `topic=order.test_ready`，payload 含 `{order_id, pass_rate, p0_p1_count}`

### Stage 5：交付包打包与验收单（30 分钟内，COO 主导）
1. COO 调用 `DeliveryPackager.build_for_order(order_id)` 收集 5 份文档：
   - `README.md`：交付清单总览（基于 `delivery-template.md`）
   - `prd.md`：基于客户需求生成的 PRD
   - `source/`：实际交付内容（文章/代码/数据）
   - `test-report.md`：Tester 验收报告
   - `acceptance.md`：客户验收单（基于 `acceptance-template.md`），含验收标准与签字位
2. 调用 `DeliveryPackager.validate(pack_path, type="order")` 校验必填字段
3. 缺失字段阻塞交付，回到对应 Stage 补产
4. 打包到 `company/orders/delivered/<order_id>/`
5. 产出 `acceptance.md`，含：
   - 交付清单（文件路径 / 用途 / 行数或字数）
   - 验收标准（与 PRD 一致）
   - 客户签字位（待客户确认）
   - 交付时间戳

### Stage 6：订单状态流转与 publish（持续）
1. 订单状态从 `confirmed` → `in_progress`（Stage 1 开始时）
2. 订单状态从 `in_progress` → `delivered`（Stage 5 完成后）
3. 每次状态流转写入 `events[]`，含 `from_status` / `to_status` / `timestamp` / `actor` / `note`
4. publish `topic=order.delivered`，payload 含：
   ```json
   {
     "order_id": "ord-20260629-001",
     "client_name": "Alice",
     "deliverables_path": "company/orders/delivered/ord-20260629-001/",
     "files_count": 5,
     "test_pass_rate": 0.95,
     "awaiting_acceptance": true
   }
   ```
5. 等待客户执行 `py main.py order accept <order_id>` 流转到 `accepted/`

## Notes（注意事项）
- **独立于日常 Phase**：本工作流由订单事件驱动，独立于日常 Phase-Morning/Build/Promote 链
- **模板强制**：所有文档必须基于 `company/templates/` 下对应模板产出，未填字段为阻塞项
- **必填字段校验**：`DeliveryPackager.validate` 检查 `[REQUIRED]` 标记的字段
- **质量红线**：任何 P0/P1 缺陷必须阻断交付，不得"先交付后修复"
- **客户澄清**：需求模糊时通过 `human_loop` 向客户澄清，记录到 `events[]`
- **降级路径**：LLM 后端失败时复用模板产出骨架文档，标记 `sop_compliance=degraded`
- **超时处理**：超过 240 分钟未完成，强制结束，已完成产物保留，未完成项标记 `phase_timeout`，订单状态保持 `in_progress`，publish `topic=order.timeout`

## Examples（示例）

### 示例：订单 yaml
```yaml
# company/orders/confirmed/ord-20260629-001.yaml
order_id: ord-20260629-001
client_name: Alice
client_contact: alice@example.com
requirement: "写一篇关于 DeFi 协议的深度分析，重点对比 Uniswap V3 与 V4 的 Hook 机制"
sop_id: WF-SERVICE
quoted_price: 30
currency: USD
expected_delivery: 2026-07-01
assigned_roles: [product_manager, architect, programmer, tester]
status: confirmed
events:
  - from_status: received
    to_status: quoted
    timestamp: 2026-06-29T09:00:00
    actor: ceo
    note: 报价 $30
  - from_status: quoted
    to_status: confirmed
    timestamp: 2026-06-29T10:00:00
    actor: user
    note: 客户确认报价
created_at: 2026-06-29T08:00:00
updated_at: 2026-06-29T10:00:00
```

### 示例：交付包 README
```markdown
# 订单 ord-20260629-001 交付清单

## 客户信息
- 客户名称: Alice
- 联系方式: alice@example.com
- 订单金额: $30 USD

## 交付清单
| 文件 | 用途 | 大小 |
| --- | --- | --- |
| prd.md | 基于客户需求生成的 PRD | 2.5 KB |
| source/defi-hook-analysis.md | DeFi 协议深度分析文章 | 12 KB |
| source/code-examples/ | Uniswap V3/V4 代码示例 | 8 KB |
| test-report.md | Tester 验收报告 | 1.8 KB |
| acceptance.md | 客户验收单 | 1.2 KB |

## 验收标准
1. 文章字数 >= 5000 字
2. 含 Uniswap V3 与 V4 Hook 机制对比
3. 含可运行代码示例
4. 通过 Tester 质量验收（无 P0/P1 缺陷）

## 交付时间
- 开始时间: 2026-06-29 10:00
- 完成时间: 2026-06-29 14:00
- 总耗时: 4 小时
```

### 示例：验收单
```markdown
# acceptance.md - 订单 ord-20260629-001

## 验收标准
| 序号 | 标准 | 是否满足 |
| --- | --- | --- |
| 1 | 文章字数 >= 5000 字 | ✅ 5800 字 |
| 2 | 含 Uniswap V3 与 V4 Hook 机制对比 | ✅ |
| 3 | 含可运行代码示例 | ✅ 12 个示例 |
| 4 | 通过 Tester 质量验收 | ✅ 通过率 96% |

## 客户签字位
- 客户名称: Alice
- 签字日期: ____ (待客户确认)
- 备注: ____

## AutoCorp 签字位
- 交付人: COO
- 交付日期: 2026-06-29
```

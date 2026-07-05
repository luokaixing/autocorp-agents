# AutoCorp SOP 标准化作业流程目录

本目录存放 AutoCorp 虚拟公司所有角色与工作流的 **SOP（Standard Operating Procedure）** 文档。
所有任务执行必须遵循对应 SOP，确保交付物格式与质量一致、决策链路可审计、协作留痕可回溯。

## 1. 目录结构

```
company/sop/
├── README.md              # 本文件：SOP 文件结构、字段定义、使用方式
├── ROLE-CEO.md            # 首席执行官每日职责 SOP
├── ROLE-CTO.md            # 首席技术官每日职责 SOP
├── ROLE-COO.md            # 首席运营官每日职责 SOP
├── ROLE-ARCHITECT.md      # 架构师每日职责 SOP
├── ROLE-PROGRAMMER.md     # 程序员每日职责 SOP
├── ROLE-TESTER.md         # 测试员每日职责 SOP
├── ROLE-PM.md             # 产品经理每日职责 SOP
├── WF-RESEARCH.md         # 市场调研与选题工作流 SOP
├── WF-DESIGN.md           # 架构设计与方案工作流 SOP
├── WF-BUILD.md            # 编码实现与测试工作流 SOP
├── WF-PROMOTE.md          # 内容发布与渠道推广工作流 SOP
├── WF-SERVICE.md          # 外部客户订单交付工作流 SOP
└── WF-REVIEW.md           # 日终复盘与战略调整工作流 SOP
```

- **角色级 SOP（ROLE-*）**：定义单个角色每日必做动作清单，由 Phase-Morning / Phase-Build 等时间触发
- **工作流级 SOP（WF-*）**：定义跨角色协作的标准工作流，由 Phase 链或订单事件触发

## 2. SOP 文件统一结构

每份 SOP 文档必须采用 **YAML frontmatter + Markdown 正文** 结构：

```
---
id: WF-BUILD                 # SOP 唯一标识，与文件名（去 .md）一致
name: 编码实现与测试工作流 SOP  # SOP 名称
trigger: 每日 12:00 Phase-Build 触发  # 触发条件（时间 / 事件 / 上游产物）
owner_role: programmer        # 拥有者角色代号（与 employees.yaml 的 role 字段一致）
inputs: []                    # 前置产物列表（文件路径或描述）
outputs: []                   # 产出物列表
acceptance_criteria: []       # 验收标准列表
sla_minutes: 30               # 服务等级协议时长（分钟），超时降级
fallback: ...                 # 降级策略描述
---

# Markdown 正文：详细 actions 步骤 / 注意事项 / 示例
```

## 3. 字段定义

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 是 | SOP 唯一标识，与文件名（去 `.md`）一致，如 `WF-BUILD` / `ROLE-CEO` |
| `name` | string | 是 | SOP 中文名称 |
| `trigger` | string | 是 | 触发条件描述，如「每日 08:00 Phase-Morning 触发」「订单 confirmed 状态触发 Phase-Service」 |
| `owner_role` | string | 是 | 拥有者角色代号，与 `company/config/employees.yaml` 的 `role` 字段一致：`ceo` / `cto` / `coo` / `architect` / `programmer` / `tester` / `product_manager` |
| `inputs` | list[string] | 是 | 前置产物列表，每项可以是文件路径（如 `company/projects/<name>/prd.md`）或产物描述（如 `昨日 KPI 报告`）。执行前由 `SOPLoader.validate_inputs` 校验 |
| `outputs` | list[string] | 是 | 产出物列表，格式同 `inputs` |
| `acceptance_criteria` | list[string] | 是 | 验收标准列表，每条为可检查的字符串描述，由 `SOPLoader.check_acceptance` 校验 |
| `sla_minutes` | int | 是 | 服务等级协议时长（分钟）。超时后触发 `fallback` 降级策略，不阻塞后续 Phase |
| `fallback` | string | 是 | 降级策略描述，如「使用上日产物 / 跳过该 Phase / 人工介入」 |

正文部分由 Markdown 编写，建议包含以下小节（非强制）：
- **Actions（执行步骤）**：按顺序列出可执行的具体动作
- **Notes（注意事项）**：边界条件、依赖、风险点
- **Examples（示例）**：产物示例或调用示例

## 4. 使用方式

### 4.1 角色执行任务时加载 SOP

任务卡（`company/config/task_queue.yaml`）新增 `sop_id` 字段后，角色在 `execute_task` 前先调用 `SOPLoader` 加载 SOP：

```python
from engine.sop_loader import SOPLoader

loader = SOPLoader()
sop = loader.load(task["sop_id"])              # 加载 SOP
if sop is None:
    # SOP 缺失：标记 sop_compliance=degraded，按原逻辑执行
    ...
else:
    passed, missing = loader.validate_inputs(sop, context)
    if not passed:
        # inputs 缺失：拒绝执行，转回上游角色
        ...
    # 按 sop["actions"] 顺序执行
    passed, failed = loader.check_acceptance(sop, output)
    if not passed:
        # 验收不通过：标记任务 failed
        ...
```

### 4.2 SOP 缺失降级

任务卡的 `sop_id` 字段为空或对应 SOP 文件不存在时，角色按现有 `execute_task` 逻辑执行，并在产出物中标记 `sop_compliance: degraded`，同时 publish 一条 `topic=sop.missing` 消息到消息池供健康监控统计。

### 4.3 SOP 违规拦截

若 SOP 规定的 `inputs` 缺失（如 `prd.md` 未产出），角色拒绝执行并通过 `request_handoff` 转回上游角色，publish 一条 `topic=task.blocked` 消息，附 `reason: missing_<input>`。

### 4.4 修改 SOP 不需改代码

SOP 是文件即数据库的体现：角色行为由 SOP 驱动，代码只负责加载与执行 SOP。修改 SOP 文档（如调整 actions 顺序、新增 acceptance_criteria）不需要修改代码，下次执行自动生效。

## 5. owner_role 与角色代号对照

| SOP 文件 | owner_role | 角色中文名 |
| --- | --- | --- |
| `ROLE-CEO.md` | `ceo` | 首席执行官 |
| `ROLE-CTO.md` | `cto` | 首席技术官 |
| `ROLE-COO.md` | `coo` | 首席运营官 |
| `ROLE-ARCHITECT.md` | `architect` | 架构师 |
| `ROLE-PROGRAMMER.md` | `programmer` | 程序员 |
| `ROLE-TESTER.md` | `tester` | 测试员 |
| `ROLE-PM.md` | `product_manager` | 产品经理 |

> 注意：`ROLE-PM.md` 文件名使用 PM 缩写，但 `owner_role` 字段使用 `product_manager`，与 `employees.yaml` 的 `role` 字段保持一致。

## 6. 与 Phase Chain 的关系

| Phase | 触发时间 | 对应工作流 SOP | 参与角色 SOP |
| --- | --- | --- | --- |
| Phase-Morning | 08:00 | — | ROLE-CEO |
| Phase-Research | 08:30 | WF-RESEARCH | ROLE-PM |
| Phase-Design | 10:00 | WF-DESIGN | ROLE-CTO / ROLE-ARCHITECT |
| Phase-Build | 12:00 | WF-BUILD | ROLE-PROGRAMMER / ROLE-TESTER |
| Phase-Promote | 15:00 | WF-PROMOTE | ROLE-COO |
| Phase-Review | 18:00 | WF-REVIEW | ROLE-CEO + 全员 |
| Phase-Service | 按需触发 | WF-SERVICE | 按订单 `sop_id` 编排 |

## 7. 验证

可使用 `SOPLoader.list_all()` 列出全部 SOP 元数据，或 `SOPLoader.load("<sop_id>")` 加载单份 SOP 进行校验。详见 `engine/sop_loader.py`。

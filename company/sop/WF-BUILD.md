---
id: WF-BUILD
name: 编码实现与测试工作流 SOP
trigger: 每日 12:00 Phase-Build 触发（监听 topic=design.completed 消息后启动）
owner_role: programmer
inputs:
  - company/projects/<product>/architecture.md
  - company/projects/<product>/modules.yaml
  - company/projects/<product>/interfaces.yaml
  - company/projects/<product>/tech-selection.md
  - company/config/task_queue.yaml
outputs:
  - company/projects/<product>/source/<module>.py
  - company/projects/<product>/source/<module>_test.py
  - company/projects/<product>/delivery-notes.md
  - company/projects/<product>/test-report.md
  - company/projects/<product>/defects.yaml
acceptance_criteria:
  - 至少 1 个模块代码文件已产出且含基本错误处理
  - 每个模块对应的单元测试文件已产出且能通过
  - 接口签名与 interfaces.yaml 中的定义一致
  - test-report.md 已产出且含测试用例/通过失败统计/缺陷清单
  - 测试用例覆盖正常/边界/异常三类场景
  - 任何 P0/P1 缺陷已阻断发布并 publish topic=task.blocked
  - 编码完成已 publish topic=task.done.code，测试完成已 publish topic=task.done.test
sla_minutes: 180
fallback: 若 architecture.md 缺失，publish topic=task.blocked reason=missing_architecture 转回 architect；若 LLM 后端失败，按模块清单产出骨架代码（含 TODO），标记 sop_compliance=degraded；若超时，未完成模块标记 failed，已完成的保留
---

# 编码实现与测试工作流 SOP

## 工作流概述
本工作流对应 Phase-Build，由 Programmer 主导编码、Tester 主导测试。从架构设计出发，按模块依赖顺序编码 → 单元测试 → 集成测试 → 产出测试报告，为 WF-PROMOTE 提供可发布的代码与质量报告。

## 工作流参与者
- **主责**：Programmer（编码）
- **协作**：Tester（测试与质量把关）
- **支持**：Architect（设计澄清）、CTO（技术评审）

## Actions（执行步骤）

### Stage 1：设计解析与任务分配（10 分钟内，Programmer）
1. 读取 `company/projects/<product>/architecture.md`，理解模块拆分与依赖关系
2. 读取 `company/projects/<product>/modules.yaml`，按依赖顺序排序待开发模块
3. 读取 `company/projects/<product>/interfaces.yaml`，记录接口签名（不得擅自更改）
4. 读取 `company/projects/<product>/tech-selection.md`，确认允许使用的依赖
5. 从 `task_queue.yaml` 读取分配给自己的任务，按 `priority` 排序
6. 若 architecture.md 缺失 → publish `topic=task.blocked` reason=`missing_architecture`，工作流终止

### Stage 2：按模块依赖顺序编码（120 分钟内，Programmer）
1. 按 modules.yaml 中的依赖顺序编码（先底层后上层）
2. 每个模块严格遵循 `interfaces.yaml` 接口定义，**禁止擅自更改接口签名**
3. **禁止引入 tech-selection.md 之外的依赖**
4. 交付代码必须包含基本错误处理：
   - LLM 调用：捕获超时与 API 错误，降级到 fallback 策略
   - 文件读写：捕获 `IOError` / `OSError`，返回错误码而非崩溃
   - 网络请求：捕获 `requests.RequestException`，重试 3 次后失败
5. 每完成一个模块立即 publish `topic=build.module_done`，payload 含 `{module, file_path, loc}`

### Stage 3：单元测试编写（30 分钟内，Programmer）
1. 为每个模块编写 `<module>_test.py`，覆盖：
   - 正常路径：典型输入 → 预期输出
   - 边界条件：空输入 / 超长输入 / 极值
   - 异常路径：依赖失败 / 网络错误 / 权限不足
2. 测试覆盖率 >= 70%（关键模块 >= 90%）
3. **禁止提交未通过自测的代码**：所有测试必须 pass
4. publish `topic=build.unit_test_done`，payload 含 `{module, coverage, passed, failed}`

### Stage 4：测试用例生成与执行（Tester 主导，25 分钟内）
1. Tester 读取 `architecture.md` / `interfaces.yaml` / `delivery-notes.md`
2. 为每个模块生成测试用例，覆盖正常/边界/异常三类场景
3. 运行 Programmer 产出的 `<module>_test.py`
4. 按生成的测试用例手工或脚本执行补充测试
5. 记录每个用例的通过 / 失败状态，失败用例捕获实际输出与异常堆栈

### Stage 5：回归测试（Tester 主导，15 分钟内）
1. 读取历史缺陷清单（`defects.yaml` 中 `status=open` 的项）
2. 对每个历史缺陷场景执行回归测试
3. **回归测试不得遗漏历史缺陷场景**
4. 已修复的缺陷标记 `status=closed`，未修复的保持 `open` 并升级优先级

### Stage 6：产出交付说明与测试报告（10 分钟内）
1. Programmer 写入 `company/projects/<product>/delivery-notes.md`，含：
   - 交付文件清单（文件路径 / 用途 / 关键实现点 / 测试覆盖）
   - 接口实现情况（每个接口的实现状态）
   - 已知问题与遗留 TODO
2. Tester 写入 `company/projects/<product>/test-report.md`，含：
   - 测试概览（模块数 / 用例总数 / 通过 / 失败 / 通过率 / 覆盖率）
   - 测试用例明细表
   - 缺陷清单（含严重程度 / 复现步骤 / 建议优先级）
3. Tester 写入 `company/projects/<product>/defects.yaml`，结构化存储缺陷

### Stage 7：发布消息与质量门禁（持续）
1. Programmer 编码完成后 publish `topic=task.done.code`，payload 含：
   ```json
   {
     "task_id": "<task_id>",
     "product": "<product>",
     "modules_count": <N>,
     "delivery_path": "company/projects/<product>/source/",
     "delivery_notes": "company/projects/<product>/delivery-notes.md"
   }
   ```
2. Tester 测试完成后 publish `topic=task.done.test`，payload 含：
   ```json
   {
     "task_id": "<task_id>",
     "product": "<product>",
     "pass_rate": <N>,
     "defect_count": <N>,
     "p0_p1_count": <N>,
     "test_report_path": "company/projects/<product>/test-report.md"
   }
   ```
3. **任何 P0/P1 缺陷必须阻断 WF-PROMOTE**：publish `topic=task.blocked` reason=`defect_p1`，附 `defect_id`
4. 若无 P0/P1 缺陷，自动触发 WF-PROMOTE（COO 监听 `task.done.test` 后启动）

## Notes（注意事项）
- **接口契约**：严格按 `interfaces.yaml` 实现接口，不得擅自更改签名
- **依赖纪律**：禁止引入 `tech-selection.md` 之外的依赖
- **错误处理**：所有外部调用必须有错误处理，禁止裸调用
- **自测要求**：提交前必须运行 `pytest <module>_test.py` 全部通过
- **质量红线**：任何 P0/P1 缺陷必须阻断发布，不得"先发布后修复"
- **回归纪律**：历史缺陷场景必须 100% 覆盖回归测试
- **降级路径**：LLM 后端失败时产出骨架代码（含 `# TODO` 标注），标记 degraded
- **超时处理**：超过 180 分钟未完成，强制结束当前 Phase，已完成模块保留，未完成标记 `failed` reason=`phase_timeout`，继续执行下一个 Phase（不阻塞）

## Examples（示例）

### 示例：模块完成消息
```json
{
  "topic": "build.module_done",
  "from_role": "programmer",
  "to_role": "tester",
  "payload": {
    "product": "seo-content-generator",
    "module": "content_generator",
    "file_path": "company/projects/seo-content-generator/source/content_generator.py",
    "loc": 145,
    "interfaces_implemented": ["generate(topic, keywords)"]
  }
}
```

### 示例：质量门禁触发
```json
{
  "topic": "task.blocked",
  "from_role": "tester",
  "to_role": "programmer",
  "payload": {
    "task_id": "task-2026-06-29-003",
    "reason": "defect_p1",
    "defect_id": "DEF-001",
    "defect_severity": "P1",
    "module": "content_generator",
    "reproduce": "LLM 超时未抛出 LLMError，返回 None"
  }
}
```

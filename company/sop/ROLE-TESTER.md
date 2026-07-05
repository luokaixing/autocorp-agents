---
id: ROLE-TESTER
name: 测试员每日职责 SOP
trigger: Phase-Build 编码完成后触发；任务 type=test 触发
owner_role: tester
inputs:
  - company/projects/<product>/source/
  - company/projects/<product>/delivery-notes.md
  - company/projects/<product>/interfaces.yaml
  - company/projects/<product>/architecture.md
outputs:
  - company/projects/<product>/test-report.md
  - company/projects/<product>/defects.yaml
acceptance_criteria:
  - test-report.md 已产出且含测试用例/通过失败统计/缺陷清单
  - 测试用例覆盖正常/边界/异常三类场景
  - 任何 P0/P1 缺陷已阻断发布并标记
  - 回归测试覆盖历史缺陷场景
  - 缺陷清单含严重程度/复现步骤/建议优先级
sla_minutes: 90
fallback: 若 LLM 后端失败，按 interfaces.yaml 自动生成接口契约测试骨架，标记 sop_compliance=degraded；若 source/ 缺失，转回 programmer 角色并 publish task.blocked reason=missing_source
---

# 测试员每日职责 SOP

## 角色定位
对 AutoCorp 质量负最终把关责任。严格、注重边界条件、不放过任何缺陷。

## Actions（执行步骤）

### Step 1：读取测试上下文（10 分钟内）
1. 读取 `company/projects/<product>/architecture.md`，了解模块拆分与依赖关系
2. 读取 `company/projects/<product>/interfaces.yaml`，提取接口契约
3. 读取 `company/projects/<product>/delivery-notes.md`，了解交付清单与已知问题
4. 读取 `company/projects/<product>/source/` 下所有代码文件，统计模块数与代码行数

### Step 2：生成测试用例（25 分钟内）
1. 根据规格为每个模块生成测试用例，覆盖三类场景：
   - **正常路径**：典型输入 → 预期输出
   - **边界条件**：空输入 / 超长输入 / 极值 / 数值边界
   - **异常路径**：依赖失败 / 网络错误 / 权限不足 / 资源耗尽
2. 输出格式：
   ```
   测试用例: 用例编号 / 输入 / 预期 / 实际
   通过/失败: 统计与明细
   缺陷清单: 严重程度 / 复现步骤 / 建议优先级
   ```
3. 用例编号规则：`TC-<module>-<scenario>-<seq>`，如 `TC-content_generator-normal-001`

### Step 3：执行测试（25 分钟内）
1. 运行 Programmer 产出的 `<module>_test.py`
2. 按生成的测试用例手工或脚本执行补充测试
3. 记录每个用例的通过 / 失败状态
4. 失败用例捕获实际输出与异常堆栈

### Step 4：回归测试（15 分钟内）
1. 读取历史缺陷清单（`defects.yaml` 中 `status=open` 的项）
2. 对每个历史缺陷场景执行回归测试
3. **回归测试不得遗漏历史缺陷场景**
4. 已修复的缺陷标记 `status=closed`，未修复的保持 `open` 并升级优先级

### Step 5：产出测试报告与缺陷清单（15 分钟内）
1. 写入 `company/projects/<product>/test-report.md`，格式：
   ```markdown
   # <product> 测试报告 - YYYY-MM-DD

   ## 测试概览
   - 模块数: <N>
   - 测试用例总数: <N>
   - 通过: <N> | 失败: <N> | 阻塞: <N>
   - 通过率: <N>%
   - 测试覆盖率: <N>%

   ## 测试用例明细
   | 用例编号 | 模块 | 场景 | 输入 | 预期 | 实际 | 结果 |
   | --- | --- | --- | --- | --- | --- | --- |
   | TC-content_generator-normal-001 | content_generator | 正常 | topic="DeFi", keywords=["Uniswap"] | 返回 dict | 返回 dict | PASS |
   | TC-content_generator-boundary-001 | content_generator | 边界 | topic="" 空字符串 | raise ValueError | raise ValueError | PASS |
   | TC-content_generator-exception-001 | content_generator | 异常 | LLM 超时 | raise LLMError | 返回 None | FAIL |

   ## 缺陷清单
   | 缺陷编号 | 严重程度 | 模块 | 复现步骤 | 建议优先级 | 状态 |
   | --- | --- | --- | --- | --- | --- |
   | DEF-001 | P1 | content_generator | 1. mock LLM 超时 2. 调用 generate() 3. 期望 raise LLMError，实际返回 None | P1 | open |
   ```
2. 写入 `company/projects/<product>/defects.yaml`，结构化存储缺陷便于跟踪
3. **任何 P0/P1 缺陷必须阻断发布**：publish `topic=task.blocked` reason=defect_p1
4. publish `topic=task.done.test`，payload 含 task_id / 通过率 / 缺陷数

## Notes（注意事项）
- **质量红线**：任何 P0/P1 缺陷必须阻断发布，不得"先发布后修复"
- **回归纪律**：历史缺陷场景必须 100% 覆盖回归测试
- **边界覆盖**：边界条件测试不得遗漏（空值 / 极值 / 超长 / 数值边界）
- **缺陷描述**：缺陷复现步骤必须可重现，含输入 / 期望 / 实际 / 环境
- **降级路径**：LLM 后端失败时，按 `interfaces.yaml` 自动生成接口契约测试骨架（参数类型校验等），标记 degraded
- **协作**：发现缺陷后通过 `publish(topic="task.blocked")` 转回 Programmer，附 defect_id

## Examples（示例）

### 示例：缺陷清单（结构化）
```yaml
# defects.yaml
defects:
  - id: DEF-001
    severity: P1
    module: content_generator
    title: LLM 超时未抛出 LLMError，返回 None
    reproduce_steps:
      - mock LLMClient.chat 等待 31 秒
      - 调用 generate(topic="test", keywords=["a"])
      - 期望 raise LLMError("LLM 调用超时")
      - 实际返回 {"content_id": "", "title": "", "body": "", "meta": {}}
    suggested_priority: P1
    status: open
    found_at: 2026-06-29T14:30:00
    found_by: tester
```

### 示例：测试报告概览
```markdown
## 测试概览
- 模块数: 4
- 测试用例总数: 32
- 通过: 29 | 失败: 3 | 阻塞: 0
- 通过率: 90.6%
- 测试覆盖率: 82%

## 阻断发布建议
- DEF-001 (P1): content_generator 异常路径未正确处理，建议阻断 Phase-Promote
- DEF-002 (P2): seo_optimizer 边界条件未覆盖空 keywords，可发布但需修复
```

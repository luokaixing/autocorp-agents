---
id: WF-DESIGN
name: 架构设计与方案工作流 SOP
trigger: 每日 10:00 Phase-Design 触发（监听 topic=research.prd_ready 消息后启动）
owner_role: architect
inputs:
  - company/projects/<product>/prd.md
  - company/decisions/ceo-YYYY-MM-DD.md
  - company/knowledge/decisions/cto-tech-direction.md
outputs:
  - company/projects/<product>/architecture.md
  - company/projects/<product>/modules.yaml
  - company/projects/<product>/interfaces.yaml
  - company/projects/<product>/tech-selection.md
acceptance_criteria:
  - architecture.md 已产出且含模块拆分清单/接口定义/技术规范三大章节
  - modules.yaml 已产出且模块依赖图为 DAG（无循环依赖）
  - interfaces.yaml 已产出且接口优先 RESTful 或 JSON RPC（非 GraphQL）
  - tech-selection.md 已产出且选用依赖均已发布稳定版
  - CTO 评审意见为 approve 或 revise（非 reject）
  - 设计完成已 publish topic=design.completed 消息
sla_minutes: 90
fallback: 若 PRD 缺失，publish topic=task.blocked reason=missing_prd 转回 PM；若 LLM 后端失败，复用 autoCorp-daily/architecture.md 模板填充新模块名，标记 sop_compliance=degraded
---

# 架构设计与方案工作流 SOP

## 工作流概述
本工作流对应 Phase-Design，由架构师主持、CTO 评审。从 PRD 出发，先做技术选型 → 再做模块拆分 → 然后定义接口 → 最后产出技术规范，为 WF-BUILD 提供可执行的设计文档。

## 工作流参与者
- **主责**：Architect（架构师）
- **评审**：CTO（技术选型与架构方案最终把关）
- **协作**：PM（需求澄清）、Programmer（实现可行性预评估，可选）

## Actions（执行步骤）

### Stage 1：PRD 解析与约束识别（10 分钟内）
1. 读取 `company/projects/<product>/prd.md`，提取：
   - 功能需求清单（按 P0/P1/P2 优先级）
   - 非功能需求（性能 / 安全 / 可维护性）
   - MVP 范围与验收标准
2. 读取 `company/decisions/ceo-YYYY-MM-DD.md`，了解预算与周期约束
3. 读取 `company/knowledge/decisions/cto-tech-direction.md`，了解标准技术栈与禁忌清单
4. 若 PRD 缺失 → publish `topic=task.blocked` reason=`missing_prd` 转回 PM，工作流终止

### Stage 2：技术选型（CTO 主导，15 分钟内）
1. CTO 从四个维度评估候选技术栈：
   - 可维护性 / 招聘成本 / 生态成熟度 / AI 自主开发可行性
2. **禁止选用尚未发布稳定版的依赖**（v0.x / alpha / beta）
3. **优先复用 AutoCorp 现有技术资产**：Python / FastAPI / pyyaml / Playwright
4. 写入 `company/projects/<product>/tech-selection.md`，含选型决策 / 理由 / 风险点

### Stage 3：模块拆分（Architect 主导，25 分钟内）
1. 按"职责单一且可独立测试"原则拆分模块
2. 每个模块定义：模块名（snake_case）/ 职责 / 依赖关系 / 对外接口
3. 写入 `company/projects/<product>/modules.yaml`
4. 检查循环依赖：依赖图必须是 DAG，发现环则重构
5. **MVP 范围不得超过 4 周开发量**（来自 PRD 约束）

### Stage 4：接口定义（Architect 主导，20 分钟内）
1. 为每个模块的关键 API 定义请求 / 响应 schema
2. **接口优先 RESTful 或简单 JSON RPC，禁止 GraphQL**
3. 定义错误码与错误响应格式
4. 写入 `company/projects/<product>/interfaces.yaml`，格式：
   ```yaml
   interfaces:
     - endpoint: POST /api/v1/<module>/<action>
       module: <module_name>
       request_schema: {...}
       response_schema: {...}
       error_codes: [{code, meaning}]
   ```

### Stage 5：技术规范（Architect 主导，10 分钟内）
1. 命名规范：模块 / 文件 / 函数 / 变量命名约定（参考 PEP 8）
2. 目录结构：明确 `src/` / `tests/` / `docs/` 等目录布局
3. 测试要求：每个模块必须有单元测试，覆盖率 >= 70%
4. 错误处理：统一异常类型与日志格式
5. 汇总 Stage 3-5 输出到 `company/projects/<product>/architecture.md`

### Stage 6：CTO 评审与 publish（10 分钟内）
1. CTO 从可维护性 / 接口契约 / 错误处理 / 测试覆盖四个维度评审
2. 评审意见写入 `company/knowledge/decisions/cto-YYYY-MM-DD.md`，含 `approve / revise / reject`
3. 若 `reject` → publish `topic=task.blocked` reason=`design_rejected`，回到 Stage 3 修订
4. 若 `approve` 或 `revise` → publish `topic=design.completed`，payload 含：
   ```json
   {
     "product": "<product>",
     "modules_count": <N>,
     "interfaces_count": <N>,
     "cto_review": "approve",
     "architecture_path": "company/projects/<product>/architecture.md"
   }
   ```
5. 触发 WF-BUILD 工作流（Programmer + Tester 进入 Phase-Build）

## Notes（注意事项）
- **职责单一**：每个模块只做一件事，避免 God Object
- **可独立测试**：模块所有依赖可 mock，单元测试不依赖外部服务
- **简单接口**：RESTful 或 JSON RPC 优先，禁止 GraphQL / gRPC
- **复用优先**：优先复用 `engine/` 下现有模块（workspace / ledger / task_queue / llm_client）
- **MVP 约束**：MVP 范围不得超过 4 周开发量，超出则拆分多期
- **降级路径**：LLM 后端失败时，复用 `autoCorp-daily/architecture.md` 模板，标记 degraded
- **超时处理**：超过 90 分钟未完成，强制结束，已有产出保留，未完成项标记 `phase_timeout`

## Examples（示例）

### 示例：模块依赖 DAG 检查
```yaml
# modules.yaml
modules:
  - name: content_generator
    depends_on: [llm_client, prompt_templates]
  - name: seo_optimizer
    depends_on: [content_generator]
  - name: channel_adapter
    depends_on: [seo_optimizer]
  - name: analytics_tracker
    depends_on: []

# 依赖图（DAG，无环）：
# llm_client ──┐
#              v
# prompt_templates ─> content_generator ─> seo_optimizer ─> channel_adapter
# analytics_tracker (独立)
```

### 示例：CTO 评审意见
```markdown
# cto-2026-06-29.md

## 评审: SEO 内容生成器架构设计
- 决策: approve
- 理由:
  1. 模块拆分清晰，职责单一
  2. 接口采用 RESTful，符合简单原则
  3. 复用 engine/llm_client.py 与 engine/workspace.py，无新依赖引入
  4. 测试要求覆盖率 >= 70% 合理
- 风险点:
  - LLM 并发上限需在 architecture.md 中明确（建议 5）
  - YAML 大文件读写需有切分策略
- 建议（非阻塞）:
  - 考虑为 analytics_tracker 增加 batch 上报接口
```

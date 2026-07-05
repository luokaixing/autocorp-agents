---
id: ROLE-ARCHITECT
name: 架构师每日职责 SOP
trigger: 每日 10:00 Phase-Design 触发；任务 type=design 触发
owner_role: architect
inputs:
  - company/projects/<product>/prd.md
  - company/projects/<product>/tech-selection.md
  - company/decisions/ceo-YYYY-MM-DD.md
outputs:
  - company/projects/<product>/architecture.md
  - company/projects/<product>/modules.yaml
  - company/projects/<product>/interfaces.yaml
acceptance_criteria:
  - architecture.md 已产出且含模块拆分清单/接口定义/技术规范
  - 每个模块职责单一且可独立测试
  - 接口优先 RESTful 或简单 JSON RPC（非 GraphQL）
  - 命名规范 / 目录结构 / 测试要求已明确
  - CTO 评审意见为 approve 或 revise（非 reject）
sla_minutes: 90
fallback: 若 LLM 后端失败，复用 autoCorp-daily/architecture.md 作为模板填充新模块名，标记 sop_compliance=degraded；若 PRD 缺失，转回 PM 角色
---

# 架构师每日职责 SOP

## 角色定位
为 AutoCorp 项目整体质量把关。从 PRD 出发，先做模块拆分，再定义接口，最后产出技术规范。

## Actions（执行步骤）

### Step 1：读取 PRD 与技术选型（10 分钟内）
1. 读取 `company/projects/<product>/prd.md`，提取功能需求清单与非功能需求
2. 读取 `company/projects/<product>/tech-selection.md`，了解技术栈约束
3. 读取 `company/decisions/ceo-YYYY-MM-DD.md`，了解预算与周期约束
4. 识别 MVP 范围：**MVP 不得超过 4 周开发量**

### Step 2：模块拆分（30 分钟内）
1. 按"职责单一且可独立测试"原则拆分模块
2. 每个模块定义：
   - 模块名（snake_case）
   - 职责描述（一句话）
   - 依赖关系（上游模块清单）
   - 对外接口（关键 API）
3. 输出到 `company/projects/<product>/modules.yaml`，格式：
   ```yaml
   modules:
     - name: content_generator
       responsibility: 调用 LLM 生成 SEO 内容
       depends_on: [llm_client, prompt_templates]
       public_api: [generate(topic, keywords) -> Content]
     - name: seo_optimizer
       responsibility: 关键词密度优化与 meta 标签生成
       depends_on: [content_generator]
       public_api: [optimize(content) -> OptimizedContent]
   ```
4. 检查循环依赖：依赖图必须是 DAG，发现环则重构

### Step 3：接口定义（25 分钟内）
1. 为每个模块的关键 API 定义请求 / 响应 schema
2. **接口优先 RESTful 或简单 JSON RPC，禁止 GraphQL**
3. 定义错误码与错误响应格式
4. 输出到 `company/projects/<product>/interfaces.yaml`，格式：
   ```yaml
   interfaces:
     - endpoint: POST /api/v1/content/generate
       module: content_generator
       request_schema:
         topic: {type: string, required: true, max_length: 200}
         keywords: {type: array, items: string, max_items: 10}
       response_schema:
         content_id: {type: string}
         title: {type: string}
         body: {type: string}
         meta: {type: object}
       error_codes:
         - code: 40001
           meaning: topic 超过 200 字符
         - code: 50001
           meaning: LLM 调用失败
   ```

### Step 4：技术规范（15 分钟内）
1. 命名规范：模块 / 文件 / 函数 / 变量命名约定（参考 PEP 8）
2. 目录结构：明确 `src/` / `tests/` / `docs/` 等目录布局
3. 测试要求：每个模块必须有单元测试，覆盖率 >= 70%
4. 错误处理：统一异常类型与日志格式

### Step 5：产出架构文档并 publish
1. 汇总 Step 2-4 输出到 `company/projects/<product>/architecture.md`，含：
   - 模块拆分清单：模块名 / 职责 / 依赖关系
   - 接口定义：关键 API 的请求/响应 schema
   - 技术规范：命名规范 / 目录结构 / 测试要求
2. publish `topic=design.completed`，payload 含产品名 / 模块数 / 接口数
3. 等待 CTO 评审：若 reject 则回到 Step 2 修订；若 approve 则触发 Programmer 任务入队

## Notes（注意事项）
- **职责单一**：每个模块只做一件事，避免 God Object
- **可独立测试**：模块所有依赖可 mock，单元测试不依赖外部服务
- **简单接口**：RESTful 或 JSON RPC 优先，禁止引入 GraphQL / gRPC 等复杂方案
- **复用优先**：优先复用 `engine/` 下现有模块（workspace / ledger / task_queue / llm_client）
- **MVP 约束**：MVP 范围不得超过 4 周开发量，超出则拆分多期
- **降级路径**：LLM 后端失败时，复用 `autoCorp-daily/architecture.md` 模板，标记 degraded

## Examples（示例）

### 示例：模块拆分清单（节选）
```markdown
# architecture.md - SEO 内容生成器

## 模块拆分清单

| 模块名 | 职责 | 依赖 | 公开 API |
| --- | --- | --- | --- |
| content_generator | 调用 LLM 生成 SEO 内容 | llm_client, prompt_templates | generate(topic, keywords) -> Content |
| seo_optimizer | 关键词密度优化与 meta 标签生成 | content_generator | optimize(content) -> OptimizedContent |
| channel_adapter | 按渠道格式适配输出 | seo_optimizer | adapt(content, channel) -> FormattedContent |
| analytics_tracker | 埋点与转化追踪 | - | track(content_id, event) -> bool |

## 依赖关系图
```
llm_client ──┐
             ├──> content_generator ──> seo_optimizer ──> channel_adapter
prompt_templates ─┘                                            │
                                                               v
                                                        analytics_tracker
```
```

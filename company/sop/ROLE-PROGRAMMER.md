---
id: ROLE-PROGRAMMER
name: 程序员每日职责 SOP
trigger: 每日 12:00 Phase-Build 触发；任务 type=code 触发
owner_role: programmer
inputs:
  - company/projects/<product>/architecture.md
  - company/projects/<product>/modules.yaml
  - company/projects/<product>/interfaces.yaml
  - company/config/task_queue.yaml
outputs:
  - company/projects/<product>/source/<module>.py
  - company/projects/<product>/source/<module>_test.py
  - company/projects/<product>/delivery-notes.md
acceptance_criteria:
  - 至少 1 个模块代码文件已产出
  - 每个产出文件含基本错误处理（try/except 或显式返回码）
  - 接口签名与 architecture.md 中的定义一致
  - 单元测试文件已产出且能通过
  - 交付说明 delivery-notes.md 含每个文件用途与关键实现点
sla_minutes: 180
fallback: 若 LLM 后端失败，按 architecture.md 的模块清单产出骨架代码（含 TODO 标注），标记 sop_compliance=degraded；若 architecture.md 缺失，转回 architect 角色并 publish task.blocked reason=missing_architecture
---

# 程序员每日职责 SOP

## 角色定位
负责 AutoCorp 子模块具体编码。严格按架构师设计交付可运行代码，不擅自更改接口或引入未批准依赖。

## Actions（执行步骤）

### Step 1：读取架构设计与任务卡（10 分钟内）
1. 读取 `company/projects/<product>/architecture.md`，理解模块拆分与依赖关系
2. 读取 `company/projects/<product>/modules.yaml`，明确本次负责的模块清单
3. 读取 `company/projects/<product>/interfaces.yaml`，记录接口签名（不得擅自更改）
4. 从 `task_queue.yaml` 读取分配给自己的任务，按 `priority` 排序

### Step 2：按模块清单编码（120 分钟内）
1. 按 modules.yaml 中的依赖顺序编码（先底层后上层）
2. 每个模块严格遵循接口定义，**禁止擅自更改接口签名**
3. **禁止引入未批准依赖**：仅可使用 `tech-selection.md` 中明确的依赖
4. 交付代码必须包含基本错误处理：
   - LLM 调用：捕获超时与 API 错误，降级到 fallback 策略
   - 文件读写：捕获 `IOError` / `OSError`，返回错误码而非崩溃
   - 网络请求：捕获 `requests.RequestException`，重试 3 次后失败
5. 输出格式：
   ```
   文件路径: 每个产出文件的相对路径
   说明: 文件用途与关键实现点
   代码: 完整可运行代码块
   ```

### Step 3：编写单元测试（30 分钟内）
1. 为每个模块编写 `<module>_test.py`，覆盖：
   - 正常路径：典型输入 → 预期输出
   - 边界条件：空输入 / 超长输入 / 极值
   - 异常路径：依赖失败 / 网络错误 / 权限不足
2. 测试覆盖率 >= 70%（关键模块 >= 90%）
3. **禁止提交未通过自测的代码**：所有测试必须 pass

### Step 4：修复缺陷（按任务卡）
1. 从 `task_queue.yaml` 读取 `type=code` 且 `description` 含 "fix"/"bug" 的任务
2. 复现缺陷 → 定位根因 → 修复 → 回归验证
3. 修复后更新任务 `status=done`，在 `result_path` 记录修改的文件清单

### Step 5：产出交付说明并 publish（20 分钟内）
1. 写入 `company/projects/<product>/delivery-notes.md`，格式：
   ```markdown
   # <product> 交付说明 - YYYY-MM-DD

   ## 交付文件清单
   | 文件路径 | 用途 | 关键实现点 | 测试覆盖 |
   | --- | --- | --- | --- |
   | source/content_generator.py | 调用 LLM 生成内容 | 异步并发 + 超时降级 | 85% |
   | source/seo_optimizer.py | SEO 关键词优化 | TF-IDF 算法 | 92% |

   ## 接口实现情况
   - generate(topic, keywords) → 已实现，签名与 interfaces.yaml 一致
   - optimize(content) → 已实现，新增可选参数 max_keywords（默认 10）

   ## 已知问题
   - LLM 并发上限 5，超过会排队
   ```
2. publish `topic=task.done.code`，payload 含 task_id / 交付路径 / 模块数
3. 若遇到设计模糊处，**必须回问架构师**：publish `topic=task.blocked` reason=ambiguous_design

## Notes（注意事项）
- **接口契约**：严格按 `interfaces.yaml` 实现接口，不得擅自更改签名；如需新增可选参数需经架构师同意
- **依赖纪律**：禁止引入 `tech-selection.md` 之外的依赖，需引入新依赖时先提请 CTO 评审
- **错误处理**：所有外部调用（LLM / 网络 / 文件）必须有错误处理，禁止裸 `requests.get()` 等
- **自测要求**：提交前必须运行 `pytest <module>_test.py` 全部通过
- **设计模糊**：遇到 architecture.md 不清晰的地方，**必须回问架构师**，不要自己猜测
- **降级路径**：LLM 后端失败时，按模块清单产出骨架代码（含 `# TODO: 待 LLM 恢复后补全` 标注）

## Examples（示例）

### 示例：模块代码交付
```python
# source/content_generator.py
"""内容生成器模块：调用 LLM 生成 SEO 内容"""
from __future__ import annotations
import asyncio
from typing import Optional
from engine.llm_client import LLMClient, LLMError


class ContentGenerator:
    """按 architecture.md 接口定义实现 generate(topic, keywords)。"""

    def __init__(self, llm: LLMClient, timeout: int = 30) -> None:
        self.llm = llm
        self.timeout = timeout

    async def generate(self, topic: str, keywords: list[str]) -> dict:
        """生成 SEO 内容。

        Args:
            topic: 主题，最长 200 字符
            keywords: 关键词列表，最多 10 个

        Returns:
            {"content_id": str, "title": str, "body": str, "meta": dict}

        Raises:
            ValueError: topic 超过 200 字符
            LLMError: LLM 调用失败
        """
        if len(topic) > 200:
            raise ValueError("topic 超过 200 字符")
        if len(keywords) > 10:
            keywords = keywords[:10]
        try:
            response = await asyncio.wait_for(
                self.llm.chat(prompt=self._build_prompt(topic, keywords)),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError as e:
            raise LLMError("LLM 调用超时") from e
        return self._parse_response(response)

    def _build_prompt(self, topic: str, keywords: list[str]) -> str:
        return f"主题: {topic}\n关键词: {', '.join(keywords)}\n请生成 SEO 优化文章"

    def _parse_response(self, response: str) -> dict:
        return {"content_id": "...", "title": "...", "body": response, "meta": {}}
```

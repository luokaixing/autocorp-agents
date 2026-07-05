"""Tester 智能体 - 测试员

对质量负最终把关责任，根据规格生成测试用例并执行，产出缺陷清单。
"""
from __future__ import annotations

from typing import Any, Dict, List

from engine.agents.base import BaseAgent
from engine.workspace import WorkspaceManager
from engine.llm_client import LLMClient


class Tester(BaseAgent):
    """测试员：负责测试、验证、缺陷报告、回归测试。"""

    def __init__(self, workspace: WorkspaceManager, llm_client: LLMClient = None):
        super().__init__("tester", workspace, llm_client)

    def run_tests(self, module_info: dict) -> dict:
        """执行测试，返回 {passed, failed, bugs, report, raw_response}。"""
        user_message = (
            f"请对以下模块执行测试，输出测试用例（含正常/边界/异常）、通过/失败统计、缺陷清单。\n"
            f"模块信息：\n{module_info}"
        )
        raw = self.call_llm(user_message, context="任务：测试与质量把关")
        # 持久化测试报告
        report_path = self.save_output(
            f"# 测试报告\n\n{raw}",
            category="report",
            filename="tester-report.md",
        )
        return {
            "passed": None,
            "failed": None,
            "bugs": None,
            "report": report_path,
            "raw_response": raw,
        }

    def generate_test_cases(self, spec: dict) -> list:
        """根据规格生成测试用例，返回用例列表（每项为 dict）。"""
        user_message = (
            f"请根据以下规格生成测试用例列表，每条用例包含：编号、输入、预期、类型（正常/边界/异常）。\n"
            f"规格：\n{spec}"
        )
        raw = self.call_llm(user_message, context="任务：测试用例生成与验证")
        # 简单结构化：将原始响应作为单条用例返回，便于上游消费
        return [{
            "id": "tc_001",
            "input": spec,
            "expected": "见 raw_response",
            "type": "generated",
            "raw_response": raw,
        }]

    # ------------------------------------------------------------------
    # 规则检查（execute_task 调用）
    # ------------------------------------------------------------------
    def test_from_task(self, task: dict) -> str:
        """对关联文章/代码执行规则检查，产出 markdown 测试报告。

        检查项：字数（≥1500）、关键词密度（≥1%）、打赏地址存在、markdown 格式正确。
        LLM 可选用于内容质量评估，失败则纯规则检查。

        Returns:
            markdown 测试报告文本。
        """
        from datetime import datetime
        from engine.secrets import SecretsManager

        # 从密钥管理器读取打赏地址（不再硬编码）
        try:
            _secrets = SecretsManager()
            TIPPING_ADDRESS = _secrets.get("tipping_address_eth") or "[配置后显示]"
        except Exception:
            TIPPING_ADDRESS = "[配置后显示]"
        result_path = task.get("result_path", "") if isinstance(task, dict) else ""
        keyword = ""
        if isinstance(task, dict):
            keyword = task.get("keyword") or task.get("title") or task.get("topic") or ""

        content = self.workspace.read_text(result_path) if result_path else ""

        checks: list[dict] = []  # [{item, result, detail}]

        if not content:
            checks.append({"item": "被测文件存在", "result": "FAIL",
                           "detail": f"未提供 result_path 或文件为空：{result_path or '（空）'}"})
            checks.append({"item": "字数 ≥ 1500", "result": "FAIL", "detail": "无内容"})
            checks.append({"item": "关键词密度 ≥ 1%", "result": "FAIL", "detail": "无内容"})
            checks.append({"item": "打赏地址存在", "result": "FAIL", "detail": "无内容"})
            checks.append({"item": "markdown 格式正确", "result": "FAIL", "detail": "无内容"})
        else:
            # 字数
            word_count = len(content.split())
            checks.append({
                "item": "字数 ≥ 1500",
                "result": "PASS" if word_count >= 1500 else "FAIL",
                "detail": f"实际字数 {word_count}",
            })
            # 关键词密度
            if keyword:
                kw_lower = keyword.lower()
                kw_count = content.lower().count(kw_lower)
                density = kw_count / max(word_count, 1) * 100
                checks.append({
                    "item": f"关键词「{keyword}」密度 ≥ 1%",
                    "result": "PASS" if density >= 1.0 else "FAIL",
                    "detail": f"出现 {kw_count} 次，密度 {density:.2f}%",
                })
            else:
                checks.append({"item": "关键词密度 ≥ 1%", "result": "SKIP",
                               "detail": "未提供 keyword，跳过"})
            # 打赏地址
            checks.append({
                "item": "打赏地址存在",
                "result": "PASS" if TIPPING_ADDRESS in content else "FAIL",
                "detail": TIPPING_ADDRESS if TIPPING_ADDRESS in content else "未找到打赏地址",
            })
            # markdown 格式
            has_md = content.lstrip().startswith("#") or "\n##" in content or "\n###" in content
            checks.append({
                "item": "markdown 格式正确",
                "result": "PASS" if has_md else "FAIL",
                "detail": "检测到标题层级" if has_md else "未检测到 markdown 标题",
            })

        # 可选：LLM 内容质量评估（失败则纯规则检查）
        llm_eval = ""
        if content:
            try:
                user_message = (
                    f"请对以下文章做简要质量评估（3-5 句），指出专业性、可读性与 SEO 友好度。\n"
                    f"文章：\n{content[:2000]}"
                )
                llm_eval = self.call_llm(user_message, context="任务：测试与质量把关")
            except Exception as e:  # noqa: BLE001 - LLM 失败不影响规则检查
                print(f"[tester] LLM 质量评估失败，使用纯规则检查：{e}")
                llm_eval = ""

        # 组装报告
        pass_count = sum(1 for c in checks if c["result"] == "PASS")
        fail_count = sum(1 for c in checks if c["result"] == "FAIL")
        skip_count = sum(1 for c in checks if c["result"] == "SKIP")
        overall = "PASS" if fail_count == 0 else "FAIL"

        lines: list[str] = []
        lines.append(f"# 测试报告 {datetime.now().isoformat(timespec='seconds')}")
        lines.append("")
        lines.append(f"- 被测文件：{result_path or '（无）'}")
        lines.append(f"- 关键词：{keyword or '（未指定）'}")
        lines.append(f"- 通过：{pass_count} / 失败：{fail_count} / 跳过：{skip_count}")
        lines.append(f"- 总体结论：**{overall}**")
        lines.append("")
        lines.append("## 检查项清单")
        lines.append("")
        lines.append("| 检查项 | 结果 | 详情 |")
        lines.append("|--------|------|------|")
        for c in checks:
            lines.append(f"| {c['item']} | {c['result']} | {c['detail']} |")
        lines.append("")
        if llm_eval:
            lines.append("## LLM 内容质量评估")
            lines.append("")
            lines.append(llm_eval)
            lines.append("")
        else:
            lines.append("## LLM 内容质量评估")
            lines.append("")
            lines.append("> LLM 评估未执行或失败，本次为纯规则检查。")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 任务执行
    # ------------------------------------------------------------------
    def execute_task(self, task: dict) -> dict:
        """执行 test 类任务：对关联产出执行规则检查并落盘测试报告。

        Returns:
            ``{status: "done"|"failed", result_path: str, error_reason: str}``
        """
        from engine.task_queue import TaskQueue

        task_id = task.get("id", "") if isinstance(task, dict) else ""
        try:
            queue = TaskQueue(self.workspace)
            queue.update_status(task_id, "in_progress")

            # 1. 执行规则检查
            report = self.test_from_task(task)

            # 2. 写入 company/reports/test-<task_id>.md
            target_path = self.workspace.reports_dir / f"test-{task_id}.md"
            self.workspace.write_text(target_path, report)
            result_path = str(target_path.resolve())

            # 3. 汇报完成（无论检查项 PASS/FAIL，报告生成成功即任务完成）
            self.report_done(task_id, result_path)
            return {"status": "done", "result_path": result_path, "error_reason": ""}
        except Exception as e:  # noqa: BLE001 - 顶层兜底
            self.report_failed(task_id, str(e))
            return {"status": "failed", "result_path": "", "error_reason": str(e)}

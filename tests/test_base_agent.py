"""BaseAgent 单元测试

使用标准库 unittest，可直接 `python -m unittest tests.test_base_agent` 运行。
也兼容 pytest 风格。

测试覆盖：
- load_config 能正确读取配置
- build_prompt 包含 persona 和 responsibilities
- save_output 能正确保存到对应目录
- check_responsibility 对相关/不相关任务返回正确布尔值
- call_llm 越界任务时附加警告
"""
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from engine.workspace import WorkspaceManager
from engine.agents.base import BaseAgent


class TestBaseAgent(unittest.TestCase):
    """BaseAgent 测试套件。"""

    def setUp(self) -> None:
        # 每个测试用例使用独立的临时目录作为工作区根目录
        self.tmp_root = Path(tempfile.mkdtemp(prefix="autocorp_agent_"))
        self.ws = WorkspaceManager(root_dir=self.tmp_root)
        self.ws.initialize()

        # 准备测试用 employees.yaml
        employees_config = {
            "employees": [
                {
                    "name": "CEO",
                    "role": "ceo",
                    "persona": "你是 AutoCorp 的 CEO，擅长成本分析与战略决策。",
                    "responsibilities": ["成本分析", "立项决策", "市场判断"],
                    "tools": ["ledger", "market-research"],
                    "system_prompt": "你是一位谨慎而果断的 CEO。",
                },
                {
                    "name": "Programmer",
                    "role": "programmer",
                    "persona": "你是 AutoCorp 的程序员，负责子模块编码实现。",
                    "responsibilities": ["编码", "模块开发", "代码实现"],
                    "tools": ["workspace"],
                    "system_prompt": "你是一位严谨的程序员。",
                },
            ]
        }
        self.ws.write_yaml(self.ws.employees_config_path, employees_config)

        # 使用 Mock LLM 客户端，避免真实网络调用
        self.mock_llm = MagicMock()
        self.mock_llm.chat.return_value = "LLM 模拟响应"

        self.ceo = BaseAgent(role="ceo", workspace=self.ws, llm_client=self.mock_llm)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    # ------------------------------------------------------------------
    # load_config
    # ------------------------------------------------------------------
    def test_load_config_returns_matching_role(self) -> None:
        """load_config 应返回与 role 匹配的完整配置。"""
        cfg = self.ceo.load_config()
        self.assertEqual(cfg["role"], "ceo")
        self.assertEqual(cfg["name"], "CEO")
        self.assertEqual(cfg["persona"], "你是 AutoCorp 的 CEO，擅长成本分析与战略决策。")
        self.assertIn("立项决策", cfg["responsibilities"])
        self.assertIn("ledger", cfg["tools"])
        self.assertEqual(cfg["system_prompt"], "你是一位谨慎而果断的 CEO。")

    def test_load_config_missing_role_returns_minimal(self) -> None:
        """未匹配到角色时应返回仅含 role 的最小字典。"""
        agent = BaseAgent(role="nonexistent", workspace=self.ws, llm_client=self.mock_llm)
        cfg = agent.load_config()
        self.assertEqual(cfg, {"role": "nonexistent"})

    def test_load_config_empty_employees(self) -> None:
        """employees.yaml 为空列表时返回最小字典。"""
        self.ws.write_yaml(self.ws.employees_config_path, {"employees": []})
        agent = BaseAgent(role="ceo", workspace=self.ws, llm_client=self.mock_llm)
        self.assertEqual(agent.config, {"role": "ceo"})

    # ------------------------------------------------------------------
    # build_prompt
    # ------------------------------------------------------------------
    def test_build_prompt_contains_persona(self) -> None:
        """build_prompt 应包含 persona 内容。"""
        prompt = self.ceo.build_prompt()
        self.assertIn("你是 AutoCorp 的 CEO", prompt)
        self.assertIn("成本分析", prompt)

    def test_build_prompt_contains_responsibilities(self) -> None:
        """build_prompt 应包含全部职责项。"""
        prompt = self.ceo.build_prompt()
        self.assertIn("立项决策", prompt)
        self.assertIn("市场判断", prompt)
        self.assertIn("成本分析", prompt)

    def test_build_prompt_includes_tools(self) -> None:
        """build_prompt 应包含可用工具说明。"""
        prompt = self.ceo.build_prompt()
        self.assertIn("ledger", prompt)
        self.assertIn("market-research", prompt)
        self.assertIn("可用工具", prompt)

    def test_build_prompt_includes_constraints(self) -> None:
        """build_prompt 应包含约束段落。"""
        prompt = self.ceo.build_prompt()
        self.assertIn("约束", prompt)
        self.assertIn("职责范围", prompt)

    def test_build_prompt_includes_context(self) -> None:
        """build_prompt 应在末尾追加 context。"""
        prompt = self.ceo.build_prompt(context="当前账户余额 $5000，目标赛道 SEO")
        self.assertIn("当前账户余额 $5000", prompt)
        self.assertIn("上下文", prompt)

    # ------------------------------------------------------------------
    # save_output
    # ------------------------------------------------------------------
    def test_save_output_to_decisions_dir(self) -> None:
        """category='decision' 应保存到 knowledge/decisions/。"""
        path = self.ceo.save_output("决策内容", category="decision")
        p = Path(path)
        self.assertTrue(p.exists())
        self.assertIn("decisions", path)
        self.assertEqual(p.read_text(encoding="utf-8"), "决策内容")

    def test_save_output_to_market_research_dir(self) -> None:
        """category='research' 应保存到 knowledge/market-research/。"""
        path = self.ceo.save_output("调研内容", category="research")
        self.assertTrue(Path(path).exists())
        self.assertIn("market-research", path)

    def test_save_output_to_reports_dir(self) -> None:
        """category='report' 应保存到 reports/。"""
        path = self.ceo.save_output("日报内容", category="report")
        self.assertTrue(Path(path).exists())
        self.assertIn("reports", path)

    def test_save_output_to_meetings_dir(self) -> None:
        """category='meeting' 应保存到 meetings/。"""
        path = self.ceo.save_output("会议纪要", category="meeting")
        self.assertTrue(Path(path).exists())
        self.assertIn("meetings", path)

    def test_save_output_to_projects_dir(self) -> None:
        """category='project' 应保存到 projects/。"""
        path = self.ceo.save_output("项目文档", category="project")
        self.assertTrue(Path(path).exists())
        self.assertIn("projects", path)

    def test_save_output_with_custom_filename(self) -> None:
        """指定 filename 时应原样使用。"""
        path = self.ceo.save_output("内容", category="report", filename="custom.md")
        p = Path(path)
        self.assertTrue(p.exists())
        self.assertEqual(p.name, "custom.md")

    def test_save_output_auto_filename_contains_role(self) -> None:
        """未指定 filename 时应自动生成：时间戳 + 角色名。"""
        path = self.ceo.save_output("内容", category="meeting")
        name = Path(path).name
        self.assertTrue(name.endswith("-ceo.md"), f"文件名应含角色名: {name}")

    def test_save_output_returns_absolute_path(self) -> None:
        """返回路径应为绝对路径。"""
        path = self.ceo.save_output("内容", category="report")
        self.assertTrue(Path(path).is_absolute())

    def test_save_output_unknown_category_defaults_to_reports(self) -> None:
        """未知 category 应回退到 reports/。"""
        path = self.ceo.save_output("内容", category="unknown")
        self.assertTrue(Path(path).exists())
        self.assertIn("reports", path)

    # ------------------------------------------------------------------
    # check_responsibility
    # ------------------------------------------------------------------
    def test_check_responsibility_related_task_returns_true(self) -> None:
        """任务描述包含职责关键词时应返回 True。"""
        result = self.ceo.check_responsibility("请进行本季度的成本分析并给出削减方案")
        self.assertTrue(result)

    def test_check_responsibility_another_keyword_returns_true(self) -> None:
        """命中任意一个职责关键词即返回 True。"""
        result = self.ceo.check_responsibility("需要你对这个产品做立项决策")
        self.assertTrue(result)

    def test_check_responsibility_unrelated_task_returns_false(self) -> None:
        """任务描述不含任何职责关键词时应返回 False。"""
        result = self.ceo.check_responsibility("请编写用户登录模块的代码")
        self.assertFalse(result)

    def test_check_responsibility_case_insensitive(self) -> None:
        """职责匹配应忽略大小写。"""
        agent = BaseAgent(role="programmer", workspace=self.ws, llm_client=self.mock_llm)
        # responsibilities 含 "编码"，任务用大写 "编码" 仍应命中
        self.assertTrue(agent.check_responsibility("请编码实现登录接口"))

    def test_check_responsibility_no_responsibilities_defaults_true(self) -> None:
        """未定义职责时默认放行返回 True。"""
        agent = BaseAgent(role="nonexistent", workspace=self.ws, llm_client=self.mock_llm)
        self.assertTrue(agent.check_responsibility("任意任务"))

    # ------------------------------------------------------------------
    # call_llm（含职责边界警告）
    # ------------------------------------------------------------------
    def test_call_llm_invokes_chat_with_built_prompt(self) -> None:
        """call_llm 应使用 build_prompt 的结果作为 system_prompt 调用 chat。"""
        self.mock_llm.chat.return_value = "响应"
        result = self.ceo.call_llm("请做成本分析", context="余额 $1000")
        self.mock_llm.chat.assert_called_once()
        args = self.mock_llm.chat.call_args
        system_prompt = args[0][0]
        user_message = args[0][1]
        self.assertIn("成本分析", system_prompt)
        self.assertIn("余额 $1000", system_prompt)
        self.assertEqual(user_message, "请做成本分析")

    def test_call_llm_no_warning_for_in_scope_task(self) -> None:
        """职责内任务不应附加警告。"""
        self.mock_llm.chat.return_value = "响应"
        result = self.ceo.call_llm("请做成本分析")
        self.assertEqual(result, "响应")

    def test_call_llm_appends_warning_for_out_of_scope_task(self) -> None:
        """超出职责的任务应在响应末尾附加警告。"""
        self.mock_llm.chat.return_value = "响应"
        result = self.ceo.call_llm("请编写用户登录模块的代码")
        self.assertTrue(result.startswith("响应"))
        self.assertIn("超出 ceo 职责范围", result)
        self.assertIn("建议转交对应角色", result)


if __name__ == "__main__":
    unittest.main()

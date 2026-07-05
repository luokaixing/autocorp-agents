"""WorkspaceManager 单元测试

使用标准库 unittest，可直接 `python -m unittest tests.test_workspace` 运行。
也兼容 pytest 风格。
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.workspace import WorkspaceManager


class TestWorkspaceManager(unittest.TestCase):
    """WorkspaceManager 测试套件。"""

    def setUp(self) -> None:
        # 每个测试用例使用独立的临时目录作为工作区根目录
        self.tmp_root = Path(tempfile.mkdtemp(prefix="autocorp_ws_"))
        self.ws = WorkspaceManager(root_dir=self.tmp_root)

    def tearDown(self) -> None:
        # 清理临时目录
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    # ------------------------------------------------------------------
    # initialize() 创建所有预期目录
    # ------------------------------------------------------------------
    def test_initialize_creates_all_directories(self) -> None:
        self.ws.initialize()

        expected_dirs = [
            self.ws.config_dir,
            self.ws.knowledge_dir,
            self.ws.projects_dir,
            self.ws.meetings_dir,
            self.ws.reports_dir,
            self.ws.market_research_dir,
            self.ws.decisions_dir,
            self.ws.lessons_learned_dir,
            self.ws.competitors_dir,
        ]
        for d in expected_dirs:
            self.assertTrue(d.exists(), f"目录应存在: {d}")
            self.assertTrue(d.is_dir(), f"应为目录: {d}")

    def test_initialize_creates_config_files(self) -> None:
        self.ws.initialize()

        self.assertTrue(self.ws.employees_config_path.exists())
        self.assertTrue(self.ws.ledger_config_path.exists())
        self.assertTrue(self.ws.meeting_config_path.exists())

    def test_initialize_ledger_default_balance(self) -> None:
        """账本默认余额应为 $10,000。"""
        self.ws.initialize()

        ledger = self.ws.read_yaml(self.ws.ledger_config_path)
        self.assertIsNotNone(ledger)
        self.assertEqual(ledger["balance"], 10000.0)
        self.assertEqual(ledger["currency"], "USD")
        self.assertEqual(ledger["transactions"], [])

    # ------------------------------------------------------------------
    # 幂等性
    # ------------------------------------------------------------------
    def test_initialize_is_idempotent(self) -> None:
        """重复调用 initialize() 不报错、不覆盖已有配置。"""
        self.ws.initialize()

        # 修改 ledger 模拟用户数据
        self.ws.write_yaml(self.ws.ledger_config_path, {"balance": 9999.0, "transactions": []})

        # 再次初始化
        self.ws.initialize()

        # 不应覆盖
        ledger = self.ws.read_yaml(self.ws.ledger_config_path)
        self.assertEqual(ledger["balance"], 9999.0)

        # employees.yaml 也应保持未覆盖
        self.ws.write_yaml(self.ws.employees_config_path, {"employees": [{"name": "CEO"}]})
        self.ws.initialize()
        employees = self.ws.read_yaml(self.ws.employees_config_path)
        self.assertEqual(employees["employees"][0]["name"], "CEO")

    # ------------------------------------------------------------------
    # read_yaml / write_yaml
    # ------------------------------------------------------------------
    def test_read_write_yaml_roundtrip(self) -> None:
        path = self.ws.config_dir / "test_data.yaml"
        payload = {"name": "AutoCorp", "tags": ["ai", "company"], "count": 7}

        self.ws.write_yaml(path, payload)
        loaded = self.ws.read_yaml(path)

        self.assertEqual(loaded, payload)

    def test_read_yaml_missing_file_returns_none(self) -> None:
        path = self.ws.config_dir / "nonexistent.yaml"
        self.assertIsNone(self.ws.read_yaml(path))

    def test_write_yaml_creates_parent_dirs(self) -> None:
        path = self.ws.knowledge_dir / "decisions" / "deep" / "nested.yaml"
        self.ws.write_yaml(path, {"ok": True})
        self.assertTrue(path.exists())
        self.assertEqual(self.ws.read_yaml(path), {"ok": True})

    # ------------------------------------------------------------------
    # read_text / write_text
    # ------------------------------------------------------------------
    def test_read_write_text_roundtrip(self) -> None:
        path = self.ws.reports_dir / "note.md"
        content = "# 日报\n今天完成了 WorkspaceManager。\n"
        self.ws.write_text(path, content)
        self.assertEqual(self.ws.read_text(path), content)

    def test_read_text_missing_file_returns_empty(self) -> None:
        path = self.ws.reports_dir / "absent.md"
        self.assertEqual(self.ws.read_text(path), "")

    # ------------------------------------------------------------------
    # ensure_dir
    # ------------------------------------------------------------------
    def test_ensure_dir_creates_nested(self) -> None:
        target = self.tmp_root / "a" / "b" / "c"
        self.ws.ensure_dir(target)
        self.assertTrue(target.is_dir())
        # 重复调用幂等
        self.ws.ensure_dir(target)

    # ------------------------------------------------------------------
    # 路径方法返回绝对路径
    # ------------------------------------------------------------------
    def test_path_methods_return_absolute_paths(self) -> None:
        # root_dir 在 __init__ 中已 resolve，因此所有路径方法返回绝对路径
        paths = [
            self.ws.config_dir,
            self.ws.knowledge_dir,
            self.ws.projects_dir,
            self.ws.meetings_dir,
            self.ws.reports_dir,
            self.ws.market_research_dir,
            self.ws.decisions_dir,
            self.ws.lessons_learned_dir,
            self.ws.competitors_dir,
            self.ws.today_meeting_dir(),
            self.ws.today_report_path(),
        ]
        for p in paths:
            self.assertTrue(p.is_absolute(), f"应为绝对路径: {p}")

    def test_today_meeting_dir_format(self) -> None:
        from datetime import date

        expected = self.ws.meetings_dir / date.today().isoformat()
        self.assertEqual(self.ws.today_meeting_dir(), expected)

    def test_today_report_path_format(self) -> None:
        from datetime import date

        expected = self.ws.reports_dir / f"{date.today().isoformat()}-daily.md"
        self.assertEqual(self.ws.today_report_path(), expected)

    # ------------------------------------------------------------------
    # list_projects
    # ------------------------------------------------------------------
    def test_list_projects_empty(self) -> None:
        self.ws.initialize()
        self.assertEqual(self.ws.list_projects(), [])

    def test_list_projects_returns_dir_names(self) -> None:
        self.ws.initialize()
        (self.ws.projects_dir / "proj-alpha").mkdir()
        (self.ws.projects_dir / "proj-beta").mkdir()
        # 普通文件应被忽略
        (self.ws.projects_dir / "not-a-dir.txt").write_text("x", encoding="utf-8")
        # 隐藏目录应被忽略
        (self.ws.projects_dir / ".hidden").mkdir()

        result = self.ws.list_projects()
        self.assertEqual(result, ["proj-alpha", "proj-beta"])


if __name__ == "__main__":
    unittest.main()

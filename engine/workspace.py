"""共享工作区管理器

基于文件持久化（文件即数据库）的 WorkspaceManager，
为所有智能体提供统一的目录结构与文件读写 API。
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any, List

import yaml


# 项目根目录（engine/ 的上一级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 默认工作区根目录：d:\autoCompany\company
DEFAULT_WORKSPACE_DIR = _PROJECT_ROOT / "company"


class WorkspaceManager:
    """共享工作区管理器：统一管理公司所有文件资产。"""

    def __init__(self, root_dir: str | os.PathLike | None = None) -> None:
        # 允许传入自定义根目录（测试或迁移时使用）
        self.root_dir: Path = Path(root_dir).resolve() if root_dir else DEFAULT_WORKSPACE_DIR

    # ------------------------------------------------------------------
    # 顶层路径访问
    # ------------------------------------------------------------------
    @property
    def config_dir(self) -> Path:
        return self.root_dir / "config"

    @property
    def knowledge_dir(self) -> Path:
        return self.root_dir / "knowledge"

    @property
    def projects_dir(self) -> Path:
        return self.root_dir / "projects"

    @property
    def meetings_dir(self) -> Path:
        return self.root_dir / "meetings"

    @property
    def reports_dir(self) -> Path:
        return self.root_dir / "reports"

    # ------------------------------------------------------------------
    # knowledge 子目录
    # ------------------------------------------------------------------
    @property
    def market_research_dir(self) -> Path:
        return self.knowledge_dir / "market-research"

    @property
    def decisions_dir(self) -> Path:
        return self.knowledge_dir / "decisions"

    @property
    def lessons_learned_dir(self) -> Path:
        return self.knowledge_dir / "lessons-learned"

    @property
    def competitors_dir(self) -> Path:
        return self.knowledge_dir / "competitors"

    # ------------------------------------------------------------------
    # 配置文件路径
    # ------------------------------------------------------------------
    @property
    def employees_config_path(self) -> Path:
        return self.config_dir / "employees.yaml"

    @property
    def ledger_config_path(self) -> Path:
        return self.config_dir / "ledger.yaml"

    @property
    def meeting_config_path(self) -> Path:
        return self.config_dir / "meeting.yaml"

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------
    def initialize(self) -> None:
        """首次初始化工作区。

        创建完整目录结构与空配置文件，幂等：已存在的不覆盖。
        """
        # 1. 目录骨架
        for directory in (
            self.config_dir,
            self.knowledge_dir,
            self.projects_dir,
            self.meetings_dir,
            self.reports_dir,
            self.market_research_dir,
            self.decisions_dir,
            self.lessons_learned_dir,
            self.competitors_dir,
        ):
            self.ensure_dir(directory)

        # 2. 配置文件（仅在不存在时写入）
        if not self.employees_config_path.exists():
            self.write_yaml(self.employees_config_path, {"employees": []})

        if not self.ledger_config_path.exists():
            self.write_yaml(
                self.ledger_config_path,
                {
                    "balance": 10000.0,
                    "currency": "USD",
                    "transactions": [],
                },
            )

        if not self.meeting_config_path.exists():
            self.write_yaml(
                self.meeting_config_path,
                {
                    "schedule": "0 8 * * *",
                    "timezone": "Asia/Shanghai",
                    "participants": [],
                },
            )

    # ------------------------------------------------------------------
    # 文件读写 API
    # ------------------------------------------------------------------
    def ensure_dir(self, path: str | os.PathLike) -> Path:
        """确保目录存在，不存在则递归创建。"""
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def read_yaml(self, path: str | os.PathLike) -> Any:
        """读取 YAML 文件并返回对应 Python 对象。文件不存在返回 None。"""
        p = Path(path)
        if not p.exists():
            return None
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def write_yaml(self, path: str | os.PathLike, data: Any) -> None:
        """将 Python 对象写入 YAML 文件。自动创建父目录。"""
        p = Path(path)
        self.ensure_dir(p.parent)
        with p.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def read_text(self, path: str | os.PathLike) -> str:
        """读取文本文件内容。文件不存在返回空字符串。"""
        p = Path(path)
        if not p.exists():
            return ""
        with p.open("r", encoding="utf-8") as f:
            return f.read()

    def write_text(self, path: str | os.PathLike, content: str) -> None:
        """写入文本文件。自动创建父目录。"""
        p = Path(path)
        self.ensure_dir(p.parent)
        with p.open("w", encoding="utf-8") as f:
            f.write(content)

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    def today_meeting_dir(self) -> Path:
        """返回今日会议目录：meetings/YYYY-MM-DD/"""
        return self.meetings_dir / date.today().isoformat()

    def today_report_path(self) -> Path:
        """返回今日日报路径：reports/YYYY-MM-DD-daily.md"""
        return self.reports_dir / f"{date.today().isoformat()}-daily.md"

    def list_projects(self) -> List[str]:
        """列出所有产品项目目录名（projects/ 下的子目录）。"""
        if not self.projects_dir.exists():
            return []
        return sorted(
            entry.name
            for entry in self.projects_dir.iterdir()
            if entry.is_dir() and not entry.name.startswith(".")
        )

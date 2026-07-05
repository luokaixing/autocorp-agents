"""空投任务跟踪器

跟踪测试网空投任务进度，确保用户不错过任何空投。

设计要点：
- 零成本原则：只跟踪零成本空投（测试网交互、社区任务），不引入需要资金的 DeFi
- 文件即数据库：每个项目一个 yaml 文件，落盘到 company/knowledge/airdrops/<project>.yaml
- 幂等性：seed_initial_projects 重复调用不会创建重复项目（先检查 yaml 是否存在）
- 优雅降级：单项目入库失败、单任务入队失败均不阻断主流程
- 用户任务标记：用户操作任务 assignee=user_assist，AI 自主任务（快照检查）assignee=coo

8 个标准子任务模板（来自 spec 空投项目入库 Scenario）：
1. 钱包配置（用户任务）
2. 测试币领取（用户任务）
3. 测试网交互 swap（用户任务）
4. 测试网交互 桥（用户任务）
5. 测试网交互 合约（用户任务）
6. 社区任务 Twitter/Discord（用户任务）
7. 快照检查（AI 自主）
8. 领取空投（用户任务，需 AI 提醒）
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional

# 子任务状态枚举（pending/in_progress/done/skipped）
TASK_STATUSES = ("pending", "in_progress", "done", "skipped")


class AirdropTracker:
    """空投任务跟踪器：管理测试网空投项目的子任务进度。"""

    # 8 个标准子任务模板（assignee: user_assist=用户操作, coo=AI 自主）
    STANDARD_TASKS: List[Dict[str, str]] = [
        {
            "title": "钱包配置",
            "category": "user",
            "assignee": "user_assist",
            "description": "配置参与空投所需钱包（MetaMask 等），连接目标测试网",
        },
        {
            "title": "测试币领取",
            "category": "user",
            "assignee": "user_assist",
            "description": "从水龙头领取测试币（零成本）",
        },
        {
            "title": "测试网交互 swap",
            "category": "user",
            "assignee": "user_assist",
            "description": "在测试网 DEX 完成 swap 交互",
        },
        {
            "title": "测试网交互 桥",
            "category": "user",
            "assignee": "user_assist",
            "description": "在测试网完成跨链桥交互",
        },
        {
            "title": "测试网交互 合约",
            "category": "user",
            "assignee": "user_assist",
            "description": "在测试网部署/调用合约交互",
        },
        {
            "title": "社区任务 Twitter/Discord",
            "category": "user",
            "assignee": "user_assist",
            "description": "完成 Twitter 关注转发、Discord 加入等社区任务",
        },
        {
            "title": "快照检查",
            "category": "ai",
            "assignee": "coo",
            "description": "AI 自主检查空投快照资格（无需用户操作）",
        },
        {
            "title": "领取空投",
            "category": "user",
            "assignee": "user_assist",
            "description": "快照合格后领取空投（需 AI 提醒用户及时领取）",
        },
    ]

    def __init__(self, workspace=None, llm_client=None):
        """初始化空投跟踪器。

        Args:
            workspace: WorkspaceManager 实例；为空则自动创建（root_dir 指向 company/）。
            llm_client: 预留接口位（未来用于分析空投公告）。
        """
        from engine.workspace import WorkspaceManager

        self.workspace = workspace or WorkspaceManager()
        self.llm_client = llm_client
        # 空投项目数据目录：company/knowledge/airdrops/
        self.airdrops_dir = self.workspace.knowledge_dir / "airdrops"

    # ==================================================================
    # SubTask 5.1: add_project 入库
    # ==================================================================
    def add_project(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """入库新空投项目，写入 company/knowledge/airdrops/<project-name>.yaml。

        幂等：若项目 yaml 已存在则跳过，直接返回已有项目数据。
        config 含字段：name / status / expected_airdrop / tasks / created_at，
        缺失字段自动补全（tasks 用 create_task_template 生成，created_at 取当前时间）。

        Args:
            name: 项目名（如 Monad）。
            config: 项目配置字典。

        Returns:
            入库后的项目数据字典。
        """
        slug = self._slugify(name)
        project_path = self.airdrops_dir / f"{slug}.yaml"

        # 幂等：已存在则跳过
        if project_path.exists():
            existing = self.workspace.read_yaml(project_path) or {}
            print(f"[airdrop_tracker] 项目已存在，跳过：{name} ({project_path})")
            return existing

        now = datetime.datetime.now().isoformat(timespec="seconds")
        # tasks 缺失则用标准模板生成
        tasks = config.get("tasks")
        if not tasks:
            tasks = self.create_task_template(name)

        project_data = {
            "name": config.get("name", name),
            "slug": slug,
            "status": config.get("status", "active"),
            "expected_airdrop": config.get("expected_airdrop", ""),
            "created_at": config.get("created_at", now),
            "updated_at": now,
            "tasks": tasks,
        }

        self.workspace.ensure_dir(self.airdrops_dir)
        self.workspace.write_yaml(project_path, project_data)
        print(f"[airdrop_tracker] 项目入库：{name} -> {project_path}")
        return project_data

    # ==================================================================
    # SubTask 5.2: create_task_template 8 个标准子任务
    # ==================================================================
    def create_task_template(self, project_name: str) -> List[Dict[str, Any]]:
        """生成 8 个标准子任务模板。

        Args:
            project_name: 项目名（用于生成 task_id 前缀）。

        Returns:
            8 个子任务字典列表，每个含 id/title/category/assignee/status/description。
        """
        slug = self._slugify(project_name)
        tasks: List[Dict[str, Any]] = []
        for idx, tmpl in enumerate(self.STANDARD_TASKS, 1):
            tasks.append(
                {
                    "id": f"{slug}-{idx:02d}",
                    "title": tmpl["title"],
                    "category": tmpl["category"],
                    "assignee": tmpl["assignee"],
                    "status": "pending",
                    "description": tmpl["description"],
                }
            )
        return tasks

    # ==================================================================
    # SubTask 5.3: enqueue_user_tasks 用户任务入队
    # ==================================================================
    def enqueue_user_tasks(self, project_name: str) -> List[Dict[str, Any]]:
        """将项目所有子任务入队 task_queue。

        用户任务 assignee=user_assist, priority=P1, source=airdrop_tracker；
        AI 自主任务（快照检查 assignee=coo）同样入队，type=promote（coo 可认领）。
        单任务入队失败不阻断其他任务。

        Args:
            project_name: 项目名。

        Returns:
            成功入队的任务字典列表。
        """
        from engine.task_queue import TaskQueue

        project = self._load_project(project_name)
        if not project:
            print(f"[airdrop_tracker] 项目不存在，无法入队：{project_name}")
            return []

        queue = TaskQueue(self.workspace)
        enqueued: List[Dict[str, Any]] = []
        mutated = False

        for task in project.get("tasks", []) or []:
            try:
                # 用户任务 type=code（可执行交互），AI 自主任务 type=promote（coo 可认领）
                task_type = "promote" if task.get("assignee") == "coo" else "code"
                title = f"[空投] {project.get('name', project_name)} - {task.get('title', '')}"
                description = (
                    f"空投项目：{project.get('name', project_name)}\n"
                    f"- 子任务：{task.get('title', '')}\n"
                    f"- 子任务 ID：{task.get('id', '')}\n"
                    f"- 执行方：{task.get('assignee', '')}\n"
                    f"- 预期空投：{project.get('expected_airdrop', '')}\n"
                    f"- 说明：{task.get('description', '')}\n"
                )
                metadata = {
                    "project": project.get("name", project_name),
                    "project_slug": project.get("slug", self._slugify(project_name)),
                    "subtask_id": task.get("id", ""),
                    "category": task.get("category", ""),
                }
                queued = queue.add_task(
                    title=title,
                    description=description,
                    type=task_type,
                    assignee=task.get("assignee"),
                    priority="P1",
                    source="airdrop_tracker",
                    metadata=metadata,
                )
                enqueued.append(queued)
                # 回写 queue_task_id 到项目 yaml，便于 update_progress 关联
                task["queue_task_id"] = queued.get("id", "")
                mutated = True
                print(
                    f"[airdrop_tracker] 子任务入队：{task.get('id', '')} "
                    f"-> {queued.get('id', '')}"
                )
            except Exception as e:  # noqa: BLE001 - 单任务入队失败不阻断
                print(f"[airdrop_tracker] 入队失败 {task.get('id', '?')}：{e}")

        # 回写 queue_task_id 到项目 yaml
        if mutated:
            self._save_project(project)
        return enqueued

    # ==================================================================
    # SubTask 5.4: update_progress 更新子任务状态
    # ==================================================================
    def update_progress(self, task_id: str, status: str) -> bool:
        """更新子任务状态（pending/in_progress/done/skipped），写回项目 yaml。

        task_id 为项目内的子任务 ID（如 monad-01），跨所有项目 yaml 查找。
        找不到或状态非法返回 False。

        状态会同步到 task_queue 中对应任务（通过 queue_task_id 关联，失败不阻断）。

        Args:
            task_id: 子任务 ID（项目 yaml 中的 id 字段）。
            status: 新状态（pending/in_progress/done/skipped）。

        Returns:
            是否更新成功。
        """
        if status not in TASK_STATUSES:
            print(f"[airdrop_tracker] 非法状态：{status}（合法：{TASK_STATUSES}）")
            return False

        for project in self._load_all_projects():
            for task in project.get("tasks", []) or []:
                if task.get("id") != task_id:
                    continue
                task["status"] = status
                now = datetime.datetime.now().isoformat(timespec="seconds")
                task["updated_at"] = now
                project["updated_at"] = now
                self._save_project(project)
                print(f"[airdrop_tracker] 进度更新：{task_id} -> {status}")
                # 同步 task_queue 中的对应任务（失败不阻断）
                queue_id = task.get("queue_task_id")
                if queue_id:
                    try:
                        from engine.task_queue import TaskQueue

                        queue = TaskQueue(self.workspace)
                        # 映射子任务状态到 task_queue 状态机
                        queue_status = {
                            "pending": "pending",
                            "in_progress": "in_progress",
                            "done": "done",
                            "skipped": "killed",
                        }.get(status, "pending")
                        queue.update_status(queue_id, queue_status)
                    except Exception as e:  # noqa: BLE001
                        print(f"[airdrop_tracker] 同步队列状态失败 {queue_id}：{e}")
                return True
        print(f"[airdrop_tracker] 子任务未找到：{task_id}")
        return False

    # ==================================================================
    # SubTask 5.5: generate_tracker_report 进度看板
    # ==================================================================
    def generate_tracker_report(self) -> str:
        """生成 markdown 表格看板，写入 company/knowledge/airdrops/tracker-YYYY-MM-DD.md。

        表格列：项目 | 总任务 | 已完成 | 进行中 | 待开始 | 预期空投

        Returns:
            报告文件路径字符串。
        """
        today = datetime.date.today().isoformat()
        report_path = self.airdrops_dir / f"tracker-{today}.md"

        projects = self._load_all_projects()

        lines: List[str] = [
            f"# 空投任务进度看板 - {today}",
            "",
            f"生成时间：{datetime.datetime.now().isoformat(timespec='seconds')}",
            f"项目总数：{len(projects)}",
            "",
            "## 进度看板",
            "",
            "| 项目 | 总任务 | 已完成 | 进行中 | 待开始 | 预期空投 |",
            "|------|--------|--------|--------|--------|----------|",
        ]

        total_tasks = 0
        total_done = 0
        total_in_progress = 0
        total_pending = 0

        for project in projects:
            tasks = project.get("tasks", []) or []
            n_total = len(tasks)
            n_done = sum(1 for t in tasks if t.get("status") == "done")
            n_skipped = sum(1 for t in tasks if t.get("status") == "skipped")
            n_in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
            n_pending = sum(1 for t in tasks if t.get("status") == "pending")
            # 已完成 = done + skipped（均为已结算状态）
            done_col = n_done + n_skipped
            lines.append(
                f"| {project.get('name', '')} | {n_total} | {done_col} | "
                f"{n_in_progress} | {n_pending} | {project.get('expected_airdrop', '')} |"
            )
            total_tasks += n_total
            total_done += done_col
            total_in_progress += n_in_progress
            total_pending += n_pending

        # 合计行
        lines.append(
            f"| **合计** | **{total_tasks}** | **{total_done}** | "
            f"**{total_in_progress}** | **{total_pending}** | - |"
        )

        # 项目明细
        lines.extend(["", "## 项目明细", ""])
        for project in projects:
            tasks = project.get("tasks", []) or []
            lines.append(f"### {project.get('name', '')}")
            lines.append("")
            lines.append(f"- 状态：{project.get('status', '')}")
            lines.append(f"- 预期空投：{project.get('expected_airdrop', '')}")
            lines.append(f"- 创建时间：{project.get('created_at', '')}")
            lines.append("")
            lines.append("| # | 子任务 | 执行方 | 状态 | 说明 |")
            lines.append("|---|--------|--------|------|------|")
            for i, t in enumerate(tasks, 1):
                lines.append(
                    f"| {i} | {t.get('title', '')} | {t.get('assignee', '')} | "
                    f"{t.get('status', 'pending')} | {t.get('description', '')} |"
                )
            lines.append("")

        lines.extend(
            [
                "## 说明",
                "- **执行方**：user_assist=用户操作，coo=AI 自主",
                "- **状态**：pending=待开始，in_progress=进行中，done=已完成，skipped=已跳过",
                "- **零成本原则**：仅跟踪零成本空投（测试网交互、社区任务）",
                "",
            ]
        )

        content = "\n".join(lines)
        self.workspace.ensure_dir(self.airdrops_dir)
        self.workspace.write_text(report_path, content)
        print(f"[airdrop_tracker] 看板已生成：{report_path}")
        return str(report_path)

    # ==================================================================
    # SubTask 5.6: seed_initial_projects 初始化 5 个项目
    # ==================================================================
    def seed_initial_projects(self) -> List[Dict[str, Any]]:
        """初始化 5 个标准空投项目（幂等）。

        项目列表（来自 spec Tier 3 测试网空投清单）：
        Monad / Berachain / Layer3 / Scroll / Espresso

        每个项目用 add_project 入库，已存在则跳过。

        Returns:
            入库/已存在的项目数据列表（单项目失败不阻断，跳过该条）。
        """
        # 5 个种子项目配置（预期空投来自 spec 的 Tier 3 清单）
        seeds = [
            {
                "name": "Monad",
                "status": "active",
                "expected_airdrop": "$200-2000",
            },
            {
                "name": "Berachain",
                "status": "active",
                "expected_airdrop": "$100-1500",
            },
            {
                "name": "Layer3",
                "status": "active",
                "expected_airdrop": "CUBE 积分→空投",
            },
            {
                "name": "Scroll",
                "status": "active",
                "expected_airdrop": "持续活动（已发币）",
            },
            {
                "name": "Espresso",
                "status": "active",
                "expected_airdrop": "已空投（查询资格申领）",
            },
        ]

        results: List[Dict[str, Any]] = []
        for seed in seeds:
            try:
                project = self.add_project(seed["name"], seed)
                results.append(project)
            except Exception as e:  # noqa: BLE001 - 单项目失败不阻断其他
                print(f"[airdrop_tracker] 种子项目入库失败 {seed.get('name', '?')}：{e}")
        return results

    # ==================================================================
    # 私有辅助方法
    # ==================================================================
    def _load_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """按项目名加载单个项目 yaml。找不到返回 None。"""
        slug = self._slugify(project_name)
        project_path = self.airdrops_dir / f"{slug}.yaml"
        if not project_path.exists():
            return None
        return self.workspace.read_yaml(project_path) or None

    def _save_project(self, project: Dict[str, Any]) -> None:
        """保存项目数据回 yaml。"""
        slug = project.get("slug") or self._slugify(
            project.get("name", "unknown")
        )
        project_path = self.airdrops_dir / f"{slug}.yaml"
        self.workspace.ensure_dir(self.airdrops_dir)
        self.workspace.write_yaml(project_path, project)

    def _load_all_projects(self) -> List[Dict[str, Any]]:
        """加载 airdrops 目录下所有项目 yaml。单文件损坏不影响其他。"""
        if not self.airdrops_dir.exists():
            return []
        projects: List[Dict[str, Any]] = []
        for path in sorted(self.airdrops_dir.glob("*.yaml")):
            # 防御性跳过非项目文件（如以 tracker 开头的文件）
            if path.name.startswith("tracker"):
                continue
            try:
                data = self.workspace.read_yaml(path)
                if data and isinstance(data, dict) and "name" in data:
                    projects.append(data)
            except Exception as e:  # noqa: BLE001 - 单文件损坏不阻断
                print(f"[airdrop_tracker] 读取项目失败 {path}：{e}")
        return projects

    @staticmethod
    def _slugify(name: str) -> str:
        """将项目名转为文件名安全的 slug（小写+连字符）。"""
        if not name:
            return "unknown"
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", str(name).strip()).strip("-").lower()
        return slug or "unknown"

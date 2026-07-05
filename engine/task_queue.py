"""全局任务队列

基于文件持久化（文件即数据库）的 TaskQueue，作为所有虚拟员工协作的唯一真实源。
队列落盘到 company/config/task_queue.yaml，提供任务入队、按角色认领、状态流转、
依赖管理、优先级批量调整等能力。

任务状态机：pending → claimed → in_progress → done / failed / killed / blocked
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable, List, Optional


# 角色可执行的任务类型映射（角色名与 company/config/employees.yaml 的 role 字段一致）
ROLE_TASK_TYPES = {
    "ceo": ["decision"],
    "cto": ["decision", "design"],
    "coo": ["promote"],
    "architect": ["design", "decision"],
    "programmer": ["code"],
    "tester": ["test"],
    "product_manager": ["research"],
}

# 任务类型枚举
TASK_TYPES = ["research", "design", "code", "test", "promote", "decision"]

# 任务状态枚举
TASK_STATUSES = ["pending", "claimed", "in_progress", "done", "failed", "killed", "blocked"]

# 优先级枚举（P0 最高）
PRIORITIES = ["P0", "P1", "P2", "P3"]

# 优先级排序权重：值越小优先级越高
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


# 跨角色协作工作流模板：定义标准任务链条，由 create_workflow_chain 使用
WORKFLOW_TEMPLATES = {
    "content_production": {
        "description": "标准内容生产链：研究→编码→测试→推广",
        "stages": [
            {"type": "research", "assignee": "product_manager", "priority_offset": 0},
            {"type": "code", "assignee": "programmer", "priority_offset": 0},
            {"type": "test", "assignee": "tester", "priority_offset": 1},
            {"type": "promote", "assignee": "coo", "priority_offset": 1},
        ],
    },
    "feature_development": {
        "description": "功能开发链：设计→编码→测试→推广",
        "stages": [
            {"type": "design", "assignee": "architect", "priority_offset": 0},
            {"type": "code", "assignee": "programmer", "priority_offset": 0},
            {"type": "test", "assignee": "tester", "priority_offset": 1},
            {"type": "promote", "assignee": "coo", "priority_offset": 1},
        ],
    },
}


class TaskQueue:
    """全局任务队列：所有角色协作的唯一真实源。

    持久化到 ``company/config/task_queue.yaml``，结构为 ``{"tasks": [task_dict, ...]}``。
    所有写操作立即落盘，保证跨进程/跨角色可见性。
    """

    def __init__(self, workspace=None):
        # 延迟导入避免潜在循环依赖，并允许 TaskQueue() 无参实例化
        from engine.workspace import WorkspaceManager
        self.workspace = workspace or WorkspaceManager()
        # 队列文件路径：company/config/task_queue.yaml
        self.queue_path = self.workspace.root_dir / "config" / "task_queue.yaml"

    # ------------------------------------------------------------------
    # 持久化读写
    # ------------------------------------------------------------------
    def _load(self) -> List[dict]:
        """读取队列文件，返回任务列表。文件不存在或为空时返回空列表。"""
        data = self.workspace.read_yaml(self.queue_path)
        if not data:
            return []
        # 兼容两种结构：{"tasks": [...]} 或顶层列表
        if isinstance(data, dict):
            return data.get("tasks", []) or []
        if isinstance(data, list):
            return data
        return []

    def _save(self, tasks: List[dict]) -> None:
        """将任务列表写回队列文件。"""
        self.workspace.write_yaml(self.queue_path, {"tasks": tasks})

    @staticmethod
    def _now() -> str:
        """当前时间 ISO 8601 seconds 精度。"""
        return datetime.now().isoformat(timespec="seconds")

    def _next_id(self, tasks: List[dict]) -> str:
        """生成下一个任务 id，格式 ``task-YYYYMMDD-NNN``。

        NNN 为当日序号，从 001 开始；扫描已有任务取当日最大序号 +1。
        """
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"task-{today}-"
        max_seq = 0
        for t in tasks:
            tid = t.get("id", "") or ""
            if tid.startswith(prefix):
                tail = tid[len(prefix):]
                try:
                    seq = int(tail)
                    if seq > max_seq:
                        max_seq = seq
                except ValueError:
                    continue
        return f"{prefix}{max_seq + 1:03d}"

    @staticmethod
    def _is_done(tasks: List[dict], task_id: str) -> bool:
        """判断指定任务是否处于 done 状态。任务不存在视为未完成（阻断依赖）。"""
        for t in tasks:
            if t.get("id") == task_id:
                return t.get("status") == "done"
        return False

    # ------------------------------------------------------------------
    # 任务入队
    # ------------------------------------------------------------------
    def add_task(
        self,
        title: str,
        description: str,
        type: str,
        assignee: Optional[str] = None,
        priority: str = "P2",
        expected_revenue: float = 0.0,
        depends_on: Optional[List[str]] = None,
        source: str = "manual",
        metadata: Optional[dict] = None,
        sop_id: Optional[str] = None,
        phase: Optional[str] = None,
        client_order_id: Optional[str] = None,
        acceptance_status: str = "pending",
    ) -> dict:
        """创建任务并入队。

        Args:
            title: 任务标题。
            description: 任务描述。
            type: 任务类型（research/design/code/test/promote/decision）。
            assignee: 指派角色；为空则允许自主认领。
            priority: 优先级 P0/P1/P2/P3，默认 P2。
            expected_revenue: 预期收益（USD），用于认领排序。
            depends_on: 依赖任务 id 列表，依赖必须 done 后才可被认领。
            source: 任务来源标记（manual / handoff_xxx / ceo_autonomous 等）。
            metadata: 任务元数据（如 unblock_task_id / next_workflow_stage 等），
                为空则不写入 metadata 字段，保持向后兼容。
            sop_id: 遵循的 SOP ID（如 ``WF-BUILD``），为空表示无 SOP 约束。
            phase: 所属 Phase 名（如 ``Phase-Build``），为空表示不属于特定 Phase。
            client_order_id: 关联的外部客户订单 ID，为空表示自产任务。
            acceptance_status: 验收状态（pending/passed/failed），默认 pending。

        Returns:
            新建的任务字典（含自动生成的 id）。
        """
        tasks = self._load()
        now = self._now()
        task = {
            "id": self._next_id(tasks),
            "title": title,
            "description": description,
            "type": type,
            "assignee": assignee,
            "priority": priority,
            "expected_revenue": expected_revenue,
            "status": "pending",
            "depends_on": list(depends_on) if depends_on else [],
            "created_at": now,
            "claimed_at": None,
            "completed_at": None,
            "result_path": None,
            "error_reason": None,
            "retry_count": 0,
            "source": source,
            # 标准化运营新增字段（向后兼容：旧任务读取时若缺失视为 None / "pending"）
            "sop_id": sop_id,
            "phase": phase,
            "client_order_id": client_order_id,
            "acceptance_status": acceptance_status or "pending",
        }
        # 仅在显式传入 metadata 时写入，避免影响既有任务结构
        if metadata is not None:
            task["metadata"] = dict(metadata)
        tasks.append(task)
        self._save(tasks)
        return dict(task)

    def add_dependent_tasks(self, parent_task_id: str, task_specs: List[dict]) -> List[dict]:
        """批量创建依赖任务，每个任务 depends_on=[parent_task_id]。

        Args:
            parent_task_id: 父任务 id，新建任务均依赖它。
            task_specs: 任务规格列表，每项是支持 add_task 各参数的字典。

        Returns:
            新建任务列表。
        """
        created = []
        for spec in task_specs or []:
            task = self.add_task(
                title=spec.get("title", ""),
                description=spec.get("description", ""),
                type=spec.get("type", "code"),
                assignee=spec.get("assignee"),
                priority=spec.get("priority", "P2"),
                expected_revenue=spec.get("expected_revenue", 0.0),
                depends_on=[parent_task_id],
                source=spec.get("source", "dependent"),
            )
            created.append(task)
        return created

    # ------------------------------------------------------------------
    # 任务认领
    # ------------------------------------------------------------------
    def claim_task(self, role: str) -> Optional[dict]:
        """按规则为指定角色认领一个可执行任务。

        认领规则：
            1. status=pending 且 (assignee 为空 或 assignee=role)
            2. 任务 type 在 ROLE_TASK_TYPES[role] 中
            3. depends_on 中所有任务 status=done
            4. 按 expected_revenue 降序 + priority 降序（P0>P1>P2>P3）排序
            5. 取第一个，状态改 claimed，assignee=role，claimed_at=now，写回 yaml

        Args:
            role: 角色名（如 programmer / ceo）。

        Returns:
            认领成功的任务字典；无匹配返回 None。
        """
        tasks = self._load()
        allowed_types = ROLE_TASK_TYPES.get(role, [])
        if not allowed_types:
            return None

        candidates = []
        for t in tasks:
            if t.get("status") != "pending":
                continue
            assignee = t.get("assignee")
            if assignee and assignee != role:
                continue
            if t.get("type") not in allowed_types:
                continue
            deps = t.get("depends_on") or []
            if not all(self._is_done(tasks, d) for d in deps):
                continue
            candidates.append(t)

        if not candidates:
            return None

        # 排序：expected_revenue 降序（高收益优先），priority 升序（P0 优先）
        candidates.sort(
            key=lambda t: (
                -(t.get("expected_revenue", 0) or 0),
                PRIORITY_ORDER.get(t.get("priority", "P2"), 99),
            )
        )

        chosen = candidates[0]
        now = self._now()
        chosen["status"] = "claimed"
        chosen["assignee"] = role
        chosen["claimed_at"] = now
        # chosen 是 tasks 列表内同一引用，已被修改；写回
        self._save(tasks)
        return dict(chosen)

    # ------------------------------------------------------------------
    # 状态流转
    # ------------------------------------------------------------------
    def update_status(self, task_id: str, status: str, **fields) -> None:
        """更新任务状态及附加字段（如 result_path/error_reason/completed_at），写回 yaml。

        Args:
            task_id: 任务 id。
            status: 新状态。
            **fields: 附加字段，合并写入任务字典。
        """
        tasks = self._load()
        for t in tasks:
            if t.get("id") == task_id:
                t["status"] = status
                if fields:
                    t.update(fields)
                break
        self._save(tasks)

    def kill_task(self, task_id: str, reason: str) -> None:
        """标记任务为 killed，并记录 kill_reason。"""
        self.update_status(task_id, "killed", kill_reason=reason)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def list_pending(self) -> List[dict]:
        """返回所有 pending 任务。"""
        return self.list_by_status("pending")

    def list_by_status(self, status: str) -> List[dict]:
        """按状态筛选任务。"""
        return [t for t in self._load() if t.get("status") == status]

    def list_all(self) -> List[dict]:
        """返回全部任务。"""
        return self._load()

    def get_task(self, task_id: str) -> Optional[dict]:
        """按 id 获取任务；不存在返回 None。"""
        for t in self._load():
            if t.get("id") == task_id:
                return t
        return None

    # ------------------------------------------------------------------
    # 优先级批量调整
    # ------------------------------------------------------------------
    def reprioritize(self, filter_fn: Callable[[dict], bool], boost: bool = True) -> int:
        """批量调整任务优先级。

        Args:
            filter_fn: 过滤函数，返回 True 的任务会被调整。
            boost: True 提升一级（P2→P1），False 降低一级（P2→P3）。
                   已在边界（P0 / P3）时保持不变。

        Returns:
            被调整的任务数量。
        """
        tasks = self._load()
        order = PRIORITIES  # ["P0", "P1", "P2", "P3"]
        changed = 0
        for t in tasks:
            if not filter_fn(t):
                continue
            cur = t.get("priority", "P2")
            try:
                idx = order.index(cur)
            except ValueError:
                idx = 2  # 未知优先级视为 P2
            if boost:
                new_idx = max(0, idx - 1)
            else:
                new_idx = min(len(order) - 1, idx + 1)
            if new_idx != idx:
                t["priority"] = order[new_idx]
                changed += 1
        self._save(tasks)
        return changed

    # ------------------------------------------------------------------
    # 工作流链条（跨角色协作）
    # ------------------------------------------------------------------
    def create_workflow_chain(
        self, parent_task_id: str, template_name: str = "content_production"
    ) -> list:
        """基于模板创建工作流链条。

        parent_task_id 是初始任务（如 PM 的 research 任务）的 id，
        后续任务按模板顺序创建，每个 depends_on 前一个任务。

        priority_offset 用于降低后续任务优先级（数字越大优先级越低）。

        返回创建的任务列表。

        Args:
            parent_task_id: 父任务 id（对应模板第一阶段，已存在）。
            template_name: WORKFLOW_TEMPLATES 中的模板名，默认 content_production。

        Returns:
            新创建的后续阶段任务列表（不含父任务）；模板不存在或父任务缺失时返回空列表。
        """
        template = WORKFLOW_TEMPLATES.get(template_name)
        if not template:
            print(f"[task_queue] 未知工作流模板: {template_name}")
            return []

        stages = template.get("stages", []) or []
        # 至少需要 2 个阶段（父任务 + 至少 1 个后续），否则无需创建链条
        if len(stages) < 2:
            return []

        parent_task = self.get_task(parent_task_id)
        if not parent_task:
            print(f"[task_queue] 父任务不存在: {parent_task_id}")
            return []

        # 以父任务优先级为基准，按 priority_offset 递降（P0+1=P1，越界则停在 P3）
        base_priority = parent_task.get("priority", "P2")
        base_idx = PRIORITY_ORDER.get(base_priority, 2)

        created: List[dict] = []
        prev_task_id = parent_task_id

        # 跳过第一阶段（父任务），从第二阶段开始创建
        for stage in stages[1:]:
            offset = int(stage.get("priority_offset", 0) or 0)
            new_idx = min(len(PRIORITIES) - 1, base_idx + offset)
            new_priority = PRIORITIES[new_idx]

            new_task = self.add_task(
                title=f"[{template_name}] {stage['type']} 阶段",
                description=(
                    f"工作流 {template_name} 的 {stage['type']} 阶段，"
                    f"由父任务 {parent_task_id} 触发"
                ),
                type=stage.get("type", "code"),
                assignee=stage.get("assignee"),
                priority=new_priority,
                depends_on=[prev_task_id],
                source=f"workflow_{template_name}",
            )
            created.append(new_task)
            prev_task_id = new_task["id"]

        return created

    # ------------------------------------------------------------------
    # 任务完成钩子与自动恢复
    # ------------------------------------------------------------------
    def unblock_tasks(self, decision_task_id: str) -> int:
        """决策任务完成后恢复被其阻塞的原任务。

        查找 decision_task 的 metadata.unblock_task_id，把对应的 blocked 任务
        恢复为 pending，并清除 blocked_for / block_reason 字段。

        Args:
            decision_task_id: 决策（handoff 创建的）任务 id。

        Returns:
            恢复的任务数量（0 表示无对应阻塞任务或任务已非 blocked 状态）。
        """
        decision = self.get_task(decision_task_id)
        if not decision:
            return 0

        metadata = decision.get("metadata") or {}
        unblock_task_id = metadata.get("unblock_task_id")
        if not unblock_task_id:
            return 0

        tasks = self._load()
        restored = 0
        for t in tasks:
            if t.get("id") == unblock_task_id and t.get("status") == "blocked":
                t["status"] = "pending"
                # 清除阻塞相关字段，避免脏数据
                t.pop("blocked_for", None)
                t.pop("block_reason", None)
                restored += 1
                break
        if restored:
            self._save(tasks)
        return restored

    def on_task_done(self, task_id: str) -> None:
        """任务完成后的钩子：触发后续工作流阶段、恢复被阻塞的任务。

        - 检查 metadata.next_workflow_stage，自动创建下一阶段任务
        - 检查 metadata.unblock_task_id，恢复对应的 blocked 任务为 pending

        由 TaskExecutor 在 report_done 后自动调用；任何异常都被吞掉，不影响主流程。

        Args:
            task_id: 刚完成的任务 id。
        """
        try:
            task = self.get_task(task_id)
            if not task:
                return
            metadata = task.get("metadata") or {}

            # 1. 自动创建下一阶段任务（动态工作流模式）
            next_stage = metadata.get("next_workflow_stage")
            if next_stage:
                self._create_next_stage_task(task_id, next_stage)

            # 2. 决策任务完成 → 恢复被其阻塞的原任务
            if metadata.get("unblock_task_id"):
                self.unblock_tasks(task_id)
        except Exception as e:  # noqa: BLE001 - 钩子失败不阻断主流程
            print(f"[task_queue] on_task_done 异常：{e}")

    def _create_next_stage_task(
        self, current_task_id: str, next_stage: dict
    ) -> Optional[dict]:
        """根据 next_workflow_stage 元数据创建下一阶段任务。

        next_stage 结构：{"template": <模板名>, "next_stage_index": <下一阶段索引>}

        Args:
            current_task_id: 当前刚完成的任务 id。
            next_stage: 下一阶段描述。

        Returns:
            新建任务 dict；模板或阶段索引越界时返回 None。
        """
        template_name = next_stage.get("template")
        stage_index = int(next_stage.get("next_stage_index", 0) or 0)
        template = WORKFLOW_TEMPLATES.get(template_name) if template_name else None
        if not template:
            return None
        stages = template.get("stages", []) or []
        if stage_index < 0 or stage_index >= len(stages):
            return None

        stage = stages[stage_index]
        current_task = self.get_task(current_task_id)
        base_idx = PRIORITY_ORDER.get(
            (current_task or {}).get("priority", "P2"), 2
        )
        offset = int(stage.get("priority_offset", 0) or 0)
        new_priority = PRIORITIES[min(len(PRIORITIES) - 1, base_idx + offset)]

        # 为再下一阶段继续链接 metadata，形成动态链条
        new_metadata: dict = {}
        next_next_index = stage_index + 1
        if next_next_index < len(stages):
            new_metadata["next_workflow_stage"] = {
                "template": template_name,
                "next_stage_index": next_next_index,
            }

        return self.add_task(
            title=f"[{template_name}] {stage.get('type', 'code')} 阶段",
            description=(
                f"工作流 {template_name} 的 {stage.get('type', 'code')} 阶段，"
                f"由 {current_task_id} 完成触发"
            ),
            type=stage.get("type", "code"),
            assignee=stage.get("assignee"),
            priority=new_priority,
            depends_on=[current_task_id],
            source=f"workflow_{template_name}",
            metadata=new_metadata if new_metadata else None,
        )

"""SOP 加载与校验模块

提供 SOPLoader 类，负责从 ``company/sop/`` 目录加载 SOP 文档（YAML frontmatter + Markdown 正文），
并提供前置产物校验、产出验收标准检查等能力，作为角色执行 SOP 任务的基础设施。

SOP 文件统一格式（详见 ``company/sop/README.md``）::

    ---
    id: WF-BUILD                 # SOP 唯一标识，与文件名（去 .md）一致
    name: 编码实现与测试工作流 SOP  # SOP 中文名称
    trigger: 每日 12:00 Phase-Build 触发  # 触发条件
    owner_role: programmer        # 拥有者角色代号（与 employees.yaml 的 role 字段一致）
    inputs: []                    # 前置产物列表（文件路径或描述）
    outputs: []                   # 产出物列表
    acceptance_criteria: []       # 验收标准列表（字符串描述）
    sla_minutes: 30               # 服务等级协议时长（分钟）
    fallback: ...                 # 降级策略描述
    ---

    # Markdown 正文：详细 actions 步骤 / 注意事项 / 示例

文件名约定：``<sop_id>.md``（如 ``WF-BUILD.md`` / ``ROLE-CEO.md``）。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from engine.workspace import WorkspaceManager


# YAML frontmatter 分隔符正则：开头一行 --- ，中间是 YAML 内容，结尾一行 ---
# 使用 DOTALL 让 . 匹配换行，lazy 匹配 front 避免贪婪吞掉正文
_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(?P<front>.*?)\n---\s*\n(?P<body>.*)$",
    re.DOTALL,
)

# 用于从验收标准文本中提取可能的文件路径 token 的正则
# 匹配带扩展名的文件名（含路径），用于 check_acceptance 的文件存在性校验
_FILE_TOKEN_RE = re.compile(
    r"[\w./\\\-]+\.(?:md|yaml|yml|json|jsonl|py|txt|html|css|js|ts|tsx)",
    re.IGNORECASE,
)


class SOPLoader:
    """SOP 加载与校验器。

    从 ``company/sop/`` 目录读取 SOP 文档，解析 YAML frontmatter 与 Markdown 正文，
    返回结构化字典。同时提供前置产物校验（``validate_inputs``）与产出验收检查
    （``check_acceptance``）能力，作为角色 ``execute_by_sop`` 的基础工具。

    典型用法::

        from engine.sop_loader import SOPLoader

        loader = SOPLoader()
        sop = loader.load("WF-BUILD")
        if sop is None:
            # SOP 缺失：标记 sop_compliance=degraded，按原逻辑执行
            ...
        else:
            passed, missing = loader.validate_inputs(sop, context)
            if not passed:
                # inputs 缺失：拒绝执行，转回上游角色
                ...
            # 按 sop["actions"] 顺序执行
            passed, failed = loader.check_acceptance(sop, output)
            if not passed:
                # 验收不通过：标记任务 failed
                ...
    """

    def __init__(self, workspace: Optional[WorkspaceManager] = None) -> None:
        """初始化 SOP 加载器。

        Args:
            workspace: WorkspaceManager 实例。为 None 时使用默认工作区
                （``d:\\autoCompany\\company``）。SOP 文件目录固定为
                ``<workspace.root_dir>/sop/``。
        """
        self.workspace: WorkspaceManager = workspace or WorkspaceManager()
        # SOP 文件目录：company/sop/
        self.sop_dir: Path = self.workspace.root_dir / "sop"

    # ------------------------------------------------------------------
    # 内部解析方法
    # ------------------------------------------------------------------
    def _path_for(self, sop_id: str) -> Path:
        """根据 sop_id 推断对应文件路径。

        Args:
            sop_id: SOP 唯一标识，如 ``WF-BUILD`` / ``ROLE-CEO``。

        Returns:
            对应的 SOP 文件绝对路径（``<sop_dir>/<sop_id>.md``）。
        """
        return self.sop_dir / f"{sop_id}.md"

    def _parse_file(self, path: Path) -> Optional[Dict[str, Any]]:
        """解析单个 SOP 文件，返回结构化字典。

        解析失败（文件不存在 / frontmatter 格式错误 / YAML 解析异常）时返回 None。
        缺失字段会被补齐为安全默认值，确保下游使用时不会 KeyError。

        Args:
            path: SOP 文件绝对路径。

        Returns:
            含以下键的字典：
                - ``id`` / ``name`` / ``trigger`` / ``owner_role``：字符串字段
                - ``inputs`` / ``outputs`` / ``acceptance_criteria``：列表字段
                - ``sla_minutes``：整数
                - ``fallback``：字符串
                - ``actions``：Markdown 正文（字符串）
                - ``_path``：源文件绝对路径（内部字段）
            解析失败返回 None。
        """
        if not path.exists():
            return None
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None

        match = _FRONTMATTER_RE.match(text)
        if not match:
            return None

        front_text = match.group("front")
        body = match.group("body").strip()

        try:
            meta = yaml.safe_load(front_text)
        except yaml.YAMLError:
            return None

        if not isinstance(meta, dict):
            return None

        # 补齐缺失字段为安全默认值，避免下游 KeyError
        meta.setdefault("id", path.stem)
        meta.setdefault("name", "")
        meta.setdefault("trigger", "")
        meta.setdefault("owner_role", "")
        # 列表字段若被写成 None 或单值，统一规整为 list
        meta["inputs"] = self._as_list(meta.get("inputs"))
        meta["outputs"] = self._as_list(meta.get("outputs"))
        meta["acceptance_criteria"] = self._as_list(meta.get("acceptance_criteria"))
        # sla_minutes 必须是整数
        try:
            meta["sla_minutes"] = int(meta.get("sla_minutes", 0) or 0)
        except (TypeError, ValueError):
            meta["sla_minutes"] = 0
        meta.setdefault("fallback", "")
        # 正文 actions 字段（Markdown 内容）
        meta["actions"] = body
        # 内部字段：源文件路径，便于调试与日志
        meta["_path"] = str(path)
        return meta

    @staticmethod
    def _as_list(value: Any) -> List[str]:
        """将输入值规整为字符串列表。

        处理 YAML 中可能出现的多种写法：
            - ``None`` → 空列表
            - ``[a, b, c]`` → 原样返回（元素转 str）
            - ``"single_value"`` → ``["single_value"]``
            - ``123`` → ``["123"]``

        Args:
            value: 待规整的原始值。

        Returns:
            字符串列表。
        """
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------
    def load(self, sop_id: str) -> Optional[Dict[str, Any]]:
        """根据 sop_id 加载对应 SOP 文档。

        文件名约定为 ``<sop_id>.md``，查找路径为 ``company/sop/<sop_id>.md``。
        文件不存在或解析失败时返回 None，调用方据此进入「SOP 缺失降级」流程
        （标记 ``sop_compliance=degraded`` 并按原逻辑执行）。

        Args:
            sop_id: SOP 唯一标识，如 ``WF-BUILD`` / ``ROLE-CEO``。

        Returns:
            结构化 SOP 字典（含 id/name/trigger/owner_role/inputs/outputs/
            acceptance_criteria/sla_minutes/fallback/actions 等字段）；
            文件不存在或解析失败返回 None。
        """
        path = self._path_for(sop_id)
        return self._parse_file(path)

    def validate_inputs(
        self,
        sop: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """校验 context 是否包含 SOP 要求的 inputs。

        按 ``sop["inputs"]`` 列表逐项检查 context 字典中是否存在对应键。
        每项 input 视为产物标识，匹配策略：
            1. 直接键匹配：``input in context``
            2. 文件路径型 input（含 ``/`` 或 ``\\``）：检查文件系统中该路径是否存在

        Args:
            sop: ``SOPLoader.load`` 返回的 SOP 字典。
            context: 上下文字典，键为产物标识 / 文件路径，值为产物内容或路径。

        Returns:
            ``(passed, missing_list)``：
                - 全部命中返回 ``(True, [])``
                - 否则返回 ``(False, [缺失项, ...])``
        """
        required: List[str] = list(sop.get("inputs", []) or [])
        missing: List[str] = []
        for item in required:
            if not isinstance(item, str) or not item:
                continue
            # 1) 直接键匹配
            if item in context:
                continue
            # 2) 文件路径型 input：检查文件系统是否存在
            if ("/" in item or "\\" in item) and Path(item).exists():
                continue
            missing.append(item)
        return (len(missing) == 0, missing)

    def check_acceptance(
        self,
        sop: Dict[str, Any],
        output: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """按 acceptance_criteria 检查 output 是否满足验收标准。

        每条 criteria 为字符串描述，匹配策略：
            1. 若 criteria 文本中包含 output 字典的某个键，视为该条通过；
            2. 若 criteria 文本中包含一个在文件系统存在的文件路径 token
               （形如 ``xxx.md`` / ``xxx.yaml`` 等），视为该条通过；
            3. 否则视为该条 criteria 未通过，加入 failed_list。

        Args:
            sop: ``SOPLoader.load`` 返回的 SOP 字典。
            output: 产出物字典，键为产物标识 / 文件路径，值为产物内容或路径。

        Returns:
            ``(passed, failed_list)``：
                - 全部通过返回 ``(True, [])``
                - 否则返回 ``(False, [未通过条目, ...])``
        """
        criteria_list: List[str] = list(sop.get("acceptance_criteria", []) or [])
        failed: List[str] = []
        for criteria in criteria_list:
            if not isinstance(criteria, str) or not criteria:
                continue
            if self._criteria_met(criteria, output):
                continue
            failed.append(criteria)
        return (len(failed) == 0, failed)

    def _criteria_met(self, criteria: str, output: Dict[str, Any]) -> bool:
        """判断单条验收标准是否满足。

        匹配规则（任一命中即视为通过）：
            1. criteria 文本中包含 output 字典的某个键
            2. criteria 文本中提取的文件路径 token 在文件系统中存在

        Args:
            criteria: 单条验收标准文本。
            output: 产出物字典。

        Returns:
            通过返回 True，否则 False。
        """
        # 1) criteria 中是否提及 output 中的某个键
        for key in output.keys():
            if not isinstance(key, str) or not key:
                continue
            if key in criteria:
                return True
        # 2) 从 criteria 中提取文件路径 token，检查文件系统存在性
        tokens = _FILE_TOKEN_RE.findall(criteria)
        for token in tokens:
            # 规整 Windows / Unix 路径分隔符
            candidate = Path(token)
            if candidate.exists():
                return True
        return False

    def list_all(self) -> List[Dict[str, Any]]:
        """列出 ``company/sop/`` 目录下所有 SOP 的元数据（不含正文 actions）。

        扫描 ``sop_dir`` 下所有 ``.md`` 文件（排除 ``README.md``），解析其 frontmatter，
        返回元数据列表。每个元数据字典只含公开字段（不含 ``actions`` / ``_path``），
        便于 CLI 展示与批量统计。

        Returns:
            元数据字典列表，按 ``id`` 升序排序。每个字典含 id/name/trigger/owner_role/
            inputs/outputs/acceptance_criteria/sla_minutes/fallback 字段。
            目录不存在时返回空列表。
        """
        if not self.sop_dir.exists():
            return []
        results: List[Dict[str, Any]] = []
        for path in sorted(self.sop_dir.glob("*.md")):
            # README.md 不是 SOP，跳过
            if path.name.upper() == "README.MD":
                continue
            sop = self._parse_file(path)
            if not sop:
                continue
            # 只保留公开元数据字段，剔除 actions / _path
            meta: Dict[str, Any] = {
                "id": sop.get("id", path.stem),
                "name": sop.get("name", ""),
                "trigger": sop.get("trigger", ""),
                "owner_role": sop.get("owner_role", ""),
                "inputs": sop.get("inputs", []),
                "outputs": sop.get("outputs", []),
                "acceptance_criteria": sop.get("acceptance_criteria", []),
                "sla_minutes": sop.get("sla_minutes", 0),
                "fallback": sop.get("fallback", ""),
            }
            results.append(meta)
        # 按 id 升序排序，便于人工查阅
        results.sort(key=lambda x: str(x.get("id", "")))
        return results

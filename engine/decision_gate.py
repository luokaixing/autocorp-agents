"""关键决策门禁 (DecisionGate)

在执行关键决策动作前（产品立项 / 对外报价 / 对外发布 / 真实出款 / 出币 /
战略调整 / 订单接拒），统一通过本模块评估是否需要人工确认，命中触发条件时
调用 HumanLoop 询问用户。

设计原则：
- 配置驱动：决策点定义在 company/config/decision-gates.yaml，改配置不改代码
- 优雅降级：配置缺失或 action_type 未定义时默认放行（gate_hit=False）
- OR 关系：trigger_condition 内多个条件字段为 OR 关系，任一命中即触发
- 兼容 HumanLoop：HumanLoop 无 request_confirmation 方法，本模块改用
  request_approval(decision_context, options) 走人工确认通道

典型用法：
    gate = DecisionGate(workspace, human_loop)
    result = gate.check("product_initiate",
                        {"expected_cost_usd": 50, "expected_duration_days": 2})
    if result["need_confirm"]:
        approved = gate.confirm("product_initiate", context)
        # approved: True=确认 / False=拒绝 / None=超时（按 timeout_action 处理）
"""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Tuple


class DecisionGate:
    """关键决策门禁 - 统一管理 7 类决策点的人工确认逻辑。

    配置文件：company/config/decision-gates.yaml
    """

    def __init__(self, workspace=None, human_loop=None):
        """初始化决策门禁。

        Args:
            workspace: WorkspaceManager 实例；为空时延迟实例化（默认工作区）。
            human_loop: HumanLoop 实例；为空时延迟实例化（用于人工确认询问）。
        """
        self.workspace = workspace
        self.human_loop = human_loop
        # gates 配置缓存（避免每次 check 都重新读盘）
        self._gates_cache: Optional[List[Dict[str, Any]]] = None

    # ------------------------------------------------------------------
    # 延迟实例化辅助
    # ------------------------------------------------------------------
    def _get_workspace(self):
        """延迟实例化 WorkspaceManager。"""
        if self.workspace is None:
            from engine.workspace import WorkspaceManager
            self.workspace = WorkspaceManager()
        return self.workspace

    def _get_human_loop(self):
        """延迟实例化 HumanLoop。"""
        if self.human_loop is None:
            from engine.human_loop import HumanLoop
            self.human_loop = HumanLoop(self._get_workspace())
        return self.human_loop

    # ------------------------------------------------------------------
    # 配置加载
    # ------------------------------------------------------------------
    @property
    def gates_config_path(self):
        """decision-gates.yaml 配置文件路径：company/config/decision-gates.yaml"""
        return self._get_workspace().config_dir / "decision-gates.yaml"

    def _load_gates(self) -> List[Dict[str, Any]]:
        """加载 decision-gates.yaml 配置。

        配置文件不存在或格式异常时优雅降级为空列表
        （默认所有 gate 都不命中，不阻塞主流程）。
        """
        if self._gates_cache is not None:
            return self._gates_cache

        try:
            data = self._get_workspace().read_yaml(self.gates_config_path)
        except Exception as e:
            print(
                f"[decision_gate] 加载配置失败: {e}，默认所有 gate 不命中",
                file=sys.stderr,
            )
            self._gates_cache = []
            return self._gates_cache

        if not data or not isinstance(data, dict):
            self._gates_cache = []
            return self._gates_cache

        gates = data.get("decision_gates") or []
        if not isinstance(gates, list):
            self._gates_cache = []
            return self._gates_cache

        self._gates_cache = gates
        return self._gates_cache

    def _find_gate(self, action_type: str) -> Optional[Dict[str, Any]]:
        """根据 action_type 查找对应 gate 配置，未找到返回 None。"""
        for gate in self._load_gates():
            if isinstance(gate, dict) and gate.get("action_type") == action_type:
                return gate
        return None

    # ------------------------------------------------------------------
    # 触发条件评估
    # ------------------------------------------------------------------
    def evaluate_trigger(
        self, condition: Dict[str, Any], context: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """评估单个 trigger_condition 是否命中。

        trigger_condition 内多个条件字段为 OR 关系，任一命中即返回 hit=True。

        字段命名约定（操作符后缀）：
        - _gt  : 大于        (context_value > threshold)
        - _lt  : 小于        (context_value < threshold)
        - _gte : 大于等于    (context_value >= threshold)
        - _lte : 小于等于    (context_value <= threshold)
        - _eq  : 等于        (context_value == threshold)
        - 无后缀: 等于判断（用于布尔/字符串字段）
        - or_ 前缀仅作可读性提示，不影响评估逻辑

        Args:
            condition: trigger_condition 字典，如
                {"expected_cost_usd_gt": 20, "or_first_time_client": true}
            context:   实际上下文，如
                {"expected_cost_usd": 50, "first_time_client": True}

        Returns:
            (hit, reason): hit=True 表示命中；reason 为命中原因（未命中时为空字符串）
        """
        if not condition or not isinstance(condition, dict):
            return False, ""
        if not context or not isinstance(context, dict):
            return False, ""

        for raw_key, threshold in condition.items():
            if threshold is None:
                continue
            # 剥离 or_ 前缀（仅可读性提示，不影响逻辑）
            key = raw_key[3:] if raw_key.startswith("or_") else raw_key

            context_value, op = self._extract_value_and_op(key, context)
            if self._apply_operator(context_value, op, threshold):
                reason = (
                    f"命中条件 {raw_key}={threshold}（上下文值: {context_value}）"
                )
                return True, reason

        return False, ""

    @staticmethod
    def _extract_value_and_op(
        key: str, context: Dict[str, Any]
    ) -> Tuple[Any, str]:
        """从 condition key 中解析出 context 字段名与操作符。

        约定 key 后缀为操作符：_gte / _lte / _gt / _lt / _eq；无后缀则默认 eq。
        返回 (context_value, op)；context_value 缺失返回 None。

        Args:
            key:      condition 字段名（已剥离 or_ 前缀），如 "expected_cost_usd_gt"
            context:  上下文字典

        Returns:
            (context_value, op): 如 (50, "gt")；context 缺该字段时 context_value=None
        """
        # 注意：必须先匹配多字符后缀（_gte / _lte），否则会被 _gt / _lt 误匹配
        ops = ("_gte", "_lte", "_gt", "_lt", "_eq")
        op = "eq"
        field_name = key
        for suffix in ops:
            if key.endswith(suffix):
                op = suffix[1:]  # 去掉前导下划线 -> gt / lt / gte / lte / eq
                field_name = key[: -len(suffix)]
                break
        return context.get(field_name), op

    @staticmethod
    def _apply_operator(context_value: Any, op: str, threshold: Any) -> bool:
        """根据操作符比较 context_value 与 threshold。

        context_value 缺失（None）或类型不兼容时返回 False（不命中）。

        Args:
            context_value: 上下文中取出的实际值（可能为 None）
            op:            操作符（gt / lt / gte / lte / eq）
            threshold:     配置中的阈值

        Returns:
            bool: 比较是否成立
        """
        if context_value is None:
            return False

        # 数值类操作符
        if op in ("gt", "lt", "gte", "lte"):
            try:
                cv = float(context_value)
                tv = float(threshold)
            except (TypeError, ValueError):
                return False
            if op == "gt":
                return cv > tv
            if op == "lt":
                return cv < tv
            if op == "gte":
                return cv >= tv
            if op == "lte":
                return cv <= tv

        # eq（含布尔/字符串/数值相等）
        if op == "eq":
            # 布尔阈值特殊处理：避免 1 == True / 0 == False 等隐式转换误判
            if isinstance(threshold, bool):
                return bool(context_value) is threshold
            return context_value == threshold

        return False

    # ------------------------------------------------------------------
    # 主入口：check
    # ------------------------------------------------------------------
    def check(self, action_type: str, context: dict) -> dict:
        """评估指定动作是否命中决策门禁。

        Args:
            action_type: 动作类型，如 "product_initiate" / "order_quote" 等
            context:     动作上下文，含触发条件评估所需字段

        Returns:
            dict: {
                gate_hit:       bool  - 是否命中触发条件
                need_confirm:   bool  - 是否需要人工确认（gate_hit=True 即需确认）
                scope:          str   - 确认人 (user/ceo/coo)，未命中时为空字符串
                timeout_action: str   - 超时降级策略 (cancel/defer/escalate)，未命中时为空字符串
                reason:         str   - 命中原因或未命中说明
            }

            配置不存在或 action_type 未定义时返回
            gate_hit=False, need_confirm=False（默认放行）。
        """
        default = {
            "gate_hit": False,
            "need_confirm": False,
            "scope": "",
            "timeout_action": "",
            "reason": "",
        }

        gate = self._find_gate(action_type)
        if gate is None:
            default["reason"] = (
                f"action_type '{action_type}' 未定义决策门禁，默认放行"
            )
            return default

        condition = gate.get("trigger_condition") or {}
        hit, reason = self.evaluate_trigger(condition, context or {})

        if not hit:
            default["reason"] = f"action_type '{action_type}' 未命中触发条件"
            return default

        return {
            "gate_hit": True,
            "need_confirm": True,
            "scope": str(gate.get("confirm_scope", "user")),
            "timeout_action": str(gate.get("timeout_action", "defer")),
            "reason": reason,
        }

    # ------------------------------------------------------------------
    # 主入口：confirm
    # ------------------------------------------------------------------
    def confirm(self, action_type: str, context: dict) -> Optional[bool]:
        """评估门禁并在命中时通过 human_loop 请求人工确认。

        Args:
            action_type: 动作类型
            context:     动作上下文

        Returns:
            - True:  用户确认（批准）
            - False: 用户拒绝
            - None:  超时 / 非交互环境跳过 / 用户要求更多信息，
                     由调用方按 timeout_action 处理

            未命中门禁时直接返回 True（无需确认即放行）。
            human_loop 不可用时打印警告并默认 True（不阻塞主流程）。
        """
        result = self.check(action_type, context)

        # 未命中或 action_type 未定义：直接放行
        if not result.get("need_confirm"):
            return True

        # 命中门禁：构造决策上下文并请求人工确认
        decision_context = self._build_decision_context(action_type, context, result)

        try:
            human_loop = self._get_human_loop()
        except Exception as e:
            print(
                f"[decision_gate] human_loop 不可用: {e}，默认放行（不阻塞）",
                file=sys.stderr,
            )
            return True

        try:
            approval = human_loop.request_approval(decision_context=decision_context)
        except AttributeError:
            # 兜底：HumanLoop 接口变动无 request_approval 时，直接打印询问
            print(
                f"[decision_gate] HumanLoop 无 request_approval 方法，"
                f"降级打印询问:\n{decision_context}"
            )
            return True
        except Exception as e:
            print(
                f"[decision_gate] human_loop 请求异常: {e}，默认放行（不阻塞）",
                file=sys.stderr,
            )
            return True

        response = approval.get("response", "") if isinstance(approval, dict) else ""

        if response == "批准":
            return True
        if response == "拒绝":
            return False
        # 「需要更多信息」/ 非交互环境自动跳过 / 超时等情形 → None
        # 由调用方按 timeout_action（cancel/defer/escalate）处理
        return None

    def _build_decision_context(
        self, action_type: str, context: dict, check_result: dict
    ) -> str:
        """构造给用户看的决策确认上下文。

        Args:
            action_type:  动作类型
            context:      原始上下文
            check_result: check() 返回的结果（含 reason / scope / timeout_action）

        Returns:
            多行字符串，作为 human_loop.request_approval 的 decision_context
        """
        gate = self._find_gate(action_type) or {}
        name = gate.get("name", action_type)
        description = gate.get("description", "")
        reason = check_result.get("reason", "")
        scope = check_result.get("scope", "user")
        timeout_action = check_result.get("timeout_action", "defer")

        lines: List[str] = [f"决策门禁: {name} ({action_type})"]
        lines.append(f"确认人: {scope}")
        if reason:
            lines.append(f"触发原因: {reason}")
        if description:
            lines.append(f"说明: {description}")
        lines.append(f"超时策略: {timeout_action}")
        lines.append("")
        lines.append("上下文:")
        for k, v in (context or {}).items():
            lines.append(f"  - {k}: {v}")
        lines.append("")
        lines.append("是否批准执行？")
        return "\n".join(lines)

"""服务订单流程（OrderManager）

实现外部客户订单的完整状态机：
    received → quoted → confirmed → in_progress → delivered → accepted → paid → closed

订单以 YAML 文件持久化到 ``company/orders/<status>/<order_id>.yaml``，
每次状态流转把订单 yaml 从当前状态目录移动到目标状态目录，并向共享消息池
publish ``order.<status>`` 消息供审计。

设计原则：
1. 文件即数据库：订单 yaml 落盘，不引入数据库
2. 优雅降级：PayPal / Ledger / PhaseChain / DecisionGate 等外部依赖全部延迟导入
   + try/except，缺失凭证或模块异常时不阻塞订单流转
3. 可观测性：每次状态流转 publish 消息到 MessagePool
4. 向后兼容：所有外部依赖按需实例化，不破坏现有模块

典型用法：
    manager = OrderManager()
    order = manager.receive("Alice", "写一篇 DeFi 分析", channel="manual")
    manager.quote(order["order_id"], price=30.0, actor="ceo")
    manager.confirm(order["order_id"])
    manager.start(order["order_id"])
    manager.deliver(order["order_id"])
    manager.accept(order["order_id"])
    manager.pay(order["order_id"])
    manager.close(order["order_id"])
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# 8 个合法的订单状态，按流转顺序排列
ORDER_STATUSES = [
    "received",
    "quoted",
    "confirmed",
    "in_progress",
    "delivered",
    "accepted",
    "paid",
    "closed",
]


class OrderManager:
    """服务订单管理器 - 管理外部客户订单的完整生命周期。

    订单状态机：
        received → quoted → confirmed → in_progress → delivered
        → accepted → paid → closed

    订单文件持久化到 ``company/orders/<status>/<order_id>.yaml``，
    状态流转时把 yaml 文件从当前状态目录移动到目标状态目录。
    """

    def __init__(
        self,
        workspace=None,
        message_pool=None,
        human_loop=None,
    ) -> None:
        """初始化订单管理器。

        Args:
            workspace: WorkspaceManager 实例；为空时延迟实例化默认工作区。
            message_pool: MessagePool 实例；为空时延迟实例化。
            human_loop: HumanLoop 实例；为空时延迟实例化（供 DecisionGate 使用）。
        """
        self.workspace = workspace
        self.message_pool = message_pool
        self.human_loop = human_loop

    # ==================================================================
    # 延迟实例化辅助
    # ==================================================================
    def _get_workspace(self):
        """延迟实例化 WorkspaceManager。"""
        if self.workspace is None:
            from engine.workspace import WorkspaceManager
            self.workspace = WorkspaceManager()
        return self.workspace

    def _get_message_pool(self):
        """延迟实例化 MessagePool。"""
        if self.message_pool is None:
            from engine.message_pool import MessagePool
            self.message_pool = MessagePool(self._get_workspace())
        return self.message_pool

    def _get_human_loop(self):
        """延迟实例化 HumanLoop。"""
        if self.human_loop is None:
            from engine.human_loop import HumanLoop
            self.human_loop = HumanLoop(self._get_workspace())
        return self.human_loop

    # ==================================================================
    # 路径与工具方法
    # ==================================================================
    @property
    def orders_dir(self) -> Path:
        """订单根目录：company/orders/"""
        return self._get_workspace().root_dir / "orders"

    def _status_dir(self, status: str) -> Path:
        """返回指定状态对应的子目录路径，并确保目录存在。"""
        path = self.orders_dir / status
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _order_path(self, order_id: str, status: str) -> Path:
        """返回指定订单在指定状态目录下的 yaml 文件路径。"""
        return self._status_dir(status) / f"{order_id}.yaml"

    @staticmethod
    def _now() -> str:
        """当前时间 ISO 8601 seconds 精度。"""
        return datetime.now().isoformat(timespec="seconds")

    def _next_order_id(self) -> str:
        """生成下一个订单 id，格式 ``ord-YYYYMMDD-NNN``。

        扫描 received/ 与 closed/ 取当日最大序号 +1（同时扫描其他状态目录
        以保证序号全局唯一）。

        Returns:
            形如 ``ord-20260629-001`` 的订单 id。
        """
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"ord-{today}-"
        max_seq = 0
        # 扫描所有状态目录，取当日最大序号
        for status in ORDER_STATUSES:
            status_dir = self.orders_dir / status
            if not status_dir.exists():
                continue
            for f in status_dir.glob("ord-*.yaml"):
                name = f.stem  # 如 ord-20260629-001
                if name.startswith(prefix):
                    tail = name[len(prefix):]
                    try:
                        seq = int(tail)
                        if seq > max_seq:
                            max_seq = seq
                    except ValueError:
                        continue
        return f"{prefix}{max_seq + 1:03d}"

    # ==================================================================
    # 订单 yaml 读写
    # ==================================================================
    def _read_order_yaml(self, path: Path) -> Optional[dict]:
        """读取订单 yaml 文件，返回订单字典；文件不存在返回 None。"""
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else None
        except (yaml.YAMLError, OSError) as e:
            print(f"[service_order] 读取订单文件失败 {path}: {e}")
            return None

    def _write_order_yaml(self, path: Path, order: dict) -> None:
        """写入订单 yaml 文件（utf-8 编码）。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(order, f, allow_unicode=True, sort_keys=False)

    def _find_order_file(self, order_id: str) -> Optional[Path]:
        """扫描所有状态目录查找订单 yaml 文件，返回路径；未找到返回 None。"""
        for status in ORDER_STATUSES:
            path = self._order_path(order_id, status)
            if path.exists():
                return path
        return None

    # ==================================================================
    # 辅助方法
    # ==================================================================
    def _append_event(
        self,
        order: dict,
        from_status: str,
        to_status: str,
        actor: str,
        note: str = "",
    ) -> dict:
        """向订单 events 列表追加一条流转事件。

        Args:
            order: 订单字典（原地修改）。
            from_status: 流转前状态（首次接收为空字符串）。
            to_status: 流转后状态。
            actor: 触发者（ceo / client / system 等）。
            note: 事件备注。

        Returns:
            修改后的订单字典。
        """
        events = order.setdefault("events", [])
        if events is None:
            events = []
            order["events"] = events
        events.append({
            "from_status": from_status,
            "to_status": to_status,
            "timestamp": self._now(),
            "actor": actor,
            "note": note,
        })
        return order

    def _move_order(self, order_id: str, to_status: str) -> Path:
        """把订单 yaml 文件从当前状态目录移动到目标状态目录。

        Args:
            order_id: 订单 id。
            to_status: 目标状态。

        Returns:
            移动后的订单 yaml 文件路径。

        Raises:
            FileNotFoundError: 订单文件在所有状态目录中均未找到。
        """
        src = self._find_order_file(order_id)
        if src is None:
            raise FileNotFoundError(f"订单 {order_id} 不存在")
        dst = self._order_path(order_id, to_status)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # 同盘移动：Path.replace 可原子替换
        src.replace(dst)
        return dst

    def _publish(self, topic: str, payload: dict) -> None:
        """publish 订单事件消息到共享消息池（失败不阻塞）。"""
        try:
            self._get_message_pool().publish(
                topic=topic,
                payload=payload,
                from_role="order_manager",
                to_role=None,
            )
        except Exception as e:  # noqa: BLE001
            print(f"[service_order] publish {topic} 失败: {e}")

    # ==================================================================
    # 核心接口：receive / quote / confirm / start / deliver / accept / pay / close
    # ==================================================================
    def receive(
        self,
        client_name: str,
        requirement: str,
        channel: str = "manual",
        client_contact: str = "",
        expected_delivery: str = "",
    ) -> dict:
        """接收一个外部客户订单，创建订单 yaml 并 publish ``order.received``。

        Args:
            client_name: 客户名称。
            requirement: 客户需求描述。
            channel: 接单渠道（manual / email / twitter），默认 manual。
            client_contact: 客户联系方式（邮箱等），可空。
            expected_delivery: 期望交付日期，可空。

        Returns:
            新建的订单字典。
        """
        order_id = self._next_order_id()
        now = self._now()
        order: Dict[str, Any] = {
            "order_id": order_id,
            "client_name": client_name,
            "client_contact": client_contact,
            "requirement": requirement,
            "channel": channel,
            "sop_id": "WF-SERVICE",
            "quoted_price": None,
            "currency": "USD",
            "expected_delivery": expected_delivery,
            "assigned_roles": [],
            "status": "received",
            "events": [],
            "created_at": now,
            "updated_at": now,
        }
        # 追加首个 receive 事件
        self._append_event(order, "", "received", actor="client", note="订单接收")

        # 写入 received/ 目录
        path = self._order_path(order_id, "received")
        self._write_order_yaml(path, order)

        # publish 消息
        self._publish("order.received", {
            "order_id": order_id,
            "client_name": client_name,
            "channel": channel,
            "requirement": requirement[:200],
        })

        return order

    def quote(
        self,
        order_id: str,
        price: float,
        currency: str = "USD",
        actor: str = "ceo",
    ) -> dict:
        """对订单进行报价，触发 DecisionGate 门禁检查。

        - 调用 ``DecisionGate.check("order_quote", {"quoted_price_usd": price})``
        - 命中门禁（price > 50）则 ``DecisionGate.confirm(...)`` 询问用户
        - 用户拒绝则订单流转到 closed/ 并标记 rejected，publish ``order.rejected``
        - 用户确认或未命中则更新 quoted_price / currency，流转到 quoted/，publish ``order.quoted``

        Args:
            order_id: 订单 id。
            price: 报价金额。
            currency: 货币，默认 USD。
            actor: 报价发起者，默认 ceo。

        Returns:
            更新后的订单字典。
        """
        # 读取订单：先在 received/ 找，找不到再扫描其他状态目录
        order = self.get_order(order_id)
        if order is None:
            raise FileNotFoundError(f"订单 {order_id} 不存在")

        from_status = order.get("status", "received")
        note = f"报价 {price} {currency}"

        # DecisionGate 门禁检查
        try:
            from engine.decision_gate import DecisionGate
            gate = DecisionGate(self._get_workspace(), self.human_loop)
            check_result = gate.check("order_quote", {"quoted_price_usd": price})
            if check_result.get("gate_hit"):
                # 命中门禁，请求人工确认
                approved = gate.confirm("order_quote", {"quoted_price_usd": price})
                if approved is False:
                    # 用户拒绝：订单流转到 closed/，标记 rejected
                    order["quoted_price"] = price
                    order["currency"] = currency
                    order["status"] = "closed"
                    order["rejected"] = True
                    order["reject_reason"] = "报价被用户拒绝"
                    order["updated_at"] = self._now()
                    self._append_event(
                        order, from_status, "closed", actor=actor,
                        note=f"报价 {price} {currency} 被用户拒绝",
                    )
                    # 移动到 closed/
                    self._move_order(order_id, "closed")
                    # 找到移动后的路径并写入更新后的订单
                    path = self._order_path(order_id, "closed")
                    self._write_order_yaml(path, order)
                    self._publish("order.rejected", {
                        "order_id": order_id,
                        "price": price,
                        "currency": currency,
                        "reason": "用户拒绝报价",
                    })
                    return order
        except Exception as e:  # noqa: BLE001 - DecisionGate 失败不阻塞报价
            print(f"[service_order] DecisionGate 检查失败（降级放行）: {e}")

        # 用户确认或未命中或 DecisionGate 降级：更新报价，流转到 quoted/
        order["quoted_price"] = float(price)
        order["currency"] = currency
        order["status"] = "quoted"
        order["updated_at"] = self._now()
        self._append_event(order, from_status, "quoted", actor=actor, note=note)

        # 移动到 quoted/ 并写入
        self._move_order(order_id, "quoted")
        path = self._order_path(order_id, "quoted")
        self._write_order_yaml(path, order)

        self._publish("order.quoted", {
            "order_id": order_id,
            "price": price,
            "currency": currency,
        })
        return order

    def confirm(self, order_id: str, actor: str = "client") -> dict:
        """客户确认报价，订单从 quoted/ 流转到 confirmed/。

        自动入队一个 ``type=service`` 任务到 task_queue，关联
        ``client_order_id=order_id``，``sop_id="WF-SERVICE"``。

        Args:
            order_id: 订单 id。
            actor: 确认者，默认 client。

        Returns:
            更新后的订单字典。
        """
        order = self.get_order(order_id)
        if order is None:
            raise FileNotFoundError(f"订单 {order_id} 不存在")

        from_status = order.get("status", "quoted")
        order["status"] = "confirmed"
        order["updated_at"] = self._now()
        self._append_event(order, from_status, "confirmed", actor=actor, note="客户确认报价")

        # 移动到 confirmed/ 并写入
        self._move_order(order_id, "confirmed")
        path = self._order_path(order_id, "confirmed")
        self._write_order_yaml(path, order)

        # 自动入队 service 任务
        try:
            from engine.task_queue import TaskQueue
            queue = TaskQueue(self._get_workspace())
            queue.add_task(
                title=f"服务订单 {order_id} 交付",
                description=order.get("requirement", "")[:500],
                type="service",
                priority="P1",
                source="order_confirm",
                sop_id="WF-SERVICE",
                phase="Phase-Service",
                client_order_id=order_id,
            )
        except Exception as e:  # noqa: BLE001 - 入队失败不阻塞订单流转
            print(f"[service_order] 入队 service 任务失败: {e}")

        self._publish("order.confirmed", {
            "order_id": order_id,
            "client_name": order.get("client_name", ""),
        })
        return order

    def start(self, order_id: str, actor: str = "system") -> dict:
        """订单从 confirmed/ 流转到 in_progress/，触发 PhaseChain.run_service_chain。

        Args:
            order_id: 订单 id。
            actor: 触发者，默认 system。

        Returns:
            更新后的订单字典。
        """
        order = self.get_order(order_id)
        if order is None:
            raise FileNotFoundError(f"订单 {order_id} 不存在")

        from_status = order.get("status", "confirmed")
        order["status"] = "in_progress"
        order["updated_at"] = self._now()
        self._append_event(order, from_status, "in_progress", actor=actor, note="开始交付")

        # 移动到 in_progress/ 并写入
        self._move_order(order_id, "in_progress")
        path = self._order_path(order_id, "in_progress")
        self._write_order_yaml(path, order)

        # 触发 PhaseChain.run_service_chain（延迟导入，失败 try/except）
        try:
            from engine.phase_chain import PhaseChain
            chain = PhaseChain(self._get_workspace())
            chain.run_service_chain(order_id)
        except Exception as e:  # noqa: BLE001 - PhaseChain 失败不阻塞订单流转
            print(f"[service_order] PhaseChain.run_service_chain 失败: {e}")

        self._publish("order.in_progress", {"order_id": order_id})
        return order

    def deliver(self, order_id: str, actor: str = "system") -> dict:
        """订单从 in_progress/ 流转到 delivered/。

        Args:
            order_id: 订单 id。
            actor: 触发者，默认 system。

        Returns:
            更新后的订单字典。
        """
        order = self.get_order(order_id)
        if order is None:
            raise FileNotFoundError(f"订单 {order_id} 不存在")

        from_status = order.get("status", "in_progress")
        order["status"] = "delivered"
        order["updated_at"] = self._now()
        self._append_event(order, from_status, "delivered", actor=actor, note="交付完成")

        # 移动到 delivered/ 并写入
        self._move_order(order_id, "delivered")
        path = self._order_path(order_id, "delivered")
        self._write_order_yaml(path, order)

        self._publish("order.delivered", {"order_id": order_id})
        return order

    def accept(self, order_id: str, actor: str = "client") -> dict:
        """客户验收通过，订单从 delivered/ 流转到 accepted/。

        自动调用 ``PayPalClient.create_order`` 创建收款订单，
        把 ``paypal_order_id`` 写入订单 events 与字段。

        Args:
            order_id: 订单 id。
            actor: 验收者，默认 client。

        Returns:
            更新后的订单字典（含 paypal_order_id 字段）。
        """
        order = self.get_order(order_id)
        if order is None:
            raise FileNotFoundError(f"订单 {order_id} 不存在")

        from_status = order.get("status", "delivered")
        order["status"] = "accepted"
        order["updated_at"] = self._now()

        paypal_order_id = ""
        # 调用 PayPalClient.create_order 创建收款订单（延迟导入，失败 try/except）
        try:
            from engine.payments.paypal import PayPalClient
            client = PayPalClient(self._get_workspace())
            amount = float(order.get("quoted_price") or 0)
            currency = order.get("currency", "USD")
            if amount > 0:
                result = client.create_order(
                    amount=amount,
                    currency=currency,
                    description=f"Order {order_id}",
                )
                paypal_order_id = result.get("order_id", "")
        except Exception as e:  # noqa: BLE001 - PayPal 失败不阻塞验收
            print(f"[service_order] PayPal create_order 失败: {e}")

        order["paypal_order_id"] = paypal_order_id
        note = "客户验收通过"
        if paypal_order_id:
            note += f"，PayPal 订单 {paypal_order_id}"
        self._append_event(order, from_status, "accepted", actor=actor, note=note)

        # 移动到 accepted/ 并写入
        self._move_order(order_id, "accepted")
        path = self._order_path(order_id, "accepted")
        self._write_order_yaml(path, order)

        self._publish("order.accepted", {
            "order_id": order_id,
            "paypal_order_id": paypal_order_id,
        })
        return order

    def pay(
        self,
        order_id: str,
        paypal_order_id: str = None,
        actor: str = "system",
    ) -> dict:
        """订单从 accepted/ 流转到 paid/，捕获付款并入账。

        - 若提供 paypal_order_id，调用 ``PayPalClient.capture_order`` 捕获付款
          （capture_order 内部已调用 ``Ledger.income_real`` 入账）
        - 若未提供 paypal_order_id，手动调用 ``Ledger.income_real`` 入账

        Args:
            order_id: 订单 id。
            paypal_order_id: PayPal 订单 id；为空时从订单字段读取。
            actor: 触发者，默认 system。

        Returns:
            更新后的订单字典。
        """
        order = self.get_order(order_id)
        if order is None:
            raise FileNotFoundError(f"订单 {order_id} 不存在")

        # paypal_order_id 优先用参数，其次读订单字段
        pp_id = paypal_order_id or order.get("paypal_order_id") or ""
        from_status = order.get("status", "accepted")
        amount = float(order.get("quoted_price") or 0)
        currency = order.get("currency", "USD")

        captured = False
        # 若有 paypal_order_id，调用 capture_order 捕获付款（capture_order 内部已入账）
        if pp_id:
            try:
                from engine.payments.paypal import PayPalClient
                client = PayPalClient(self._get_workspace())
                client.capture_order(pp_id)
                captured = True
            except Exception as e:  # noqa: BLE001 - 捕获失败不阻塞流转
                print(f"[service_order] PayPal capture_order 失败: {e}")

        # 若未走 capture_order（无 paypal_order_id 或捕获失败），手动入账
        if not captured and amount > 0:
            try:
                from engine.ledger import Ledger
                ledger = Ledger(self._get_workspace())
                # income_real 签名: (amount, source, tx_ref, description="")
                ledger.income_real(
                    amount=amount,
                    source=order_id,
                    tx_ref=pp_id or order_id,
                    description=f"Order {order_id} payment",
                )
            except Exception as e:  # noqa: BLE001 - 入账失败不阻塞流转
                print(f"[service_order] Ledger.income_real 失败: {e}")

        order["status"] = "paid"
        order["updated_at"] = self._now()
        note = "收款完成"
        if pp_id:
            note += f"，PayPal 订单 {pp_id}"
        self._append_event(order, from_status, "paid", actor=actor, note=note)

        # 移动到 paid/ 并写入
        self._move_order(order_id, "paid")
        path = self._order_path(order_id, "paid")
        self._write_order_yaml(path, order)

        self._publish("order.paid", {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "paypal_order_id": pp_id,
        })
        return order

    def close(
        self,
        order_id: str,
        actor: str = "system",
        note: str = "",
    ) -> dict:
        """订单从任意状态流转到 closed/，提取经验写入 lessons-learned。

        Args:
            order_id: 订单 id。
            actor: 触发者，默认 system。
            note: 关闭备注。

        Returns:
            更新后的订单字典。
        """
        order = self.get_order(order_id)
        if order is None:
            raise FileNotFoundError(f"订单 {order_id} 不存在")

        from_status = order.get("status", "unknown")
        order["status"] = "closed"
        order["updated_at"] = self._now()
        close_note = note or "订单关闭"
        self._append_event(order, from_status, "closed", actor=actor, note=close_note)

        # 移动到 closed/ 并写入
        self._move_order(order_id, "closed")
        path = self._order_path(order_id, "closed")
        self._write_order_yaml(path, order)

        # 提取经验写入 lessons-learned（可选，失败 try/except）
        try:
            self._write_lesson_learned(order)
        except Exception as e:  # noqa: BLE001
            print(f"[service_order] 提取经验失败: {e}")

        self._publish("order.closed", {
            "order_id": order_id,
            "from_status": from_status,
        })
        return order

    def _write_lesson_learned(self, order: dict) -> None:
        """把订单经验写入 company/knowledge/lessons-learned/ 目录。"""
        workspace = self._get_workspace()
        lessons_dir = workspace.lessons_learned_dir
        lessons_dir.mkdir(parents=True, exist_ok=True)
        order_id = order.get("order_id", "unknown")
        path = lessons_dir / f"order-{order_id}.md"
        lines = [
            f"# 订单经验总结: {order_id}",
            "",
            f"- 客户: {order.get('client_name', '')}",
            f"- 需求: {order.get('requirement', '')[:200]}",
            f"- 报价: {order.get('quoted_price', '')} {order.get('currency', '')}",
            f"- 渠道: {order.get('channel', '')}",
            f"- 最终状态: {order.get('status', '')}",
            f"- 创建时间: {order.get('created_at', '')}",
            f"- 关闭时间: {order.get('updated_at', '')}",
            "",
            "## 事件流转",
            "",
        ]
        for ev in order.get("events", []) or []:
            lines.append(
                f"- {ev.get('timestamp', '')} "
                f"{ev.get('from_status', '')} → {ev.get('to_status', '')} "
                f"({ev.get('actor', '')}): {ev.get('note', '')}"
            )
        path.write_text("\n".join(lines), encoding="utf-8")

    # ==================================================================
    # 查询接口
    # ==================================================================
    def list_orders(self, status: Optional[str] = None) -> List[dict]:
        """列出指定状态的订单；无 status 列出全部。

        Args:
            status: 订单状态筛选；为空则列出所有状态的订单。

        Returns:
            订单字典列表。
        """
        orders: List[dict] = []
        statuses = [status] if status else ORDER_STATUSES
        for st in statuses:
            status_dir = self.orders_dir / st
            if not status_dir.exists():
                continue
            for f in sorted(status_dir.glob("*.yaml")):
                order = self._read_order_yaml(f)
                if order:
                    orders.append(order)
        return orders

    def get_order(self, order_id: str) -> Optional[dict]:
        """扫描所有状态目录查找订单，返回订单字典；未找到返回 None。"""
        path = self._find_order_file(order_id)
        if path is None:
            return None
        return self._read_order_yaml(path)

"""共享消息池

基于文件持久化（文件即数据库）的 MessagePool，作为所有虚拟员工协作事件的留痕中心。
所有关键事件（任务流转、跨角色转交、CEO 决策、订单状态变更、健康警报）均 publish 到
本消息池，持久化到 ``company/messages/message-pool-YYYY-MM-DD.jsonl``（按日切分，
append 模式写入，每行一条 JSON），形成可审计的决策链路。

设计原则：
1. 文件即数据库：不引入额外数据库依赖，所有消息落盘到 JSONL。
2. 优雅降级：单条消息写入失败不应阻塞主流程，try/except 兜底。
3. 向后兼容：旧调用方未传入 to_role 时按广播处理（to_role=None）。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class MessagePool:
    """共享消息池 - 所有角色协作事件的留痕中心。

    持久化目录：``company/messages/``，按日切分文件
    ``message-pool-YYYY-MM-DD.jsonl``，每行一条 JSON 消息，append 模式写入。

    消息结构：
        ``{id, from_role, to_role, topic, payload, created_at, read_by: []}``
        - ``id``: ``msg-YYYYMMDDHHMMSS-NNN``，NNN 为当日序号
        - ``created_at``: ISO 8601 seconds 精度
        - ``read_by``: 已读角色列表，初始为空
    """

    def __init__(self, workspace=None) -> None:
        """初始化消息池。

        Args:
            workspace: WorkspaceManager 实例；为空则自动实例化默认工作区。
        """
        # 延迟导入避免潜在循环依赖
        from engine.workspace import WorkspaceManager
        self.workspace = workspace or WorkspaceManager()
        # 消息池目录：company/messages/
        self.messages_dir: Path = self.workspace.root_dir / "messages"
        # 目录不存在则创建（幂等）
        self.messages_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    @staticmethod
    def _now_iso() -> str:
        """当前时间 ISO 8601 seconds 精度。"""
        return datetime.now().isoformat(timespec="seconds")

    def _file_for_date(self, date_str: Optional[str] = None) -> Path:
        """返回指定日期对应的 jsonl 文件路径。

        Args:
            date_str: ``YYYY-MM-DD`` 格式日期；为空则使用今日。

        Returns:
            对应日期的 ``message-pool-YYYY-MM-DD.jsonl`` 绝对路径。
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        return self.messages_dir / f"message-pool-{date_str}.jsonl"

    def _next_id(self, date_str: Optional[str] = None) -> str:
        """生成下一个消息 id，格式 ``msg-YYYYMMDDHHMMSS-NNN``。

        NNN 为当日序号，从 001 开始；扫描当日消息文件取最大序号 +1。

        Args:
            date_str: 指定日期（仅用于定位文件），默认今日。

        Returns:
            形如 ``msg-20260629120000-001`` 的 id。
        """
        now = datetime.now()
        prefix_ts = now.strftime("%Y%m%d%H%M%S")
        date_part = date_str or now.strftime("%Y-%m-%d")
        file_path = self._file_for_date(date_part)

        max_seq = 0
        if file_path.exists():
            # 扫描当日消息文件，取所有 id 的序号最大值 +1，保证当日序号单调递增
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            msg = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        msg_id = msg.get("id", "") or ""
                        # id 形如 msg-YYYYMMDDHHMMSS-NNN，按 "-" 拆分后末段即序号
                        if msg_id.startswith("msg-"):
                            parts = msg_id.split("-")
                            if len(parts) >= 3:
                                try:
                                    seq = int(parts[-1])
                                    if seq > max_seq:
                                        max_seq = seq
                                except ValueError:
                                    continue
            except OSError:
                # 读取失败时按序号 001 起，不阻塞
                pass

        return f"msg-{prefix_ts}-{max_seq + 1:03d}"

    def _read_messages_from_file(self, file_path: Path) -> List[dict]:
        """读取指定 jsonl 文件全部消息。文件不存在返回空列表。

        Args:
            file_path: jsonl 文件路径。

        Returns:
            消息字典列表（按文件顺序）。
        """
        if not file_path.exists():
            return []
        messages: List[dict] = []
        try:
            with file_path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        # 跳过损坏行
                        continue
        except OSError as e:
            print(f"[message_pool] 读取消息文件失败 {file_path}: {e}")
        return messages

    def _rewrite_file(self, file_path: Path, messages: List[dict]) -> None:
        """将消息列表整体写回 jsonl 文件（用于更新 read_by 字段）。

        Args:
            file_path: jsonl 文件路径。
            messages: 全量消息列表。
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("w", encoding="utf-8") as f:
                for msg in messages:
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        except OSError as e:
            print(f"[message_pool] 写回消息文件失败 {file_path}: {e}")

    # ------------------------------------------------------------------
    # 发布消息
    # ------------------------------------------------------------------
    def publish(
        self,
        topic: str,
        payload: dict,
        from_role: str,
        to_role: Optional[str] = None,
    ) -> dict:
        """发布一条消息到共享消息池。

        Args:
            topic: 消息主题，如 ``task.done.code`` / ``decision.initiate``。
                支持点分层级，订阅方可用前缀匹配（如 ``task.done.*``）。
            payload: 消息负载字典，承载具体事件数据。
            from_role: 发送方角色名（如 ``ceo`` / ``programmer``）。
            to_role: 接收方角色名；为空表示广播，所有角色可读。

        Returns:
            已发布的消息字典（含生成的 id 与 created_at）。
            单条消息写入失败时不抛异常，仍返回消息字典（已优雅降级）。
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        message = {
            "id": self._next_id(date_str),
            "from_role": from_role,
            "to_role": to_role,
            "topic": topic,
            "payload": dict(payload) if payload else {},
            "created_at": self._now_iso(),
            "read_by": [],
        }

        # append 模式写入当日 jsonl 文件，单条失败不阻塞
        file_path = self._file_for_date(date_str)
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(message, ensure_ascii=False) + "\n")
        except Exception as e:  # noqa: BLE001 - 写入失败优雅降级
            print(f"[message_pool] 消息写入失败 topic={topic}: {e}")

        return message

    # ------------------------------------------------------------------
    # 读取未读消息
    # ------------------------------------------------------------------
    def read_unread(
        self,
        role: str,
        topic_filter: Optional[str] = None,
    ) -> List[dict]:
        """读取当日消息池中目标角色未读的消息。

        筛选规则：
            1. ``to_role == role`` 或 ``to_role`` 为 None（广播）
            2. ``role`` 未在消息的 ``read_by`` 列表中
            3. 若提供 ``topic_filter``，按前缀匹配过滤
               （如 ``task.done.*`` 匹配 ``task.done.code``）

        命中后会把 ``role`` 加入返回消息的 ``read_by`` 列表并写回文件，
        实现一次性消费语义。

        Args:
            role: 读取方角色名。
            topic_filter: 主题前缀过滤；为空则不过滤。

        Returns:
            未读消息列表（按文件顺序）；读取/写回失败时返回已能读到的部分。
        """
        file_path = self._file_for_date()
        messages = self._read_messages_from_file(file_path)

        matched: List[dict] = []
        changed = False
        for msg in messages:
            to_role = msg.get("to_role")
            # 目标角色不匹配且非广播，跳过
            if to_role is not None and to_role != role:
                continue
            # 已读跳过
            if role in (msg.get("read_by") or []):
                continue
            # 主题前缀过滤
            if topic_filter and not self._topic_match(msg.get("topic", ""), topic_filter):
                continue
            # 命中：加入 read_by 并收集
            msg.setdefault("read_by", [])
            if role not in msg["read_by"]:
                msg["read_by"].append(role)
                changed = True
            matched.append(msg)

        # 把 read_by 更新写回文件
        if changed and matched:
            self._rewrite_file(file_path, messages)

        return matched

    @staticmethod
    def _topic_match(topic: str, topic_filter: str) -> bool:
        """前缀匹配 topic。

        支持两种形式：
            - ``task.done.*``：匹配 ``task.done.`` 开头的所有 topic（``*`` 仅作为通配标记）
            - ``task.done``：精确前缀匹配（``task.done`` 与 ``task.done.code`` 均命中）

        Args:
            topic: 实际消息 topic。
            topic_filter: 过滤表达式。

        Returns:
            命中返回 True。
        """
        if not topic or not topic_filter:
            return False
        # 去掉末尾的通配符
        flt = topic_filter
        if flt.endswith(".*"):
            flt = flt[:-2]
            # task.done.* 匹配 task.done.code，也匹配 task.done（更宽松）
            return topic == flt or topic.startswith(flt + ".")
        # 无通配符：前缀匹配（含完全相等）
        if topic == flt:
            return True
        return topic.startswith(flt + ".")

    # ------------------------------------------------------------------
    # 查询接口
    # ------------------------------------------------------------------
    def list_by_topic(
        self,
        topic: str,
        date_str: Optional[str] = None,
    ) -> List[dict]:
        """按 topic 完全匹配查询消息。

        Args:
            topic: 完全匹配的 topic 字符串。
            date_str: 指定日期（``YYYY-MM-DD``）；为空则查询今日。

        Returns:
            命中的消息列表（按文件顺序）。
        """
        file_path = self._file_for_date(date_str)
        messages = self._read_messages_from_file(file_path)
        return [m for m in messages if m.get("topic") == topic]

    def list_by_date(self, date_str: str) -> List[dict]:
        """返回指定日期的所有消息。

        Args:
            date_str: ``YYYY-MM-DD`` 格式日期。

        Returns:
            该日期全部消息列表（按文件顺序）。
        """
        file_path = self._file_for_date(date_str)
        return self._read_messages_from_file(file_path)

    def list_all_today(self) -> List[dict]:
        """返回今日所有消息。

        Returns:
            今日全部消息列表（按文件顺序）。
        """
        return self.list_by_date(datetime.now().strftime("%Y-%m-%d"))

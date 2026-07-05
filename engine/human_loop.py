"""人工协助请求机制

在运营过程中可能遇到需要用户协助（如需要域名/服务器）或高风险决策需要用户拍板的场景。
通过本模块主动询问用户，支持两种模式：
1. 终端交互退化：未注册外部处理器时，通过 stdin 询问用户
2. 回调 hook 桥接：主控 Agent 可注册 handler，将询问转发为 AskUserQuestion 工具调用

非交互环境（cron/后台调度，stdin 非 tty）下自动跳过并记录，避免卡死。
所有请求与响应均记录到 company/human-requests/YYYY-MM-DD.md。

附加能力：
- check_vpn()：探测翻墙状态（Twitter/Reddit/Mirror/Binance 等需翻墙访问）
  不通时主动通过 request_assistance 让用户开启翻墙，避免反复超时。
"""
from __future__ import annotations

import socket
import sys
from datetime import date, datetime
from typing import Callable, List, Optional


# 国内被墙、需翻墙访问的常用服务域名（用于 check_vpn 探测）
# 选用 google.com 作主探测点（最稳定且响应快）；附加被墙服务作辅助判断
_VPN_PROBE_HOSTS = (
    ("www.google.com", 443),       # 主探测：GFW 标志性封锁
    ("twitter.com", 443),          # AI 公司引流渠道
    ("www.reddit.com", 443),       # AI 公司引流渠道
    ("mirror.xyz", 443),           # 文章发布平台
)

# 翻墙请求消息模板（符合 project_memory 约定）
_VPN_REQUEST_MSG_TEMPLATE = "需要访问 {host}，请协助打开翻墙软件后回复已开启"
_VPN_REQUEST_OPTIONS = ["已开启翻墙", "跳过此任务", "稍后再试"]


class HumanLoop:
    """人工协助请求机制 - 需要用户协助或决策确认时主动询问"""

    def __init__(self, workspace=None):
        from engine.workspace import WorkspaceManager
        self.workspace = workspace or WorkspaceManager()
        self._handler: Optional[Callable[[str, List[str]], str]] = None  # 可注册的外部处理器（如 AskUserQuestion 桥接）

    # ------------------------------------------------------------------
    # 处理器注册
    # ------------------------------------------------------------------
    def register_handler(self, handler: Callable[[str, List[str]], str]) -> None:
        """注册外部处理器函数 `handler(message, options) -> str`。

        上层（如主控 Agent）可注册 AskUserQuestion 桥接，将询问转发为工具调用。
        注册后，_ask 不再走终端交互，而是调用此 handler。
        """
        self._handler = handler

    # ------------------------------------------------------------------
    # 对外 API
    # ------------------------------------------------------------------
    def request_assistance(self, message: str, options: Optional[List[str]] = None, context: str = "") -> dict:
        """请求用户资源协助（如「需要域名和服务器部署产品 X」）。

        Args:
            message: 协助请求说明
            options: 可选项，默认 ["已提供", "跳过", "稍后"]
            context: 上下文说明（如触发该请求的 agent / 任务）

        Returns:
            dict: {question, options, response, timestamp, context, log_path}
        """
        if options is None:
            options = ["已提供", "跳过", "稍后"]

        response = self._ask(message, options)
        record = {
            "type": "assistance",
            "question": message,
            "options": list(options),
            "response": response,
            "timestamp": self._now_ts(),
            "context": context,
        }
        record["log_path"] = self._log_request(record)
        return record

    def request_approval(self, decision_context: str, options: Optional[List[str]] = None) -> dict:
        """请求高风险决策确认（大额出款、加密货币出币、新产品立项等）。

        Args:
            decision_context: 决策上下文说明
            options: 可选项，默认 ["批准", "拒绝", "需要更多信息"]

        Returns:
            dict: {question, options, response, timestamp, context, decision_context, log_path}
        """
        if options is None:
            options = ["批准", "拒绝", "需要更多信息"]

        # 决策类问题加上前缀以区分普通协助请求
        question = f"【决策确认】{decision_context}"
        response = self._ask(question, options)
        record = {
            "type": "approval",
            "question": question,
            "options": list(options),
            "response": response,
            "timestamp": self._now_ts(),
            "context": "",
            "decision_context": decision_context,
        }
        record["log_path"] = self._log_request(record)
        return record

    # ------------------------------------------------------------------
    # 翻墙状态探测
    # ------------------------------------------------------------------
    def check_vpn(self, host: str = "www.google.com", timeout: float = 3.0) -> bool:
        """探测翻墙状态，不通时主动请求用户开启翻墙。

        避免后续访问 Twitter/Reddit/Mirror/Binance 等被墙服务时反复超时。
        探测逻辑：用 socket 测试 TCP 连接到 host:443，超时即视为不通。

        Args:
            host: 要访问的目标域名（默认 google.com，最稳定的 GFW 探测点）。
                  仅用于显示消息，实际探测固定走 _VPN_PROBE_HOSTS。
            timeout: 单次 TCP 连接超时秒数。

        Returns:
            bool: True 表示翻墙已开启（或本就可达）；False 表示未开启/用户跳过。
        """
        # Step 1: 先探测一次，通就直接返回（避免无谓打扰用户）
        if self._probe_reachable(timeout=timeout):
            return True

        # Step 2: 不通 → 按模板请求协助
        message = _VPN_REQUEST_MSG_TEMPLATE.format(host=host)
        record = self.request_assistance(
            message=message,
            options=list(_VPN_REQUEST_OPTIONS),
            context=f"check_vpn(host={host})",
        )
        response = record.get("response", "")

        # Step 3: 用户回复"已开启翻墙" → 重新探测确认
        if response == "已开启翻墙":
            if self._probe_reachable(timeout=timeout):
                print("[human_loop] 翻墙已确认开启")
                return True
            print("[human_loop] 用户已回复开启，但探测仍不通，可能 VPN 未生效或延迟")
            return False

        # Step 4: 用户跳过 / 稍后再试
        print(f"[human_loop] 用户选择 {response}，跳过翻墙依赖任务")
        return False

    @staticmethod
    def _probe_reachable(timeout: float = 3.0) -> bool:
        """用 socket TCP 连接探测 _VPN_PROBE_HOSTS，任一通即返回 True。

        Args:
            timeout: 单次连接超时秒数。

        Returns:
            bool: 任一被墙服务可达即视为翻墙已开启。
        """
        for host, port in _VPN_PROBE_HOSTS:
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except (socket.timeout, OSError, ConnectionError):
                continue
        return False

    # ------------------------------------------------------------------
    # 内部分发
    # ------------------------------------------------------------------
    def _ask(self, message: str, options: List[str]) -> str:
        """内部分发：若注册了 _handler 则调用它，否则走终端 input() 交互。

        非交互环境（stdin 非 tty）：返回 options 中的 "跳过"（若存在）或最后一项，
        并记录「非交互环境自动跳过」。
        """
        # 1. 注册了外部处理器：直接转发（如 AskUserQuestion 桥接）
        if self._handler is not None:
            try:
                resp = self._handler(message, options)
                if resp is not None:
                    return str(resp)
            except Exception as e:
                # handler 异常时降级到终端模式，并打印错误
                print(f"[human_loop] handler 调用异常: {e}，降级到终端交互", file=sys.stderr)

        # 2. 非交互环境（cron/后台调度，stdin 非 tty）：自动跳过，避免卡死
        if not sys.stdin or not sys.stdin.isatty():
            skip = "跳过" if "跳过" in options else (options[-1] if options else "跳过")
            print(f"[human_loop] 非交互环境自动跳过: {skip}", file=sys.stderr)
            return skip

        # 3. 终端交互模式：打印问题和选项，读取用户输入
        print("\n" + "=" * 60)
        print(f"[需协助] {message}")
        print("-" * 60)
        for idx, opt in enumerate(options, 1):
            print(f"  {idx}. {opt}")
        print("=" * 60)

        while True:
            try:
                raw = input("请输入选项序号或名称: ").strip()
            except (EOFError, KeyboardInterrupt):
                # 输入被中断（如管道关闭），降级为跳过
                skip = "跳过" if "跳过" in options else (options[-1] if options else "跳过")
                print(f"\n[human_loop] 输入中断，自动跳过: {skip}", file=sys.stderr)
                return skip

            if not raw:
                continue

            # 支持序号匹配
            if raw.isdigit():
                idx = int(raw)
                if 1 <= idx <= len(options):
                    return options[idx - 1]
            # 支持名称精确匹配
            if raw in options:
                return raw
            # 忽略大小写的模糊匹配
            for opt in options:
                if opt.lower() == raw.lower():
                    return opt

            print(f"无效输入，请选择 1-{len(options)} 或输入选项名称。")

    # ------------------------------------------------------------------
    # 日志记录
    # ------------------------------------------------------------------
    def _log_request(self, record: dict) -> str:
        """将请求记录追加到 `company/human-requests/YYYY-MM-DD.md`。

        格式：时间戳 / 问题 / 选项 / 用户响应 / 上下文（决策类额外记录决策上下文）。
        返回日志文件路径。
        """
        log_dir = self.workspace.root_dir / "human-requests"
        self.workspace.ensure_dir(log_dir)
        log_file = log_dir / f"{date.today().isoformat()}.md"

        ts = record.get("timestamp", "")
        rtype = record.get("type", "")
        question = record.get("question", "")
        options = record.get("options", [])
        response = record.get("response", "")
        context = record.get("context", "")
        decision_context = record.get("decision_context", "")

        options_str = " | ".join(str(o) for o in options) if options else ""

        block = [f"## [{ts}] {rtype}".rstrip()]
        block.append(f"- 问题: {question}")
        if decision_context:
            block.append(f"- 决策上下文: {decision_context}")
        block.append(f"- 选项: {options_str}")
        block.append(f"- 用户响应: {response}")
        if context:
            block.append(f"- 上下文: {context}")
        block.append("")  # 末尾空行分隔

        # 追加写入：文件不存在则带标题创建，已存在则追加
        existing = self.workspace.read_text(log_file)
        if not existing.strip():
            content = f"# 人工协助请求日志 - {date.today().isoformat()}\n\n" + "\n".join(block) + "\n"
        else:
            content = existing.rstrip() + "\n\n" + "\n".join(block) + "\n"

        self.workspace.write_text(log_file, content)
        return str(log_file.resolve())

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _now_ts() -> str:
        """返回当前时间戳字符串 YYYY-MM-DD HH:MM:SS。"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

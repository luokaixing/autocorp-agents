"""agent-browser 封装模块

基于 agent-browser CLI（self-healing harness），通过 CDP 连接已运行的 Chrome。
核心优势：
- 复用日常 Chrome：用户用 9222 调试端口启动日常 Chrome（保留所有登录态）
- agent-browser 通过 --auto-connect 连接，不自己启动 Chrome
- self-healing：页面 DOM 变化不崩
- 自动等待：CLI 内置智能等待

使用前置条件：
  用户需先用 start-chrome-debug.bat 启动 Chrome（带 9222 调试端口）
  该脚本会用日常 profile 启动 Chrome，保留所有已登录账号（Google/Twitter/Reddit 等）

使用方式：
  from engine.browser.agent_browser import AgentBrowser
  ab = AgentBrowser()  # 自动检测 9222 端口
  ab.open("https://twitter.com")  # 已登录态，无需重新登录
  ab.snapshot()                            # 获取元素 refs
  ab.click("@e1")                           # 用 ref 交互
  ab.close()                                # 只断开连接，不关 Chrome

设计原则：
- 不杀 Chrome，不重启 Chrome，只连接已运行的实例
- 失败时打印错误并返回空结果，不抛异常阻断主流程
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional


# agent-browser CLI 路径（npm 全局安装位置）
# Windows 上必须用 .cmd 版本（.ps1 不能被 subprocess 直接执行）
_CLI_CANDIDATES = [
    "agent-browser",  # PATH 优先（shutil.which 会自动找 .cmd/.exe）
    r"D:\app\useful\nodejs\node_global\agent-browser.cmd",
    r"D:\app\useful\nodejs\node_global\agent-browser.ps1",
    r"D:\app\useful\nodejs\node_global\agent-browser",
]

# Chrome 调试端口（与 start-chrome-debug.bat 一致）
_CDP_PORT = 9222

# start-chrome-debug.bat 的绝对路径（项目根）
_QUICK_LAUNCH_BAT = str(Path(__file__).resolve().parents[2] / "start-chrome-debug.bat")


def _find_cli() -> str:
    """找到可用的 agent-browser CLI 路径。"""
    found = shutil.which("agent-browser")
    if found:
        return found
    for p in _CLI_CANDIDATES[1:]:
        if Path(p).exists():
            return p
    raise RuntimeError(
        "agent-browser CLI 未找到。请运行: npm i -g agent-browser "
        "--registry=https://registry.npmjs.org/"
    )


def is_chrome_debug_alive(port: int = _CDP_PORT, timeout: float = 2.0) -> bool:
    """检查 Chrome 调试端口是否在线。

    Args:
        port: CDP 调试端口（默认 9222）
        timeout: HTTP 请求超时秒数

    Returns:
        True 如果端口在线（Chrome 已用调试端口启动）
    """
    try:
        import urllib.request
        req = urllib.request.Request(
            f"http://localhost:{port}/json/version",
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


def ensure_chrome_debug(port: int = _CDP_PORT, auto_start: bool = False) -> bool:
    """确保 Chrome 调试端口在线。

    如果端口不在线且 auto_start=True，尝试启动 Chrome（用日常 profile + 调试端口）。
    启动前只会清理之前 AI 公司启动的调试 Chrome（命令行含 remote-debugging-port=9222），
    不会杀用户正在使用的普通 Chrome。

    Args:
        port: CDP 调试端口
        auto_start: 是否自动启动 Chrome（默认 False，按需启动，避免频繁开关浏览器影响用户）

    Returns:
        True 如果端口在线（已就绪），False 如果启动失败
    """
    if is_chrome_debug_alive(port):
        return True

    if not auto_start:
        return False

    # 只杀之前 AI 公司启动的调试 Chrome（命令行含 remote-debugging-port=port），
    # 不影响用户正在使用的普通 Chrome（普通 Chrome 命令行不含此参数）
    print(f"[agent_browser] Chrome 调试端口未在线，启动 Chrome（端口 {port}）...")
    try:
        if os.name == "nt":
            # WMIC 通过命令行参数精确匹配，只清理 AI 公司自己的调试 Chrome 实例
            os.system(
                f'wmic process where "name=\'chrome.exe\' and CommandLine like \'%remote-debugging-port={port}%\'" '
                "call terminate >NUL 2>&1"
            )
        else:
            os.system(f"pkill -f 'remote-debugging-port={port}' >NUL 2>&1")
        time.sleep(1)
    except Exception as e:  # noqa: BLE001
        print(f"[agent_browser] 清理旧调试 Chrome 进程异常（可忽略）: {e}")

    # 用日常 profile + 调试端口启动 Chrome
    # 必须显式指定 --user-data-dir，否则 Chrome 不会开启调试端口（安全限制）
    chrome_exe = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not Path(chrome_exe).exists():
        print(f"[agent_browser] Chrome 未找到: {chrome_exe}")
        return False

    # 日常 user-data-dir（包含所有登录态）
    user_data_dir = os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")

    try:
        subprocess.Popen(
            [
                chrome_exe,
                f"--remote-debugging-port={port}",
                f"--user-data-dir={user_data_dir}",
                "--restore-last-session",
            ],
            shell=False,
        )
    except Exception as e:  # noqa: BLE001
        print(f"[agent_browser] 启动 Chrome 失败: {e}")
        return False

    # 等待 Chrome 启动并就绪
    for i in range(30):  # 最多等 30 秒
        time.sleep(1)
        if is_chrome_debug_alive(port):
            print(f"[agent_browser] Chrome 调试端口 {port} 已就绪（等待 {i+1}s）")
            return True

    print(f"[agent_browser] Chrome 启动后 {port} 端口仍未就绪（等了 30s）")
    print(f"[agent_browser] 请手动运行: {_QUICK_LAUNCH_BAT}")
    print(f"[agent_browser] 或双击桌面的 AutoCorp Chrome 图标")
    return False


class AgentBrowser:
    """agent-browser CLI 封装 - 通过 CDP 连接已运行的日常 Chrome。

    核心机制：
    - 用户用 start-chrome-debug.bat 启动 Chrome（日常 profile + 9222 调试端口）
    - agent-browser 通过 --auto-connect 连接该 Chrome，继承所有已登录账号
    - 不自己启动 Chrome，不杀 Chrome，只连接

    Attributes:
        auto_ensure: 首次调用时是否自动确保 Chrome 调试端口在线（默认 False，按需启动）
    """

    def __init__(self, auto_ensure: bool = False, cdp_port: int = _CDP_PORT):
        self.auto_ensure = auto_ensure
        self.cdp_port = cdp_port
        self._cli = _find_cli()
        self._ensured = False  # 标记是否已确保 Chrome 就绪

    # ------------------------------------------------------------------
    # 核心命令执行
    # ------------------------------------------------------------------
    def _ensure_chrome(self):
        """首次调用前确保 Chrome 调试端口在线（仅一次）。"""
        if self.auto_ensure and not self._ensured:
            if not ensure_chrome_debug(self.cdp_port, auto_start=True):
                print(f"[agent_browser] 警告: Chrome 调试端口 {self.cdp_port} 未就绪，命令可能失败")
                print(f"[agent_browser] 请手动运行: {_QUICK_LAUNCH_BAT}")
                print(f"[agent_browser] 或双击桌面的 AutoCorp Chrome 图标")
            self._ensured = True

    def _run(self, *args, timeout: int = 60) -> dict:
        """执行 agent-browser 命令，返回 {ok, stdout, stderr, returncode}。

        使用 --auto-connect 连接已运行的 Chrome（日常 profile，保留所有登录态）。
        Windows 上 .cmd 必须用 shell=True。
        失败时打印错误，不抛异常。
        """
        # 首次执行前确保 Chrome 就绪
        if args and args[0] in ("open", "goto", "navigate", "snapshot"):
            self._ensure_chrome()

        # --cdp: 明确指定 CDP 端口连接已运行的 Chrome（日常 profile，保留所有登录态）
        # 注意: --auto-connect 和 --cdp 不能同时用，这里用 --cdp 更明确
        cmd_parts = [
            self._cli,
            "--cdp", str(self.cdp_port),
        ]
        cmd_parts.extend(str(a) for a in args)

        # Windows 上 .cmd 文件必须用 shell=True
        # 用字符串形式传给 shell，避免列表被当成单一参数
        if self._cli.endswith(".cmd") or self._cli.endswith(".ps1"):
            # shell=True 模式：拼成字符串
            # 用 subprocess.list2cmdline 正确处理 Windows 引号
            cmd_str = subprocess.list2cmdline(cmd_parts)
            try:
                result = subprocess.run(
                    cmd_str,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=True,
                    encoding="utf-8",
                    errors="replace",
                )
            except subprocess.TimeoutExpired:
                print(f"[agent_browser] 命令超时: {' '.join(args)}")
                return {"ok": False, "stdout": "", "stderr": "timeout", "returncode": -1}
            except Exception as e:  # noqa: BLE001
                print(f"[agent_browser] 命令异常: {' '.join(args)} → {e}")
                return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -1}
        else:
            # shell=False 模式（Linux/Mac 或 .exe）
            try:
                result = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=False,
                    encoding="utf-8",
                    errors="replace",
                )
            except subprocess.TimeoutExpired:
                print(f"[agent_browser] 命令超时: {' '.join(args)}")
                return {"ok": False, "stdout": "", "stderr": "timeout", "returncode": -1}
            except Exception as e:  # noqa: BLE001
                print(f"[agent_browser] 命令异常: {' '.join(args)} → {e}")
                return {"ok": False, "stdout": "", "stderr": str(e), "returncode": -1}

        ok = result.returncode == 0
        if not ok:
            print(f"[agent_browser] 命令失败: {' '.join(args)}")
            print(f"  stderr: {result.stderr[:500]}")
        return {
            "ok": ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    # ------------------------------------------------------------------
    # 导航
    # ------------------------------------------------------------------
    def open(self, url: str, wait_networkidle: bool = True) -> bool:
        """打开 URL。默认等待网络空闲。"""
        args = ["open", url]
        if wait_networkidle:
            # 链式等待 networkidle
            r = self._run("open", url)
            if not r["ok"]:
                return False
            r2 = self._run("wait", "--load", "networkidle", timeout=30)
            return r2["ok"]
        r = self._run(*args)
        return r["ok"]

    def get_url(self) -> Optional[str]:
        """获取当前页面 URL。"""
        r = self._run("get", "url")
        if not r["ok"]:
            return None
        return r["stdout"].strip()

    def get_title(self) -> Optional[str]:
        """获取当前页面标题。"""
        r = self._run("get", "title")
        if not r["ok"]:
            return None
        return r["stdout"].strip()

    # ------------------------------------------------------------------
    # 快照与交互
    # ------------------------------------------------------------------
    def snapshot(self) -> str:
        """获取页面交互元素快照（含 @e1 @e2 等 ref）。

        Returns:
            快照文本，失败返回空字符串。
        """
        r = self._run("snapshot", "-i")
        return r["stdout"] if r["ok"] else ""

    def click(self, ref: str, new_tab: bool = False) -> bool:
        """点击元素。ref 形如 "@e1"。"""
        args = ["click", ref]
        if new_tab:
            args.append("--new-tab")
        return self._run(*args)["ok"]

    def fill(self, ref: str, text: str) -> bool:
        """清空输入框并填入文本。"""
        return self._run("fill", ref, text)["ok"]

    def type_text(self, ref: str, text: str) -> bool:
        """在元素上键入文本（不清空）。"""
        return self._run("type", ref, text)["ok"]

    def press(self, key: str) -> bool:
        """按键，如 Enter / Tab / Escape。"""
        return self._run("press", key)["ok"]

    def scroll(self, direction: str, amount: int = 500) -> bool:
        """滚动页面。direction: "up" / "down"。"""
        return self._run("scroll", direction, str(amount))["ok"]

    def find_and_click(self, text: str) -> bool:
        """按可见文本查找并点击元素（语义定位，无需 ref）。"""
        return self._run("find", "text", text, "click")["ok"]

    def find_and_fill(self, label: str, text: str) -> bool:
        """按 label 文本查找输入框并填入文本。"""
        return self._run("find", "label", label, "fill", text)["ok"]

    # ------------------------------------------------------------------
    # 等待
    # ------------------------------------------------------------------
    def wait_load(self, timeout: int = 30) -> bool:
        """等待网络空闲。"""
        return self._run("wait", "--load", "networkidle", timeout=timeout)["ok"]

    def wait_selector(self, selector: str, timeout: int = 30) -> bool:
        """等待 CSS 选择器元素出现。"""
        return self._run("wait", selector, timeout=timeout)["ok"]

    def wait_url(self, pattern: str, timeout: int = 30) -> bool:
        """等待 URL 匹配 glob 模式，如 "**/dashboard"。"""
        return self._run("wait", "--url", pattern, timeout=timeout)["ok"]

    def wait_ms(self, ms: int) -> bool:
        """固定等待毫秒数。"""
        return self._run("wait", str(ms))["ok"]

    # ------------------------------------------------------------------
    # 截图与数据提取
    # ------------------------------------------------------------------
    def screenshot(self, path: Optional[str] = None, full: bool = False) -> Optional[str]:
        """截图。返回图片路径。"""
        args = ["screenshot"]
        if path:
            args.append(path)
        if full:
            args.append("--full")
        r = self._run(*args)
        if not r["ok"]:
            return None
        # CLI 通常把路径打印在 stdout
        return path or r["stdout"].strip()

    def get_text(self, ref_or_selector: str) -> Optional[str]:
        """获取元素文本。"""
        r = self._run("get", "text", ref_or_selector)
        return r["stdout"].strip() if r["ok"] else None

    # ------------------------------------------------------------------
    # 会话管理
    # ------------------------------------------------------------------
    def close(self) -> bool:
        """关闭当前 session 浏览器（登录态自动保存）。"""
        return self._run("close")["ok"]

    def close_all(self) -> bool:
        """关闭所有 session。"""
        return self._run("close", "--all")["ok"]

    def is_alive(self) -> bool:
        """检查 session 是否还在运行。"""
        r = self._run("session", "list")
        return r["ok"] and self.session in r["stdout"]

    # ------------------------------------------------------------------
    # 高级
    # ------------------------------------------------------------------
    def eval_js(self, js: str) -> Optional[str]:
        """在浏览器上下文执行 JavaScript。"""
        r = self._run("eval", js)
        return r["stdout"].strip() if r["ok"] else None

    def state_save(self, path: str) -> bool:
        """保存当前登录态到文件。"""
        return self._run("state", "save", path)["ok"]

    def state_load(self, path: str) -> bool:
        """从文件加载登录态。"""
        return self._run("state", "load", path)["ok"]


# 模块级便捷单例（固定 session="autocorp"）
_default: Optional[AgentBrowser] = None


def get_default() -> AgentBrowser:
    """获取默认 AgentBrowser 单例（session="autocorp"，headed=True）。"""
    global _default
    if _default is None:
        _default = AgentBrowser()
    return _default


if __name__ == "__main__":
    # 自测：打开 example.com 并打印标题
    ab = AgentBrowser()
    print(f"CLI: {ab._cli}")
    print(f"Session: {ab.session}")
    print("打开 example.com ...")
    if ab.open("https://example.com"):
        print(f"标题: {ab.get_title()}")
        print(f"URL: {ab.get_url()}")
        print("\n快照预览:")
        snap = ab.snapshot()
        print(snap[:500] if snap else "(空)")
        ab.close()
    else:
        print("打开失败")

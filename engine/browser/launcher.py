"""Playwright 浏览器启动器

用 Playwright 连接用户原 Chrome profile（保留 Google 账号/MetaMask/扩展），
提供 AI 公司自主操作浏览器的能力。

使用方式：
  from engine.browser.launcher import launch_browser, get_page
  page = get_page()  # 获取已启动的 page，若未启动则自动启动
  page.goto("https://example.com")

启动逻辑：
  1. 检测 Chrome 是否在运行，若有则先关闭
  2. 清理 lockfile / SingletonLock
  3. 用 Playwright launch_persistent_context 启动 Chrome，指向原 User Data 目录
  4. 自动加 --remote-debugging-port=9222 参数
  5. 返回 page 对象供 AI 操作
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

# Playwright 专用独立 profile（首次需手动登录 Google + 导入 MetaMask，之后永久保留）
CHROME_USER_DATA = r"C:\Users\admin\AppData\Local\Google\Chrome\PlaywrightProfile"
CHROME_EXECUTABLE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DEBUG_PORT = 9222

# 全局 browser context（单例）
_persistent_context = None
_page = None


def _kill_chrome() -> None:
    """只关闭 Playwright 专用 Chrome（基于 user-data-dir 匹配），不杀用户的普通 Chrome。

    通过命令行参数中的 PlaywrightProfile 关键字精确匹配，确保只清理 AI 公司
    自己启动的 Chrome 实例，不影响用户正在使用的日常 Chrome。
    """
    if os.name == "nt":
        # 只杀命令行包含 PlaywrightProfile 的 Chrome 进程
        os.system(
            'wmic process where "name=\'chrome.exe\' and CommandLine like \'%PlaywrightProfile%\'" '
            "call terminate >NUL 2>&1"
        )
    else:
        os.system("pkill -f PlaywrightProfile >NUL 2>&1")
    time.sleep(3)

    # 清理 lockfile（Chrome 异常退出后会残留，导致新实例无法启动）
    user_data = Path(CHROME_USER_DATA)
    for lock in ["lockfile", "SingletonLock", "SingletonSocket", "SingletonCookie"]:
        lock_path = user_data / lock
        if lock_path.exists():
            try:
                lock_path.unlink()
            except Exception:
                pass


def launch_browser(headless: bool = False, url: str = "about:blank"):
    """启动 Playwright 持久化 Chrome（用原 profile）。

    Args:
        headless: 是否无头模式（默认 False，有界面方便用户观察）
        url: 启动后打开的 URL

    Returns:
        Playwright Page 对象

    Raises:
        RuntimeError: Chrome profile 不存在或启动失败
    """
    global _persistent_context, _page

    if _page is not None:
        try:
            _page.url  # 测试 page 是否还活着
            return _page
        except Exception:
            _page = None
            _persistent_context = None

    # 检查 profile 存在，不存在则创建（首次启动）
    profile_path = Path(CHROME_USER_DATA)
    if not profile_path.exists():
        profile_path.mkdir(parents=True, exist_ok=True)
        print(f"[browser] 首次启动，创建 profile 目录: {CHROME_USER_DATA}")
        print("[browser] 请在浏览器中登录 Google 账号 + 安装 MetaMask 扩展，之后永久保留")

    # 检查 Chrome 可执行文件
    if not Path(CHROME_EXECUTABLE).exists():
        raise RuntimeError(f"Chrome 可执行文件不存在: {CHROME_EXECUTABLE}")

    # 关闭已有 Chrome + 清理 lockfile
    print("[browser] 关闭已有 Chrome 进程...")
    _kill_chrome()

    # 启动 Playwright
    print("[browser] 启动 Playwright Chrome（用原 profile）...")
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()

    # 启动参数：保留调试端口 + 恢复 session + 常用参数
    # 注意：不加 --disable-extensions，否则 MetaMask 无法安装
    launch_args = [
        f"--remote-debugging-port={DEBUG_PORT}",
        "--restore-last-session",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-blink-features=AutomationControlled",  # 避免被网站检测为自动化
        "--enable-extensions",  # 显式启用扩展支持
    ]

    try:
        _persistent_context = pw.chromium.launch_persistent_context(
            user_data_dir=CHROME_USER_DATA,
            executable_path=CHROME_EXECUTABLE,
            channel="chrome",
            headless=headless,
            args=launch_args,
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
            # 关键：不传 ignore_default_args，让 Playwright 用最小默认参数
            # 但需要去掉 --disable-extensions（Playwright 默认会加）
            ignore_default_args=["--disable-extensions"],
        )
    except Exception as e:
        # 如果 launch_persistent_context 失败，尝试用 launch + CDP 连接
        print(f"[browser] launch_persistent_context 失败: {e}")
        print("[browser] 尝试用 launch + CDP 连接...")
        browser = pw.chromium.launch(
            executable_path=CHROME_EXECUTABLE,
            headless=headless,
            args=launch_args,
            ignore_default_args=["--disable-extensions"],
        )
        _persistent_context = browser.new_context()

    # 获取或创建 page
    if _persistent_context.pages:
        _page = _persistent_context.pages[0]
    else:
        _page = _persistent_context.new_page()

    if url and url != "about:blank":
        try:
            _page.goto(url, timeout=30000)
        except Exception as e:
            print(f"[browser] 导航到 {url} 失败: {e}")

    print(f"[browser] Chrome 已启动，page 已就绪。当前 URL: {_page.url}")
    return _page


def get_page() -> Optional[object]:
    """获取已启动的 page，若未启动则返回 None。"""
    global _page
    if _page is None:
        return None
    try:
        _page.url  # 测试是否还活着
        return _page
    except Exception:
        _page = None
        _persistent_context = None
        return None


def close_browser() -> None:
    """关闭浏览器。"""
    global _persistent_context, _page
    if _persistent_context:
        try:
            _persistent_context.close()
        except Exception:
            pass
    _persistent_context = None
    _page = None


if __name__ == "__main__":
    # 测试启动
    page = launch_browser(url="https://paragraph.com")
    print(f"页面标题: {page.title()}")
    print(f"页面 URL: {page.url}")
    print("浏览器保持打开，按 Enter 关闭...")
    input()
    close_browser()

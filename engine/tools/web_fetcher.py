"""智能网页抓取器

让 AI 公司 Python 代码能自主抓取网页内容，支持：
- 普通 HTTP 抓取（httpx）
- JS 渲染页面降级（Playwright）
- HTML → Markdown 转换
- 自动重试 + 超时

替代 MCP fetch server，集成到 AutonomousLoop 中。
"""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse


def fetch_url(url: str, timeout: int = 30, render_js: bool = False) -> dict:
    """抓取 URL 内容，返回 {status, content, markdown, title, error}。

    Args:
        url: 目标 URL
        timeout: 超时秒数
        render_js: 是否用 Playwright 渲染 JS（针对 SPA）

    Returns:
        dict: {status, content, markdown, title, error}
    """
    result = {"status": "fail", "content": "", "markdown": "", "title": "", "error": ""}

    # 先尝试普通 HTTP 抓取（快）
    if not render_js:
        try:
            import httpx
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }
            with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                html = resp.text
                result["status"] = "ok"
                result["content"] = html
                result["title"] = _extract_title(html)
                result["markdown"] = _html_to_markdown(html)
                return result
        except Exception as e:
            result["error"] = f"httpx 失败: {e}"

    # 普通抓取失败或要求 JS 渲染 → 用 Playwright
    try:
        from engine.browser.launcher import get_page, launch_browser
        page = get_page()
        if page is None:
            page = launch_browser(url=url)
        else:
            page.goto(url, timeout=timeout * 1000)
        page.wait_for_load_state("networkidle", timeout=timeout * 1000)
        html = page.content()
        title = page.title()
        result["status"] = "ok"
        result["content"] = html
        result["title"] = title
        result["markdown"] = _html_to_markdown(html)
    except Exception as e:
        result["error"] = f"Playwright 失败: {e}"

    return result


def fetch_markdown(url: str, timeout: int = 30, render_js: bool = False) -> str:
    """便捷方法：抓取 URL 并返回 markdown 文本。失败返回空字符串。

    Args:
        url: 目标 URL
        timeout: 超时秒数
        render_js: 是否用 Playwright 渲染 JS（默认 False，避免频繁启动浏览器影响用户；
                   仅在显式要求 JS 渲染时才启动浏览器）
    """
    r = fetch_url(url, timeout=timeout)
    if r["status"] == "ok":
        return r["markdown"]
    # 普通抓取失败，仅在显式要求时才降级到 JS 渲染（启动浏览器）
    if render_js:
        r = fetch_url(url, timeout=timeout, render_js=True)
        return r.get("markdown", "")
    return ""


def _extract_title(html: str) -> str:
    """从 HTML 提取 <title> 内容。"""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else ""


def _html_to_markdown(html: str) -> str:
    """简易 HTML → Markdown 转换（不依赖第三方库）。

    只处理核心标签：h1-h6, p, a, ul/ol/li, code, pre, strong, em。
    复杂页面建议用 Playwright 抓取后用 markdownify。
    """
    try:
        from markdownify import markdownify as md
        return md(html, heading_style="ATX", strip=["script", "style", "nav", "footer"])
    except ImportError:
        # 无 markdownify，用简易正则转换
        text = html
        # 移除 script/style
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.IGNORECASE | re.DOTALL)
        # 标题
        for i in range(6, 0, -1):
            text = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>", rf"{'#' * i} \1\n\n", text, flags=re.IGNORECASE | re.DOTALL)
        # 链接
        text = re.sub(r"<a[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", r"[\2](\1)", text, flags=re.IGNORECASE | re.DOTALL)
        # 段落/换行
        text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1\n", text, flags=re.IGNORECASE | re.DOTALL)
        # 加粗/斜体
        text = re.sub(r"<(strong|b)[^>]*>(.*?)</\1>", r"**\2**", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<(em|i)[^>]*>(.*?)</\1>", r"*\2*", text, flags=re.IGNORECASE | re.DOTALL)
        # 代码
        text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"<pre[^>]*>(.*?)</pre>", r"```\n\1\n```\n", text, flags=re.IGNORECASE | re.DOTALL)
        # 移除剩余标签
        text = re.sub(r"<[^>]+>", "", text)
        # HTML 实体
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        # 压缩多余空行
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


if __name__ == "__main__":
    # 测试
    r = fetch_url("https://paragraph.com")
    print(f"status: {r['status']}")
    print(f"title: {r['title']}")
    print(f"markdown length: {len(r['markdown'])}")
    print(r["markdown"][:500])

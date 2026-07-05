"""AI 公司工具集

整合网页抓取、搜索、浏览器控制能力，供 AutonomousLoop 调用。

这三个模块替代了 MCP fetch/brave-search/playwright server，
让 AI 公司 Python 代码能自主：
- 抓网页内容（web_fetcher）
- 搜索网页（web_searcher）
- 控制浏览器（engine.browser.launcher）
"""
from engine.tools.web_fetcher import fetch_url, fetch_markdown
from engine.tools.web_searcher import search, search_summaries

__all__ = ["fetch_url", "fetch_markdown", "search", "search_summaries"]

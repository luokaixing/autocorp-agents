"""网页搜索器

让 AI 公司 Python 代码能自主搜索网页，支持：
- DuckDuckGo 搜索（免费无 key）
- 结果解析为结构化数据
- 便捷方法：搜索并返回前 N 条摘要

替代 MCP brave-search server，集成到 AutonomousLoop 中。
"""
from __future__ import annotations

from typing import List


def search(query: str, max_results: int = 10, timeout: int = 30) -> List[dict]:
    """搜索网页，返回结果列表。

    依次尝试：DuckDuckGo → Bing → 百度，任一成功即返回。

    Args:
        query: 搜索关键词
        max_results: 最多返回结果数
        timeout: 超时秒数

    Returns:
        List[dict]: 每条结果 {title, url, snippet}
    """
    # 1. 优先用 duckduckgo-search 库（免费无 key，国外可用）
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("url", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })
        if results:
            return results
    except ImportError:
        pass
    except Exception as e:
        print(f"[search] duckduckgo 失败: {e}")

    # 2. 降级到 Bing（国内可访问，无需 key）
    try:
        results = _search_bing(query, max_results, timeout)
        if results:
            return results
    except Exception as e:
        print(f"[search] Bing 降级失败: {e}")

    # 3. 最后降级到百度（国内最稳定）
    try:
        results = _search_baidu(query, max_results, timeout)
        if results:
            return results
    except Exception as e:
        print(f"[search] 百度降级失败: {e}")

    return []


def _search_bing(query: str, max_results: int, timeout: int) -> List[dict]:
    """用 Bing 搜索（国内可访问，无需 key）。"""
    import httpx
    import re
    from urllib.parse import quote_plus
    url = f"https://cn.bing.com/search?q={quote_plus(query)}&count={max_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text
    # Bing 结果格式：<li class="b_algo"><h2><a href="...">title</a></h2><p>snippet</p></li>
    results = []
    blocks = re.split(r'<li class="b_algo">', html)
    for block in blocks[1:max_results + 1]:
        title_m = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a></h2>', block, re.DOTALL)
        snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
        if title_m:
            url_found = title_m.group(1)
            title = re.sub(r'<[^>]+>', '', title_m.group(2)).strip()
            snippet = ""
            if snippet_m:
                snippet = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip()
            results.append({"title": title, "url": url_found, "snippet": snippet})
    return results


def _search_baidu(query: str, max_results: int, timeout: int) -> List[dict]:
    """用百度搜索（国内最稳定，无需 key）。"""
    import httpx
    import re
    from urllib.parse import quote_plus
    url = f"https://www.baidu.com/s?wd={quote_plus(query)}&rn={max_results}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text
    # 百度结果格式：<div class="result ..."><h3><a href="...">title</a></h3>...<span>snippet</span></div>
    results = []
    blocks = re.split(r'<div class="result', html)
    for block in blocks[1:max_results + 1]:
        title_m = re.search(r'<h3[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a></h3>', block, re.DOTALL)
        if title_m:
            url_found = title_m.group(1)
            title = re.sub(r'<[^>]+>', '', title_m.group(2)).strip()
            # 百度的 URL 是跳转链接，保留原始链接（用户可点击）
            snippet_m = re.search(r'<span class="content-right_[^"]*">(.*?)</span>', block, re.DOTALL)
            if not snippet_m:
                snippet_m = re.search(r'<div class="c-abstract[^"]*">(.*?)</div>', block, re.DOTALL)
            snippet = ""
            if snippet_m:
                snippet = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip()
            results.append({"title": title, "url": url_found, "snippet": snippet})
    return results


def search_summaries(query: str, max_results: int = 5) -> str:
    """便捷方法：搜索并返回格式化的摘要文本。"""
    results = search(query, max_results=max_results)
    if not results:
        return f"（搜索 '{query}' 无结果）"
    lines = [f"搜索 '{query}' 的前 {len(results)} 条结果：\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['title']}")
        lines.append(f"   URL: {r['url']}")
        if r['snippet']:
            lines.append(f"   摘要: {r['snippet'][:200]}")
        lines.append("")
    return "\n".join(lines)


def _parse_ddg_html(html: str, max_results: int) -> List[dict]:
    """解析 DuckDuckGo HTML 搜索结果页。"""
    import re
    results = []
    # DuckDuckGo HTML 结果格式：<a class="result__a" href="...">title</a>
    # 摘要：<a class="result__snippet">...</a>
    blocks = re.split(r'<div class="result ', html)
    for block in blocks[1:max_results + 1]:
        title_m = re.search(r'class="result__a"[^>]*>(.*?)</a>', block, re.DOTALL)
        url_m = re.search(r'href="([^"]+)"', block)
        snippet_m = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', block, re.DOTALL)
        if title_m and url_m:
            title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
            url = url_m.group(1)
            # DuckDuckGo 的 URL 是重定向格式，提取真实 URL
            if "uddg=" in url:
                from urllib.parse import parse_qs, urlparse
                qs = parse_qs(urlparse(url).query)
                url = qs.get("uddg", [url])[0]
            snippet = ""
            if snippet_m:
                snippet = re.sub(r'<[^>]+>', '', snippet_m.group(1)).strip()
            results.append({"title": title, "url": url, "snippet": snippet})
    return results


if __name__ == "__main__":
    # 测试
    results = search("ethereum wallet security 2026", max_results=3)
    for r in results:
        print(f"- {r['title']}")
        print(f"  {r['url']}")
        print(f"  {r['snippet'][:100]}")
        print()

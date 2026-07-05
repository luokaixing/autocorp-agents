"""社交平台零 API 抓取模块

通过 Agent-Reach（如可用）或自实现 httpx 抓取 Twitter/Reddit/YouTube/B站/小红书
公开内容，作为 PM 选题源与 COO 竞品监控数据。

设计要点：
- 多后端降级：agent_reach（Python 包，存在则用） → httpx（直接抓取平台搜索页）
  → WebSearch（最终降级，调用 engine.tools.web_searcher）
- 频率限制：≤ 1 次/分钟/平台，超限抛 RateLimitError
- 翻墙检测：抓取 Twitter/Reddit/YouTube 失败（超时/连接重置/SSL）时通过
  engine.human_loop 请求用户开启翻墙，仍失败则降级到 WebSearch
- 接口稳定：无论后端如何变化，fetch_trending / fetch_competitor 始终返回
  标准化帖子列表（含 title/url/content/snippet/engagement/author/fetched_at）

不修改现有 task_queue / ledger 流程。
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# 平台支持列表
SUPPORTED_PLATFORMS = ["twitter", "reddit", "youtube", "bilibili", "xiaohongshu"]

# 频率限制：每平台 60 秒 1 次（spec 要求 ≤ 1 次/分钟/平台）
RATE_LIMIT_SECONDS = 60

# 翻墙失败信号：错误信息中命中任一即视为网络封锁
_BLOCKED_SIGNALS = ("timeout", "connection reset", "ssl", "nameresolution",
                    "timed out", "proxyerror", "connectionrefused", "connect error")

# 需翻墙平台（国内默认不可达）
_BLOCKED_PLATFORMS = ("twitter", "reddit", "youtube")

# 通用浏览器 UA（避免被平台 403）
_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)


class RateLimitError(Exception):
    """频率限制异常：单个平台 1 分钟内调用超过 1 次。"""
    pass


class SocialReach:
    """社交平台抓取器

    多后端降级链：
        agent_reach（Python 包） → httpx（直接抓取） → WebSearch（最终降级）

    用法：
        reach = SocialReach()
        posts = reach.fetch_trending("reddit", keyword="DeFi", limit=20)
    """

    def __init__(self, cache_dir: str = "company/knowledge/social-cache"):
        # cache_dir 相对工作目录；延迟到 workspace 可用时再创建
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:  # noqa: BLE001 - 缓存目录创建失败不阻断
            logger.warning(f"社交缓存目录创建失败：{e}")
        # {platform: last_call_timestamp}
        self._last_call: dict[str, float] = {}
        self._backend = self._detect_backend()
        # 延迟初始化 human_loop（避免循环依赖与无谓 stdin 探测）
        self._human_loop = None

    # ------------------------------------------------------------------
    # 后端检测
    # ------------------------------------------------------------------
    def _detect_backend(self) -> str:
        """检测可用后端，返回 'agent_reach' / 'httpx' / 'websearch'。"""
        # 1. 优先使用 agent_reach Python 包（注意：agent-reach 实际是 CLI 脚手架，
        #    但若用户通过 pip install agent-reach 装了 Python 包则可用）
        try:
            import agent_reach  # noqa: F401
            return "agent_reach"
        except ImportError:
            pass
        # 2. 次选 httpx 直接抓取
        try:
            import httpx  # noqa: F401
            return "httpx"
        except ImportError:
            pass
        # 3. 最终降级：WebSearch
        return "websearch"

    # ------------------------------------------------------------------
    # 对外 API：抓取热门话题
    # ------------------------------------------------------------------
    def fetch_trending(self, platform: str, keyword: str = "DeFi",
                       limit: int = 50) -> List[dict]:
        """抓取平台热门话题（按关键词搜索）

        Args:
            platform: 平台名（twitter/reddit/youtube/bilibili/xiaohongshu）
            keyword: 搜索关键词，默认 "DeFi"
            limit: 返回数量上限

        Returns:
            标准化帖子列表，每条含：
                - title: str
                - url: str
                - content: str
                - snippet: str
                - engagement: dict (likes/comments/shares/upvotes/views)
                - author: str
                - fetched_at: str (ISO 格式)

        Raises:
            ValueError: 不支持的平台
            RateLimitError: 平台 1 分钟内已调用过
        """
        platform = platform.lower()
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"不支持的平台: {platform}，支持: {SUPPORTED_PLATFORMS}"
            )

        # 频率限制：1 次/分钟/平台
        now = time.time()
        last = self._last_call.get(platform, 0.0)
        if now - last < RATE_LIMIT_SECONDS:
            wait = int(RATE_LIMIT_SECONDS - (now - last))
            raise RateLimitError(
                f"平台 {platform} 频率限制，请 {wait} 秒后重试"
            )
        self._last_call[platform] = now

        # 调用后端（异常不抛出，返回空列表，由翻墙检测/human_loop 兜底）
        try:
            if self._backend == "agent_reach":
                return self._fetch_with_agent_reach(platform, keyword, limit)
            if self._backend == "httpx":
                return self._fetch_with_httpx(platform, keyword, limit)
            return self._fetch_with_websearch(platform, keyword, limit)
        except Exception as e:  # noqa: BLE001 - 顶层兜底，保证接口稳定
            logger.error(f"抓取 {platform} 失败（{self._backend}）：{e}")
            # 翻墙检测：被墙平台 + 网络信号 → 请求协助
            if self._is_network_blocked(platform, str(e)):
                self._request_vpn_assist(platform)
                # 用户确认后重试一次（仅 httpx 后端有意义）
                if self._backend == "httpx":
                    try:
                        return self._fetch_with_httpx(platform, keyword, limit)
                    except Exception as e2:  # noqa: BLE001
                        logger.warning(
                            f"{platform} 翻墙后重试仍失败，降级 WebSearch：{e2}"
                        )
                # 重试失败 / 非 httpx 后端 → 降级 WebSearch
                try:
                    return self._fetch_with_websearch(platform, keyword, limit)
                except Exception as e3:  # noqa: BLE001
                    logger.error(f"{platform} WebSearch 降级也失败：{e3}")
                    return []
            # 非翻墙问题：直接降级到 WebSearch 兜底
            try:
                return self._fetch_with_websearch(platform, keyword, limit)
            except Exception as e4:  # noqa: BLE001
                logger.error(f"{platform} WebSearch 降级失败：{e4}")
                return []

    # ------------------------------------------------------------------
    # 对外 API：抓取竞品账号最近帖子（COO 竞品监控用）
    # ------------------------------------------------------------------
    def fetch_competitor(self, platform: str, competitor_handle: str,
                         limit: int = 20) -> List[dict]:
        """抓取竞品社交账号最近帖子

        Args:
            platform: 平台名（如 "twitter"）
            competitor_handle: 竞品账号句柄（如 "@aave"）
            limit: 返回数量上限

        Returns:
            标准化帖子列表（同 fetch_trending 结构）
        """
        platform = platform.lower()
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(
                f"不支持的平台: {platform}，支持: {SUPPORTED_PLATFORMS}"
            )

        # 频率限制（与 fetch_trending 共享配额）
        now = time.time()
        last = self._last_call.get(platform, 0.0)
        if now - last < RATE_LIMIT_SECONDS:
            wait = int(RATE_LIMIT_SECONDS - (now - last))
            raise RateLimitError(
                f"平台 {platform} 频率限制，请 {wait} 秒后重试"
            )
        self._last_call[platform] = now

        # 去掉 @ 前缀
        handle = competitor_handle.lstrip("@")

        try:
            if self._backend == "agent_reach":
                return self._fetch_competitor_with_agent_reach(
                    platform, handle, limit
                )
            if self._backend == "httpx":
                return self._fetch_competitor_with_httpx(
                    platform, handle, limit
                )
            return self._fetch_competitor_with_websearch(
                platform, handle, limit
            )
        except Exception as e:  # noqa: BLE001
            logger.error(
                f"抓取竞品 {competitor_handle}@{platform} 失败：{e}"
            )
            if self._is_network_blocked(platform, str(e)):
                self._request_vpn_assist(platform)
            try:
                return self._fetch_competitor_with_websearch(
                    platform, handle, limit
                )
            except Exception as e2:  # noqa: BLE001
                logger.error(f"竞品 WebSearch 降级失败：{e2}")
                return []

    # ------------------------------------------------------------------
    # 后端 1：agent_reach Python 包（如可 import）
    # ------------------------------------------------------------------
    def _fetch_with_agent_reach(self, platform: str, keyword: str,
                                limit: int) -> List[dict]:
        """使用 agent_reach 后端抓取热门话题

        agent-reach 项目实际是 CLI 脚手架（pip install agent-reach 装的是 CLI），
        若用户环境装了同名的 Python 模块则调用其 fetch 接口；接口不存在则抛
        NotImplementedError 由上层降级到 httpx / WebSearch。
        """
        import agent_reach  # type: ignore
        # 兼容两种可能的 API：fetch_trending(platform, query, limit)
        # 或 search(platform, query, limit)
        fn = getattr(agent_reach, "fetch_trending", None) or \
            getattr(agent_reach, "search", None)
        if fn is None:
            raise NotImplementedError(
                "agent_reach 模块未提供 fetch_trending/search 接口，降级"
            )
        raw_list = fn(platform=platform, query=keyword, limit=limit) or []
        return [self._normalize_post(platform, item) for item in raw_list[:limit]]

    def _fetch_competitor_with_agent_reach(self, platform: str, handle: str,
                                           limit: int) -> List[dict]:
        """使用 agent_reach 后端抓取竞品账号帖子"""
        import agent_reach  # type: ignore
        fn = getattr(agent_reach, "fetch_user_posts", None) or \
            getattr(agent_reach, "user_timeline", None)
        if fn is None:
            raise NotImplementedError(
                "agent_reach 未提供 fetch_user_posts/user_timeline 接口，降级"
            )
        raw_list = fn(platform=platform, user=handle, limit=limit) or []
        return [self._normalize_post(platform, item) for item in raw_list[:limit]]

    # ------------------------------------------------------------------
    # 后端 2：httpx 直接抓取平台搜索页
    # ------------------------------------------------------------------
    def _fetch_with_httpx(self, platform: str, keyword: str,
                          limit: int) -> List[dict]:
        """降级：使用 httpx 直接抓取平台搜索页 / 公开 JSON 接口

        各平台策略：
        - reddit：官方 .json 公开接口（无需认证，国内可访问）
        - youtube：搜索页 HTML 解析（需翻墙）
        - twitter：nitter 镜像搜索（需翻墙，多数镜像已挂）
        - bilibili：站内搜索 JSON API（国内可访问）
        - xiaohongshu：搜索页 HTML（需 Cookie，降级到 WebSearch）
        """
        import httpx

        results: List[dict] = []
        if platform == "reddit":
            results = self._fetch_reddit_httpx(httpx, keyword, limit)
        elif platform == "youtube":
            results = self._fetch_youtube_httpx(httpx, keyword, limit)
        elif platform == "twitter":
            results = self._fetch_twitter_httpx(httpx, keyword, limit)
        elif platform == "bilibili":
            results = self._fetch_bilibili_httpx(httpx, keyword, limit)
        elif platform == "xiaohongshu":
            results = self._fetch_xiaohongshu_httpx(httpx, keyword, limit)
        return results[:limit]

    def _fetch_reddit_httpx(self, httpx, keyword: str, limit: int) -> List[dict]:
        """Reddit 搜索：reddit.com/search.json 公开接口"""
        url = (
            f"https://www.reddit.com/search.json"
            f"?q={quote_plus(keyword)}&limit={limit}&sort=hot"
        )
        headers = {"User-Agent": "AutoCorp/1.0 (research bot)"}
        with httpx.Client(timeout=15, follow_redirects=True, verify=False) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        out: List[dict] = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            out.append({
                "title": d.get("title", ""),
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "content": (d.get("selftext", "") or "")[:500],
                "snippet": d.get("title", ""),
                "engagement": {
                    "upvotes": d.get("ups", 0),
                    "comments": d.get("num_comments", 0),
                    "likes": d.get("ups", 0),
                    "shares": 0,
                },
                "author": d.get("author", ""),
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
            })
        return out

    def _fetch_youtube_httpx(self, httpx, keyword: str, limit: int) -> List[dict]:
        """YouTube 搜索页 HTML 解析（需翻墙）

        通过正则提取 videoId / title / channel；HTML 结构变化可能导致失败，
        失败由上层降级到 WebSearch。
        """
        url = f"https://www.youtube.com/results?search_query={quote_plus(keyword)}"
        headers = {"User-Agent": _DEFAULT_UA, "Accept-Language": "en-US,en;q=0.9"}
        with httpx.Client(timeout=15, follow_redirects=True, verify=False) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            html = resp.text
        out: List[dict] = []
        # 提取 videoRenderer 块
        for m in re.finditer(
            r'"videoRenderer":\{"videoId":"([^"]+)".*?"title":\{"runs":\[\{"text":"([^"]*)"\}.*?'
            r'"ownerText":\{"runs":\[\{"text":"([^"]*)"', html, re.DOTALL
        ):
            vid, title, channel = m.group(1), m.group(2), m.group(3)
            if not title:
                continue
            out.append({
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "content": title,
                "snippet": title,
                "engagement": {"views": 0, "likes": 0, "comments": 0},
                "author": channel,
                "fetched_at": datetime.now().isoformat(timespec="seconds"),
            })
            if len(out) >= limit:
                break
        return out

    def _fetch_twitter_httpx(self, httpx, keyword: str, limit: int) -> List[dict]:
        """Twitter 搜索：尝试 nitter 镜像，失败则抛异常触发翻墙检测

        nitter 镜像多数已挂，仅作尝试；上层会降级到 WebSearch。
        """
        # 候选 nitter 镜像（多数已失效，仅作尝试）
        mirrors = [
            "https://nitter.net",
            "https://nitter.privacydev.net",
            "https://nitter.poast.org",
        ]
        headers = {"User-Agent": _DEFAULT_UA}
        for base in mirrors:
            try:
                url = f"{base}/search?f=tweets&q={quote_plus(keyword)}"
                with httpx.Client(timeout=10, follow_redirects=True,
                                  verify=False) as client:
                    resp = client.get(url, headers=headers)
                    if resp.status_code != 200:
                        continue
                    html = resp.text
                out: List[dict] = []
                for m in re.finditer(
                    r'<a class="tweet-link"[^>]*href="([^"]+)"[^>]*></a>.*?'
                    r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>',
                    html, re.DOTALL,
                ):
                    href = m.group(1)
                    content_html = m.group(2)
                    content = re.sub(r"<[^>]+>", "", content_html).strip()
                    if not content:
                        continue
                    out.append({
                        "title": content[:80],
                        "url": f"https://x.com{href}" if href.startswith("/")
                        else href,
                        "content": content[:500],
                        "snippet": content[:120],
                        "engagement": {"likes": 0, "comments": 0, "shares": 0},
                        "author": "",
                        "fetched_at": datetime.now().isoformat(timespec="seconds"),
                    })
                    if len(out) >= limit:
                        return out
                if out:
                    return out
            except Exception as e:  # noqa: BLE001
                logger.debug(f"nitter 镜像 {base} 失败：{e}")
                continue
        # 所有镜像失败 → 抛 timeout 触发翻墙检测
        raise ConnectionError(
            "timeout: 所有 nitter 镜像不可达，可能需要翻墙访问 Twitter"
        )

    def _fetch_bilibili_httpx(self, httpx, keyword: str, limit: int) -> List[dict]:
        """B 站搜索：api.bilibili.com/x/web-interface/search/all/v2"""
        url = (
            f"https://api.bilibili.com/x/web-interface/search/all/v2"
            f"?keyword={quote_plus(keyword)}&pagesize={limit}"
        )
        headers = {
            "User-Agent": _DEFAULT_UA,
            "Referer": "https://search.bilibili.com",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        with httpx.Client(timeout=15, follow_redirects=True, verify=False) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        out: List[dict] = []
        result = data.get("data", {}).get("result", []) or []
        for group in result:
            if group.get("result_type") != "video":
                continue
            for item in group.get("data", []) or []:
                title = re.sub(r"<[^>]+>", "", item.get("title", ""))
                out.append({
                    "title": title,
                    "url": item.get("arcurl", ""),
                    "content": (item.get("description", "") or "")[:500],
                    "snippet": title,
                    "engagement": {
                        "views": _safe_int(item.get("play")),
                        "likes": _safe_int(item.get("like")),
                        "comments": _safe_int(item.get("review")),
                        "shares": _safe_int(item.get("video_review")),
                    },
                    "author": item.get("author", ""),
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                })
                if len(out) >= limit:
                    return out
        return out

    def _fetch_xiaohongshu_httpx(self, httpx, keyword: str,
                                  limit: int) -> List[dict]:
        """小红书：无 Cookie 无法抓搜索，直接抛异常降级 WebSearch"""
        raise ConnectionError(
            "timeout: 小红书需 Cookie 认证，降级到 WebSearch"
        )

    def _fetch_competitor_with_httpx(self, platform: str, handle: str,
                                     limit: int) -> List[dict]:
        """httpx 后端抓取竞品账号最近帖子"""
        import httpx
        if platform == "reddit":
            # reddit 用户帖子：/user/{handle}/.json
            url = f"https://www.reddit.com/user/{handle}/.json?limit={limit}"
            headers = {"User-Agent": "AutoCorp/1.0 (research bot)"}
            with httpx.Client(timeout=15, follow_redirects=True,
                              verify=False) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            out: List[dict] = []
            for child in data.get("data", {}).get("children", []):
                d = child.get("data", {})
                out.append({
                    "title": d.get("title", ""),
                    "url": f"https://reddit.com{d.get('permalink', '')}",
                    "content": (d.get("selftext", "") or "")[:500],
                    "snippet": d.get("title", ""),
                    "engagement": {
                        "upvotes": d.get("ups", 0),
                        "comments": d.get("num_comments", 0),
                        "likes": d.get("ups", 0),
                        "shares": 0,
                    },
                    "author": d.get("author", ""),
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                })
            return out[:limit]
        if platform == "twitter":
            # twitter 竞品账号：nitter 用户页（多数已挂，触发翻墙检测降级）
            mirrors = ["https://nitter.net", "https://nitter.poast.org"]
            headers = {"User-Agent": _DEFAULT_UA}
            for base in mirrors:
                try:
                    url = f"{base}/{handle}"
                    with httpx.Client(timeout=10, follow_redirects=True,
                                      verify=False) as client:
                        resp = client.get(url, headers=headers)
                        if resp.status_code != 200:
                            continue
                        html = resp.text
                    out = []
                    for m in re.finditer(
                        r'<a class="tweet-link"[^>]*href="([^"]+)"[^>]*></a>.*?'
                        r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>',
                        html, re.DOTALL,
                    ):
                        href = m.group(1)
                        content = re.sub(r"<[^>]+>", "", m.group(2)).strip()
                        if not content:
                            continue
                        out.append({
                            "title": content[:80],
                            "url": f"https://x.com{href}"
                            if href.startswith("/") else href,
                            "content": content[:500],
                            "snippet": content[:120],
                            "engagement": {
                                "likes": 0, "comments": 0, "shares": 0
                            },
                            "author": handle,
                            "fetched_at": datetime.now().isoformat(
                                timespec="seconds"
                            ),
                        })
                        if len(out) >= limit:
                            return out
                    if out:
                        return out
                except Exception as e:  # noqa: BLE001
                    logger.debug(f"nitter {base} 抓 {handle} 失败：{e}")
                    continue
            raise ConnectionError(
                f"timeout: twitter 竞品 {handle} 抓取失败，可能需翻墙"
            )
        if platform == "bilibili":
            # B 站用户视频：api.bilibili.com/x/space/wbi/arc/search
            url = (
                f"https://api.bilibili.com/x/space/arc/search"
                f"?mid={handle}&pn=1&ps={limit}"
            )
            headers = {
                "User-Agent": _DEFAULT_UA,
                "Referer": f"https://space.bilibili.com/{handle}",
            }
            with httpx.Client(timeout=15, follow_redirects=True,
                              verify=False) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            out = []
            vlist = (data.get("data", {}).get("list", {}) or {}).get("vlist", []) or []
            for item in vlist:
                out.append({
                    "title": item.get("title", ""),
                    "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                    "content": (item.get("description", "") or "")[:500],
                    "snippet": item.get("title", ""),
                    "engagement": {
                        "views": _safe_int(item.get("play")),
                        "comments": _safe_int(item.get("video_review")),
                        "likes": 0,
                        "shares": 0,
                    },
                    "author": item.get("author", ""),
                    "fetched_at": datetime.now().isoformat(timespec="seconds"),
                })
            return out[:limit]
        # youtube / xiaohongshu 竞品账号抓取：降级到 WebSearch
        raise NotImplementedError(
            f"httpx 后端暂不支持 {platform} 竞品账号抓取，降级 WebSearch"
        )

    # ------------------------------------------------------------------
    # 后端 3：WebSearch 最终降级
    # ------------------------------------------------------------------
    def _fetch_with_websearch(self, platform: str, keyword: str,
                              limit: int) -> List[dict]:
        """最终降级：用 WebSearch 搜索 site:{platform}.com {keyword}

        调用 engine.tools.web_searcher.search()，将结果归一化为标准帖子结构。
        """
        from engine.tools.web_searcher import search as web_search

        site_map = {
            "twitter": "x.com",
            "reddit": "reddit.com",
            "youtube": "youtube.com",
            "bilibili": "bilibili.com",
            "xiaohongshu": "xiaohongshu.com",
        }
        site = site_map.get(platform, f"{platform}.com")
        query = f"site:{site} {keyword} trending"
        raw = web_search(query, max_results=limit) or []
        fetched_at = datetime.now().isoformat(timespec="seconds")
        return [{
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("snippet", ""),
            "snippet": r.get("snippet", ""),
            "engagement": {"likes": 0, "comments": 0, "shares": 0},
            "author": "",
            "fetched_at": fetched_at,
        } for r in raw]

    def _fetch_competitor_with_websearch(self, platform: str, handle: str,
                                          limit: int) -> List[dict]:
        """WebSearch 降级：搜索 {handle} on {platform}"""
        from engine.tools.web_searcher import search as web_search

        site_map = {
            "twitter": "x.com",
            "reddit": "reddit.com",
            "youtube": "youtube.com",
            "bilibili": "bilibili.com",
            "xiaohongshu": "xiaohongshu.com",
        }
        site = site_map.get(platform, f"{platform}.com")
        query = f"site:{site} {handle}"
        raw = web_search(query, max_results=limit) or []
        fetched_at = datetime.now().isoformat(timespec="seconds")
        return [{
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("snippet", ""),
            "snippet": r.get("snippet", ""),
            "engagement": {"likes": 0, "comments": 0, "shares": 0},
            "author": handle,
            "fetched_at": fetched_at,
        } for r in raw]

    # ------------------------------------------------------------------
    # 翻墙检测与人工协助
    # ------------------------------------------------------------------
    def _is_network_blocked(self, platform: str, error: str) -> bool:
        """判断是否为翻墙问题：被墙平台 + 错误信息命中网络信号"""
        if platform not in _BLOCKED_PLATFORMS:
            return False
        err_lower = error.lower()
        return any(sig in err_lower for sig in _BLOCKED_SIGNALS)

    def _request_vpn_assist(self, platform: str) -> None:
        """通过 human_loop 请求用户开启翻墙

        human_loop 不可用时降级为日志告警，不阻断主流程。
        """
        try:
            if self._human_loop is None:
                from engine.human_loop import HumanLoop
                self._human_loop = HumanLoop()
            self._human_loop.request_assistance(
                message=(
                    f"需要访问 {platform}，请协助打开翻墙软件后回复已开启"
                ),
                options=["已开启翻墙", "跳过此任务", "稍后再试"],
                context=f"social_reach.fetch({platform})",
            )
        except Exception as e:  # noqa: BLE001 - human_loop 不可用降级
            logger.warning(
                f"human_loop 不可用，无法请求翻墙协助（{platform}）：{e}"
            )

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_post(platform: str, item: dict) -> dict:
        """将 agent_reach 原始返回归一化为标准帖子结构

        兼容多种字段命名（title/heading/text/content/body ...）。
        """
        title = (item.get("title") or item.get("heading")
                 or item.get("text") or "")[:200]
        content = (item.get("content") or item.get("body")
                   or item.get("text") or "")[:500]
        url = item.get("url") or item.get("link") or ""
        author = (item.get("author") or item.get("user")
                  or item.get("username") or "")
        eng = item.get("engagement") or item.get("metrics") or {}
        return {
            "title": title,
            "url": url,
            "content": content,
            "snippet": (item.get("snippet") or title)[:200],
            "engagement": {
                "likes": _safe_int(eng.get("likes") or eng.get("upvotes")),
                "comments": _safe_int(eng.get("comments") or eng.get("replies")),
                "shares": _safe_int(eng.get("shares") or eng.get("retweets")),
            },
            "author": author,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
        }


def _safe_int(v) -> int:
    """安全转 int：None / 空字符串 / 非数字 → 0"""
    if v is None:
        return 0
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return 0


__all__ = ["SocialReach", "RateLimitError", "SUPPORTED_PLATFORMS",
           "RATE_LIMIT_SECONDS"]

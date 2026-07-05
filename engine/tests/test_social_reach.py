"""engine.social_reach 单元测试

覆盖 SubTask 5.8 要求的 6 个测试用例：
- test_fetch_trending_raises_on_invalid_platform：不支持平台抛 ValueError
- test_fetch_trending_raises_on_rate_limit：1 分钟内重复调用抛 RateLimitError
- test_fetch_trending_returns_list：抓取返回标准化帖子列表（mock httpx）
- test_is_network_blocked_detects_timeout：翻墙检测识别 timeout 信号
- test_fetch_social_trends_pm_integration：PM.fetch_social_trends 集成测试
- test_monitor_competitors_coo_integration：COO.monitor_competitors 集成测试

运行：
    cd d:\\autoCompany
    python -m unittest engine.tests.test_social_reach -v
或：
    python -m pytest engine/tests/test_social_reach.py -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

# 确保项目根目录在 sys.path 中（支持直接运行本文件）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from engine.social_reach import (  # noqa: E402
    RATE_LIMIT_SECONDS,
    SUPPORTED_PLATFORMS,
    RateLimitError,
    SocialReach,
)


def _make_post(**overrides) -> dict:
    """构造标准化帖子字典（用于断言）"""
    base = {
        "title": "Test post",
        "url": "https://example.com/post/1",
        "content": "Test content",
        "snippet": "Test snippet",
        "engagement": {"likes": 10, "comments": 2, "shares": 1},
        "author": "testuser",
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }
    base.update(overrides)
    return base


class _FakeResponse:
    """模拟 httpx.Response"""

    def __init__(self, status_code: int = 200, json_data: dict = None,
                 text: str = ""):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class _FakeClient:
    """模拟 httpx.Client 上下文管理器"""

    def __init__(self, response: _FakeResponse = None,
                 exc: Exception = None):
        self._response = response
        self._exc = exc

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url, headers=None):
        if self._exc is not None:
            raise self._exc
        return self._response or _FakeResponse()


# ----------------------------------------------------------------------
# 测试用例
# ----------------------------------------------------------------------


class TestFetchTrendingInvalidPlatform(unittest.TestCase):
    """SubTask 5.8: test_fetch_trending_raises_on_invalid_platform"""

    def test_invalid_platform_raises_value_error(self):
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        with self.assertRaises(ValueError) as ctx:
            reach.fetch_trending("facebook", keyword="DeFi", limit=10)
        self.assertIn("不支持的平台", str(ctx.exception))
        self.assertIn("facebook", str(ctx.exception))

    def test_valid_platforms_no_value_error(self):
        """合法平台不应抛 ValueError（可能抛 RateLimitError/WebSearch 失败）"""
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        for p in SUPPORTED_PLATFORMS:
            # 仅验证平台名校验通过（不实际抓取，第一次调用会被 mock 兜底或失败）
            # 用 monkey patch 替换 _fetch_with_* 直接返回空列表
            reach._fetch_with_httpx = lambda *a, **k: []
            reach._fetch_with_websearch = lambda *a, **k: []
            reach._fetch_with_agent_reach = lambda *a, **k: []
            try:
                result = reach.fetch_trending(p, keyword="test", limit=1)
                self.assertIsInstance(result, list)
            except RateLimitError:
                # 频率限制也合法（说明校验已通过）
                pass
            # 重置频率限制状态，避免影响下一平台
            reach._last_call.clear()


class TestFetchTrendingRateLimit(unittest.TestCase):
    """SubTask 5.8: test_fetch_trending_raises_on_rate_limit"""

    def test_rate_limit_raises_on_second_call(self):
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        # mock 后端避免实际网络请求
        reach._fetch_with_httpx = lambda *a, **k: [_make_post()]
        reach._fetch_with_websearch = lambda *a, **k: []
        # 第一次调用应成功
        result1 = reach.fetch_trending("reddit", keyword="DeFi", limit=5)
        self.assertEqual(len(result1), 1)
        # 第二次调用（同平台、60 秒内）应抛 RateLimitError
        with self.assertRaises(RateLimitError) as ctx:
            reach.fetch_trending("reddit", keyword="DeFi", limit=5)
        self.assertIn("频率限制", str(ctx.exception))

    def test_rate_limit_independent_per_platform(self):
        """不同平台频率限制互不影响"""
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        reach._fetch_with_httpx = lambda *a, **k: []
        reach._fetch_with_websearch = lambda *a, **k: []
        # reddit 第一次
        reach.fetch_trending("reddit", keyword="DeFi", limit=1)
        # twitter 第一次（不同平台，不应被 reddit 的限频影响）
        try:
            reach.fetch_trending("twitter", keyword="DeFi", limit=1)
        except RateLimitError:
            self.fail("twitter 不应被 reddit 的频率限制影响")

    def test_rate_limit_clears_after_window(self):
        """频率限制窗口过后可再次调用"""
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        reach._fetch_with_httpx = lambda *a, **k: []
        reach._fetch_with_websearch = lambda *a, **k: []
        # 模拟已记录 65 秒前的调用
        reach._last_call["reddit"] = time.time() - (RATE_LIMIT_SECONDS + 5)
        # 现在调用应成功（不再限频）
        try:
            reach.fetch_trending("reddit", keyword="DeFi", limit=1)
        except RateLimitError as e:
            self.fail(f"频率窗口已过不应限频：{e}")


class TestFetchTrendingReturnsList(unittest.TestCase):
    """SubTask 5.8: test_fetch_trending_returns_list"""

    def test_returns_standardized_post_list(self):
        """reddit 后端返回标准化帖子列表（mock httpx）"""
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        # 强制走 httpx 后端
        reach._backend = "httpx"

        # 构造 reddit .json 响应
        fake_json = {
            "data": {
                "children": [
                    {"data": {
                        "title": "DeFi lending guide",
                        "permalink": "/r/defi/comments/abc/defi_lending/",
                        "selftext": "A deep dive into DeFi lending",
                        "ups": 42,
                        "num_comments": 5,
                        "author": "u/tester",
                    }},
                    {"data": {
                        "title": "Aave vs Compound",
                        "permalink": "/r/defi/comments/def/aave_vs/",
                        "selftext": "",
                        "ups": 88,
                        "num_comments": 12,
                        "author": "u/alice",
                    }},
                ]
            }
        }
        fake_resp = _FakeResponse(status_code=200, json_data=fake_json)

        with mock.patch("httpx.Client", return_value=_FakeClient(fake_resp)):
            result = reach.fetch_trending("reddit", keyword="DeFi", limit=10)

        # 断言：返回列表，长度 == 2
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # 断言：每条帖子含全部标准化字段
        required_fields = {"title", "url", "content", "snippet",
                            "engagement", "author", "fetched_at"}
        for post in result:
            self.assertTrue(required_fields.issubset(post.keys()),
                            f"帖子缺少字段：{required_fields - set(post.keys())}")

        # 断言：第一条字段值正确
        first = result[0]
        self.assertEqual(first["title"], "DeFi lending guide")
        self.assertEqual(first["url"],
                         "https://reddit.com/r/defi/comments/abc/defi_lending/")
        self.assertIn("DeFi", first["content"])
        self.assertEqual(first["engagement"]["upvotes"], 42)
        self.assertEqual(first["engagement"]["comments"], 5)
        self.assertEqual(first["author"], "u/tester")
        # fetched_at 应为 ISO 格式字符串
        self.assertIsInstance(first["fetched_at"], str)
        datetime.fromisoformat(first["fetched_at"])  # 不抛异常即合法

    def test_returns_empty_list_on_http_error(self):
        """httpx 抓取失败时降级到 WebSearch，仍返回 list"""
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        reach._backend = "httpx"
        # mock httpx 抛异常 → 触发 WebSearch 降级
        exc = ConnectionError("timeout: connection refused")
        with mock.patch("httpx.Client", return_value=_FakeClient(exc=exc)), \
             mock.patch("engine.tools.web_searcher.search",
                         return_value=[]):
            result = reach.fetch_trending("reddit", keyword="DeFi", limit=5)
        self.assertIsInstance(result, list)


class TestIsNetworkBlocked(unittest.TestCase):
    """SubTask 5.8: test_is_network_blocked_detects_timeout"""

    def test_detects_timeout_for_blocked_platform(self):
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        # twitter + timeout → True
        self.assertTrue(
            reach._is_network_blocked("twitter",
                                      "Connection timeout: timed out")
        )
        # reddit + SSL → True
        self.assertTrue(
            reach._is_network_blocked("reddit", "SSL certificate error")
        )
        # youtube + connection reset → True
        self.assertTrue(
            reach._is_network_blocked("youtube",
                                      "ConnectionResetError: connection reset")
        )

    def test_returns_false_for_unblocked_platform(self):
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        # bilibili（国内可访问）即使有 timeout 也不视为翻墙问题
        self.assertFalse(
            reach._is_network_blocked("bilibili", "timeout: timed out")
        )
        # xiaohongshu 同理
        self.assertFalse(
            reach._is_network_blocked("xiaohongshu", "SSL error")
        )

    def test_returns_false_for_non_network_error(self):
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        # twitter 但错误是 JSON 解析失败（非网络问题）→ False
        self.assertFalse(
            reach._is_network_blocked("twitter",
                                      "JSONDecodeError: invalid json")
        )

    def test_case_insensitive_match(self):
        reach = SocialReach(cache_dir=tempfile.mkdtemp())
        # 大写 TIMEOUT 也应命中
        self.assertTrue(
            reach._is_network_blocked("twitter", "TIMEOUT: 30s")
        )


class TestPmFetchSocialTrendsIntegration(unittest.TestCase):
    """SubTask 5.8: test_fetch_social_trends_pm_integration"""

    def test_pm_fetch_social_trends_returns_dict(self):
        """PM.fetch_social_trends 返回 {platform: [posts]} 结构"""
        from engine.agents.product_manager import ProductManager
        from engine.workspace import WorkspaceManager

        # 用临时目录作工作区，避免污染真实数据
        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceManager(root_dir=tmp)
            pm = ProductManager(workspace=ws, llm_client=None)

            # mock SocialReach.fetch_trending 返回固定帖子
            fake_posts = [_make_post(title="DeFi on reddit")]
            with mock.patch(
                "engine.social_reach.SocialReach.fetch_trending",
                return_value=fake_posts,
            ):
                result = pm.fetch_social_trends(platforms=["reddit"])

        self.assertIsInstance(result, dict)
        self.assertIn("reddit", result)
        self.assertEqual(len(result["reddit"]), 1)
        self.assertEqual(result["reddit"][0]["title"], "DeFi on reddit")

    def test_pm_fetch_social_trends_continues_on_failure(self):
        """单平台失败不阻断，对应键值为空列表"""
        from engine.agents.product_manager import ProductManager
        from engine.workspace import WorkspaceManager

        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceManager(root_dir=tmp)
            pm = ProductManager(workspace=ws, llm_client=None)

            def fake_fetch(platform, **kwargs):
                if platform == "twitter":
                    raise RateLimitError("频率限制")
                return [_make_post(title=f"{platform} post")]

            with mock.patch(
                "engine.social_reach.SocialReach.fetch_trending",
                side_effect=fake_fetch,
            ):
                result = pm.fetch_social_trends(
                    platforms=["reddit", "twitter"]
                )

        self.assertIn("reddit", result)
        self.assertEqual(len(result["reddit"]), 1)
        self.assertIn("twitter", result)
        self.assertEqual(result["twitter"], [])  # 失败降级为空列表


class TestCooMonitorCompetitorsIntegration(unittest.TestCase):
    """SubTask 5.8: test_monitor_competitors_coo_integration"""

    def test_monitor_competitors_returns_dict(self):
        """COO.monitor_competitors 返回 {competitor: {posts, avg_engagement}}"""
        from engine.agents.coo import COO
        from engine.workspace import WorkspaceManager

        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceManager(root_dir=tmp)
            coo = COO(workspace=ws, llm_client=None)

            # mock fetch_competitor：aave 返 2 条，compound 返 0 条
            # 注意：mock 拦截 fetch_competitor 自身（在 lstrip 之前），
            # 故 handle 仍带 @ 前缀，与 monitor_competitors 传入的 c 一致
            def fake_fetch(platform, handle, limit):
                if handle == "@aave":
                    return [
                        _make_post(engagement={"likes": 100, "comments": 5,
                                                "shares": 2}),
                        _make_post(engagement={"likes": 50, "comments": 3,
                                                "shares": 1}),
                    ]
                return []

            with mock.patch(
                "engine.social_reach.SocialReach.fetch_competitor",
                side_effect=fake_fetch,
            ):
                result = coo.monitor_competitors(
                    competitors=["@aave", "@CompoundFinance"]
                )

        self.assertIsInstance(result, dict)
        self.assertIn("@aave", result)
        self.assertIn("@CompoundFinance", result)
        # aave：2 条帖子，平均 likes = (100+50)/2 = 75.0
        self.assertEqual(len(result["@aave"]["posts"]), 2)
        self.assertEqual(result["@aave"]["avg_engagement"], 75.0)
        # CompoundFinance：0 条，avg = 0
        self.assertEqual(len(result["@CompoundFinance"]["posts"]), 0)
        self.assertEqual(result["@CompoundFinance"]["avg_engagement"], 0)

    def test_monitor_competitors_continues_on_failure(self):
        """单竞品抓取失败不阻断，对应键值为空列表 + avg=0"""
        from engine.agents.coo import COO
        from engine.workspace import WorkspaceManager

        with tempfile.TemporaryDirectory() as tmp:
            ws = WorkspaceManager(root_dir=tmp)
            coo = COO(workspace=ws, llm_client=None)

            def fake_fetch(platform, handle, limit):
                if handle == "@aave":
                    raise ConnectionError("timeout: twitter blocked")
                return [_make_post(engagement={"likes": 30, "comments": 0,
                                                "shares": 0})]

            with mock.patch(
                "engine.social_reach.SocialReach.fetch_competitor",
                side_effect=fake_fetch,
            ):
                result = coo.monitor_competitors(
                    competitors=["@aave", "@LidoFinance"]
                )

        # aave 失败 → posts=[], avg=0
        self.assertEqual(result["@aave"]["posts"], [])
        self.assertEqual(result["@aave"]["avg_engagement"], 0)
        # LidoFinance 成功 → 1 条，avg=30
        self.assertEqual(len(result["@LidoFinance"]["posts"]), 1)
        self.assertEqual(result["@LidoFinance"]["avg_engagement"], 30.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

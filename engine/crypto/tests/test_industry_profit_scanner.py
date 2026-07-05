"""RealtimeOpportunityScanner 行业利润池扫描扩展单元测试（Task 7）。

覆盖：
- scan_most_profitable_industries() 返回结构正确
- scan_value_chain_entry_opportunities() 返回结构正确
- scan_value_chain_entry_opportunities(industry_name=...) 按行业过滤
- scan_all() 排序逻辑正确（high-profit-chain 优先）
- scan_all() 报告输出含 industry_profit_pool_position 字段
- graceful degradation（verify 失败时 scan_all 不抛异常并返回降级结果）

使用标准库 unittest，可直接 `python -m unittest engine.crypto.tests.test_industry_profit_scanner` 运行，
也兼容 pytest 风格（`python -m pytest engine/crypto/tests/ -v`）。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# 让 tests 包可导入 engine 包（上级目录）
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from engine.crypto.realtime_opportunity_scanner import (  # noqa: E402
    RealtimeOpportunityScanner,
    _PROFIT_POOL_HIGH,
    _PROFIT_POOL_MID,
    _PROFIT_POOL_LOW,
)


# ----------------------------------------------------------------------
# 期望字段定义（与任务要求一致）
# ----------------------------------------------------------------------
_INDUSTRY_REQUIRED_KEYS = {
    "industry_name",
    "profit_scale",
    "profit_margin",
    "growth_rate",
    "profit_pool_distribution",
    "entry_barrier",
    "ai_company_accessible",
    "opportunity_points",
    "risks",
    "data_sources",
    "scanned_at",
}

_VALUE_CHAIN_REQUIRED_KEYS = {
    "industry",
    "chain_segment",
    "entry_type",
    "description",
    "target_customer",
    "value_proposition",
    "barrier_analysis",
    "startup_cost",
    "time_to_revenue",
    "sustainability",
    "resource_match",
    "profit_pool_position",
    "scanned_at",
}

_VALID_ENTRY_TYPES = {
    "efficiency_tool",
    "content_support",
    "data_service",
    "automation",
    "marketing_support",
}

_VALID_PROFIT_POOL_POSITIONS = {
    _PROFIT_POOL_HIGH,
    _PROFIT_POOL_MID,
    _PROFIT_POOL_LOW,
}


def _make_failing_verify(url: str) -> dict:
    """模拟 verify() 网络失败的返回值（graceful degradation 测试用）。"""
    return {
        "url": url,
        "status_code": 0,
        "accessible": False,
        "fetch_time": 0.0,
        "error": "ConnectionError: 模拟网络失败",
    }


def _make_success_verify(url: str) -> dict:
    """模拟 verify() 成功的返回值（避免真实网络调用）。"""
    return {
        "url": url,
        "status_code": 200,
        "accessible": True,
        "fetch_time": 0.001,
        "error": "",
    }


class TestScanMostProfitableIndustries(unittest.TestCase):
    """scan_most_profitable_industries() 结构与内容测试。"""

    def setUp(self) -> None:
        self.scanner = RealtimeOpportunityScanner()
        self.industries = self.scanner.scan_most_profitable_industries()

    def test_returns_non_empty_list(self) -> None:
        """应返回非空列表（至少 8 个行业，覆盖 spec 要求）。"""
        self.assertIsInstance(self.industries, list)
        self.assertGreaterEqual(
            len(self.industries), 8,
            f"行业数 {len(self.industries)} 不足 8 个",
        )

    def test_each_industry_has_required_keys(self) -> None:
        """每个行业字典必须包含任务要求的全部字段。"""
        for i, ind in enumerate(self.industries):
            missing = _INDUSTRY_REQUIRED_KEYS - set(ind.keys())
            self.assertFalse(
                missing,
                f"第 {i} 个行业 {ind.get('industry_name', '?')} 缺少字段: {missing}",
            )

    def test_ai_company_accessible_is_dict_with_bool(self) -> None:
        """ai_company_accessible 应为 dict，含 accessible(bool) 与 reason(str)。"""
        for ind in self.industries:
            aca = ind["ai_company_accessible"]
            self.assertIsInstance(aca, dict, f"{ind['industry_name']} ai_company_accessible 应为 dict")
            self.assertIn("accessible", aca)
            self.assertIsInstance(aca["accessible"], bool)
            self.assertIn("reason", aca)
            self.assertIsInstance(aca["reason"], str)

    def test_profit_pool_distribution_is_dict(self) -> None:
        """profit_pool_distribution 应为 dict（价值链各环节利润占比）。"""
        for ind in self.industries:
            ppd = ind["profit_pool_distribution"]
            self.assertIsInstance(ppd, dict, f"{ind['industry_name']} profit_pool_distribution 应为 dict")
            self.assertGreaterEqual(len(ppd), 3, "利润池分布应至少 3 个环节")

    def test_opportunity_points_has_three_items(self) -> None:
        """opportunity_points 应为列表且至少 3 个机会点。"""
        for ind in self.industries:
            ops = ind["opportunity_points"]
            self.assertIsInstance(ops, list, f"{ind['industry_name']} opportunity_points 应为 list")
            self.assertGreaterEqual(len(ops), 3, "应至少 3 个机会点")

    def test_data_sources_is_url_list(self) -> None:
        """data_sources 应为 URL 字符串列表。"""
        for ind in self.industries:
            ds = ind["data_sources"]
            self.assertIsInstance(ds, list, f"{ind['industry_name']} data_sources 应为 list")
            self.assertGreaterEqual(len(ds), 2, "应至少 2 个数据来源")
            for url in ds:
                self.assertIsInstance(url, str)
                self.assertTrue(url.startswith("http"), f"数据源应为 URL: {url}")

    def test_scanned_at_is_iso_timestamp(self) -> None:
        """scanned_at 应为非空 ISO 时间戳字符串。"""
        for ind in self.industries:
            self.assertTrue(ind["scanned_at"], "scanned_at 不应为空")


class TestScanValueChainEntryOpportunities(unittest.TestCase):
    """scan_value_chain_entry_opportunities() 结构与内容测试。"""

    def setUp(self) -> None:
        self.scanner = RealtimeOpportunityScanner()
        self.entries = self.scanner.scan_value_chain_entry_opportunities()

    def test_returns_non_empty_list(self) -> None:
        """应返回非空列表（8 行业 × 3 切入点 = 至少 24 个）。"""
        self.assertIsInstance(self.entries, list)
        self.assertGreaterEqual(
            len(self.entries), 24,
            f"切入点数 {len(self.entries)} 不足 24 个（8 行业 × 3）",
        )

    def test_each_entry_has_required_keys(self) -> None:
        """每个切入点字典必须包含任务要求的全部字段。"""
        for i, entry in enumerate(self.entries):
            missing = _VALUE_CHAIN_REQUIRED_KEYS - set(entry.keys())
            self.assertFalse(
                missing,
                f"第 {i} 个切入点缺少字段: {missing}",
            )

    def test_entry_type_values_are_valid(self) -> None:
        """entry_type 必须为 5 种合法类型之一。"""
        for entry in self.entries:
            self.assertIn(
                entry["entry_type"], _VALID_ENTRY_TYPES,
                f"非法 entry_type: {entry['entry_type']}",
            )

    def test_profit_pool_position_is_high(self) -> None:
        """所有价值链切入点的 profit_pool_position 应为 high-profit-chain。"""
        for entry in self.entries:
            self.assertEqual(
                entry["profit_pool_position"], _PROFIT_POOL_HIGH,
                f"切入点 {entry.get('description', '?')} 利润池定位应为 high-profit-chain",
            )

    def test_sustainability_values_are_valid(self) -> None:
        """sustainability 应为 asset 或 service。"""
        for entry in self.entries:
            self.assertIn(
                entry["sustainability"], {"asset", "service"},
                f"非法 sustainability: {entry['sustainability']}",
            )

    def test_covers_at_least_three_entry_types(self) -> None:
        """全部切入点应覆盖至少 3 种 entry_type。"""
        used_types = {e["entry_type"] for e in self.entries}
        self.assertGreaterEqual(
            len(used_types), 3,
            f"仅覆盖 {len(used_types)} 种 entry_type，应至少 3 种: {used_types}",
        )

    def test_scanned_at_is_iso_timestamp(self) -> None:
        """scanned_at 应为非空 ISO 时间戳字符串。"""
        for entry in self.entries:
            self.assertTrue(entry["scanned_at"], "scanned_at 不应为空")

    def test_filter_by_industry_name(self) -> None:
        """指定 industry_name 时应只返回该行业的切入点。"""
        # 先获取全部切入点中第一个出现的行业名
        first_industry = self.entries[0]["industry"]
        filtered = self.scanner.scan_value_chain_entry_opportunities(
            industry_name=first_industry
        )
        self.assertGreater(len(filtered), 0, "过滤后应至少有 1 个切入点")
        for entry in filtered:
            self.assertEqual(
                entry["industry"], first_industry,
                "过滤后所有切入点的 industry 应与参数一致",
            )

    def test_filter_by_nonexistent_industry_returns_empty(self) -> None:
        """指定不存在的行业名时应返回空列表（graceful degradation）。"""
        result = self.scanner.scan_value_chain_entry_opportunities(
            industry_name="不存在的行业 XYZ"
        )
        self.assertEqual(result, [], "不存在的行业应返回空列表")


class TestScanAllSorting(unittest.TestCase):
    """scan_all() 排序逻辑测试（high-profit-chain 优先）。

    使用 mock 避免 verify() 真实网络调用。
    """

    def setUp(self) -> None:
        self.scanner = RealtimeOpportunityScanner()

    def test_scan_all_sorts_high_profit_chain_first(self) -> None:
        """scan_all() 结果应按 high-profit-chain → mid → low-red-ocean 排序。"""
        with patch.object(
            self.scanner, "verify", side_effect=_make_success_verify
        ):
            results = self.scanner.scan_all()

        self.assertGreater(len(results), 0, "scan_all 应返回非空结果")

        # 收集所有利润池定位
        positions = [r.get("industry_profit_pool_position") for r in results]
        self.assertTrue(positions, "结果应包含利润池定位字段")

        # 验证排序：high-profit-chain 在前，low-red-ocean 在后
        first_position = positions[0]
        last_position = positions[-1]
        # 第一个应为 high-profit-chain（因为有 24 个价值链切入点）
        self.assertEqual(
            first_position, _PROFIT_POOL_HIGH,
            f"首位应为 high-profit-chain，实际为 {first_position}",
        )
        # 最后一个应为 low-red-ocean（加密/联盟营销等红海平台）
        self.assertEqual(
            last_position, _PROFIT_POOL_LOW,
            f"末位应为 low-red-ocean，实际为 {last_position}",
        )

        # 验证整体顺序：不应出现 high 在 mid 之后的情况
        order_map = {_PROFIT_POOL_HIGH: 0, _PROFIT_POOL_MID: 1, _PROFIT_POOL_LOW: 2}
        order_indices = [order_map.get(p, 1) for p in positions]
        self.assertEqual(
            order_indices, sorted(order_indices),
            "利润池定位未按 high → mid → low 升序排列",
        )

    def test_scan_all_all_entries_have_profit_pool_position(self) -> None:
        """scan_all() 所有结果都应包含 industry_profit_pool_position 字段。"""
        with patch.object(
            self.scanner, "verify", side_effect=_make_success_verify
        ):
            results = self.scanner.scan_all()

        for i, r in enumerate(results):
            self.assertIn(
                "industry_profit_pool_position", r,
                f"第 {i} 条结果缺少 industry_profit_pool_position 字段",
            )
            self.assertIn(
                r["industry_profit_pool_position"], _VALID_PROFIT_POOL_POSITIONS,
                f"第 {i} 条结果利润池定位值非法: {r['industry_profit_pool_position']}",
            )

    def test_scan_all_includes_value_chain_entries(self) -> None:
        """scan_all() 应包含 value-chain-entry 类型的切入点。"""
        with patch.object(
            self.scanner, "verify", side_effect=_make_success_verify
        ):
            results = self.scanner.scan_all()

        vc_entries = [
            r for r in results if r.get("track_category") == "value-chain-entry"
        ]
        self.assertGreaterEqual(
            len(vc_entries), 24,
            f"价值链切入点数 {len(vc_entries)} 不足 24 个",
        )
        # 所有价值链切入点应为 high-profit-chain
        for vc in vc_entries:
            self.assertEqual(
                vc["industry_profit_pool_position"], _PROFIT_POOL_HIGH,
                "价值链切入点应为 high-profit-chain",
            )

    def test_scan_all_preserves_existing_track_categories(self) -> None:
        """scan_all() 应保留原有的赛道类别（crypto / content-service 等）。"""
        with patch.object(
            self.scanner, "verify", side_effect=_make_success_verify
        ):
            results = self.scanner.scan_all()

        track_cats = {r.get("track_category", "") for r in results}
        # 原有赛道类别应存在
        self.assertIn("crypto", track_cats, "crypto 赛道应保留")
        # 新增赛道类别应存在
        self.assertIn("value-chain-entry", track_cats, "value-chain-entry 赛道应存在")


class TestGracefulDegradation(unittest.TestCase):
    """graceful degradation 测试：网络失败时返回降级结果而非抛异常。"""

    def setUp(self) -> None:
        self.scanner = RealtimeOpportunityScanner()

    def test_scan_all_does_not_raise_on_verify_failure(self) -> None:
        """verify() 全部失败时 scan_all() 不应抛异常，应返回降级结果。"""
        with patch.object(
            self.scanner, "verify", side_effect=_make_failing_verify
        ):
            # 不应抛异常
            results = self.scanner.scan_all()

        # 应返回非空结果（即使所有平台验证失败，价值链切入点仍应返回）
        self.assertGreater(len(results), 0, "降级结果不应为空")
        # 价值链切入点不依赖网络，应正常返回
        vc_entries = [
            r for r in results if r.get("track_category") == "value-chain-entry"
        ]
        self.assertGreaterEqual(len(vc_entries), 24, "价值链切入点应不受网络失败影响")

    def test_scan_all_does_not_raise_on_verify_exception(self) -> None:
        """verify() 抛异常时 scan_all() 不应抛异常（双重 try/except 兜底）。"""
        def _raising_verify(url: str) -> dict:
            raise RuntimeError("模拟 verify 内部异常")

        with patch.object(self.scanner, "verify", side_effect=_raising_verify):
            # 不应抛异常
            results = self.scanner.scan_all()

        # 应返回非空结果
        self.assertGreater(len(results), 0, "异常降级结果不应为空")

    def test_scan_most_profitable_industries_does_not_raise(self) -> None:
        """scan_most_profitable_industries() 不依赖网络，不应抛异常。"""
        industries = self.scanner.scan_most_profitable_industries()
        self.assertGreaterEqual(len(industries), 8, "行业基线数据应始终返回")

    def test_scan_value_chain_does_not_raise_on_network_failure(self) -> None:
        """scan_value_chain_entry_opportunities() 不依赖网络，不应抛异常。"""
        entries = self.scanner.scan_value_chain_entry_opportunities()
        self.assertGreaterEqual(len(entries), 24, "切入点基线数据应始终返回")


class TestGenerateReportWithProfitPool(unittest.TestCase):
    """generate_report() 报告输出含 industry_profit_pool_position 字段测试。"""

    def setUp(self) -> None:
        self.scanner = RealtimeOpportunityScanner()

    def test_report_contains_profit_pool_section(self) -> None:
        """报告应包含「行业利润池定位说明」章节。"""
        with patch.object(
            self.scanner, "verify", side_effect=_make_success_verify
        ):
            report_path_str = self.scanner.generate_report()
            report_path = Path(report_path_str)
            self.assertTrue(report_path.exists(), f"报告文件不存在: {report_path}")
            content = report_path.read_text(encoding="utf-8")

        self.assertIn("行业利润池定位说明", content, "报告应含行业利润池定位说明章节")
        self.assertIn("high-profit-chain", content, "报告应含 high-profit-chain 字样")
        self.assertIn("low-red-ocean", content, "报告应含 low-red-ocean 字样")

    def test_report_contains_value_chain_section(self) -> None:
        """报告应包含「最挣钱行业价值链切入点」章节。"""
        with patch.object(
            self.scanner, "verify", side_effect=_make_success_verify
        ):
            report_path_str = self.scanner.generate_report()
            content = Path(report_path_str).read_text(encoding="utf-8")

        self.assertIn("最挣钱行业价值链切入点", content, "报告应含价值链切入点章节")
        self.assertIn("价值链切入", content, "报告应含价值链切入标识")

    def test_report_status_table_has_pool_column(self) -> None:
        """报告状态总览表应含「行业利润池定位」列。"""
        with patch.object(
            self.scanner, "verify", side_effect=_make_success_verify
        ):
            report_path_str = self.scanner.generate_report()
            content = Path(report_path_str).read_text(encoding="utf-8")

        self.assertIn(
            "行业利润池定位", content,
            "报告状态表应含「行业利润池定位」列头",
        )


if __name__ == "__main__":
    unittest.main()

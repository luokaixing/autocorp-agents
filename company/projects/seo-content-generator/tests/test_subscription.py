"""SubscriptionManager 单元测试

覆盖订阅新增 / 扣减 / 查询 / 过期 / 持久化等场景。
所有测试使用 tempfile.mkdtemp 创建临时数据目录，不污染真实数据。
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta

from seo_generator.subscription import SUBSCRIPTION_PLANS, SubscriptionManager


class TestSubscriptionManager(unittest.TestCase):
    """SubscriptionManager 核心功能测试。"""

    def setUp(self):
        """每个测试用例使用独立的临时数据目录。"""
        self.tmpdir = tempfile.mkdtemp(prefix="sub_test_")
        self.mgr = SubscriptionManager(data_dir=self.tmpdir)

    # --------------------------------------------------------------------------
    # add_subscription
    # --------------------------------------------------------------------------

    def test_add_subscription_new(self):
        """新用户添加订阅成功，字段完整且状态为 active。"""
        record = self.mgr.add_subscription(
            "alice@example.com", "STARTER_MONTHLY", "sub_001"
        )
        self.assertEqual(record["email"], "alice@example.com")
        self.assertEqual(record["plan_id"], "STARTER_MONTHLY")
        self.assertEqual(record["subscription_id"], "sub_001")
        self.assertEqual(record["quota"], SUBSCRIPTION_PLANS["STARTER_MONTHLY"]["quota"])
        self.assertEqual(record["used"], 0)
        self.assertEqual(record["status"], "active")
        self.assertIn("started_at", record)
        self.assertIn("expires_at", record)
        self.assertIn("created_at", record)
        # expires_at = started_at + 30 天
        started = datetime.fromisoformat(record["started_at"])
        expires = datetime.fromisoformat(record["expires_at"])
        self.assertEqual((expires - started).days, 30)

    def test_add_subscription_replace_old(self):
        """同 email 新增订阅时，旧 active 订阅标记为 cancelled。"""
        self.mgr.add_subscription("bob@example.com", "STARTER_MONTHLY", "sub_old")
        self.mgr.add_subscription("bob@example.com", "PRO_MONTHLY", "sub_new")

        subs = self.mgr.list_subscriptions("bob@example.com")
        self.assertEqual(len(subs), 2)
        # 旧订阅 cancelled
        old = next(s for s in subs if s["subscription_id"] == "sub_old")
        self.assertEqual(old["status"], "cancelled")
        # 新订阅 active
        new = next(s for s in subs if s["subscription_id"] == "sub_new")
        self.assertEqual(new["status"], "active")
        self.assertEqual(new["plan_id"], "PRO_MONTHLY")
        self.assertEqual(new["quota"], 200)

    def test_add_subscription_unknown_plan(self):
        """未知 plan_id 抛出 ValueError。"""
        with self.assertRaises(ValueError):
            self.mgr.add_subscription("x@example.com", "UNKNOWN_PLAN", "sub_x")

    # --------------------------------------------------------------------------
    # consume_quota
    # --------------------------------------------------------------------------

    def test_consume_quota_success(self):
        """扣减额度成功，remaining 正确递减。"""
        self.mgr.add_subscription("carol@example.com", "STARTER_MONTHLY", "sub_c")
        r1 = self.mgr.consume_quota("carol@example.com")
        self.assertTrue(r1["success"])
        self.assertEqual(r1["remaining"], 49)
        r2 = self.mgr.consume_quota("carol@example.com")
        self.assertTrue(r2["success"])
        self.assertEqual(r2["remaining"], 48)
        # 查询 used 已更新
        q = self.mgr.check_quota("carol@example.com")
        self.assertEqual(q["used"], 2)
        self.assertEqual(q["remaining"], 48)

    def test_consume_quota_exhausted(self):
        """额度耗尽返回 success=False，不继续扣减。"""
        self.mgr.add_subscription("dave@example.com", "ARTICLE_SINGLE", "sub_d")
        r1 = self.mgr.consume_quota("dave@example.com")
        self.assertTrue(r1["success"])
        self.assertEqual(r1["remaining"], 0)
        # 再次扣减应失败
        r2 = self.mgr.consume_quota("dave@example.com")
        self.assertFalse(r2["success"])
        self.assertEqual(r2["remaining"], 0)
        # used 不再增加
        q = self.mgr.check_quota("dave@example.com")
        self.assertEqual(q["used"], 1)

    def test_consume_quota_no_subscription(self):
        """无订阅抛出 ValueError。"""
        with self.assertRaises(ValueError):
            self.mgr.consume_quota("nobody@example.com")

    # --------------------------------------------------------------------------
    # check_quota
    # --------------------------------------------------------------------------

    def test_check_quota(self):
        """查询剩余额度：有订阅 / 无订阅两种情况。"""
        # 无订阅
        q0 = self.mgr.check_quota("ghost@example.com")
        self.assertEqual(q0["quota"], 0)
        self.assertEqual(q0["used"], 0)
        self.assertEqual(q0["remaining"], 0)
        self.assertIsNone(q0["plan_id"])

        # 有订阅
        self.mgr.add_subscription("eve@example.com", "PRO_MONTHLY", "sub_e")
        q1 = self.mgr.check_quota("eve@example.com")
        self.assertEqual(q1["quota"], 200)
        self.assertEqual(q1["used"], 0)
        self.assertEqual(q1["remaining"], 200)
        self.assertEqual(q1["plan_id"], "PRO_MONTHLY")
        self.assertEqual(q1["status"], "active")
        self.assertIsNotNone(q1["expires_at"])

    # --------------------------------------------------------------------------
    # is_active
    # --------------------------------------------------------------------------

    def test_is_active(self):
        """is_active：有效 / 过期 / 无订阅三种情况。"""
        # 无订阅
        self.assertFalse(self.mgr.is_active("stranger@example.com"))

        # 有效订阅
        self.mgr.add_subscription("frank@example.com", "STARTER_MONTHLY", "sub_f")
        self.assertTrue(self.mgr.is_active("frank@example.com"))

        # 过期订阅：手动注入一条 expires_at 已过期的记录
        self._inject_expired_subscription(
            "expired@example.com", "STARTER_MONTHLY", "sub_exp"
        )
        self.assertFalse(self.mgr.is_active("expired@example.com"))

    # --------------------------------------------------------------------------
    # _refresh_status / 过期
    # --------------------------------------------------------------------------

    def test_refresh_status(self):
        """到期订阅自动标记 expired，未到期保持 active。"""
        # 注入一条已过期 + 一条未过期
        self._inject_expired_subscription(
            "past@example.com", "STARTER_MONTHLY", "sub_past"
        )
        self.mgr.add_subscription("future@example.com", "STARTER_MONTHLY", "sub_future")

        # 触发刷新（list_subscriptions 内部会调用 _refresh_status）
        subs = {s["email"]: s for s in self.mgr.list_subscriptions()}
        self.assertEqual(subs["past@example.com"]["status"], "expired")
        self.assertEqual(subs["future@example.com"]["status"], "active")

    def test_expired_blocks_consume(self):
        """过期订阅不能扣减额度，应抛出 ValueError。"""
        self._inject_expired_subscription(
            "expired2@example.com", "STARTER_MONTHLY", "sub_exp2"
        )
        with self.assertRaises(ValueError):
            self.mgr.consume_quota("expired2@example.com")

    # --------------------------------------------------------------------------
    # 计划覆盖
    # --------------------------------------------------------------------------

    def test_article_single_plan(self):
        """单篇计划额度=1，扣减后归零，再次扣减失败。"""
        self.mgr.add_subscription("gina@example.com", "ARTICLE_SINGLE", "sub_g")
        q = self.mgr.check_quota("gina@example.com")
        self.assertEqual(q["quota"], 1)
        r = self.mgr.consume_quota("gina@example.com")
        self.assertTrue(r["success"])
        self.assertEqual(r["remaining"], 0)
        # 再次扣减失败
        r2 = self.mgr.consume_quota("gina@example.com")
        self.assertFalse(r2["success"])

    def test_pro_monthly_plan_quota(self):
        """Pro Monthly 计划额度=200。"""
        self.mgr.add_subscription("hank@example.com", "PRO_MONTHLY", "sub_h")
        q = self.mgr.check_quota("hank@example.com")
        self.assertEqual(q["quota"], 200)
        self.assertEqual(q["remaining"], 200)

    # --------------------------------------------------------------------------
    # 持久化
    # --------------------------------------------------------------------------

    def test_persistence(self):
        """数据写入文件后重新加载实例仍存在。"""
        self.mgr.add_subscription("ivy@example.com", "STARTER_MONTHLY", "sub_i")
        self.mgr.consume_quota("ivy@example.com")
        self.mgr.consume_quota("ivy@example.com")

        # 重新加载一个新实例指向同一数据目录
        mgr2 = SubscriptionManager(data_dir=self.tmpdir)
        q = mgr2.check_quota("ivy@example.com")
        self.assertEqual(q["quota"], 50)
        self.assertEqual(q["used"], 2)
        self.assertEqual(q["remaining"], 48)
        self.assertTrue(mgr2.is_active("ivy@example.com"))

        # 数据文件确实存在且为合法 JSON
        self.assertTrue(os.path.exists(mgr2.data_file))
        with open(mgr2.data_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.assertIn("subscriptions", raw)
        self.assertEqual(len(raw["subscriptions"]), 1)

    # --------------------------------------------------------------------------
    # 辅助方法
    # --------------------------------------------------------------------------

    def _inject_expired_subscription(
        self, email: str, plan_id: str, subscription_id: str
    ):
        """向数据文件注入一条 expires_at 已过期的订阅记录（用于测试过期逻辑）。"""
        data = self.mgr._read()
        now = datetime.now()
        past_start = now - timedelta(days=40)
        past_expire = now - timedelta(days=10)  # 已过期 10 天
        plan = SUBSCRIPTION_PLANS[plan_id]
        data.setdefault("subscriptions", []).append({
            "email": email,
            "plan_id": plan_id,
            "subscription_id": subscription_id,
            "quota": plan["quota"],
            "used": 0,
            "status": "active",  # 初始置 active，由 _refresh_status 改为 expired
            "started_at": past_start.replace(microsecond=0).isoformat(),
            "expires_at": past_expire.replace(microsecond=0).isoformat(),
            "created_at": past_start.replace(microsecond=0).isoformat(),
        })
        self.mgr._write(data)


if __name__ == "__main__":
    unittest.main()

"""PaymentBridge 单元测试（Task 3）

覆盖支付桥接层核心场景：
- create_article_order：mock PayPalClient.create_order，验证返回结构与 order_context 存储
- create_subscription_order：mock create_subscription，验证返回结构
- handle_payment_success（按篇）：mock capture_order 返回成功，验证 add_subscription(ARTICLE_SINGLE)
- handle_payment_success（订阅）：mock activate_subscription + check_subscription，验证 add_subscription(STARTER_MONTHLY)
- generate_for_paid_user_success：mock consume_quota 返回 success，验证生成文章与评分
- generate_for_paid_user_no_quota：mock consume_quota 返回 success=False，验证错误返回
- generate_for_paid_user_no_subscription：mock consume_quota 抛 ValueError，验证异常传播
- order_context_persistence：验证 order_context 写入与读取

使用 unittest.mock.MagicMock 替换 PayPalClient；SubscriptionManager 使用真实实例 + 临时数据目录。
SEO 生成流水线使用 TemplateProvider（无外部 API 依赖）。
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from seo_generator.payment_bridge import PaymentBridge, ARTICLE_PRICE
from seo_generator.subscription import SubscriptionManager


class TestPaymentBridge(unittest.TestCase):
    """PaymentBridge 核心功能测试。"""

    def setUp(self):
        """每个测试用例使用独立的临时数据目录与 mock PayPalClient。"""
        self.tmpdir = tempfile.mkdtemp(prefix="bridge_test_")
        self.sub_manager = SubscriptionManager(data_dir=self.tmpdir)
        self.mock_paypal = MagicMock()
        self.bridge = PaymentBridge(
            paypal_client=self.mock_paypal,
            subscription_manager=self.sub_manager,
        )

    # --------------------------------------------------------------------------
    # create_article_order
    # --------------------------------------------------------------------------

    def test_create_article_order(self):
        """创建按篇订单：返回结构正确 + order_context 已存储。"""
        self.mock_paypal.create_order.return_value = {
            "order_id": "ORDER-001",
            "approve_url": "https://www.sandbox.paypal.com/checkout?token=ORDER-001",
            "status": "CREATED",
            "amount": "2.00",
            "currency": "USD",
        }

        result = self.bridge.create_article_order(
            "alice@example.com", "email marketing", "en"
        )

        # PayPalClient.create_order 调用参数正确
        self.mock_paypal.create_order.assert_called_once()
        call_kwargs = self.mock_paypal.create_order.call_args
        self.assertEqual(call_kwargs.kwargs["amount"], ARTICLE_PRICE)
        self.assertEqual(call_kwargs.kwargs["currency"], "USD")
        self.assertIn("email marketing", call_kwargs.kwargs["description"])

        # 返回结构
        self.assertEqual(result["order_id"], "ORDER-001")
        self.assertEqual(result["approve_url"], "https://www.sandbox.paypal.com/checkout?token=ORDER-001")
        self.assertEqual(result["amount"], 2.0)
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["email"], "alice@example.com")
        self.assertEqual(result["keyword"], "email marketing")
        self.assertEqual(result["lang"], "en")

        # order_context 已写入 orders.json
        ctx = self.bridge._load_order_context("ORDER-001")
        self.assertEqual(ctx["email"], "alice@example.com")
        self.assertEqual(ctx["keyword"], "email marketing")
        self.assertEqual(ctx["lang"], "en")
        self.assertEqual(ctx["amount"], 2.0)
        self.assertEqual(ctx["currency"], "USD")
        self.assertFalse(ctx["captured"])
        self.assertIn("created_at", ctx)

    def test_create_article_order_invalid_email(self):
        """非法邮箱抛 ValueError。"""
        with self.assertRaises(ValueError):
            self.bridge.create_article_order("not-an-email", "kw")
        with self.assertRaises(ValueError):
            self.bridge.create_article_order("", "kw")

    def test_create_article_order_empty_keyword(self):
        """空关键词抛 ValueError。"""
        with self.assertRaises(ValueError):
            self.bridge.create_article_order("x@example.com", "")

    # --------------------------------------------------------------------------
    # create_subscription_order
    # --------------------------------------------------------------------------

    def test_create_subscription_order(self):
        """创建订阅订单：返回结构正确。"""
        self.mock_paypal.create_subscription.return_value = {
            "subscription_id": "I-SUB001",
            "approve_url": "https://www.sandbox.paypal.com/sub?ba_token=BA-001",
            "plan_id": "STARTER_MONTHLY",
            "plan_name": "Starter Monthly",
            "price": 29.00,
            "currency": "USD",
            "quota": 50,
            "status": "APPROVAL_PENDING",
            "subscriber_email": "bob@example.com",
        }

        result = self.bridge.create_subscription_order(
            "bob@example.com", "STARTER_MONTHLY"
        )

        self.mock_paypal.create_subscription.assert_called_once_with(
            "STARTER_MONTHLY", "bob@example.com"
        )

        self.assertEqual(result["subscription_id"], "I-SUB001")
        self.assertEqual(result["approve_url"], "https://www.sandbox.paypal.com/sub?ba_token=BA-001")
        self.assertEqual(result["plan_id"], "STARTER_MONTHLY")
        self.assertEqual(result["email"], "bob@example.com")

    def test_create_subscription_order_invalid_plan(self):
        """未知 plan_id 抛 ValueError。"""
        with self.assertRaises(ValueError):
            self.bridge.create_subscription_order("bob@example.com", "UNKNOWN_PLAN")

    def test_create_subscription_order_invalid_email(self):
        """非法邮箱抛 ValueError。"""
        with self.assertRaises(ValueError):
            self.bridge.create_subscription_order("bad-email", "STARTER_MONTHLY")

    # --------------------------------------------------------------------------
    # handle_payment_success（按篇）
    # --------------------------------------------------------------------------

    def test_handle_payment_success_article(self):
        """按篇支付成功：capture_order 成功 → add_subscription(ARTICLE_SINGLE)。"""
        # 预置订单上下文
        self.bridge._save_order_context(
            order_id="ORDER-PAID",
            email="carol@example.com",
            keyword="content marketing",
            lang="en",
            amount=2.0,
            currency="USD",
        )

        self.mock_paypal.capture_order.return_value = {
            "status": "COMPLETED",
            "amount": "2.00",
            "currency": "USD",
            "transaction_id": "TX-001",
            "order_id": "ORDER-PAID",
        }

        result = self.bridge.handle_payment_success(order_id="ORDER-PAID")

        # capture_order 调用
        self.mock_paypal.capture_order.assert_called_once_with("ORDER-PAID")

        # 返回结构
        self.assertTrue(result["success"])
        self.assertEqual(result["type"], "article")
        self.assertEqual(result["email"], "carol@example.com")
        self.assertEqual(result["article_info"]["keyword"], "content marketing")
        self.assertEqual(result["article_info"]["lang"], "en")
        self.assertIn("message", result)

        # 订阅已添加（ARTICLE_SINGLE，subscription_id=order_id）
        q = self.sub_manager.check_quota("carol@example.com")
        self.assertEqual(q["plan_id"], "ARTICLE_SINGLE")
        self.assertEqual(q["quota"], 1)
        self.assertEqual(q["remaining"], 1)
        self.assertTrue(self.sub_manager.is_active("carol@example.com"))

        # 订单已标记 captured
        ctx = self.bridge._load_order_context("ORDER-PAID")
        self.assertTrue(ctx["captured"])

    def test_handle_payment_success_article_capture_fails(self):
        """capture_order 抛异常时传播。"""
        from engine.payments.paypal import PayPalError

        self.bridge._save_order_context(
            order_id="ORDER-FAIL",
            email="dave@example.com",
            keyword="kw",
            lang="en",
            amount=2.0,
            currency="USD",
        )
        self.mock_paypal.capture_order.side_effect = PayPalError("支付未完成")

        with self.assertRaises(PayPalError):
            self.bridge.handle_payment_success(order_id="ORDER-FAIL")

        # 不应添加额度
        self.assertFalse(self.sub_manager.is_active("dave@example.com"))

    # --------------------------------------------------------------------------
    # handle_payment_success（订阅）
    # --------------------------------------------------------------------------

    def test_handle_payment_success_subscription(self):
        """订阅支付成功：activate + check → add_subscription(STARTER_MONTHLY)。"""
        self.mock_paypal.activate_subscription.return_value = {
            "subscription_id": "I-ACTIVE01",
            "status": "ACTIVE",
        }
        self.mock_paypal.check_subscription.return_value = {
            "subscription_id": "I-ACTIVE01",
            "status": "ACTIVE",
            "plan_id": "STARTER_MONTHLY",
            "subscriber_email": "eve@example.com",
            "start_time": "2026-06-27T10:00:00Z",
        }

        result = self.bridge.handle_payment_success(subscription_id="I-ACTIVE01")

        # activate_subscription 调用
        self.mock_paypal.activate_subscription.assert_called_once_with("I-ACTIVE01")
        # check_subscription 调用
        self.mock_paypal.check_subscription.assert_called_once_with("I-ACTIVE01")

        # 返回结构
        self.assertTrue(result["success"])
        self.assertEqual(result["type"], "subscription")
        self.assertEqual(result["email"], "eve@example.com")
        self.assertEqual(result["plan_id"], "STARTER_MONTHLY")
        self.assertEqual(result["subscription_id"], "I-ACTIVE01")

        # 订阅已添加
        q = self.sub_manager.check_quota("eve@example.com")
        self.assertEqual(q["plan_id"], "STARTER_MONTHLY")
        self.assertEqual(q["quota"], 50)
        self.assertEqual(q["remaining"], 50)
        self.assertTrue(self.sub_manager.is_active("eve@example.com"))

    def test_handle_payment_success_subscription_pro_plan(self):
        """订阅 PRO_MONTHLY：额度为 200。"""
        self.mock_paypal.activate_subscription.return_value = {
            "subscription_id": "I-PRO01",
            "status": "ACTIVE",
        }
        self.mock_paypal.check_subscription.return_value = {
            "subscription_id": "I-PRO01",
            "status": "ACTIVE",
            "plan_id": "PRO_MONTHLY",
            "subscriber_email": "frank@example.com",
        }

        result = self.bridge.handle_payment_success(subscription_id="I-PRO01")

        self.assertTrue(result["success"])
        self.assertEqual(result["plan_id"], "PRO_MONTHLY")
        q = self.sub_manager.check_quota("frank@example.com")
        self.assertEqual(q["quota"], 200)
        self.assertEqual(q["remaining"], 200)

    def test_handle_payment_success_no_args(self):
        """未提供 order_id 和 subscription_id 抛 ValueError。"""
        with self.assertRaises(ValueError):
            self.bridge.handle_payment_success()

    # --------------------------------------------------------------------------
    # generate_for_paid_user
    # --------------------------------------------------------------------------

    def test_generate_for_paid_user_success(self):
        """付费用户生成文章成功：扣额度 → 生成 → 评分。"""
        # 预置订阅额度
        self.sub_manager.add_subscription(
            "gina@example.com", "STARTER_MONTHLY", "sub_g"
        )
        # mock consume_quota 返回 success（剩余 49）
        # 注意：这里直接用真实 SubscriptionManager，consume_quota 会真实扣减

        result = self.bridge.generate_for_paid_user(
            "gina@example.com", "email marketing", "en"
        )

        self.assertTrue(result["success"])
        self.assertIn("article", result)
        self.assertIn("score", result)
        self.assertEqual(result["remaining"], 49)

        article = result["article"]
        self.assertIn("meta_description", article)
        self.assertIn("body_markdown", article)
        self.assertIn("word_count", article)
        self.assertIn("internal_links", article)
        # 正文非空且字数 > 0
        self.assertGreater(article["word_count"], 0)
        self.assertTrue(article["body_markdown"])

        # 评分结构
        score = result["score"]
        self.assertIn("score", score)
        self.assertIsInstance(score["score"], int)
        self.assertIn("suggestions", score)

        # 额度已扣减（50 → 49）
        q = self.sub_manager.check_quota("gina@example.com")
        self.assertEqual(q["used"], 1)
        self.assertEqual(q["remaining"], 49)

    def test_generate_for_paid_user_no_quota(self):
        """额度耗尽：返回 success=False。"""
        # 预置单篇额度（quota=1）
        self.sub_manager.add_subscription(
            "hank@example.com", "ARTICLE_SINGLE", "sub_h"
        )
        # 先扣减一次，耗尽额度
        self.sub_manager.consume_quota("hank@example.com")

        result = self.bridge.generate_for_paid_user(
            "hank@example.com", "email marketing", "en"
        )

        self.assertFalse(result["success"])
        self.assertIn("message", result)
        self.assertEqual(result["remaining"], 0)

    def test_generate_for_paid_user_no_subscription(self):
        """无订阅：consume_quota 抛 ValueError 并传播。"""
        with self.assertRaises(ValueError):
            self.bridge.generate_for_paid_user(
                "nobody@example.com", "email marketing", "en"
            )

    # --------------------------------------------------------------------------
    # 订单上下文持久化
    # --------------------------------------------------------------------------

    def test_order_context_persistence(self):
        """订单上下文写入与读取一致。"""
        self.bridge._save_order_context(
            order_id="ORDER-PERSIST",
            email="ivy@example.com",
            keyword="seo tips",
            lang="zh",
            amount=2.0,
            currency="USD",
        )

        # 读取
        ctx = self.bridge._load_order_context("ORDER-PERSIST")
        self.assertEqual(ctx["order_id"], "ORDER-PERSIST")
        self.assertEqual(ctx["email"], "ivy@example.com")
        self.assertEqual(ctx["keyword"], "seo tips")
        self.assertEqual(ctx["lang"], "zh")
        self.assertFalse(ctx["captured"])

        # 文件确实存在且为合法 JSON
        self.assertTrue(os.path.exists(self.bridge.orders_file))
        with open(self.bridge.orders_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.assertIn("orders", raw)
        self.assertEqual(len(raw["orders"]), 1)
        self.assertEqual(raw["orders"][0]["order_id"], "ORDER-PERSIST")

        # 标记 captured 后再读取
        self.bridge._mark_order_captured("ORDER-PERSIST")
        ctx2 = self.bridge._load_order_context("ORDER-PERSIST")
        self.assertTrue(ctx2["captured"])

    def test_order_context_not_found(self):
        """读取不存在的订单返回空字典。"""
        ctx = self.bridge._load_order_context("NOT-EXIST")
        self.assertEqual(ctx, {})

    def test_order_context_overwrite_on_duplicate(self):
        """重复 order_id 保存时覆盖原记录。"""
        self.bridge._save_order_context(
            order_id="ORDER-DUP",
            email="jack@example.com",
            keyword="kw1",
            lang="en",
            amount=2.0,
            currency="USD",
        )
        self.bridge._save_order_context(
            order_id="ORDER-DUP",
            email="jack@example.com",
            keyword="kw2",
            lang="zh",
            amount=2.0,
            currency="USD",
        )

        with open(self.bridge.orders_file, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # 仍只有一条记录
        self.assertEqual(len(raw["orders"]), 1)
        ctx = self.bridge._load_order_context("ORDER-DUP")
        self.assertEqual(ctx["keyword"], "kw2")
        self.assertEqual(ctx["lang"], "zh")

    # --------------------------------------------------------------------------
    # 端到端集成：按篇支付 → 生成文章
    # --------------------------------------------------------------------------

    def test_e2e_article_payment_to_generation(self):
        """端到端：按篇订单 → 支付成功 → 生成文章（额度从 0→1→0）。"""
        # 1. 创建按篇订单
        self.mock_paypal.create_order.return_value = {
            "order_id": "ORDER-E2E",
            "approve_url": "https://sandbox.paypal.com/approve?ORDER-E2E",
            "status": "CREATED",
        }
        order = self.bridge.create_article_order(
            "kate@example.com", "content marketing", "en"
        )
        self.assertEqual(order["order_id"], "ORDER-E2E")

        # 此时无额度
        self.assertFalse(self.sub_manager.is_active("kate@example.com"))

        # 2. 支付成功回调
        self.mock_paypal.capture_order.return_value = {
            "status": "COMPLETED",
            "amount": "2.00",
            "currency": "USD",
            "transaction_id": "TX-E2E",
            "order_id": "ORDER-E2E",
        }
        pay_result = self.bridge.handle_payment_success(order_id="ORDER-E2E")
        self.assertTrue(pay_result["success"])

        # 现在有 1 篇额度
        q = self.sub_manager.check_quota("kate@example.com")
        self.assertEqual(q["quota"], 1)
        self.assertEqual(q["remaining"], 1)

        # 3. 生成文章
        gen_result = self.bridge.generate_for_paid_user(
            "kate@example.com", "content marketing", "en"
        )
        self.assertTrue(gen_result["success"])
        self.assertEqual(gen_result["remaining"], 0)
        self.assertGreater(gen_result["article"]["word_count"], 0)

        # 额度已耗尽
        q2 = self.sub_manager.check_quota("kate@example.com")
        self.assertEqual(q2["remaining"], 0)
        self.assertEqual(q2["used"], 1)


if __name__ == "__main__":
    unittest.main()

"""支付桥接层

连接 PayPal 支付与 SEO Content Generator 产品逻辑。
- 按篇支付：用户付 $2 → 生成 1 篇文章
- 订阅支付：用户付 $29/$79 → 加额度 → 扣额度生成文章

数据存储：
- data/orders.json：按篇订单上下文（email/keyword/lang/amount/captured）
- data/subscriptions.json：由 SubscriptionManager 管理
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# 确保能 import engine 模块（AutoCorp 主项目）
# 从 seo_generator/payment_bridge.py 向上 4 级到达 d:\autoCompany（engine 包所在）
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from engine.payments.paypal import (  # noqa: E402
    PayPalClient,
    PayPalError,
    SUBSCRIPTION_PLANS as PAYPAL_PLANS,
)
from seo_generator.content_writer import ContentWriter  # noqa: E402
from seo_generator.keyword_analyzer import KeywordAnalyzer  # noqa: E402
from seo_generator.outline_generator import OutlineGenerator  # noqa: E402
from seo_generator.seo_scorer import SEOScorer  # noqa: E402
from seo_generator.subscription import (  # noqa: E402
    SUBSCRIPTION_PLANS as LOCAL_PLANS,
    SubscriptionManager,
)


# 单篇订单价格
ARTICLE_PRICE = 2.0
ARTICLE_CURRENCY = "USD"


class PaymentBridge:
    """支付与产品生成的桥接层。

    职责：
    1. 创建支付订单（按篇 / 订阅），调用 PayPalClient。
    2. 支付成功回调：按篇→添加单篇额度；订阅→激活并添加订阅额度。
    3. 付费用户生成文章：校验并扣减额度，调用 SEO 生成流水线。

    使用示例：
        >>> bridge = PaymentBridge()
        >>> order = bridge.create_article_order("user@example.com", "email marketing")
        >>> # 用户在 approve_url 完成支付后...
        >>> result = bridge.handle_payment_success(order_id=order["order_id"])
        >>> article = bridge.generate_for_paid_user("user@example.com", "email marketing")
    """

    def __init__(
        self,
        paypal_client: PayPalClient = None,
        subscription_manager: SubscriptionManager = None,
    ):
        """初始化桥接层。

        Args:
            paypal_client: PayPal 客户端实例（默认沙盒）。为 None 时创建沙盒客户端。
            subscription_manager: 订阅管理器实例。为 None 时创建默认实例。
        """
        self.paypal = paypal_client or PayPalClient(sandbox=True)
        self.sub_manager = subscription_manager or SubscriptionManager()
        self.keyword_analyzer = KeywordAnalyzer()
        self.outline_generator = OutlineGenerator()
        self.content_writer = ContentWriter()
        self.seo_scorer = SEOScorer()
        # 订单上下文存储在与订阅管理器相同的数据目录
        self.data_dir = self.sub_manager.data_dir
        self.orders_file = os.path.join(self.data_dir, "orders.json")
        self._ensure_orders_file()

    # ------------------------------------------------------------------
    # 订单上下文持久化
    # ------------------------------------------------------------------

    def _ensure_orders_file(self) -> None:
        """确保 orders.json 存在，不存在则创建空结构。"""
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.orders_file):
            self._write_orders({"orders": []})

    def _read_orders(self) -> Dict[str, Any]:
        """读取订单数据。"""
        with open(self.orders_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_orders(self, data: Dict[str, Any]) -> None:
        """写入订单数据。"""
        with open(self.orders_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_order_context(
        self,
        order_id: str,
        email: str,
        keyword: str,
        lang: str,
        amount: float,
        currency: str,
    ) -> None:
        """保存订单上下文到 data/orders.json，供支付成功后使用。"""
        data = self._read_orders()
        orders = data.setdefault("orders", [])
        record = {
            "order_id": order_id,
            "email": email,
            "keyword": keyword,
            "lang": lang,
            "amount": amount,
            "currency": currency,
            "created_at": datetime.now().replace(microsecond=0).isoformat(),
            "captured": False,
        }
        # 若 order_id 已存在则覆盖，避免重复
        for i, o in enumerate(orders):
            if o.get("order_id") == order_id:
                orders[i] = record
                self._write_orders(data)
                return
        orders.append(record)
        self._write_orders(data)

    def _load_order_context(self, order_id: str) -> Dict[str, Any]:
        """读取订单上下文；不存在返回空字典。"""
        data = self._read_orders()
        for o in data.get("orders", []):
            if o.get("order_id") == order_id:
                return dict(o)
        return {}

    def _mark_order_captured(self, order_id: str) -> None:
        """标记订单为已捕获。"""
        data = self._read_orders()
        for o in data.get("orders", []):
            if o.get("order_id") == order_id:
                o["captured"] = True
                break
        self._write_orders(data)

    # ------------------------------------------------------------------
    # 公开 API：创建订单
    # ------------------------------------------------------------------

    def create_article_order(
        self, email: str, keyword: str, lang: str = "en"
    ) -> Dict[str, Any]:
        """创建按篇订单（$2）。

        Args:
            email: 用户邮箱。
            keyword: 目标关键词。
            lang: 语言（en/zh）。

        Returns:
            {order_id, approve_url, amount, currency, email, keyword, lang}

        Raises:
            ValueError: email 或 keyword 非法。
            PayPalError: 创建订单失败。
        """
        if not email or "@" not in email:
            raise ValueError("email 非法或为空")
        if not keyword or not keyword.strip():
            raise ValueError("keyword 不能为空")

        description = f"SEO Article: {keyword}"
        order = self.paypal.create_order(
            amount=ARTICLE_PRICE,
            currency=ARTICLE_CURRENCY,
            description=description,
        )
        order_id = order["order_id"]

        # 把 email/keyword/lang 与 order_id 关联，存到本地
        self._save_order_context(
            order_id=order_id,
            email=email,
            keyword=keyword,
            lang=lang,
            amount=ARTICLE_PRICE,
            currency=ARTICLE_CURRENCY,
        )

        return {
            "order_id": order_id,
            "approve_url": order.get("approve_url", ""),
            "amount": ARTICLE_PRICE,
            "currency": ARTICLE_CURRENCY,
            "email": email,
            "keyword": keyword,
            "lang": lang,
        }

    def create_subscription_order(
        self, email: str, plan_id: str
    ) -> Dict[str, Any]:
        """创建订阅订单。

        Args:
            email: 用户邮箱。
            plan_id: STARTER_MONTHLY 或 PRO_MONTHLY。

        Returns:
            {subscription_id, approve_url, plan_id, email}

        Raises:
            ValueError: email 非法或 plan_id 未知。
            PayPalError: 创建订阅失败。
        """
        if not email or "@" not in email:
            raise ValueError("email 非法或为空")
        if plan_id not in PAYPAL_PLANS:
            raise ValueError(
                f"未知订阅计划 plan_id={plan_id}，"
                f"可选：{list(PAYPAL_PLANS.keys())}"
            )

        sub = self.paypal.create_subscription(plan_id, email)

        return {
            "subscription_id": sub["subscription_id"],
            "approve_url": sub.get("approve_url", ""),
            "plan_id": sub["plan_id"],
            "email": email,
        }

    # ------------------------------------------------------------------
    # 公开 API：支付成功回调
    # ------------------------------------------------------------------

    def handle_payment_success(
        self,
        order_id: Optional[str] = None,
        subscription_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """支付成功回调。

        两种模式（二选一）：
        - 按篇：传入 order_id，capture_order 后记录单篇额度。
        - 订阅：传入 subscription_id，activate_subscription 后添加订阅额度。

        Args:
            order_id: 按篇订单 ID。
            subscription_id: 订阅 ID。

        Returns:
            按篇：{success, type: "article", email, article_info, message, capture}
            订阅：{success, type: "subscription", email, plan_id, subscription_id, message}

        Raises:
            ValueError: 未提供 order_id 或 subscription_id。
            PayPalError: 支付验证失败或订阅详情缺失。
        """
        if order_id:
            return self._handle_article_payment(order_id)
        if subscription_id:
            return self._handle_subscription_payment(subscription_id)
        raise ValueError("必须提供 order_id 或 subscription_id 之一")

    def _handle_article_payment(self, order_id: str) -> Dict[str, Any]:
        """按篇支付成功处理：捕获付款 → 添加单篇额度。"""
        # 1. 捕获付款（验证支付完成，状态非 COMPLETED 时 PayPalClient 抛 PayPalError）
        capture = self.paypal.capture_order(order_id)

        # 2. 从本地订单记录读取 email/keyword/lang
        ctx = self._load_order_context(order_id)
        email = ctx.get("email", "")
        keyword = ctx.get("keyword", "")
        lang = ctx.get("lang", "en")

        if not email:
            raise PayPalError(
                f"订单 {order_id} 缺少 email 上下文，无法添加额度"
            )

        # 3. 添加单篇额度（plan_id=ARTICLE_SINGLE，subscription_id=order_id）
        self.sub_manager.add_subscription(email, "ARTICLE_SINGLE", order_id)

        # 4. 标记订单已捕获
        self._mark_order_captured(order_id)

        return {
            "success": True,
            "type": "article",
            "email": email,
            "message": f"按篇支付成功，已为 {email} 添加 1 篇文章额度",
            "article_info": {
                "keyword": keyword,
                "lang": lang,
            },
            "capture": capture,
        }

    def _handle_subscription_payment(self, subscription_id: str) -> Dict[str, Any]:
        """订阅支付成功处理：激活订阅 → 添加订阅额度。"""
        # 1. 激活订阅（PayPal 端）
        self.paypal.activate_subscription(subscription_id)

        # 2. 查询订阅详情（获取 plan_id 和 subscriber_email）
        details = self.paypal.check_subscription(subscription_id)
        plan_id = details.get("plan_id", "")
        email = details.get("subscriber_email", "")

        if not plan_id or not email:
            raise PayPalError(
                f"订阅 {subscription_id} 缺少 plan_id 或 subscriber_email，"
                f"无法添加额度"
            )

        # 3. 添加订阅额度
        self.sub_manager.add_subscription(email, plan_id, subscription_id)

        return {
            "success": True,
            "type": "subscription",
            "email": email,
            "plan_id": plan_id,
            "subscription_id": subscription_id,
            "message": f"订阅激活成功，已为 {email} 添加 {plan_id} 额度",
        }

    # ------------------------------------------------------------------
    # 公开 API：付费用户生成文章
    # ------------------------------------------------------------------

    def generate_for_paid_user(
        self, email: str, keyword: str, lang: str = "en"
    ) -> Dict[str, Any]:
        """付费用户生成文章（校验额度）。

        流程：
        1. consume_quota 扣减额度。
           - 无订阅 → 抛 ValueError。
           - 额度耗尽 → 返回 {success: False, message}。
        2. 调用 SEO 生成流水线：关键词分析 → 大纲 → 正文 → 评分。

        Args:
            email: 用户邮箱。
            keyword: 目标关键词。
            lang: 语言（en/zh）。

        Returns:
            成功：{success, article, score, remaining, message}
            额度耗尽：{success: False, message, remaining}

        Raises:
            ValueError: 用户无有效订阅。
        """
        # 1. 扣减额度
        consume = self.sub_manager.consume_quota(email)
        if not consume.get("success"):
            return {
                "success": False,
                "message": consume.get("message", "额度耗尽"),
                "remaining": consume.get("remaining", 0),
            }

        remaining = consume.get("remaining", 0)

        # 2. 生成文章
        keyword_analysis = self.keyword_analyzer.analyze(keyword, lang)
        outline = self.outline_generator.generate(keyword_analysis, lang)
        content = self.content_writer.write(outline, keyword_analysis, lang)
        score = self.seo_scorer.score(content, keyword_analysis)

        return {
            "success": True,
            "article": {
                "meta_description": content.get("meta_description", ""),
                "body_markdown": content.get("body_markdown", ""),
                "word_count": content.get("word_count", 0),
                "internal_links": content.get("internal_links", []),
                "outline": outline,
                "keyword_analysis": keyword_analysis,
            },
            "score": score,
            "remaining": remaining,
            "message": f"文章生成成功，剩余额度 {remaining}",
        }

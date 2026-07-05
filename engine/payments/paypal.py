"""PayPal 收款客户端

对接 PayPal REST API 完成收款：
- 创建订单（create_order）
- 捕获付款（capture_order）→ 验证 COMPLETED 后入真实账本
- 查询订单（check_order）
- 创建订阅（create_subscription）→ 调用 Billing API /v1/billing/subscriptions
- 查询订阅（check_subscription）
- 激活订阅（activate_subscription）

安全约定：
- client_id / client_secret 从 SecretsManager 读取，绝不打印或进入日志
- 默认使用沙箱环境（sandbox=True），生产环境需显式开启
- 仅使用标准库 urllib.request，避免引入新依赖

订单文件流转：
- 创建订单 → company/orders/pending/{order_id}.json
- 支付成功 → 移至 company/orders/paid/{order_id}.json + 调用 Ledger.income_real 入账

订阅文件流转：
- 创建订阅 → company/orders/subscriptions/{subscription_id}.json
- 沙盒/正式切换：仅改 .secrets/secrets.json 中 paypal_client_id / paypal_client_secret
  （订阅 API 路径沙盒正式一致，仅 base_url 不同）
"""
from __future__ import annotations

import base64
import datetime
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from engine.ledger import Ledger


# 订阅计划预定义（PayPal plan_id 需在沙盒后台创建，这里用占位 ID）
# 真实 plan_id 在 PayPal 后台创建后，替换 plan_id 字段即可
SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "STARTER_MONTHLY": {
        "plan_id": "P-STARTER-MONTHLY",  # 沙盒占位，真实 plan_id 在 PayPal 后台创建
        "name": "Starter Monthly",
        "price": 29.00,
        "currency": "USD",
        "quota": 50,  # 每月 50 篇文章
        "interval": "MONTH",
    },
    "PRO_MONTHLY": {
        "plan_id": "P-PRO-MONTHLY",
        "name": "Pro Monthly",
        "price": 79.00,
        "currency": "USD",
        "quota": 200,
        "interval": "MONTH",
    },
}


class PayPalError(Exception):
    """PayPal 调用异常 - 携带清晰错误信息供用户排查。"""


class PayPalClient:
    """PayPal 收款客户端 - 从 secrets 读取凭证，不进 Prompt/日志"""

    # PayPal API 端点
    SANDBOX_BASE = "https://api-m.sandbox.paypal.com"
    LIVE_BASE = "https://api-m.paypal.com"

    def __init__(self, workspace=None, sandbox: bool = True) -> None:
        from engine.secrets import SecretsManager
        from engine.workspace import WorkspaceManager
        self.workspace = workspace or WorkspaceManager()
        self.secrets = SecretsManager(self.workspace)
        self.sandbox = sandbox
        self.base_url = self.SANDBOX_BASE if sandbox else self.LIVE_BASE
        # 从 secrets 读取凭证（不打印，不进 Prompt）
        self.client_id = self.secrets.get("paypal_client_id")
        self.client_secret = self.secrets.get("paypal_client_secret")
        self._access_token: Optional[str] = None

    # ------------------------------------------------------------------
    # 凭证校验
    # ------------------------------------------------------------------
    def _ensure_credentials(self) -> None:
        """校验凭证已配置；缺失时抛 PayPalError 给出清晰提示。"""
        if not self.client_id:
            raise PayPalError(
                "未配置 paypal_client_id，请先执行："
                "main.py secrets set paypal_client_id <your_client_id>"
            )
        if not self.client_secret:
            raise PayPalError(
                "未配置 paypal_client_secret，请先执行："
                "main.py secrets set paypal_client_secret <your_client_secret>"
            )

    # ------------------------------------------------------------------
    # 底层 HTTP 请求封装
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """统一 HTTP 请求入口。

        - method: GET / POST
        - path: 相对 base_url 的路径（如 /v2/checkout/orders）
        - headers: 额外请求头
        - body: 请求体字节；None 表示无请求体
        返回解析后的 JSON 字典。
        """
        url = f"{self.base_url}{path}"
        req_headers = {"Accept": "application/json"}
        if headers:
            req_headers.update(headers)

        req = urllib.request.Request(url, data=body, method=method, headers=req_headers)
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            # PayPal 错误响应体含 error_description / message
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
            except (OSError, UnicodeDecodeError):
                pass
            raise PayPalError(
                f"PayPal API 返回 HTTP {e.code}: {err_body or e.reason}"
            ) from e
        except urllib.error.URLError as e:
            # 网络层错误（DNS 解析失败、连接超时等）
            raise PayPalError(f"网络错误，无法连接 PayPal API：{e.reason}") from e

        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise PayPalError(f"PayPal 响应非合法 JSON：{e}") from e

    # ------------------------------------------------------------------
    # access_token 获取与缓存
    # ------------------------------------------------------------------
    def _get_access_token(self) -> str:
        """获取并缓存 PayPal access_token。

        POST {base_url}/v1/oauth2/token
        - Basic auth: client_id:client_secret
        - body: grant_type=client_credentials
        """
        if self._access_token:
            return self._access_token
        self._ensure_credentials()

        # Basic auth：base64(client_id:client_secret)
        raw = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        b64 = base64.b64encode(raw).decode("ascii")

        body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")
        headers = {
            "Authorization": f"Basic {b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = self._request("POST", "/v1/oauth2/token", headers=headers, body=body)
        token = data.get("access_token")
        if not token:
            raise PayPalError(
                f"PayPal 未返回 access_token：{data.get('error_description', data)}"
            )
        self._access_token = token
        return token

    # ------------------------------------------------------------------
    # 订单文件管理（pending → paid）
    # ------------------------------------------------------------------
    @property
    def pending_dir(self) -> Path:
        """待支付订单目录：company/orders/pending/"""
        return self.workspace.root_dir / "orders" / "pending"

    @property
    def paid_dir(self) -> Path:
        """已支付订单目录：company/orders/paid/"""
        return self.workspace.root_dir / "orders" / "paid"

    def _pending_order_path(self, order_id: str) -> Path:
        return self.pending_dir / f"{order_id}.json"

    def _paid_order_path(self, order_id: str) -> Path:
        return self.paid_dir / f"{order_id}.json"

    def _write_pending_order(self, order_data: Dict[str, Any]) -> None:
        """将订单详情写入 pending 目录。"""
        self.workspace.ensure_dir(self.pending_dir)
        path = self._pending_order_path(order_data["order_id"])
        with path.open("w", encoding="utf-8") as f:
            json.dump(order_data, f, ensure_ascii=False, indent=2)

    def _move_order_to_paid(self, order_id: str) -> None:
        """将订单文件从 pending 移至 paid。"""
        src = self._pending_order_path(order_id)
        if not src.exists():
            # 兼容：pending 文件不存在时不阻断入账
            return
        self.workspace.ensure_dir(self.paid_dir)
        dst = self._paid_order_path(order_id)
        # 跨目录移动（Path.replace 在同盘可原子替换）
        src.replace(dst)

    def _load_pending_order(self, order_id: str) -> Dict[str, Any]:
        """读取 pending 订单详情；不存在返回空字典。"""
        path = self._pending_order_path(order_id)
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    # ------------------------------------------------------------------
    # 订阅文件管理（subscriptions/）
    # ------------------------------------------------------------------
    @property
    def subscriptions_dir(self) -> Path:
        """订阅记录目录：company/orders/subscriptions/"""
        return self.workspace.root_dir / "orders" / "subscriptions"

    def _subscription_path(self, subscription_id: str) -> Path:
        return self.subscriptions_dir / f"{subscription_id}.json"

    def _write_subscription(self, sub_data: Dict[str, Any]) -> None:
        """将订阅详情写入 subscriptions 目录。"""
        self.workspace.ensure_dir(self.subscriptions_dir)
        path = self._subscription_path(sub_data["subscription_id"])
        with path.open("w", encoding="utf-8") as f:
            json.dump(sub_data, f, ensure_ascii=False, indent=2)

    def _load_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """读取本地订阅记录；不存在返回空字典。"""
        path = self._subscription_path(subscription_id)
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _update_subscription(self, subscription_id: str, patch: Dict[str, Any]) -> None:
        """用 patch 字典更新本地订阅记录字段；文件不存在则忽略。"""
        data = self._load_subscription(subscription_id)
        if not data:
            return
        data.update(patch)
        path = self._subscription_path(subscription_id)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # 核心 API：创建订单
    # ------------------------------------------------------------------
    def create_order(
        self,
        amount: float,
        currency: str = "USD",
        description: str = "",
    ) -> Dict[str, Any]:
        """创建收款订单。

        POST {base_url}/v2/checkout/orders
        返回 {order_id, approve_url, status}；
        并将订单详情写入 company/orders/pending/{order_id}.json。
        """
        self._ensure_credentials()
        if amount <= 0:
            raise PayPalError("金额必须为正数")

        token = self._get_access_token()
        # 金额格式化为两位小数字符串（PayPal 要求字符串）
        value = f"{float(amount):.2f}"
        body_dict = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {"currency_code": currency, "value": value},
                    "description": description,
                }
            ],
        }
        body = json.dumps(body_dict).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        data = self._request("POST", "/v2/checkout/orders", headers=headers, body=body)
        order_id = data.get("id")
        if not order_id:
            raise PayPalError(f"PayPal 未返回 order id：{data}")

        # 从 links 数组提取 approve 链接
        approve_url = ""
        for link in data.get("links", []) or []:
            if link.get("rel") == "approve":
                approve_url = link.get("href", "")
                break

        status = data.get("status", "CREATED")
        result = {
            "order_id": order_id,
            "approve_url": approve_url,
            "status": status,
            "amount": value,
            "currency": currency,
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "sandbox": self.sandbox,
        }
        # 写入 pending 订单文件
        self._write_pending_order(result)
        return result

    # ------------------------------------------------------------------
    # 核心 API：捕获付款（资金到账）
    # ------------------------------------------------------------------
    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """捕获订单付款。

        POST {base_url}/v2/checkout/orders/{order_id}/capture
        - 验证状态为 COMPLETED
        - 订单文件移至 paid/
        - 调用 Ledger.income_real 入真实账本
        返回 {status, amount, transaction_id, currency}。
        """
        if not order_id:
            raise PayPalError("order_id 不能为空")

        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        path = f"/v2/checkout/orders/{urllib.parse.quote(order_id)}/capture"
        data = self._request("POST", path, headers=headers, body=b"")

        status = data.get("status", "")
        if status != "COMPLETED":
            raise PayPalError(
                f"订单 {order_id} 状态为 {status}，未完成付款捕获"
            )

        # 从 purchase_units[0].payments.captures[0] 提取金额与交易号
        amount_str = ""
        currency = ""
        transaction_id = ""
        units = data.get("purchase_units", []) or []
        if units:
            captures = (units[0].get("payments") or {}).get("captures") or []
            if captures:
                cap = captures[0]
                transaction_id = cap.get("id", "")
                amt = cap.get("amount") or {}
                amount_str = amt.get("value", "")
                currency = amt.get("currency_code", "")

        # 读取 pending 订单详情（金额兜底 + 入账描述）；在移动前读取
        pending = self._load_pending_order(order_id)
        if not amount_str:
            amount_str = pending.get("amount", "0")
        if not currency:
            currency = pending.get("currency", "USD")
        description = pending.get("description", "") or f"PayPal 收款 {order_id}"

        try:
            amount_float = float(amount_str)
        except (TypeError, ValueError):
            amount_float = 0.0

        # 订单文件移至 paid/
        self._move_order_to_paid(order_id)

        # 入真实账本（仅在金额 > 0 时）
        if amount_float > 0:
            ledger = Ledger(self.workspace)
            ledger.income_real(
                amount_float,
                source="paypal",
                tx_ref=order_id,
                description=description,
            )

        return {
            "status": status,
            "amount": amount_str,
            "currency": currency,
            "transaction_id": transaction_id,
            "order_id": order_id,
        }

    # ------------------------------------------------------------------
    # 核心 API：查询订单
    # ------------------------------------------------------------------
    def check_order(self, order_id: str) -> Dict[str, Any]:
        """查询订单状态。

        GET {base_url}/v2/checkout/orders/{order_id}
        返回 {status, amount, payer_info, order_id}。
        """
        if not order_id:
            raise PayPalError("order_id 不能为空")

        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        path = f"/v2/checkout/orders/{urllib.parse.quote(order_id)}"
        data = self._request("GET", path, headers=headers)

        # 金额
        amount_str = ""
        currency = ""
        units = data.get("purchase_units", []) or []
        if units:
            amt = units[0].get("amount") or {}
            amount_str = amt.get("value", "")
            currency = amt.get("currency_code", "")

        # 付款人信息（脱敏保留，不含明文凭证）
        payer = data.get("payer") or {}
        payer_info = {
            "payer_id": payer.get("payer_id", ""),
            "email": payer.get("email_address", ""),
            "name": (
                (payer.get("name") or {}).get("given_name", "")
                + " "
                + (payer.get("name") or {}).get("surname", "")
            ).strip(),
        }

        return {
            "order_id": data.get("id", order_id),
            "status": data.get("status", ""),
            "amount": amount_str,
            "currency": currency,
            "payer_info": payer_info,
        }

    # ------------------------------------------------------------------
    # 核心 API：创建订阅（Billing API）
    # ------------------------------------------------------------------
    def create_subscription(self, plan_id: str, subscriber_email: str) -> Dict[str, Any]:
        """创建订阅。

        POST {base_url}/v1/billing/subscriptions
        - plan_id: 订阅计划 ID（STARTER_MONTHLY 或 PRO_MONTHLY）
        - subscriber_email: 订阅者邮箱

        返回 {subscription_id, approve_url, plan_id, status}；
        并将订阅详情写入 company/orders/subscriptions/{subscription_id}.json。

        Raises:
            PayPalError: 创建失败（无效 plan_id / API 错误 / 缺邮箱）
        """
        self._ensure_credentials()

        # 校验 plan_id（接受别名如 STARTER_MONTHLY，也接受 PayPal plan_id 字符串）
        plan_def = SUBSCRIPTION_PLANS.get(plan_id)
        if plan_def is None:
            # 允许直接传入 PayPal plan_id（如 P-STARTER-MONTHLY）
            for alias, definition in SUBSCRIPTION_PLANS.items():
                if definition.get("plan_id") == plan_id:
                    plan_def = definition
                    plan_id = alias
                    break
        if plan_def is None:
            raise PayPalError(
                f"无效订阅计划 plan_id={plan_id}，可选："
                f"{', '.join(SUBSCRIPTION_PLANS.keys())}"
            )

        if not subscriber_email or "@" not in subscriber_email:
            raise PayPalError("subscriber_email 非法或为空")

        token = self._get_access_token()
        # PayPal Billing API 请求体
        body_dict = {
            "plan_id": plan_def["plan_id"],
            "subscriber": {
                "email_address": subscriber_email,
            },
            "application_context": {
                "brand_name": "AutoCorp",
                "locale": "en-US",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {
                    "payer_selected": "PAYPAL",
                    "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED",
                },
            },
        }
        body = json.dumps(body_dict).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            # PayPal Billing API 推荐：返回完整资源
            "PayPal-Request-Id": f"autocorp-sub-{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        }

        data = self._request("POST", "/v1/billing/subscriptions", headers=headers, body=body)
        subscription_id = data.get("id")
        if not subscription_id:
            raise PayPalError(f"PayPal 未返回 subscription id：{data}")

        # 从 links 数组提取 approve 链接（用户跳转支付）
        approve_url = ""
        for link in data.get("links", []) or []:
            if link.get("rel") == "approve":
                approve_url = link.get("href", "")
                break

        status = data.get("status", "APPROVAL_PENDING")
        result = {
            "subscription_id": subscription_id,
            "approve_url": approve_url,
            "plan_id": plan_id,
            "plan_name": plan_def["name"],
            "price": plan_def["price"],
            "currency": plan_def["currency"],
            "quota": plan_def["quota"],
            "interval": plan_def["interval"],
            "status": status,
            "subscriber_email": subscriber_email,
            "start_time": data.get("start_time", ""),
            "created_at": datetime.datetime.now().isoformat(),
            "sandbox": self.sandbox,
        }
        # 写入订阅文件
        self._write_subscription(result)
        return result

    # ------------------------------------------------------------------
    # 核心 API：查询订阅状态
    # ------------------------------------------------------------------
    def check_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """查询订阅状态。

        GET {base_url}/v1/billing/subscriptions/{subscription_id}
        status 可能值：APPROVAL_PENDING / ACTIVE / SUSPENDED / CANCELLED / EXPIRED

        返回 {subscription_id, status, plan_id, start_time, subscriber_email}。
        """
        if not subscription_id:
            raise PayPalError("subscription_id 不能为空")

        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        path = f"/v1/billing/subscriptions/{urllib.parse.quote(subscription_id)}"
        data = self._request("GET", path, headers=headers)

        # plan_id：PayPal 返回的 plan_id 字符串 → 反查本地别名（兜底用原值）
        raw_plan_id = data.get("plan_id", "")
        plan_alias = ""
        for alias, definition in SUBSCRIPTION_PLANS.items():
            if definition.get("plan_id") == raw_plan_id:
                plan_alias = alias
                break
        # 若远程未返回 plan_id，回退到本地订阅记录
        if not plan_alias:
            local = self._load_subscription(subscription_id)
            plan_alias = local.get("plan_id", "")

        subscriber = data.get("subscriber") or {}
        email = subscriber.get("email_address", "")
        if not email:
            # 回退到本地记录
            local = self._load_subscription(subscription_id)
            email = local.get("subscriber_email", "")

        return {
            "subscription_id": data.get("id", subscription_id),
            "status": data.get("status", ""),
            "plan_id": plan_alias,
            "start_time": data.get("start_time", ""),
            "subscriber_email": email,
        }

    # ------------------------------------------------------------------
    # 核心 API：激活订阅（用户支付完成后调用）
    # ------------------------------------------------------------------
    def activate_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """激活订阅（用户支付完成后调用）。

        POST {base_url}/v1/billing/subscriptions/{subscription_id}/activate
        PayPal 激活接口无响应体；本方法激活后立即查询并返回最新状态。
        返回 {subscription_id, status}。
        """
        if not subscription_id:
            raise PayPalError("subscription_id 不能为空")

        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        path = f"/v1/billing/subscriptions/{urllib.parse.quote(subscription_id)}/activate"
        # PayPal 激活接口要求空 body（POST 空 JSON）
        self._request("POST", path, headers=headers, body=b"")

        # 激活接口无响应体，立即查询最新状态
        latest = self.check_subscription(subscription_id)
        # 同步更新本地订阅记录状态
        self._update_subscription(subscription_id, {"status": latest["status"]})
        return {
            "subscription_id": latest["subscription_id"],
            "status": latest["status"],
        }

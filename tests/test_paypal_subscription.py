"""PayPalClient 订阅功能单元测试（Task 1）

mock urllib.request.urlopen 模拟 PayPal Billing API 响应，验证：
- create_subscription 返回正确结构 + 写入 subscriptions 记录文件
- create_subscription 无效 plan_id / 非法邮箱 → 抛 PayPalError
- check_subscription ACTIVE / 404 → 正确解析或抛错
- activate_subscription 调用激活接口后查询最新状态
- SUBSCRIPTION_PLANS 预定义结构完整
- 沙盒/正式切换：sandbox=True/False 影响 base_url

使用标准库 unittest，可直接 `python -m unittest tests.test_paypal_subscription` 运行。
也兼容 pytest 风格。
"""
import json
import shutil
import tempfile
import unittest
import urllib.error
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

from engine.workspace import WorkspaceManager
from engine.secrets import SecretsManager
from engine.payments.paypal import PayPalClient, PayPalError, SUBSCRIPTION_PLANS


def _make_response(payload: dict) -> MagicMock:
    """构造支持 with 语句 + read() 的假 HTTP 响应。"""
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    return resp


def _make_http_error(code: int, body: dict) -> urllib.error.HTTPError:
    """构造 HTTPError（PayPal 错误响应）。"""
    return urllib.error.HTTPError(
        url="https://api-m.sandbox.paypal.com/v1/billing/subscriptions/test",
        code=code,
        msg="Error",
        hdrs=None,  # type: ignore[arg-type]
        fp=BytesIO(json.dumps(body).encode("utf-8")),
    )


class TestPayPalSubscription(unittest.TestCase):
    """PayPalClient 订阅功能测试套件。"""

    def setUp(self) -> None:
        # 临时项目根：内含 company/ 工作区与 .secrets/ 目录
        self.tmp_project = Path(tempfile.mkdtemp(prefix="autocorp_paypal_sub_"))
        self.workspace = WorkspaceManager(root_dir=self.tmp_project / "company")
        self.workspace.initialize()
        # 写入测试用 PayPal 凭证
        self.sm = SecretsManager(workspace=self.workspace)
        self.sm.set("paypal_client_id", "test-client-id")
        self.sm.set("paypal_client_secret", "test-client-secret")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_project, ignore_errors=True)

    def _new_client(self, sandbox: bool = True) -> PayPalClient:
        """新建 PayPalClient。"""
        return PayPalClient(workspace=self.workspace, sandbox=sandbox)

    # ------------------------------------------------------------------
    # SUBSCRIPTION_PLANS 预定义结构
    # ------------------------------------------------------------------
    def test_subscription_plans_definition(self) -> None:
        """SUBSCRIPTION_PLANS 应包含 STARTER_MONTHLY 与 PRO_MONTHLY 两个计划。"""
        self.assertIn("STARTER_MONTHLY", SUBSCRIPTION_PLANS)
        self.assertIn("PRO_MONTHLY", SUBSCRIPTION_PLANS)

        required_fields = {"plan_id", "name", "price", "currency", "quota", "interval"}
        for alias, plan in SUBSCRIPTION_PLANS.items():
            for field in required_fields:
                self.assertIn(field, plan, f"计划 {alias} 缺少字段 {field}")

        # 校验 STARTER 配额与价格
        starter = SUBSCRIPTION_PLANS["STARTER_MONTHLY"]
        self.assertEqual(starter["price"], 29.00)
        self.assertEqual(starter["quota"], 50)
        self.assertEqual(starter["currency"], "USD")
        self.assertEqual(starter["interval"], "MONTH")

        # 校验 PRO 配额与价格
        pro = SUBSCRIPTION_PLANS["PRO_MONTHLY"]
        self.assertEqual(pro["price"], 79.00)
        self.assertEqual(pro["quota"], 200)
        self.assertEqual(pro["currency"], "USD")

        # plan_id 为非空字符串
        self.assertTrue(starter["plan_id"])
        self.assertTrue(pro["plan_id"])
        self.assertNotEqual(starter["plan_id"], pro["plan_id"])

    # ------------------------------------------------------------------
    # create_subscription 成功路径
    # ------------------------------------------------------------------
    def test_create_subscription_success(self) -> None:
        """create_subscription 应返回 {subscription_id, approve_url, plan_id, status} 并写文件。"""
        token_resp = _make_response({"access_token": "token-sub-abc", "expires_in": 3600})
        sub_resp = _make_response({
            "id": "I-ABC12345SUB",
            "status": "APPROVAL_PENDING",
            "plan_id": "P-STARTER-MONTHLY",
            "start_time": "2026-06-27T10:00:00Z",
            "links": [
                {"rel": "self", "href": "https://api-m.sandbox.paypal.com/v1/billing/subscriptions/I-ABC12345SUB", "method": "GET"},
                {"rel": "approve", "href": "https://www.sandbox.paypal.com/webapps/billing/subscriptions?ba_token=BA-ABC", "method": "GET"},
            ],
        })

        with patch("urllib.request.urlopen", side_effect=[token_resp, sub_resp]):
            client = self._new_client()
            result = client.create_subscription("STARTER_MONTHLY", "buyer@example.com")

        # 返回结构正确
        self.assertEqual(result["subscription_id"], "I-ABC12345SUB")
        self.assertEqual(result["status"], "APPROVAL_PENDING")
        self.assertEqual(result["plan_id"], "STARTER_MONTHLY")
        self.assertEqual(result["approve_url"], "https://www.sandbox.paypal.com/webapps/billing/subscriptions?ba_token=BA-ABC")
        self.assertEqual(result["subscriber_email"], "buyer@example.com")
        self.assertEqual(result["plan_name"], "Starter Monthly")
        self.assertEqual(result["price"], 29.00)
        self.assertEqual(result["quota"], 50)
        self.assertTrue(result["sandbox"])

        # subscriptions 记录文件已写入
        sub_path = self.workspace.root_dir / "orders" / "subscriptions" / "I-ABC12345SUB.json"
        self.assertTrue(sub_path.exists())
        with sub_path.open("r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["subscription_id"], "I-ABC12345SUB")
        self.assertEqual(saved["plan_id"], "STARTER_MONTHLY")
        self.assertEqual(saved["subscriber_email"], "buyer@example.com")

    def test_create_subscription_accepts_paypal_plan_id(self) -> None:
        """create_subscription 也应接受直接传入 PayPal plan_id 字符串（如 P-PRO-MONTHLY）。"""
        token_resp = _make_response({"access_token": "token-sub-abc"})
        sub_resp = _make_response({
            "id": "I-PRO999",
            "status": "APPROVAL_PENDING",
            "plan_id": "P-PRO-MONTHLY",
            "links": [{"rel": "approve", "href": "https://approve/I-PRO999"}],
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp, sub_resp]):
            client = self._new_client()
            result = client.create_subscription("P-PRO-MONTHLY", "pro@example.com")
        # plan_id 在返回结果中归一化为别名
        self.assertEqual(result["plan_id"], "PRO_MONTHLY")
        self.assertEqual(result["quota"], 200)

    # ------------------------------------------------------------------
    # create_subscription 无效 plan_id → PayPalError
    # ------------------------------------------------------------------
    def test_create_subscription_invalid_plan(self) -> None:
        """无效 plan_id 应抛 PayPalError，不应发起 HTTP 请求。"""
        client = self._new_client()
        with self.assertRaises(PayPalError) as ctx:
            client.create_subscription("INVALID_PLAN", "buyer@example.com")
        self.assertIn("无效订阅计划", str(ctx.exception))
        self.assertIn("STARTER_MONTHLY", str(ctx.exception))

    def test_create_subscription_invalid_email(self) -> None:
        """非法邮箱应抛 PayPalError。"""
        client = self._new_client()
        with self.assertRaises(PayPalError):
            client.create_subscription("STARTER_MONTHLY", "not-an-email")
        with self.assertRaises(PayPalError):
            client.create_subscription("STARTER_MONTHLY", "")

    def test_create_subscription_api_error_raises(self) -> None:
        """PayPal API 返回 HTTP 错误时应抛 PayPalError。"""
        token_resp = _make_response({"access_token": "token-sub-abc"})
        err = _make_http_error(422, {
            "name": "UNPROCESSABLE_ENTITY",
            "details": [{"issue": "INVALID_REQUEST"}],
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp, err]):
            client = self._new_client()
            with self.assertRaises(PayPalError) as ctx:
                client.create_subscription("STARTER_MONTHLY", "buyer@example.com")
        self.assertIn("422", str(ctx.exception))

    # ------------------------------------------------------------------
    # check_subscription 状态查询
    # ------------------------------------------------------------------
    def test_check_subscription_active(self) -> None:
        """check_subscription 应返回 ACTIVE 状态及订阅详情。"""
        token_resp = _make_response({"access_token": "token-chk-abc"})
        sub_resp = _make_response({
            "id": "I-ACTIVE01",
            "status": "ACTIVE",
            "plan_id": "P-STARTER-MONTHLY",
            "start_time": "2026-06-27T10:00:00Z",
            "subscriber": {
                "email_address": "active@example.com",
                "payer_id": "PAYER-001",
            },
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp, sub_resp]):
            client = self._new_client()
            result = client.check_subscription("I-ACTIVE01")

        self.assertEqual(result["subscription_id"], "I-ACTIVE01")
        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["plan_id"], "STARTER_MONTHLY")
        self.assertEqual(result["start_time"], "2026-06-27T10:00:00Z")
        self.assertEqual(result["subscriber_email"], "active@example.com")

    def test_check_subscription_status_variants(self) -> None:
        """check_subscription 应能解析 SUSPENDED/CANCELLED/EXPIRED/APPROVAL_PENDING 等状态。"""
        for status in ("APPROVAL_PENDING", "ACTIVE", "SUSPENDED", "CANCELLED", "EXPIRED"):
            token_resp = _make_response({"access_token": "token-chk-abc"})
            sub_resp = _make_response({
                "id": f"I-{status}",
                "status": status,
                "plan_id": "P-PRO-MONTHLY",
                "subscriber": {"email_address": f"{status.lower()}@example.com"},
            })
            with patch("urllib.request.urlopen", side_effect=[token_resp, sub_resp]):
                client = self._new_client()
                result = client.check_subscription(f"I-{status}")
            self.assertEqual(result["status"], status)
            self.assertEqual(result["plan_id"], "PRO_MONTHLY")

    def test_check_subscription_not_found(self) -> None:
        """订阅不存在（404）应抛 PayPalError。"""
        token_resp = _make_response({"access_token": "token-chk-abc"})
        err = _make_http_error(404, {"name": "RESOURCE_NOT_FOUND", "message": "Not Found"})
        with patch("urllib.request.urlopen", side_effect=[token_resp, err]):
            client = self._new_client()
            with self.assertRaises(PayPalError) as ctx:
                client.check_subscription("I-NOTEXIST")
        self.assertIn("404", str(ctx.exception))

    def test_check_subscription_empty_id_raises(self) -> None:
        """空 subscription_id 应抛 PayPalError。"""
        client = self._new_client()
        with self.assertRaises(PayPalError):
            client.check_subscription("")

    def test_check_subscription_falls_back_to_local_record(self) -> None:
        """远程响应缺少 plan_id/email 时，回退到本地 subscriptions 记录。"""
        # 预置本地订阅文件
        subs_dir = self.workspace.root_dir / "orders" / "subscriptions"
        subs_dir.mkdir(parents=True, exist_ok=True)
        local_data = {
            "subscription_id": "I-FALLBACK",
            "plan_id": "STARTER_MONTHLY",
            "subscriber_email": "fallback@example.com",
            "status": "APPROVAL_PENDING",
        }
        with (subs_dir / "I-FALLBACK.json").open("w", encoding="utf-8") as f:
            json.dump(local_data, f)

        token_resp = _make_response({"access_token": "token-chk-abc"})
        # 远程响应未返回 plan_id 与 subscriber
        sub_resp = _make_response({"id": "I-FALLBACK", "status": "ACTIVE"})
        with patch("urllib.request.urlopen", side_effect=[token_resp, sub_resp]):
            client = self._new_client()
            result = client.check_subscription("I-FALLBACK")
        self.assertEqual(result["status"], "ACTIVE")
        self.assertEqual(result["plan_id"], "STARTER_MONTHLY")
        self.assertEqual(result["subscriber_email"], "fallback@example.com")

    # ------------------------------------------------------------------
    # activate_subscription
    # ------------------------------------------------------------------
    def test_activate_subscription_returns_active_status(self) -> None:
        """activate_subscription 调用激活接口后应立即查询并返回最新状态。"""
        # 预置本地订阅文件（激活后用于本地状态同步）
        subs_dir = self.workspace.root_dir / "orders" / "subscriptions"
        subs_dir.mkdir(parents=True, exist_ok=True)
        with (subs_dir / "I-ACT.json").open("w", encoding="utf-8") as f:
            json.dump({"subscription_id": "I-ACT", "status": "APPROVAL_PENDING",
                       "plan_id": "STARTER_MONTHLY", "subscriber_email": "x@example.com"}, f)

        token_resp = _make_response({"access_token": "token-act"})
        activate_resp = _make_response({})  # 激活接口无响应体
        check_resp = _make_response({
            "id": "I-ACT",
            "status": "ACTIVE",
            "plan_id": "P-STARTER-MONTHLY",
            "subscriber": {"email_address": "x@example.com"},
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp, activate_resp, check_resp]):
            client = self._new_client()
            result = client.activate_subscription("I-ACT")

        self.assertEqual(result["subscription_id"], "I-ACT")
        self.assertEqual(result["status"], "ACTIVE")

        # 本地订阅文件已同步状态
        with (subs_dir / "I-ACT.json").open("r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["status"], "ACTIVE")

    def test_activate_subscription_empty_id_raises(self) -> None:
        """空 subscription_id 应抛 PayPalError。"""
        client = self._new_client()
        with self.assertRaises(PayPalError):
            client.activate_subscription("")

    # ------------------------------------------------------------------
    # 沙盒/正式切换
    # ------------------------------------------------------------------
    def test_sandbox_live_switch(self) -> None:
        """sandbox=True 用沙盒端点，sandbox=False 用正式端点。"""
        sandbox_client = self._new_client(sandbox=True)
        self.assertTrue(sandbox_client.sandbox)
        self.assertEqual(sandbox_client.base_url, PayPalClient.SANDBOX_BASE)

        live_client = self._new_client(sandbox=False)
        self.assertFalse(live_client.sandbox)
        self.assertEqual(live_client.base_url, PayPalClient.LIVE_BASE)

        # 两种模式的 base_url 不同
        self.assertNotEqual(sandbox_client.base_url, live_client.base_url)

    def test_subscription_uses_base_url(self) -> None:
        """订阅请求应基于 base_url 拼接（沙盒模式下访问 sandbox 域）。"""
        token_resp = _make_response({"access_token": "token-sub-abc"})
        sub_resp = _make_response({
            "id": "I-URLTEST",
            "status": "APPROVAL_PENDING",
            "plan_id": "P-STARTER-MONTHLY",
            "links": [{"rel": "approve", "href": "https://approve/I-URLTEST"}],
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp, sub_resp]) as mock_open:
            client = self._new_client(sandbox=True)
            client.create_subscription("STARTER_MONTHLY", "buyer@example.com")
            # 第二次调用（创建订阅）的 URL 应指向沙盒 /v1/billing/subscriptions
            second_call_url = mock_open.call_args_list[1].args[0].full_url
            self.assertIn("sandbox.paypal.com", second_call_url)
            self.assertIn("/v1/billing/subscriptions", second_call_url)


if __name__ == "__main__":
    unittest.main()

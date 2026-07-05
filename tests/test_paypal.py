"""PayPalClient 单元测试

mock urllib.request.urlopen 模拟 PayPal API 响应，验证：
- create_order 返回正确结构 + 写入 pending 订单文件
- capture_order COMPLETED 时入真实账本（Ledger.income_real）
- 订单文件正确移动 pending → paid
- 缺少 secrets 时给出清晰错误
- check_order 返回正确结构
- access_token 缓存（同一实例多次调用只取一次 token）

使用标准库 unittest，可直接 `python -m unittest tests.test_paypal` 运行。
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
from engine.ledger import Ledger
from engine.payments.paypal import PayPalClient, PayPalError


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
        url="https://api-m.sandbox.paypal.com/test",
        code=code,
        msg="Error",
        hdrs=None,  # type: ignore[arg-type]
        fp=BytesIO(json.dumps(body).encode("utf-8")),
    )


class TestPayPalClient(unittest.TestCase):
    """PayPalClient 测试套件。"""

    def setUp(self) -> None:
        # 临时项目根：内含 company/ 工作区与 .secrets/ 目录
        self.tmp_project = Path(tempfile.mkdtemp(prefix="autocorp_paypal_"))
        self.workspace = WorkspaceManager(root_dir=self.tmp_project / "company")
        self.workspace.initialize()
        # 写入测试用 PayPal 凭证
        self.sm = SecretsManager(workspace=self.workspace)
        self.sm.set("paypal_client_id", "test-client-id")
        self.sm.set("paypal_client_secret", "test-client-secret")
        # 初始化账本（income_real 需要）
        self.ledger = Ledger(self.workspace)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_project, ignore_errors=True)

    def _new_client(self) -> PayPalClient:
        """新建 PayPalClient（沙箱）。"""
        return PayPalClient(workspace=self.workspace, sandbox=True)

    # ------------------------------------------------------------------
    # 凭证缺失 → 清晰错误
    # ------------------------------------------------------------------
    def test_missing_client_id_raises_clear_error(self) -> None:
        """未配置 paypal_client_id 时应抛 PayPalError 并给出设置提示。"""
        # 删除 client_id
        self.sm.delete("paypal_client_id")
        client = PayPalClient(workspace=self.workspace)
        with self.assertRaises(PayPalError) as ctx:
            client.create_order(100.0)
        self.assertIn("paypal_client_id", str(ctx.exception))
        self.assertIn("secrets set", str(ctx.exception))

    def test_missing_client_secret_raises_clear_error(self) -> None:
        """未配置 paypal_client_secret 时应抛 PayPalError。"""
        self.sm.delete("paypal_client_secret")
        client = PayPalClient(workspace=self.workspace)
        with self.assertRaises(PayPalError) as ctx:
            client.create_order(100.0)
        self.assertIn("paypal_client_secret", str(ctx.exception))

    def test_missing_credentials_does_not_leak_secret(self) -> None:
        """错误信息中不应出现已配置的另一个凭证明文。"""
        # 仅保留 client_id，删除 secret
        self.sm.delete("paypal_client_secret")
        client = PayPalClient(workspace=self.workspace)
        with self.assertRaises(PayPalError) as ctx:
            client.create_order(100.0)
        # client_id 明文不应出现在错误信息
        self.assertNotIn("test-client-id", str(ctx.exception))

    # ------------------------------------------------------------------
    # create_order 返回正确结构 + 写入 pending 文件
    # ------------------------------------------------------------------
    def test_create_order_returns_correct_structure(self) -> None:
        """create_order 应返回 {order_id, approve_url, status} 并写入 pending 文件。"""
        token_resp = _make_response({"access_token": "token-abc", "expires_in": 3600})
        order_resp = _make_response({
            "id": "ORDER-123",
            "status": "CREATED",
            "links": [
                {"rel": "self", "href": "https://api-m.sandbox.paypal.com/v2/checkout/orders/ORDER-123", "method": "GET"},
                {"rel": "approve", "href": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123", "method": "GET"},
            ],
        })

        with patch("urllib.request.urlopen", side_effect=[token_resp, order_resp]):
            client = self._new_client()
            result = client.create_order(99.50, "USD", "测试商品")

        # 返回结构正确
        self.assertEqual(result["order_id"], "ORDER-123")
        self.assertEqual(result["status"], "CREATED")
        self.assertEqual(result["approve_url"], "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-123")
        self.assertEqual(result["amount"], "99.50")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["description"], "测试商品")
        self.assertTrue(result["sandbox"])

        # pending 订单文件已写入
        pending_path = self.workspace.root_dir / "orders" / "pending" / "ORDER-123.json"
        self.assertTrue(pending_path.exists())
        with pending_path.open("r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["order_id"], "ORDER-123")
        self.assertEqual(saved["amount"], "99.50")

    def test_create_order_invalid_amount_raises(self) -> None:
        """非正金额应抛 PayPalError。"""
        client = self._new_client()
        with self.assertRaises(PayPalError):
            client.create_order(0)
        with self.assertRaises(PayPalError):
            client.create_order(-10)

    def test_create_order_api_error_raises_paypal_error(self) -> None:
        """PayPal API 返回 HTTP 错误时应抛 PayPalError。"""
        token_resp = _make_response({"access_token": "token-abc"})
        err = _make_http_error(401, {"error": "invalid_token", "error_description": "AUTHENTICATION_FAILURE"})
        with patch("urllib.request.urlopen", side_effect=[token_resp, err]):
            client = self._new_client()
            with self.assertRaises(PayPalError) as ctx:
                client.create_order(50.0)
        self.assertIn("401", str(ctx.exception))

    # ------------------------------------------------------------------
    # capture_order COMPLETED → 入真实账本
    # ------------------------------------------------------------------
    def test_capture_order_completed_books_to_ledger(self) -> None:
        """capture_order 返回 COMPLETED 时应调用 Ledger.income_real 入账。"""
        # 先创建订单（写入 pending 文件）
        token_resp = _make_response({"access_token": "token-abc"})
        order_resp = _make_response({
            "id": "ORDER-PAY-1",
            "status": "CREATED",
            "links": [{"rel": "approve", "href": "https://approve/ORDER-PAY-1"}],
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp, order_resp]):
            client = self._new_client()
            client.create_order(150.0, "USD", "Pro 订阅")

        # 捕获付款（新 client，token 重新获取）
        token_resp2 = _make_response({"access_token": "token-xyz"})
        capture_resp = _make_response({
            "id": "ORDER-PAY-1",
            "status": "COMPLETED",
            "purchase_units": [{
                "payments": {
                    "captures": [{
                        "id": "CAP-987",
                        "amount": {"currency_code": "USD", "value": "150.00"},
                    }]
                }
            }],
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp2, capture_resp]):
            client2 = self._new_client()
            result = client2.capture_order("ORDER-PAY-1")

        # 返回结构正确
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["amount"], "150.00")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["transaction_id"], "CAP-987")

        # 账本已入真实收入：余额 = 10000 + 150 = 10150
        self.assertEqual(self.ledger.balance(), 10150.0)
        txns = self.ledger.list_transactions()
        self.assertEqual(len(txns), 1)
        tx = txns[0]
        self.assertTrue(tx["is_real"])
        self.assertEqual(tx["source"], "paypal")
        self.assertEqual(tx["tx_ref"], "ORDER-PAY-1")
        self.assertEqual(tx["amount"], 150.0)
        self.assertEqual(tx["description"], "Pro 订阅")

    # ------------------------------------------------------------------
    # 订单文件正确移动 pending → paid
    # ------------------------------------------------------------------
    def test_capture_order_moves_file_pending_to_paid(self) -> None:
        """capture 成功后订单文件应从 pending/ 移至 paid/。"""
        # 预置 pending 订单文件
        pending_dir = self.workspace.root_dir / "orders" / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        order_data = {
            "order_id": "ORDER-MOVE-1",
            "approve_url": "https://approve/ORDER-MOVE-1",
            "status": "CREATED",
            "amount": "200.00",
            "currency": "USD",
            "description": "移动测试",
        }
        pending_path = pending_dir / "ORDER-MOVE-1.json"
        with pending_path.open("w", encoding="utf-8") as f:
            json.dump(order_data, f)

        token_resp = _make_response({"access_token": "token-abc"})
        capture_resp = _make_response({
            "id": "ORDER-MOVE-1",
            "status": "COMPLETED",
            "purchase_units": [{
                "payments": {"captures": [{"id": "CAP-1", "amount": {"currency_code": "USD", "value": "200.00"}}]}
            }],
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp, capture_resp]):
            client = self._new_client()
            client.capture_order("ORDER-MOVE-1")

        # pending 文件已消失
        self.assertFalse(pending_path.exists())
        # paid 文件已存在
        paid_path = self.workspace.root_dir / "orders" / "paid" / "ORDER-MOVE-1.json"
        self.assertTrue(paid_path.exists())

    def test_capture_order_uses_pending_amount_when_capture_omits_amount(self) -> None:
        """capture 响应未含金额时，应回退到 pending 订单文件中的金额。"""
        # 预置 pending 订单文件
        pending_dir = self.workspace.root_dir / "orders" / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        order_data = {
            "order_id": "ORDER-FALLBACK-1",
            "amount": "88.00",
            "currency": "USD",
            "description": "金额兜底",
        }
        with (pending_dir / "ORDER-FALLBACK-1.json").open("w", encoding="utf-8") as f:
            json.dump(order_data, f)

        token_resp = _make_response({"access_token": "token-abc"})
        # capture 响应无 purchase_units（异常但 status=COMPLETED）
        capture_resp = _make_response({"id": "ORDER-FALLBACK-1", "status": "COMPLETED"})
        with patch("urllib.request.urlopen", side_effect=[token_resp, capture_resp]):
            client = self._new_client()
            result = client.capture_order("ORDER-FALLBACK-1")

        self.assertEqual(result["amount"], "88.00")
        # 入账金额 88
        self.assertEqual(self.ledger.balance(), 10088.0)

    def test_capture_order_non_completed_raises(self) -> None:
        """capture 返回非 COMPLETED 状态应抛 PayPalError，不入账。"""
        token_resp = _make_response({"access_token": "token-abc"})
        capture_resp = _make_response({"id": "ORDER-PEND", "status": "PENDING"})
        with patch("urllib.request.urlopen", side_effect=[token_resp, capture_resp]):
            client = self._new_client()
            with self.assertRaises(PayPalError) as ctx:
                client.capture_order("ORDER-PEND")
        self.assertIn("PENDING", str(ctx.exception))
        # 未入账
        self.assertEqual(self.ledger.balance(), 10000.0)
        self.assertEqual(self.ledger.list_transactions(), [])

    def test_capture_empty_order_id_raises(self) -> None:
        """空 order_id 应抛 PayPalError。"""
        client = self._new_client()
        with self.assertRaises(PayPalError):
            client.capture_order("")

    # ------------------------------------------------------------------
    # check_order 返回正确结构
    # ------------------------------------------------------------------
    def test_check_order_returns_correct_structure(self) -> None:
        """check_order 应返回 {status, amount, payer_info}。"""
        token_resp = _make_response({"access_token": "token-abc"})
        order_resp = _make_response({
            "id": "ORDER-CHK-1",
            "status": "APPROVED",
            "purchase_units": [{
                "amount": {"currency_code": "USD", "value": "75.00"}
            }],
            "payer": {
                "payer_id": "PAYER-XYZ",
                "email_address": "buyer@example.com",
                "name": {"given_name": "San", "surname": "Zhang"},
            },
        })
        with patch("urllib.request.urlopen", side_effect=[token_resp, order_resp]):
            client = self._new_client()
            result = client.check_order("ORDER-CHK-1")

        self.assertEqual(result["order_id"], "ORDER-CHK-1")
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["amount"], "75.00")
        self.assertEqual(result["currency"], "USD")
        self.assertEqual(result["payer_info"]["payer_id"], "PAYER-XYZ")
        self.assertEqual(result["payer_info"]["email"], "buyer@example.com")
        self.assertEqual(result["payer_info"]["name"], "San Zhang")

    # ------------------------------------------------------------------
    # access_token 缓存：同一实例多次调用只取一次 token
    # ------------------------------------------------------------------
    def test_access_token_cached_across_calls(self) -> None:
        """同一 client 实例多次 API 调用应复用 access_token（urlopen 次数 = 1 token + N 业务）。"""
        client = self._new_client()
        # 预置 pending 文件，避免 capture 时读取失败
        pending_dir = self.workspace.root_dir / "orders" / "pending"
        pending_dir.mkdir(parents=True, exist_ok=True)
        with (pending_dir / "ORDER-CACHE-1.json").open("w", encoding="utf-8") as f:
            json.dump({"order_id": "ORDER-CACHE-1", "amount": "10.00", "currency": "USD", "description": ""}, f)

        token_resp = _make_response({"access_token": "token-cached"})
        check_resp = _make_response({"id": "ORDER-CACHE-1", "status": "APPROVED", "purchase_units": [], "payer": {}})
        capture_resp = _make_response({
            "id": "ORDER-CACHE-1",
            "status": "COMPLETED",
            "purchase_units": [{"payments": {"captures": [{"id": "C1", "amount": {"currency_code": "USD", "value": "10.00"}}]}}],
        })
        # 仅 3 次 urlopen：1 token + 1 check + 1 capture（第二次复用 token）
        with patch("urllib.request.urlopen", side_effect=[token_resp, check_resp, capture_resp]) as mock_open:
            client.check_order("ORDER-CACHE-1")
            client.capture_order("ORDER-CACHE-1")
            self.assertEqual(mock_open.call_count, 3)

    # ------------------------------------------------------------------
    # 网络错误处理
    # ------------------------------------------------------------------
    def test_network_error_raises_paypal_error(self) -> None:
        """网络层错误应转为 PayPalError 并给出网络提示。"""
        import socket
        # URLError 模拟 DNS/连接失败
        url_err = urllib.error.URLError(socket.error("getaddrinfo failed"))
        with patch("urllib.request.urlopen", side_effect=url_err):
            client = self._new_client()
            with self.assertRaises(PayPalError) as ctx:
                client._get_access_token()
        self.assertIn("网络错误", str(ctx.exception))

    # ------------------------------------------------------------------
    # 沙箱为默认环境
    # ------------------------------------------------------------------
    def test_sandbox_is_default(self) -> None:
        """默认应使用沙箱环境。"""
        client = PayPalClient(workspace=self.workspace)
        self.assertTrue(client.sandbox)
        self.assertEqual(client.base_url, PayPalClient.SANDBOX_BASE)

    def test_live_mode_uses_live_base(self) -> None:
        """sandbox=False 应使用正式环境端点。"""
        client = PayPalClient(workspace=self.workspace, sandbox=False)
        self.assertFalse(client.sandbox)
        self.assertEqual(client.base_url, PayPalClient.LIVE_BASE)


if __name__ == "__main__":
    unittest.main()

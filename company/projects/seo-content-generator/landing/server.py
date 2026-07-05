"""SEO Content Generator 本地预览服务器

基于 Python 标准库 http.server，无外部依赖。
连接 Landing Page 前端（landing/index.html、thank-you.html、assets/app.js）
与支付/生成后端（PaymentBridge、PayPalClient、SEO 生成流水线）。

启动：
    py landing/server.py
    （也可在项目根执行 py -m seo_generator 后由 cli 分发，但本文件可独立运行）

访问：http://127.0.0.1:8000

路由清单：
    GET  /                              返回 index.html（注入 PAYPAL_CLIENT_ID）
    GET  /index.html                    同上
    GET  /thank-you.html                返回支付成功页
    GET  /assets/<file>                 静态资源（js/css/png/jpg/svg/...）
    GET  /api/paypal/client-id          返回 {client_id} 供前端 SDK 使用
    POST /api/demo                      生成示例文章片段（前 500 字 + SEO 评分）
    POST /api/paypal/create-order       创建按篇订单（$2）
    POST /api/paypal/capture            捕获订单并添加单篇额度
    POST /api/paypal/create-subscription 创建订阅（starter/pro）
    POST /api/paypal/activate-subscription 激活订阅并添加订阅额度
    POST /api/paypal/generate-article   付费用户生成完整文章
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# 路径修正：确保能 import engine（d:\autoCompany）与 seo_generator（本项目）
# landing/ 向上 1 级 = seo-content-generator（seo_generator 包所在）
# landing/ 向上 4 级 = autoCompany（engine 包所在）
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.abspath(os.path.join(_HERE, ".."))          # seo-content-generator
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", ".."))  # d:\autoCompany
for _p in (_PROJECT_DIR, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 导入业务模块
from engine.payments.paypal import PayPalClient, PayPalError  # noqa: E402
from engine.secrets import SecretsManager  # noqa: E402
from seo_generator.content_writer import ContentWriter  # noqa: E402
from seo_generator.keyword_analyzer import KeywordAnalyzer  # noqa: E402
from seo_generator.outline_generator import OutlineGenerator  # noqa: E402
from seo_generator.payment_bridge import PaymentBridge  # noqa: E402
from seo_generator.seo_scorer import SEOScorer  # noqa: E402
from seo_generator.subscription import SubscriptionManager  # noqa: E402


# ---------------------------------------------------------------------------
# 全局业务实例（在启动时初始化）
# ---------------------------------------------------------------------------
_bridge: PaymentBridge | None = None
_keyword_analyzer: KeywordAnalyzer | None = None
_outline_generator: OutlineGenerator | None = None
_content_writer: ContentWriter | None = None
_seo_scorer: SEOScorer | None = None

# 前端 plan 标识 → 后端订阅计划 ID
_PLAN_MAP = {
    "starter": "STARTER_MONTHLY",
    "pro": "PRO_MONTHLY",
}

# 静态文件扩展名 → Content-Type
_CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".map": "application/json; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
}

# 关键词最大长度（基本输入限制）
_MAX_KEYWORD_LEN = 200


def _init_services() -> None:
    """初始化业务服务（在启动时调用一次）。"""
    global _bridge, _keyword_analyzer, _outline_generator, _content_writer, _seo_scorer
    # PaymentBridge 内部会创建 PayPalClient(沙盒) 与 SubscriptionManager，
    # 以及自己的 SEO 流水线组件。这里同时保留独立的 SEO 组件供 demo 使用。
    _bridge = PaymentBridge()
    _keyword_analyzer = KeywordAnalyzer()
    _outline_generator = OutlineGenerator()
    _content_writer = ContentWriter()
    _seo_scorer = SEOScorer()


def _get_paypal_client_id() -> str:
    """从 secrets 读取 PayPal client_id（可暴露在前端）。未配置时回退 'test'。"""
    try:
        sm = SecretsManager()
        return sm.get("paypal_client_id") or "test"
    except Exception:
        return "test"


def _read_landing_file(name: str) -> str:
    """读取 landing 目录下的文本文件。"""
    path = os.path.join(_HERE, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _resolve_user_email(order_or_sub_id: str) -> str:
    """从订单上下文或订阅记录中解析用户邮箱。

    前端在 generate-article 请求中只携带 order_id（按篇）或 subscription_id（订阅），
    不携带 email，因此需要服务端根据支付记录反查。
    """
    if not order_or_sub_id:
        return ""
    # 1. 按篇订单上下文（data/orders.json）
    ctx = _bridge._load_order_context(order_or_sub_id)
    if ctx.get("email"):
        return ctx["email"]
    # 2. PayPal 本地订阅记录（company/orders/subscriptions/*.json）
    sub = _bridge.paypal._load_subscription(order_or_sub_id)
    if sub.get("subscriber_email"):
        return sub["subscriber_email"]
    # 3. SubscriptionManager 记录（data/subscriptions.json）
    for s in _bridge.sub_manager.list_subscriptions():
        if s.get("subscription_id") == order_or_sub_id and s.get("status") == "active":
            return s.get("email", "") or ""
    return ""


class LandingHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器。"""

    # Python 3.11+ 默认 HTTP/1.0；提升到 HTTP/1.1 以支持 keep-alive
    protocol_version = "HTTP/1.1"

    # ------------------------------------------------------------------
    # 响应辅助
    # ------------------------------------------------------------------
    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status: int = 200) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, abs_path: str) -> None:
        try:
            with open(abs_path, "rb") as f:
                body = f.read()
        except OSError:
            self._send_json({"error": "Not Found"}, 404)
            return
        ext = os.path.splitext(abs_path)[1].lower()
        content_type = _CONTENT_TYPES.get(ext, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        """读取 POST body 并解析 JSON。空 body 返回 {}；非法 JSON 抛 ValueError。"""
        content_length = int(self.headers.get("Content-Length", 0) or 0)
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length)
        text = raw.decode("utf-8") if raw else ""
        if not text:
            return {}
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON body: {e}") from e
        return data if isinstance(data, dict) else {}

    # ------------------------------------------------------------------
    # GET 路由
    # ------------------------------------------------------------------
    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._serve_index()
        elif path == "/thank-you.html":
            self._serve_thank_you()
        elif path.startswith("/assets/"):
            self._serve_asset(path)
        elif path == "/api/paypal/client-id":
            self._send_json({"client_id": _get_paypal_client_id()})
        elif path == "/favicon.ico":
            self._send_json({"error": "Not Found"}, 404)
        else:
            self._send_json({"error": "Not Found"}, 404)

    def _serve_index(self) -> None:
        try:
            html = _read_landing_file("index.html")
        except OSError as e:
            self._send_json({"error": f"index.html not found: {e}"}, 500)
            return
        client_id = _get_paypal_client_id()
        # 转义，防止 client_id 破坏 JS 字符串 / HTML
        safe_id = (
            client_id
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("<", "")
            .replace(">", "")
        )
        inject = f'<script>window.PAYPAL_CLIENT_ID = "{safe_id}";</script>'
        # 注入到 <head> 之后（首次出现）
        if "<head>" in html:
            html = html.replace("<head>", "<head>\n  " + inject, 1)
        self._send_html(html)

    def _serve_thank_you(self) -> None:
        try:
            html = _read_landing_file("thank-you.html")
        except OSError as e:
            self._send_json({"error": f"thank-you.html not found: {e}"}, 500)
            return
        self._send_html(html)

    def _serve_asset(self, path: str) -> None:
        assets_dir = os.path.join(_HERE, "assets")
        relative = path[len("/assets/"):]
        # 防止路径穿越：归一化后必须仍在 assets_dir 内
        abs_path = os.path.normpath(os.path.join(assets_dir, relative))
        if not abs_path.startswith(assets_dir + os.sep) and abs_path != assets_dir:
            self._send_json({"error": "Forbidden"}, 403)
            return
        if not os.path.isfile(abs_path):
            self._send_json({"error": "Not Found"}, 404)
            return
        self._send_static(abs_path)

    # ------------------------------------------------------------------
    # POST 路由
    # ------------------------------------------------------------------
    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._read_body()
        except ValueError as e:
            self._send_json({"error": str(e)}, 400)
            return
        try:
            if path == "/api/demo":
                self._handle_demo(body)
            elif path == "/api/paypal/create-order":
                self._handle_create_order(body)
            elif path == "/api/paypal/capture":
                self._handle_capture(body)
            elif path == "/api/paypal/create-subscription":
                self._handle_create_subscription(body)
            elif path == "/api/paypal/activate-subscription":
                self._handle_activate_subscription(body)
            elif path == "/api/paypal/generate-article":
                self._handle_generate_article(body)
            else:
                self._send_json({"error": "Not Found"}, 404)
        except Exception as e:  # noqa: BLE001 - 兜底，保证返回 JSON
            self._send_json({"error": str(e)}, 500)

    # ------------------------------------------------------------------
    # API: Demo（免费示例，前 500 字 + SEO 评分）
    # ------------------------------------------------------------------
    def _handle_demo(self, body: dict) -> None:
        keyword = (body.get("keyword") or "").strip()
        lang = body.get("lang", "en")
        if not keyword:
            self._send_json({"error": "keyword is required"}, 400)
            return
        if len(keyword) > _MAX_KEYWORD_LEN:
            self._send_json({"error": "keyword too long (max 200 characters)"}, 400)
            return
        # 调用 SEO 生成流水线（使用 TemplateProvider，无需 API key）
        ka = _keyword_analyzer.analyze(keyword, lang)
        outline = _outline_generator.generate(ka, lang)
        content = _content_writer.write(outline, ka, lang)
        score = _seo_scorer.score(content, ka)
        # 截取前 500 字作为预览
        full_body = content.get("body_markdown", "") or ""
        excerpt = full_body[:500] + "..." if len(full_body) > 500 else full_body
        # seo_score 返回完整对象 {score, suggestions}，前端 extractScore / buildSuggestions 均兼容
        self._send_json({
            "body_markdown": excerpt,
            "seo_score": score,
            "word_count": content.get("word_count", 0),
            "primary_keyword": ka.get("primary_keyword", keyword),
            "title": outline.get("h1", ""),
            "meta_description": content.get("meta_description", ""),
            "keywords": ka,
            "lang": lang,
        })

    # ------------------------------------------------------------------
    # API: 创建按篇订单
    # ------------------------------------------------------------------
    def _handle_create_order(self, body: dict) -> None:
        email = body.get("email") or "guest@example.com"
        keyword = body.get("keyword") or "single-article"
        lang = body.get("lang", "en")
        try:
            result = _bridge.create_article_order(email, keyword, lang)
            self._send_json({
                "order_id": result["order_id"],
                "approve_url": result.get("approve_url", ""),
            })
        except ValueError as e:
            self._send_json({"error": str(e)}, 400)
        except PayPalError as e:
            self._send_json({"error": str(e)}, 500)

    # ------------------------------------------------------------------
    # API: 捕获订单
    # ------------------------------------------------------------------
    def _handle_capture(self, body: dict) -> None:
        order_id = body.get("order_id")
        if not order_id:
            self._send_json({"error": "order_id is required"}, 400)
            return
        try:
            result = _bridge.handle_payment_success(order_id=order_id)
            self._send_json({
                "order_id": order_id,
                "status": "captured" if result.get("success") else "failed",
                "email": result.get("email"),
                "type": result.get("type"),
            })
        except PayPalError as e:
            self._send_json({"error": str(e)}, 500)
        except Exception as e:  # noqa: BLE001
            self._send_json({"error": str(e)}, 500)

    # ------------------------------------------------------------------
    # API: 创建订阅
    # ------------------------------------------------------------------
    def _handle_create_subscription(self, body: dict) -> None:
        email = body.get("email") or "guest@example.com"
        plan = (body.get("plan") or "starter").lower()
        plan_id = _PLAN_MAP.get(plan)
        if not plan_id:
            self._send_json({"error": f"unknown plan: {plan}"}, 400)
            return
        try:
            result = _bridge.create_subscription_order(email, plan_id)
            self._send_json({
                "subscription_id": result["subscription_id"],
                "approve_url": result.get("approve_url", ""),
            })
        except ValueError as e:
            self._send_json({"error": str(e)}, 400)
        except PayPalError as e:
            self._send_json({"error": str(e)}, 500)

    # ------------------------------------------------------------------
    # API: 激活订阅
    # ------------------------------------------------------------------
    def _handle_activate_subscription(self, body: dict) -> None:
        subscription_id = body.get("subscription_id")
        if not subscription_id:
            self._send_json({"error": "subscription_id is required"}, 400)
            return
        try:
            result = _bridge.handle_payment_success(subscription_id=subscription_id)
            self._send_json({
                "subscription_id": subscription_id,
                "status": "active" if result.get("success") else "failed",
                "email": result.get("email"),
                "plan_id": result.get("plan_id"),
            })
        except PayPalError as e:
            self._send_json({"error": str(e)}, 500)
        except Exception as e:  # noqa: BLE001
            self._send_json({"error": str(e)}, 500)

    # ------------------------------------------------------------------
    # API: 付费用户生成完整文章
    # ------------------------------------------------------------------
    def _handle_generate_article(self, body: dict) -> None:
        order_id = body.get("order_id") or body.get("subscription_id")
        keyword = (body.get("keyword") or "").strip()
        lang = body.get("lang", "en")
        if not keyword:
            self._send_json({"error": "keyword is required"}, 400)
            return
        if len(keyword) > _MAX_KEYWORD_LEN:
            self._send_json({"error": "keyword too long (max 200 characters)"}, 400)
            return
        # 前端不传 email，从订单/订阅记录反查
        email = _resolve_user_email(order_id) if order_id else ""
        if not email:
            self._send_json(
                {"error": "无法确定用户身份，请重新完成支付或联系支持"},
                403,
            )
            return
        try:
            result = _bridge.generate_for_paid_user(email, keyword, lang)
        except ValueError as e:
            self._send_json({"error": str(e)}, 403)
            return
        if not result.get("success"):
            self._send_json(
                {"error": result.get("message", "额度不足")}, 403,
            )
            return
        article = result.get("article", {}) or {}
        ka = article.get("keyword_analysis", {}) or {}
        outline = article.get("outline", {}) or {}
        score = result.get("score", {}) or {}
        # 组装前端 app.js renderArticleResult / buildMarkdownFile 期望的结构
        self._send_json({
            "body_markdown": article.get("body_markdown", ""),
            "seo_score": score,
            "word_count": article.get("word_count", 0),
            "primary_keyword": ka.get("primary_keyword", keyword),
            "title": outline.get("h1", ""),
            "meta_description": article.get("meta_description", ""),
            "keywords": ka,
            "internal_links": article.get("internal_links", []),
            "lang": lang,
            "remaining": result.get("remaining", 0),
        })

    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------
    def log_message(self, format, *args) -> None:
        print(f"[landing] {self.address_string()} - {format % args}", flush=True)


def run_server(port: int = 8000, host: str = "127.0.0.1") -> None:
    """启动本地预览服务器。

    Args:
        port: 端口号，默认 8000。
        host: 监听地址，默认 127.0.0.1（仅本地访问，安全）。
    """
    _init_services()
    client_id = _get_paypal_client_id()
    server = HTTPServer((host, port), LandingHandler)
    print("=" * 56)
    print("SEO Content Generator - 本地预览服务器")
    print("=" * 56)
    print(f"访问地址: http://{host}:{port}")
    print(f"PayPal 模式: 沙盒（client_id={'已配置' if client_id != 'test' else 'test 占位'}）")
    print("按 Ctrl+C 停止")
    print("=" * 56)
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止", flush=True)
        server.server_close()


if __name__ == "__main__":
    run_server()

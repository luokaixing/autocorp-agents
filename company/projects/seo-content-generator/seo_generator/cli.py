"""CLI 入口

基于 Click 提供 6 个命令：

免费/分析命令：
    py -m seo_generator generate --keyword "email marketing" --lang en --output article.md
    py -m seo_generator analyze --keyword "email marketing"

订阅/付费命令（沙盒模式，需配置 PayPal 凭证）：
    py -m seo_generator subscribe --email user@example.com --plan STARTER_MONTHLY
    py -m seo_generator generate-paid --email user@example.com --keyword "email marketing" --output article.md
    py -m seo_generator quota --email user@example.com

预览服务器：
    py -m seo_generator landing --port 8000

generate 命令完整流程：分析关键词 → 生成大纲 → 写内容 → SEO 评分 → 输出 Markdown 文件。
输出文件含 YAML frontmatter（title, description, keywords, score）。

subscribe / generate-paid / quota 命令通过 PaymentBridge 与 SubscriptionManager
实现付费流程：创建订阅订单 → 支付 → 扣减额度 → 生成文章。所有 PayPal 调用默认走沙盒模式。
"""
from __future__ import annotations

import sys
from pathlib import Path

import click

from . import __version__
from .content_writer import ContentWriter
from .keyword_analyzer import KeywordAnalyzer
from .llm_provider import LLMProvider, get_provider
from .outline_generator import OutlineGenerator
from .payment_bridge import PaymentBridge
from .seo_scorer import SEOScorer
from .subscription import SUBSCRIPTION_PLANS, SubscriptionManager


@click.group()
@click.version_option(version=__version__, prog_name="seo-generator")
def cli() -> None:
    """SEO Content Generator - SEO 内容自动化生成器。"""


@cli.command()
@click.option("--keyword", "-k", required=True, help="种子关键词，例如 'email marketing'。")
@click.option("--lang", "-l", default="en", show_default=True,
              help="目标语言：en（英文）/ zh（中文）。")
@click.option("--audience", "-a", default="general", show_default=True,
              help="目标受众描述（如 'small business owners'）。")
@click.option("--output", "-o", default=None,
              help="输出 Markdown 文件路径；未指定时打印到 stdout。")
@click.option("--provider", "-p", default="template", show_default=True,
              type=click.Choice(["template", "openai"]),
              help="LLM 提供方：template（兜底，无需 API）/ openai（需配置）。")
def generate(keyword: str, lang: str, audience: str, output: str,
             provider: str) -> None:
    """生成完整 SEO 文章（关键词分析→大纲→正文→评分→输出）。"""
    llm_provider = get_provider(provider)

    click.echo(f"[1/4] 分析关键词：{keyword} (lang={lang}) ...")
    analyzer = KeywordAnalyzer(provider=llm_provider)
    analysis = analyzer.analyze(keyword, language=lang)
    _echo_analysis(analysis)

    click.echo("[2/4] 生成大纲 ...")
    outliner = OutlineGenerator(provider=llm_provider)
    outline = outliner.generate(analysis, language=lang)
    click.echo(f"  H1: {outline.get('h1', '')}")
    click.echo(f"  章节数：{len(outline.get('sections', []))}")

    click.echo("[3/4] 撰写正文 ...")
    writer = ContentWriter(provider=llm_provider)
    content = writer.write(outline, analysis, language=lang)
    click.echo(f"  字数：{content.get('word_count', 0)} | 内链：{len(content.get('internal_links', []))}")

    click.echo("[4/4] SEO 评分 ...")
    scorer = SEOScorer()
    result = scorer.score(content, analysis)
    score = result["score"]
    click.echo(f"  SEO 评分：{score}/100")
    for sug in result.get("suggestions", []):
        click.echo(f"    - {sug}")

    # 组装最终 Markdown（含 frontmatter）
    markdown = build_markdown_document(analysis, outline, content, result, audience)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        click.echo(f"\n已输出：{out_path.resolve()}")
    else:
        click.echo(markdown)


@cli.command()
@click.option("--keyword", "-k", required=True, help="种子关键词。")
@click.option("--lang", "-l", default="en", show_default=True, help="目标语言：en / zh。")
@click.option("--provider", "-p", default="template", show_default=True,
              type=click.Choice(["template", "openai"]),
              help="LLM 提供方。")
def analyze(keyword: str, lang: str, provider: str) -> None:
    """仅输出关键词分析结果。"""
    llm_provider = get_provider(provider)
    analyzer = KeywordAnalyzer(provider=llm_provider)
    analysis = analyzer.analyze(keyword, language=lang)
    _echo_analysis(analysis)


# =============================================================================
# 订阅 / 付费 / 额度 / 预览服务器命令
# =============================================================================

@cli.command(name="subscribe")
@click.option("--email", required=True, help="订阅用户邮箱。")
@click.option("--plan", "plan_id", required=True,
              type=click.Choice(["STARTER_MONTHLY", "PRO_MONTHLY"]),
              help="订阅计划：STARTER_MONTHLY ($29/月, 50篇) / PRO_MONTHLY ($79/月, 200篇)。")
def subscribe(email: str, plan_id: str) -> None:
    """创建 PayPal 订阅订单，返回 approve_url 供用户支付。

    默认走沙盒模式。需在 .secrets/secrets.json 配置 paypal_client_id /
    paypal_client_secret（沙盒凭证）。支付完成后，订阅额度会自动添加。
    """
    # 延迟导入 PayPalError：避免模块加载时硬依赖 engine 路径
    try:
        from engine.payments.paypal import PayPalError
    except ImportError:  # engine 路径未配置时兜底
        PayPalError = type("PayPalError", (Exception,), {})  # type: ignore

    click.echo(f"正在为 {email} 创建 {plan_id} 订阅订单（沙盒模式）...")
    plan = SUBSCRIPTION_PLANS.get(plan_id, {})
    click.echo(f"  套餐：{plan.get('name', plan_id)} | "
               f"价格：{plan.get('price', '?')} {plan.get('currency', 'USD')} | "
               f"额度：{plan.get('quota', '?')} 篇")

    bridge = PaymentBridge()
    try:
        result = bridge.create_subscription_order(email, plan_id)
    except ValueError as e:
        click.echo(f"参数错误：{e}", err=True)
        sys.exit(1)
    except PayPalError as e:
        click.echo(f"PayPal 错误：{e}", err=True)
        click.echo("提示：请确认已配置 PayPal 沙盒凭证（.secrets/secrets.json 中的 "
                   "paypal_client_id 与 paypal_client_secret）", err=True)
        sys.exit(1)

    click.echo("")
    click.echo("订阅订单已创建")
    click.echo(f"  订阅 ID：{result.get('subscription_id', '')}")
    click.echo(f"  套餐：{result.get('plan_id', plan_id)}")
    click.echo(f"  支付链接：{result.get('approve_url', '')}")
    click.echo("")
    click.echo("请在浏览器打开 approve_url 完成支付，支付完成后运行：")
    click.echo(f"  py -m seo_generator activate --subscription-id "
               f"{result.get('subscription_id', '<id>')}")


@cli.command(name="generate-paid")
@click.option("--email", required=True, help="付费用户邮箱。")
@click.option("--keyword", "-k", required=True, help="种子关键词，例如 'email marketing'。")
@click.option("--lang", "-l", default="en", show_default=True,
              help="目标语言：en（英文）/ zh（中文）。")
@click.option("--audience", "-a", default="general", show_default=True,
              help="目标受众描述。")
@click.option("--output", "-o", default=None,
              help="输出 Markdown 文件路径；未指定时打印到 stdout。")
def generate_paid(email: str, keyword: str, lang: str, audience: str,
                  output: str) -> None:
    """付费用户生成文章（校验额度后生成）。

    流程：校验并扣减额度 → 关键词分析 → 大纲 → 正文 → SEO 评分 → 输出。
    额度不足时退出码 1。需先通过 subscribe 命令订阅或按篇支付获得额度。
    """
    click.echo(f"正在为 {email} 生成文章（关键词：{keyword}, lang={lang}）...")

    bridge = PaymentBridge()
    try:
        result = bridge.generate_for_paid_user(email, keyword, lang)
    except ValueError as e:
        # 无有效订阅
        click.echo(f"错误：{e}", err=True)
        click.echo("提示：请先订阅以获得生成额度：", err=True)
        click.echo("  py -m seo_generator subscribe --email <email> --plan STARTER_MONTHLY",
                   err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"生成失败：{e}", err=True)
        sys.exit(1)

    if not result.get("success"):
        # 额度不足
        click.echo(f"额度不足：{result.get('message', '额度已耗尽')}", err=True)
        click.echo("提示：请续费或订阅以获得更多额度：", err=True)
        click.echo("  py -m seo_generator subscribe --email <email> --plan STARTER_MONTHLY",
                   err=True)
        sys.exit(1)

    article = result.get("article", {})
    score_result = result.get("score", {})
    remaining = result.get("remaining", 0)
    score = score_result.get("score", 0) if isinstance(score_result, dict) else 0

    click.echo(f"  SEO 评分：{score}/100")
    click.echo(f"  字数：{article.get('word_count', 0)} | "
               f"内链：{len(article.get('internal_links', []))}")
    click.echo(f"  剩余额度：{remaining}")

    # 组装 Markdown（复用 generate 命令的文档构建逻辑）
    markdown = build_markdown_document(
        article.get("keyword_analysis", {}),
        article.get("outline", {}),
        article,
        score_result if isinstance(score_result, dict) else {"score": score},
        audience,
    )

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown, encoding="utf-8")
        click.echo(f"\n已输出：{out_path.resolve()}")
    else:
        click.echo("")
        click.echo(markdown)


@cli.command(name="quota")
@click.option("--email", required=True, help="查询用户邮箱。")
def quota(email: str) -> None:
    """查询用户剩余额度。

    输出：套餐 / 总额度 / 已用 / 剩余 / 到期时间 / 状态。
    无订阅时输出额度 0。
    """
    mgr = SubscriptionManager()
    info = mgr.check_quota(email)

    plan_id = info.get("plan_id")
    if not plan_id:
        click.echo(f"用户 {email} 无有效订阅")
        click.echo("  套餐：无")
        click.echo("  总额度：0 | 已用：0 | 剩余：0")
        click.echo("")
        click.echo("提示：请先订阅以获得生成额度：")
        click.echo("  py -m seo_generator subscribe --email <email> --plan STARTER_MONTHLY")
        return

    plan = SUBSCRIPTION_PLANS.get(plan_id, {})
    plan_name = plan.get("name", plan_id)
    quota_total = info.get("quota", 0)
    used = info.get("used", 0)
    remaining = info.get("remaining", 0)
    expires_at = info.get("expires_at", "未知")
    status = info.get("status", "未知")

    click.echo(f"用户 {email} 额度查询")
    click.echo(f"  套餐：{plan_name}（{plan_id}）")
    click.echo(f"  总额度：{quota_total} | 已用：{used} | 剩余：{remaining}")
    click.echo(f"  到期时间：{expires_at}")
    click.echo(f"  状态：{status}")


@cli.command(name="landing")
@click.option("--port", "-p", default=8000, show_default=True, type=int,
              help="监听端口。")
@click.option("--host", "-h", default="127.0.0.1", show_default=True,
              help="绑定地址（默认仅本机访问）。")
def landing(port: int, host: str) -> None:
    """启动本地预览服务器。

    提供 landing 页面静态文件服务与 /api/demo 端点。
    阻塞运行，按 Ctrl+C 停止。
    """
    try:
        # 延迟导入：仅在调用时加载服务器模块
        from landing.server import run_server
    except ImportError as e:
        click.echo(f"无法加载 landing 服务器模块：{e}", err=True)
        click.echo("提示：请确保在项目根目录（seo-content-generator/）下运行此命令",
                   err=True)
        sys.exit(1)

    try:
        run_server(port=port, host=host)
    except OSError as e:
        click.echo(f"服务器启动失败：{e}", err=True)
        click.echo(f"提示：端口 {port} 可能被占用，请尝试其他端口（--port 8001）",
                   err=True)
        sys.exit(1)


# =============================================================================
# 辅助函数
# =============================================================================

def build_markdown_document(analysis: dict, outline: dict, content: dict,
                            score_result: dict, audience: str) -> str:
    """组装最终 Markdown 文档（含 YAML frontmatter）。

    Args:
        analysis: 关键词分析结果。
        outline: 大纲结果。
        content: 正文写作结果。
        score_result: SEO 评分结果。
        audience: 目标受众。

    Returns:
        完整 Markdown 字符串。
    """
    h1 = outline.get("h1", analysis.get("primary_keyword", "Article"))
    meta = content.get("meta_description", "")
    primary = analysis.get("primary_keyword", "")
    secondary = analysis.get("secondary_keywords", [])
    long_tail = analysis.get("long_tail", [])
    keywords = ", ".join([primary] + list(secondary)[:5])
    score = score_result.get("score", 0)
    suggestions = score_result.get("suggestions", [])

    # frontmatter（YAML）
    front_lines = [
        "---",
        f"title: {_yaml_escape(h1)}",
        f"description: {_yaml_escape(meta)}",
        f"keywords: {_yaml_escape(keywords)}",
        f"primary_keyword: {_yaml_escape(primary)}",
        f"search_intent: {_yaml_escape(analysis.get('search_intent', ''))}",
        f"audience: {_yaml_escape(audience)}",
        f"seo_score: {score}",
        f"word_count: {content.get('word_count', 0)}",
        "---",
        "",
    ]

    # 正文
    body = content.get("body_markdown", "")

    # 文末附 SEO 评分与建议（便于人工复核）
    footer_lines = [
        "",
        "---",
        "",
        "## SEO 评分报告",
        "",
        f"**综合评分：{score}/100**",
        "",
    ]
    if suggestions:
        footer_lines.append("### 优化建议")
        footer_lines.append("")
        for sug in suggestions:
            footer_lines.append(f"- {sug}")
        footer_lines.append("")

    # 关键词数据附录
    footer_lines.extend([
        "### 关键词数据",
        "",
        f"- 主关键词：{primary}",
        f"- 搜索意图：{analysis.get('search_intent', '')}",
        f"- 次要关键词：{', '.join(secondary) if secondary else 'N/A'}",
        f"- 长尾关键词（部分）：{', '.join(long_tail[:5]) if long_tail else 'N/A'}",
        "",
    ])

    return "\n".join(front_lines) + body + "\n".join(footer_lines)


def _yaml_escape(value: str) -> str:
    """简单 YAML 转义：包裹含特殊字符的值。"""
    if value is None:
        return ""
    text = str(value)
    if any(c in text for c in [":", "#", "'", '"', "\n", "{", "}", "[", "]", ","]):
        # 用双引号包裹并转义内部双引号
        return '"' + text.replace('"', '\\"') + '"'
    return text


def _echo_analysis(analysis: dict) -> None:
    """在 CLI 输出关键词分析摘要。"""
    click.echo(f"  主关键词：{analysis.get('primary_keyword', '')}")
    click.echo(f"  搜索意图：{analysis.get('search_intent', '')}")
    secondary = analysis.get("secondary_keywords", [])
    if secondary:
        click.echo(f"  次要关键词：{', '.join(secondary)}")
    long_tail = analysis.get("long_tail", [])
    if long_tail:
        click.echo(f"  长尾词（{len(long_tail)} 个）：{', '.join(long_tail[:5])} ...")


def main() -> None:
    """CLI 入口函数（支持 `python -m seo_generator` 调用）。"""
    try:
        cli()
    except Exception as e:
        click.echo(f"错误：{e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

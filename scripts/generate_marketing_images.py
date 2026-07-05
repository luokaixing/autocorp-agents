"""Fiverr gig + Gumroad 产品图生成

基于 memory 教训：text_to_image API 返回占位符，必须用 Pillow 直接绘制。
生成 6 张图：
- Fiverr gig 1（加密分析）：1 张封面 + 2 张内页
- Fiverr gig 2（AI Agent 咨询）：1 张封面 + 2 张内页
- Gumroad PDF：1 张封面 + 2 张预览

输出目录：company/knowledge/marketing/images/
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path("company/knowledge/marketing/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def find_font(size: int = 24, bold: bool = False) -> ImageFont.FreeTypeFont:
    """寻找可用字体。"""
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_gradient_bg(img: Image.Image, draw: ImageDraw.ImageDraw, color_top: tuple, color_bottom: tuple):
    """画垂直渐变背景。"""
    W, H = img.size
    for y in range(H):
        ratio = y / H
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * ratio)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * ratio)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def draw_centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, font, W: int, fill: tuple):
    """画居中文本。"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = (W - text_w) // 2
    draw.text((x, y), text, font=font, fill=fill)


# ====================================================================
# Fiverr gig 1 封面：加密市场深度分析报告
# ====================================================================
def gen_fiverr_crypto_cover():
    W, H = 1280, 768
    img = Image.new('RGB', (W, H), '#0a0e27')
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, draw, (10, 14, 39), (30, 20, 60))

    # 顶部标识带
    draw.rectangle([0, 0, W, 6], fill='#00d4aa')
    # 底部标识带
    draw.rectangle([0, H - 6, W, H], fill='#00d4aa')

    # 顶部 LOGO
    font_logo = find_font(20, bold=True)
    draw_centered_text(draw, "AUTOCORP RESEARCH DESK", 40, font_logo, W, (0, 212, 170))

    # 主标题（大号）
    font_title = find_font(58, bold=True)
    draw_centered_text(draw, "Crypto Market", 130, font_title, W, (255, 255, 255))
    draw_centered_text(draw, "Deep Analysis Report", 200, font_title, W, (255, 255, 255))

    # 副标题
    font_sub = find_font(28, bold=False)
    draw_centered_text(draw, "RWA  •  DePIN  •  AI Agent", 290, font_sub, W, (0, 212, 170))

    # 中间分隔线
    draw.line([(W // 2 - 200, 360), (W // 2 + 200, 360)], fill='#00d4aa', width=2)

    # 三大服务点
    font_feat = find_font(24, bold=True)
    features = [
        "•  1,500+ word non-marketing analysis",
        "•  On-chain TVL & fee data (DefiLlama + Dune)",
        "•  Top 10 protocol comparison tables",
        "•  Risk analysis nobody mentions",
        "•  48-hour delivery",
    ]
    y_start = 400
    for i, feat in enumerate(features):
        draw_centered_text(draw, feat, y_start + i * 40, font_feat, W, (220, 220, 220))

    # 底部价格
    font_price = find_font(36, bold=True)
    draw_centered_text(draw, "Starting at $50", H - 90, font_price, W, (255, 200, 0))

    out = OUTPUT_DIR / "fiverr_crypto_cover.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


def gen_fiverr_crypto_inner_1():
    """Fiverr gig 1 内页：服务详情"""
    W, H = 1280, 768
    img = Image.new('RGB', (W, H), '#f5f5f5')
    draw = ImageDraw.Draw(img)

    # 顶部条
    draw.rectangle([0, 0, W, 80], fill='#0a0e27')
    font_h = find_font(32, bold=True)
    draw_centered_text(draw, "What You Get", 25, font_h, W, (255, 255, 255))

    # 三栏定价
    plans = [
        {"name": "BASIC", "price": "$50", "desc": "5-page report\n1,500 words\nSingle narrative\n2-day delivery\n1 revision", "color": "#4a90e2"},
        {"name": "STANDARD", "price": "$100", "desc": "10-page report\n3,000 words\n+ On-chain data\n+ Top 10 protocols\n5-day delivery\n2 revisions", "color": "#00d4aa"},
        {"name": "PREMIUM", "price": "$200", "desc": "Everything in Standard\n+ 1h Zoom consult\n+ Custom scenarios\n7-day delivery\n3 revisions", "color": "#ff6b6b"},
    ]
    col_w = 380
    col_gap = 30
    total_w = col_w * 3 + col_gap * 2
    x_start = (W - total_w) // 2

    font_plan = find_font(28, bold=True)
    font_price = find_font(42, bold=True)
    font_desc = find_font(18, bold=False)

    for i, plan in enumerate(plans):
        x = x_start + i * (col_w + col_gap)
        y = 120
        # 卡片背景
        draw.rectangle([x, y, x + col_w, y + 480], fill='white', outline=plan["color"], width=3)
        # 顶部色带
        draw.rectangle([x, y, x + col_w, y + 60], fill=plan["color"])
        draw_centered_text(draw, plan["name"], y + 15, font_plan, W, (255, 255, 255))
        # 价格
        draw_centered_text(draw, plan["price"], y + 90, font_price, W, plan["color"])
        # 描述
        for j, line in enumerate(plan["desc"].split("\n")):
            draw_centered_text(draw, line, y + 170 + j * 35, font_desc, W, (60, 60, 60))

    out = OUTPUT_DIR / "fiverr_crypto_inner_1.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


def gen_fiverr_crypto_inner_2():
    """Fiverr gig 1 内页：可覆盖赛道"""
    W, H = 1280, 768
    img = Image.new('RGB', (W, H), '#0a0e27')
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, draw, (10, 14, 39), (50, 20, 80))

    font_title = find_font(42, bold=True)
    draw_centered_text(draw, "Narratives I Cover", 60, font_title, W, (255, 255, 255))
    draw.line([(W // 2 - 200, 115), (W // 2 + 200, 115)], fill='#00d4aa', width=2)

    narratives = [
        ("RWA", "Real World Assets", "Ondo • BUIDL • Centrifuge • Maple • MakerDAO"),
        ("DePIN", "Decentralized Physical Infrastructure", "Render • Akash • Filecoin • Helium • io.net"),
        ("AI Agent", "On-chain Autonomous Agents", "Bittensor • Ritual • CopilotKit • CrewAI"),
        ("Stablecoin Yields", "Cross-chain Yield Comparison", "Aave • Compound • MakerDAO sDAI"),
        ("L2 Ecosystems", "Rollup & Validium Comparison", "Arbitrum • Optimism • Base • Mantle"),
        ("MEV & Restaking", "Maximal Extractable Value", "Flashbots • EigenLayer • Symbiotic"),
    ]

    font_cat = find_font(26, bold=True)
    font_desc = find_font(20, bold=False)
    font_proto = find_font(16, bold=False)

    y = 160
    for code, name, protocols in narratives:
        # 序号圆圈
        draw.ellipse([100, y + 5, 145, y + 50], fill='#00d4aa', outline='#00d4aa')
        # 类别代号
        font_num = find_font(20, bold=True)
        draw.text((110, y + 12), code[0], font=font_num, fill='#0a0e27')
        # 类别名
        draw.text((170, y), code, font=font_cat, fill='#00d4aa')
        draw.text((170, y + 32), name, font=font_desc, fill=(220, 220, 220))
        # 协议列表
        draw.text((170, y + 62), protocols, font=font_proto, fill=(150, 150, 180))
        y += 95

    out = OUTPUT_DIR / "fiverr_crypto_inner_2.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


# ====================================================================
# Fiverr gig 2 封面：AI Agent 开发咨询
# ====================================================================
def gen_fiverr_agent_cover():
    W, H = 1280, 768
    img = Image.new('RGB', (W, H), '#1a1a2e')
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, draw, (26, 26, 46), (50, 30, 80))

    # 顶部底部带
    draw.rectangle([0, 0, W, 6], fill='#ff6b6b')
    draw.rectangle([0, H - 6, W, H], fill='#ff6b6b')

    font_logo = find_font(20, bold=True)
    draw_centered_text(draw, "AUTOCORP  •  AI AGENT ARCHITECT", 40, font_logo, W, (255, 107, 107))

    font_title = find_font(58, bold=True)
    draw_centered_text(draw, "AI Agent", 130, font_title, W, (255, 255, 255))
    draw_centered_text(draw, "Architecture & Consulting", 200, font_title, W, (255, 255, 255))

    font_sub = find_font(28, bold=False)
    draw_centered_text(draw, "CrewAI  •  AutoGen  •  LangGraph  •  LangChain", 290, font_sub, W, (255, 200, 100))

    draw.line([(W // 2 - 200, 360), (W // 2 + 200, 360)], fill='#ff6b6b', width=2)

    font_feat = find_font(22, bold=True)
    features = [
        "•  Production-grade architecture review",
        "•  Multi-agent orchestration (CrewAI/AutoGen)",
        "•  Custom Python reference code included",
        "•  1-hour Zoom consultation (EN/ZH)",
        "•  Real shipped systems (not theory)",
    ]
    y_start = 400
    for i, feat in enumerate(features):
        draw_centered_text(draw, feat, y_start + i * 40, font_feat, W, (220, 220, 220))

    font_price = find_font(36, bold=True)
    draw_centered_text(draw, "From $50 / 30min", H - 90, font_price, W, (255, 200, 0))

    out = OUTPUT_DIR / "fiverr_agent_cover.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


def gen_fiverr_agent_inner_1():
    """Fiverr gig 2 内页：技术栈"""
    W, H = 1280, 768
    img = Image.new('RGB', (W, H), '#1a1a2e')
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 80], fill='#ff6b6b')
    font_h = find_font(32, bold=True)
    draw_centered_text(draw, "Tech Stack I Work With Daily", 25, font_h, W, (255, 255, 255))

    frameworks = [
        ("CrewAI", "Role-based agent teams", "★★★★★", "Primary - production use"),
        ("AutoGen", "Multi-agent orchestration", "★★★★☆", "Microsoft - enterprise"),
        ("LangGraph", "Graph-based workflows", "★★★★☆", "Complex state machines"),
        ("LangChain", "Chains, tools, RAG", "★★★★★", "Foundation library"),
        ("OpenAI SDK", "Vertical agents", "★★★☆☆", "Newer, focused use"),
        ("Playwright", "Browser automation", "★★★★☆", "Web UI agents"),
    ]

    font_name = find_font(28, bold=True)
    font_desc = find_font(20, bold=False)
    font_stars = find_font(18, bold=False)
    font_note = find_font(16, bold=False)

    y = 120
    for name, desc, stars, note in frameworks:
        draw.rectangle([80, y, W - 80, y + 90], fill=(40, 40, 70), outline='#ff6b6b', width=1)
        draw.text((110, y + 15), name, font=font_name, fill='#ff6b6b')
        draw.text((110, y + 50), desc, font=font_desc, fill=(220, 220, 220))
        draw.text((W - 280, y + 15), stars, font=font_stars, fill='#ffd700')
        draw.text((W - 280, y + 50), note, font=font_note, fill=(150, 150, 180))
        y += 105

    out = OUTPUT_DIR / "fiverr_agent_inner_1.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


def gen_fiverr_agent_inner_2():
    """Fiverr gig 2 内页：交付案例"""
    W, H = 1280, 768
    img = Image.new('RGB', (W, H), '#f5f5f5')
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, W, 80], fill='#1a1a2e')
    font_h = find_font(32, bold=True)
    draw_centered_text(draw, "Production Use Cases", 25, font_h, W, (255, 255, 255))

    cases = [
        ("Content Production Pipeline", "7 agents: PM → Architect → Programmer → Tester → COO", "AutoCorp"),
        ("Crypto Market Research", "Multi-source ingestion + LLM synthesis", "AutoCorp"),
        ("Browser Automation", "Playwright + LLM for web tasks", "AutoCorp"),
        ("Newsletter Publishing", "Mirror.xyz + Paragraph integration", "AutoCorp"),
    ]

    font_title = find_font(26, bold=True)
    font_desc = find_font(20, bold=False)
    font_tag = find_font(18, bold=True)

    y = 130
    for title, desc, tag in cases:
        # 卡片
        draw.rectangle([80, y, W - 80, y + 130], fill='white', outline='#1a1a2e', width=2)
        # 标签
        draw.rectangle([W - 200, y + 10, W - 90, y + 45], fill='#00d4aa')
        draw.text((W - 195, y + 16), tag, font=font_tag, fill='#0a0e27')
        # 标题
        draw.text((110, y + 20), title, font=font_title, fill='#1a1a2e')
        # 描述
        draw.text((110, y + 65), desc, font=font_desc, fill=(60, 60, 60))
        y += 145

    # 底部 disclaimer
    font_dis = find_font(16, bold=False)
    draw_centered_text(draw, "Note: I do NOT build trading bots or hold private keys. No autonomous financial agents.", H - 60, font_dis, W, (150, 150, 150))

    out = OUTPUT_DIR / "fiverr_agent_inner_2.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


# ====================================================================
# Gumroad 产品图：PDF 报告
# ====================================================================
def gen_gumroad_cover():
    """Gumroad PDF 封面图（模拟书的封面）"""
    W, H = 1000, 1400  # 书封面比例
    img = Image.new('RGB', (W, H), '#0a0e27')
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, draw, (10, 14, 39), (40, 20, 80))

    # 顶部金条
    draw.rectangle([0, 0, W, 30], fill='#ffd700')
    # 底部金条
    draw.rectangle([0, H - 30, W, H], fill='#ffd700')

    # 标题区
    font_brand = find_font(28, bold=True)
    draw_centered_text(draw, "AUTOCORP RESEARCH DESK", 100, font_brand, W, (255, 215, 0))

    # 报告类型
    font_type = find_font(22, bold=False)
    draw_centered_text(draw, "FLAGSHIP REPORT  |  H2 2026", 150, font_type, W, (180, 180, 220))

    # 大标题
    font_t1 = find_font(76, bold=True)
    draw_centered_text(draw, "THE THREE", 280, font_t1, W, (255, 255, 255))
    draw_centered_text(draw, "CRYPTO MAINLINES", 370, font_t1, W, (255, 255, 255))

    font_t2 = find_font(48, bold=True)
    draw_centered_text(draw, "of H2 2026", 480, font_t2, W, (0, 212, 170))

    # 分隔
    draw.line([(W // 2 - 100, 570), (W // 2 + 100, 570)], fill='#ffd700', width=3)

    # 三大主题
    font_topic = find_font(36, bold=True)
    draw_centered_text(draw, "RWA", 620, font_topic, W, (100, 180, 255))
    draw_centered_text(draw, "DePIN", 680, font_topic, W, (0, 212, 170))
    draw_centered_text(draw, "AI Agent", 740, font_topic, W, (255, 107, 107))

    # 副标题
    font_sub = find_font(24, bold=False)
    draw_centered_text(draw, "Real World Assets  •  Decentralized", 830, font_sub, W, (200, 200, 220))
    draw_centered_text(draw, "Physical Infrastructure  •  Agentic Web", 870, font_sub, W, (200, 200, 220))

    # 数据点
    font_data = find_font(20, bold=False)
    draw_centered_text(draw, "•  2,500+ word deep analysis", 980, font_data, W, (220, 220, 220))
    draw_centered_text(draw, "•  Top 10 protocol comparison tables", 1020, font_data, W, (220, 220, 220))
    draw_centered_text(draw, "•  On-chain TVL & fee data", 1060, font_data, W, (220, 220, 220))
    draw_centered_text(draw, "•  Risk analysis nobody mentions", 1100, font_data, W, (220, 220, 220))
    draw_centered_text(draw, "•  30-day catalyst calendar", 1140, font_data, W, (220, 220, 220))

    # 价格
    font_price = find_font(44, bold=True)
    draw_centered_text(draw, "$12", 1240, font_price, W, (255, 215, 0))

    out = OUTPUT_DIR / "gumroad_pdf_cover.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


def gen_gumroad_preview_1():
    """Gumroad PDF 内页预览 1：协议对比表"""
    W, H = 1280, 900
    img = Image.new('RGB', (W, H), 'white')
    draw = ImageDraw.Draw(img)

    # 顶部
    draw.rectangle([0, 0, W, 70], fill='#0a0e27')
    font_h = find_font(28, bold=True)
    draw_centered_text(draw, "Inside: Top 10 RWA Protocols Compared", 20, font_h, W, (255, 215, 0))

    # 表格
    headers = ["Protocol", "Asset Class", "TVL", "Yield", "Risk"]
    rows = [
        ("Ondo Finance", "Tokenized T-Bills", "$1.2B+", "4.2-5.1%", "Reg-S/D"),
        ("BlackRock BUIDL", "Institutional T-Bills", "$2.5B+", "4.0-4.8%", "Inst-only"),
        ("Centrifuge", "Private credit", "$700M+", "5.5-9.0%", "Default"),
        ("Maple Finance", "Undercollateralized", "$600M+", "6.0-10.0%", "Counterparty"),
        ("MakerDAO", "Mixed RWA", "$4B+", "Variable", "Governance"),
        ("Chainlink", "Oracle layer", "n/a", "n/a", "Centralization"),
    ]

    col_x = [80, 320, 580, 780, 980, 1140]
    col_w = [220, 240, 180, 180, 140, 100]
    row_h = 60
    y_start = 110

    font_th = find_font(18, bold=True)
    font_td = find_font(16, bold=False)

    # 表头
    draw.rectangle([80, y_start, W - 80, y_start + row_h], fill='#0a0e27')
    for i, h in enumerate(headers):
        draw.text((col_x[i] + 10, y_start + 18), h, font=font_th, fill='white')

    # 表行
    for r_idx, row in enumerate(rows):
        y = y_start + (r_idx + 1) * row_h
        bg = '#f5f5f5' if r_idx % 2 == 0 else 'white'
        draw.rectangle([80, y, W - 80, y + row_h], fill=bg, outline='#ddd')
        for i, cell in enumerate(row):
            draw.text((col_x[i] + 10, y + 18), cell, font=font_td, fill=(60, 60, 60))

    # 底部说明
    font_note = find_font(14, bold=False)
    draw.text((80, y_start + (len(rows) + 1) * row_h + 30),
              "* Data as of Q2 2026. Full report includes 10 protocols with detailed analysis.",
              font=font_note, fill=(120, 120, 120))

    out = OUTPUT_DIR / "gumroad_preview_1.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


def gen_gumroad_preview_2():
    """Gumroad PDF 内页预览 2：三大主线一图概览"""
    W, H = 1280, 900
    img = Image.new('RGB', (W, H), '#0a0e27')
    draw = ImageDraw.Draw(img)
    draw_gradient_bg(img, draw, (10, 14, 39), (30, 20, 60))

    font_title = find_font(36, bold=True)
    draw_centered_text(draw, "The Three Mainlines at a Glance", 50, font_title, W, (255, 255, 255))
    draw.line([(W // 2 - 200, 100), (W // 2 + 200, 100)], fill='#ffd700', width=2)

    # 三栏
    col_w = 380
    gap = 30
    total_w = col_w * 3 + gap * 2
    x_start = (W - total_w) // 2

    mainlines = [
        {
            "name": "RWA",
            "color": "#4a90e2",
            "driver": "TradFi on-chain",
            "proto": "Ondo • BUIDL\nCentrifuge • Maple\nMakerDAO",
            "tvl": "TVL: $9B+",
            "yield": "Yield: 4-10%",
        },
        {
            "name": "DePIN",
            "color": "#00d4aa",
            "driver": "AI compute shortage",
            "proto": "Render • Akash\nFilecoin • Helium\nio.net",
            "tvl": "Compute: 200k+ GPUs",
            "yield": "Revenue: real",
        },
        {
            "name": "AI Agent",
            "color": "#ff6b6b",
            "driver": "On-chain agents",
            "proto": "Bittensor • Ritual\nCopilotKit • CrewAI\nobra/superpowers",
            "tvl": "Stars: 19,921/week",
            "yield": "Payment: 25% by EOY",
        },
    ]

    font_name = find_font(34, bold=True)
    font_driver = find_font(18, bold=False)
    font_proto = find_font(16, bold=False)
    font_metric = find_font(14, bold=True)

    for i, ml in enumerate(mainlines):
        x = x_start + i * (col_w + gap)
        y = 140
        # 卡片
        draw.rectangle([x, y, x + col_w, y + 500], fill=(30, 30, 60), outline=ml["color"], width=3)
        # 顶部色块
        draw.rectangle([x, y, x + col_w, y + 70], fill=ml["color"])
        draw_centered_text(draw, ml["name"], x - (W - col_w) // 2 + y + 15, font_name, W, (255, 255, 255))

        # 驱动力
        draw.text((x + 20, y + 90), "Driver:", font=font_metric, fill=ml["color"])
        draw.text((x + 20, y + 115), ml["driver"], font=font_driver, fill=(220, 220, 220))

        # 代表协议
        draw.text((x + 20, y + 170), "Top Protocols:", font=font_metric, fill=ml["color"])
        for j, line in enumerate(ml["proto"].split("\n")):
            draw.text((x + 20, y + 200 + j * 28), line, font=font_proto, fill=(200, 200, 220))

        # 指标
        draw.text((x + 20, y + 350), "Key Metric:", font=font_metric, fill=ml["color"])
        draw.text((x + 20, y + 380), ml["tvl"], font=font_proto, fill=(255, 215, 0))
        draw.text((x + 20, y + 410), ml["yield"], font=font_proto, fill=(255, 215, 0))

    # 底部
    font_foot = find_font(16, bold=False)
    draw_centered_text(draw, "Full report includes protocol-by-protocol deep dives, risk analysis, and 30-day catalyst calendar", H - 60, font_foot, W, (180, 180, 200))

    out = OUTPUT_DIR / "gumroad_preview_2.jpg"
    img.save(out, "JPEG", quality=90)
    print(f"  saved: {out}")


if __name__ == "__main__":
    print("Generating Fiverr gig images (2 gigs × 3 images)...")
    gen_fiverr_crypto_cover()
    gen_fiverr_crypto_inner_1()
    gen_fiverr_crypto_inner_2()
    gen_fiverr_agent_cover()
    gen_fiverr_agent_inner_1()
    gen_fiverr_agent_inner_2()

    print("\nGenerating Gumroad product images (3 images)...")
    gen_gumroad_cover()
    gen_gumroad_preview_1()
    gen_gumroad_preview_2()

    print("\nAll 9 images generated in:", OUTPUT_DIR.resolve())

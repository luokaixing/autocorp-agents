"""
推广图生成工具 v2 - 使用 Pillow 直接绘制（不依赖失效的 text_to_image API）

用法:
    py scripts/generate_cover_image.py --mode defi-yield --output art_004-cover.jpg
    py scripts/generate_cover_image.py --mode ai-coup --output art_005-cover.jpg

支持的模板:
    defi-yield: DeFi 收益对比推广图（深色仪表盘 + APY 柱状图）
    ai-coup: AI 6月政变推广图（深色科技风 + 三大事件时间线）
"""

import argparse
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def find_font(size: int = 24, bold: bool = False) -> ImageFont.FreeTypeFont:
    """寻找可用的字体。"""
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


def draw_rounded_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill=None, outline=None, width: int = 1):
    """画圆角矩形。"""
    x1, y1, x2, y2 = xy
    if radius > min(x2 - x1, y2 - y1) // 2:
        radius = min(x2 - x1, y2 - y1) // 2

    if fill:
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        draw.pieslice([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=fill)
        draw.pieslice([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=fill)
        draw.pieslice([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=fill)
        draw.pieslice([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=fill)

    if outline:
        draw.arc([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=outline, width=width)
        draw.arc([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=outline, width=width)
        draw.arc([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=outline, width=width)
        draw.arc([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=outline, width=width)
        draw.line([x1 + radius, y1, x2 - radius, y1], fill=outline, width=width)
        draw.line([x1 + radius, y2, x2 - radius, y2], fill=outline, width=width)
        draw.line([x1, y1 + radius, x1, y2 - radius], fill=outline, width=width)
        draw.line([x2, y1 + radius, x2, y2 - radius], fill=outline, width=width)


def generate_defi_yield_cover(output_path: str):
    """生成 DeFi 收益对比推广图。
    
    设计:
    - 深色背景（藏青/深蓝渐变）
    - 顶部: 大标题 + 副标题
    - 中部: APY 对比柱状图（Aave Mantle 8.39% / Aave Mainnet 6.96% / Compound 3.27%）
    - 底部: 数据来源 + 日期
    - 装饰: 浮动的数字和网格线
    """
    W, H = 1600, 900
    img = Image.new('RGB', (W, H), '#0a0e27')
    draw = ImageDraw.Draw(img)

    for y in range(H):
        r = int(10 + (y / H) * 5)
        g = int(14 + (y / H) * 10)
        b = int(39 + (y / H) * 30)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    for y in range(100, H - 100, 60):
        draw.line([(80, y), (W - 80, y)], fill=(30, 50, 100, 30), width=1)
    for x in range(80, W - 80, 80):
        draw.line([(x, 100), (x, H - 100)], fill=(30, 50, 100, 30), width=1)

    accent_green = '#00ff88'
    accent_blue = '#00b4ff'
    accent_orange = '#ff6b35'
    text_white = '#ffffff'
    text_gray = '#8899aa'

    font_title = find_font(64, bold=True)
    font_subtitle = find_font(28)
    font_label = find_font(22)
    font_big_num = find_font(48, bold=True)
    font_small = find_font(18)
    font_tag = find_font(16)

    tag_text = "REAL-TIME DATA  |  JUNE 30, 2026"
    tag_w = draw.textlength(tag_text, font=font_tag)
    draw.text(((W - tag_w) // 2, 50), tag_text, fill=accent_blue, font=font_tag)

    title = "Where to Earn the Highest"
    title2 = "DeFi Yield Right Now"
    title_w = draw.textlength(title, font=font_title)
    draw.text(((W - title_w) // 2, 90), title, fill=text_white, font=font_title)
    title2_w = draw.textlength(title2, font=font_title)
    draw.text(((W - title2_w) // 2, 165), title2, fill=accent_green, font=font_title)

    subtitle = "Aave vs Compound  —  Live data from DefiLlama & CoinGecko"
    sub_w = draw.textlength(subtitle, font=font_subtitle)
    draw.text(((W - sub_w) // 2, 250), subtitle, fill=text_gray, font=font_subtitle)

    chart_top = 360
    chart_bottom = 700
    chart_left = 200
    chart_right = W - 200
    chart_w = chart_right - chart_left
    chart_h = chart_bottom - chart_top

    pools = [
        ("Aave USDC\nMantle", 8.39, accent_green),
        ("Aave USDC\nMainnet", 6.96, accent_blue),
        ("Compound USDC\nMainnet", 3.27, accent_orange),
        ("Morpho Blue\n(Optimized)", 5.18, '#9b59ff'),
    ]

    max_apy = 10.0
    bar_w = 120
    gap = (chart_w - bar_w * len(pools)) // (len(pools) + 1)

    for i, (label, apy, color) in enumerate(pools):
        x = chart_left + gap + i * (bar_w + gap)
        bar_h = int((apy / max_apy) * chart_h * 0.85)
        y_bottom = chart_bottom
        y_top = y_bottom - bar_h

        draw_rounded_rect(draw, [x, y_top, x + bar_w, y_bottom], 12, fill=color)

        glow = Image.new('RGBA', (bar_w + 40, bar_h + 40), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.rectangle([20, 20, bar_w + 20, bar_h + 20], fill=color)
        glow.putalpha(int(color[1:], 16) if False else 30)

        num_text = f"{apy:.2f}%"
        num_w = draw.textlength(num_text, font=font_big_num)
        draw.text((x + (bar_w - num_w) // 2, y_top - 60), num_text, fill=color, font=font_big_num)

        label_lines = label.split('\n')
        for li, line in enumerate(label_lines):
            lw = draw.textlength(line, font=font_label)
            draw.text((x + (bar_w - lw) // 2, y_bottom + 20 + li * 28), line, fill=text_white, font=font_label)

    baseline_y = chart_bottom
    draw.line([(chart_left - 30, baseline_y), (chart_right + 30, baseline_y)], fill=text_gray, width=2)

    stat_y = 760
    stat_w = (W - 200) // 3

    stats = [
        ("238", "Aave Pools Analyzed", accent_green),
        ("$37.27B", "Total DeFi TVL", accent_blue),
        ("Live Data", "Snapshot Jun 29, 2026", accent_orange),
    ]

    for i, (val, label, color) in enumerate(stats):
        x = 100 + i * stat_w
        val_w = draw.textlength(val, font=font_big_num)
        draw.text((x + (stat_w - val_w) // 2, stat_y), val, fill=color, font=font_big_num)
        label_w = draw.textlength(label, font=font_small)
        draw.text((x + (stat_w - label_w) // 2, stat_y + 55), label, fill=text_gray, font=font_small)

    footer = "AutoCorp Insights  •  Data: DefiLlama / CoinGecko  •  Verified Jun 30, 2026"
    footer_w = draw.textlength(footer, font=font_small)
    draw.text(((W - footer_w) // 2, H - 50), footer, fill=text_gray, font=font_small)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, quality=92)
    print(f"[OK] 生成完成: {output.resolve()}")
    print(f"     尺寸: {W}x{H}")
    return str(output.resolve())


def generate_ai_coup_cover(output_path: str):
    """生成 AI 6月政变推广图。
    
    设计:
    - 深色科技风背景
    - 大标题: AI's June Coup
    - 三大事件时间线（Fable 5 禁令 / SpaceX 收购 Cursor / ChatGPT 跌破 50%）
    - 底部: 72 Hours That Reshaped AI
    """
    W, H = 1600, 900
    img = Image.new('RGB', (W, H), '#050510')
    draw = ImageDraw.Draw(img)

    for y in range(H):
        r = int(5 + (y / H) * 15)
        g = int(5 + (y / H) * 5)
        b = int(16 + (y / H) * 20)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    for i in range(50):
        import random
        random.seed(i * 7)
        x = random.randint(0, W)
        y = random.randint(0, H)
        size = random.randint(1, 3)
        brightness = random.randint(40, 100)
        draw.ellipse([x, y, x + size, y + size], fill=(brightness, brightness, brightness + 20))

    accent_red = '#ff3b5c'
    accent_yellow = '#ffc048'
    accent_blue = '#00b4ff'
    text_white = '#ffffff'
    text_gray = '#667788'

    font_title = find_font(72, bold=True)
    font_subtitle = find_font(26)
    font_event = find_font(20, bold=True)
    font_event_date = find_font(16)
    font_big = find_font(42, bold=True)
    font_small = find_font(18)
    font_tag = find_font(16)

    tag_text = "72 HOURS THAT CHANGED AI FOREVER"
    tag_w = draw.textlength(tag_text, font=font_tag)
    draw.text(((W - tag_w) // 2, 45), tag_text, fill=accent_red, font=font_tag)

    title = "AI's June Coup"
    title_w = draw.textlength(title, font=font_title)
    draw.text(((W - title_w) // 2, 85), title, fill=text_white, font=font_title)

    subtitle = "Three Shots, One Week, A $200 Billion Market Redrawn"
    sub_w = draw.textlength(subtitle, font=font_subtitle)
    draw.text(((W - sub_w) // 2, 175), subtitle, fill=text_gray, font=font_subtitle)

    timeline_y = 280
    timeline_x_start = 150
    timeline_x_end = W - 150

    events = [
        ("JUN 12", "Fable 5 Shut Down", "US Gov halts Anthropic's\nmost powerful model — 72 hours\nafter launch", accent_red),
        ("JUN 16", "SpaceX Buys Cursor", "$60B all-stock deal for\nthe AI coding tool with\n7M daily devs", accent_yellow),
        ("JUN 16", "ChatGPT < 50%", "Market share drops below\n50% for the first time\nsince launch", accent_blue),
    ]

    card_w = 320
    card_h = 280
    gap = (timeline_x_end - timeline_x_start - card_w * 3) // 2

    line_y = timeline_y + 20
    draw.line([(timeline_x_start - 30, line_y), (timeline_x_end + 30, line_y)], fill='#222244', width=3)

    for i, (date, title, desc, color) in enumerate(events):
        x = timeline_x_start + i * (card_w + gap)
        y = timeline_y

        dot_x = x + card_w // 2
        dot_y = line_y
        draw.ellipse([dot_x - 10, dot_y - 10, dot_x + 10, dot_y + 10], fill=color)
        draw.ellipse([dot_x - 6, dot_y - 6, dot_x + 6, dot_y + 6], fill='#050510')

        card_top = y + 50
        draw_rounded_rect(draw, [x, card_top, x + card_w, card_top + card_h], 16, fill='#0c0c1e', outline=color, width=2)

        date_w = draw.textlength(date, font=font_event_date)
        draw.text((x + (card_w - date_w) // 2, card_top + 20), date, fill=color, font=font_event_date)

        title_w = draw.textlength(title, font=font_event)
        draw.text((x + (card_w - title_w) // 2, card_top + 50), title, fill=text_white, font=font_event)

        desc_lines = desc.split('\n')
        for li, line in enumerate(desc_lines):
            lw = draw.textlength(line, font=font_small)
            draw.text((x + (card_w - lw) // 2, card_top + 85 + li * 26), line, fill=text_gray, font=font_small)

    bottom_y = 680

    big_text = "THE ERA OF OPEN AI COMPETITION"
    big_w = draw.textlength(big_text, font=font_big)
    draw.text(((W - big_w) // 2, bottom_y), big_text, fill=text_white, font=font_big)

    big_text2 = "Is Over."
    big_w2 = draw.textlength(big_text2, font=font_big)
    draw.text(((W - big_w2) // 2, bottom_y + 50), big_text2, fill=accent_red, font=font_big)

    footer = "AutoCorp Insights  •  Deep Analysis of the AI Market Inflection Point  •  Jun 30, 2026"
    footer_w = draw.textlength(footer, font=font_small)
    draw.text(((W - footer_w) // 2, H - 50), footer, fill=text_gray, font=font_small)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, quality=92)
    print(f"[OK] 生成完成: {output.resolve()}")
    print(f"     尺寸: {W}x{H}")
    return str(output.resolve())


def main():
    parser = argparse.ArgumentParser(description='生成推广图（Pillow 绘制，不依赖失效的 text_to_image API）')
    parser.add_argument('--mode', required=True, choices=['defi-yield', 'ai-coup'],
                        help='推广图模板')
    parser.add_argument('--output', required=True, help='输出文件路径')
    args = parser.parse_args()

    if args.mode == 'defi-yield':
        generate_defi_yield_cover(args.output)
    elif args.mode == 'ai-coup':
        generate_ai_coup_cover(args.output)


if __name__ == '__main__':
    main()

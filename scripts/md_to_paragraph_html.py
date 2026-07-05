"""Convert 03-aave-protocol-v2.md to a clean HTML for copy-paste into Paragraph."""
from pathlib import Path
import markdown

MD_PATH = Path(r"d:\autoCompany\company\projects\seo-content-generator\articles\03-aave-protocol-v2.md")
HTML_PATH = Path(r"d:\autoCompany\company\projects\seo-content-generator\articles\03-aave-protocol-v2.html")

md_text = MD_PATH.read_text(encoding="utf-8")

# Convert markdown -> HTML with tables + fenced code extensions
html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "sane_lists", "toc"],
    output_format="html5",
)

# Wrap with clean article styling (Paragraph-friendly typography)
html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Aave Protocol Guide 2026 - Preview</title>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    max-width: 760px;
    margin: 40px auto;
    padding: 0 24px;
    color: #1a1a1a;
    line-height: 1.7;
    font-size: 17px;
  }}
  h1 {{ font-size: 36px; font-weight: 800; line-height: 1.2; margin: 0 0 24px; color: #111; }}
  h2 {{ font-size: 26px; font-weight: 700; margin: 40px 0 12px; color: #111; border-top: 1px solid #eee; padding-top: 24px; }}
  h3 {{ font-size: 20px; font-weight: 700; margin: 28px 0 10px; color: #222; }}
  p {{ margin: 0 0 16px; }}
  ul, ol {{ margin: 0 0 16px; padding-left: 24px; }}
  li {{ margin-bottom: 6px; }}
  strong {{ font-weight: 700; color: #000; }}
  em {{ font-style: italic; }}
  code {{
    background: #f4f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 14px;
    color: #b6509e;
    word-break: break-all;
  }}
  pre {{ background: #f4f4f6; padding: 16px; border-radius: 8px; overflow-x: auto; }}
  pre code {{ background: none; padding: 0; color: #1a1a1a; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0 24px;
    font-size: 15px;
  }}
  th, td {{
    border: 1px solid #ddd;
    padding: 10px 12px;
    text-align: left;
  }}
  th {{ background: #f8f8fa; font-weight: 700; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 36px 0; }}
  blockquote {{
    border-left: 3px solid #b6509e;
    padding: 8px 16px;
    margin: 16px 0;
    color: #555;
    background: #faf8fc;
  }}
  a {{ color: #b6509e; text-decoration: underline; }}
  /* 复制提示 */
  .copy-banner {{
    position: fixed;
    top: 0; left: 0; right: 0;
    background: #b6509e;
    color: white;
    padding: 12px;
    text-align: center;
    font-size: 14px;
    font-weight: 600;
    z-index: 1000;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  }}
  .copy-banner small {{ font-weight: 400; opacity: 0.9; }}
</style>
</head>
<body>
  <div class="copy-banner">
    📋 Ctrl+A 全选此页内容 → Ctrl+C 复制 → 到 Paragraph 编辑器 Ctrl+V 粘贴（富文本格式会保留）
    <br><small>提示：粘贴后 Paragraph 会自动渲染标题/列表/表格/代码块，无需手动调整</small>
  </div>
  <div style="margin-top: 80px;">
{html_body}
  </div>
</body>
</html>
"""

HTML_PATH.write_text(html_doc, encoding="utf-8")
print(f"HTML saved: {HTML_PATH}")
print(f"Size: {HTML_PATH.stat().st_size // 1024} KB")

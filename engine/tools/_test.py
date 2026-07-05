"""工具测试脚本"""
from engine.tools.web_searcher import search, search_summaries
from engine.tools.web_fetcher import fetch_url, fetch_markdown

print("=== 测试 1: 网页搜索 ===")
results = search("ethereum learn and earn 2026", max_results=3)
print(f"结果数: {len(results)}")
for r in results:
    title = r["title"][:60]
    print(f"- {title}")
    print(f"  URL: {r['url']}")
    print(f"  摘要: {r['snippet'][:100]}")
    print()

print("\n=== 测试 2: 网页抓取 ===")
r = fetch_url("https://paragraph.com")
print(f"状态: {r['status']}")
print(f"标题: {r['title']}")
print(f"markdown 长度: {len(r['markdown'])}")
print(f"前 300 字符:")
print(r['markdown'][:300])

print("\n=== 测试 3: 搜索摘要 ===")
summary = search_summaries("crypto airdrop 2026", max_results=2)
print(summary[:500])

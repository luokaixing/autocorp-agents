"""将 aave-promo.html 截图为 aave-promo-2026.png，再转为 jpg"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

HTML_PATH = Path(r"d:\autoCompany\company\projects\seo-content-generator\articles\aave-promo.html").resolve()
PNG_PATH = Path(r"d:\autoCompany\company\projects\seo-content-generator\articles\aave-promo-2026.png")
JPG_PATH = Path(r"d:\autoCompany\company\projects\seo-content-generator\articles\aave-promo-2026.jpg")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1200, "height": 675}, device_scale_factor=2)
        page = await context.new_page()
        await page.goto(f"file:///{HTML_PATH}")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(500)  # 让字体/渐变稳定
        await page.screenshot(path=str(PNG_PATH), full_page=False, omit_background=False)
        await browser.close()
    print(f"PNG saved: {PNG_PATH} ({PNG_PATH.stat().st_size//1024} KB)")

    # PNG -> JPG
    from PIL import Image
    img = Image.open(PNG_PATH).convert("RGB")
    img.save(JPG_PATH, "JPEG", quality=92, optimize=True)
    print(f"JPG saved: {JPG_PATH} ({JPG_PATH.stat().st_size//1024} KB)")
    print(f"Final size: {img.size}")

if __name__ == "__main__":
    asyncio.run(main())

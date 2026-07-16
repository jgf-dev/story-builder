import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
    os.makedirs("/home/jules/verification/videos", exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            record_video_dir="/home/jules/verification/videos"
        )
        page = await context.new_page()
        file_url = f"file://{os.path.abspath('dashboard.html')}"
        await page.goto(file_url)

        # Wait a bit to ensure rendering
        await page.wait_for_timeout(1000)

        # Capture screenshot
        await page.screenshot(path="/home/jules/verification/screenshots/dashboard.png")

        await context.close()
        await browser.close()
        print("Verification artifacts created.")

asyncio.run(main())

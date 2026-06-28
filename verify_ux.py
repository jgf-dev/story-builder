from playwright.sync_api import sync_playwright

def run_cuj(page):
    # The fix was in dashboard.html, a standalone HTML file.
    # Let's open it directly.
    page.goto("file:///app/dashboard.html")
    page.wait_for_timeout(1000)

    # Initial state: no unsaved changes, Save button should be disabled
    page.screenshot(path="/home/jules/verification/screenshots/verification-initial.png")
    page.wait_for_timeout(500)

    # Type something to make it dirty
    page.locator("#editor").fill("some new text")
    page.wait_for_timeout(1000)

    # Now Save button should be enabled
    page.screenshot(path="/home/jules/verification/screenshots/verification-dirty.png")
    page.wait_for_timeout(500)

    # Click Save
    # Mocking file picker / download can be tricky, but we should at least see the state change
    page.locator("#saveBtn").click()
    page.wait_for_timeout(1000)

    # Take a screenshot after clicking save
    page.screenshot(path="/home/jules/verification/screenshots/verification-after-save.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()

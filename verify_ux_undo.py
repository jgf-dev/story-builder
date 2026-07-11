from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("file:///app/dashboard.html")
    page.wait_for_timeout(1000)

    # Type something to make it dirty
    original_text = page.locator("#editor").input_value()
    page.locator("#editor").fill(original_text + "\nsome new text")
    page.wait_for_timeout(1000)

    # Now Save button should be enabled
    page.screenshot(path="/home/jules/verification/screenshots/verification-dirty-2.png")
    page.wait_for_timeout(500)

    # Undo the changes (put original text back)
    page.locator("#editor").fill(original_text)
    page.wait_for_timeout(1000)

    # Save button should be disabled again
    page.screenshot(path="/home/jules/verification/screenshots/verification-undone.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()

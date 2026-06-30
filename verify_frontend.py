import urllib.request
import time
import subprocess
import os

# Ensure playwright is installed
os.system("uv pip install playwright && uv run playwright install chromium")

# Start Streamlit server in the background
server = subprocess.Popen(["uv", "run", "streamlit", "run", "scripts/dashboard.py", "--server.port=8501", "--server.headless=true"])
time.sleep(5)  # Wait for server to start

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:8501")
    time.sleep(3)  # Wait for page to load

    # Try to navigate to Archive Stats tab
    try:
        # Streamlit sidebar is usually an iframe or complex DOM structure
        # Best effort attempt to click the tab
        page.locator('text="📊 Archive Stats"').click()
        time.sleep(3)
        page.screenshot(path="dashboard_stats.png")
        print("Successfully navigated to Archive Stats and took screenshot.")
    except Exception as e:
        print(f"Error navigating: {e}")
        page.screenshot(path="dashboard_error.png")

    browser.close()

# Terminate server
server.terminate()

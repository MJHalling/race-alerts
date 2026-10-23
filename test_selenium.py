from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

url = "https://eclipsetbpartners.com/stable/upcoming-races/upcoming"

options = Options()
options.binary_location = "/repl/tools/bin/chromium"
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

print("Starting Chrome...")

driver = webdriver.Chrome(options=options)

try:
    print("Opening Eclipse...")
    driver.get(url)

    time.sleep(10)

    print("Page title:", driver.title)
    print("Current URL:", driver.current_url)

    if "Flooding" in driver.page_source:
        print("SUCCESS: Race information loaded.")
    elif "Just a moment" in driver.page_source:
        print("BLOCKED: Cloudflare challenge is still showing.")
    else:
        print("UNKNOWN: Page loaded, but expected race information was not found.")

finally:
    driver.quit()
    print("Chrome closed.")
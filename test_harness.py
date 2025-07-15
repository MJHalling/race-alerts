# test_harness.py
import requests
from your_alert_module import check_site_once

# 1. Fetch the live “Upcoming” page
URL = "https://eclipsetbpartners.com/stable/upcoming-races/upcoming"
response = requests.get(URL, timeout=10)
response.raise_for_status()
html_page = response.text

# 2. Initialize empty cache
seen = set()

# 3. First run – should fire alerts
print("First run (live site):")
alerts_first = check_site_once(html_page, seen)
for key in alerts_first:
    print("  → Alert Key:", key)

# 4. Second run – should be silent
print("\nSecond run (same snapshot):")
alerts_second = check_site_once(html_page, seen)
print("  Alerts fired:", len(alerts_second))

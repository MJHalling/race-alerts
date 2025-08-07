import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import os
import time

# ✅ Tracked horses
tracked_horses = {
    "Velocity", "Air Force Red", "Silversmith", "La Ville Lumiere",
    "Julia Street", "Toodles", "Cultural", "Ariri", "Needlepoint",
    "There Goes Harvard"
}

# ✅ Normalize helper
def normalize_row_text(raw):
    return " ".join(raw.lower().split())

# ✅ Twilio setup
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO_LIST = os.getenv("TWILIO_TO", "").split(",")
twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

# ✅ Cache file path helper
def cache_path():
    return os.path.join(os.path.dirname(__file__), "seen_entries.txt")

def load_seen_entries():
    try:
        with open(cache_path(), "r") as f:
            seen = set(line.strip() for line in f)
            print(f"[DEBUG] Loaded {len(seen)} cache entries at startup.")
            return seen
    except FileNotFoundError:
        print("[DEBUG] No cache file found. Starting fresh.")
        return set()

def save_entry(entry):
    with open(cache_path(), "a") as f:
        f.write(entry + "\n")
        print(f"[DEBUG] Wrote cache entry: {entry[:60]}…")

seen_entries = load_seen_entries()
previous_snapshot = set()
entry_data = {}

# ✅ SMS alert sender
def send_alert(message, horse, subject_override=None):
    title = subject_override if subject_override else f"{horse} 🏇 Race Target!"
    sms_content = f"{title}\n\n{message}"

    for recipient in TWILIO_TO_LIST:
        try:
            twilio_client.messages.create(
                body=sms_content,
                from_=TWILIO_FROM,
                to=recipient.strip()
            )
            print(f"📲 SMS alert sent to {recipient} for {horse}.")
        except Exception as e:
            print(f"❌ Failed to send SMS to {recipient}: {e}")

# ✅ Scrape and alert for upcoming races
def check_site():
    global entry_data
    global previous_snapshot

    current_snapshot = set()
    current_entry_data = {}
    new_alerts = []
    removed_alerts = []

    base_url = "https://eclipsetbpartners.com/stable/upcoming-races/upcoming"

    for page_num in range(1, 6):
        url = base_url if page_num == 1 else f"{base_url}/page/{page_num}/"
        print(f"🔍 Checking: {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ Page {page_num} returned status {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            for row in soup.find_all("tr"):
                raw = row.get_text(separator="|").strip()
                normalized = normalize_row_text(raw)

                for horse in tracked_horses:
                    horse_key = horse.lower()
                    if horse_key in normalized:
                        current_snapshot.add(horse)
                        current_entry_data[horse] = raw
                        cache_key = f"{horse_key}::{normalized}"
                        if cache_key not in seen_entries:
                            seen_entries.add(cache_key)
                            save_entry(cache_key)
                            new_alerts.append((horse, raw))
                        else:
                            print(f"[DEBUG] Skipping already seen: {cache_key[:60]}…")
        except Exception as e:
            print(f"⚠️ Error on page {page_num}: {e}")

    for horse in previous_snapshot:
        if horse not in current_snapshot and horse in entry_data:
            removed_alerts.append((horse, entry_data[horse]))

    for horse, details in new_alerts:
        clean_details = "\n".join(
            line.strip() for line in details.replace("|", "\n").splitlines() if line.strip()
        )
        msg = f"{clean_details}"
        send_alert(msg, horse)
        entry_data[horse] = details

    for horse, last_details in removed_alerts:
        clean_details = "\n".join(
            line.strip() for line in last_details.replace("|", "\n").splitlines() if line.strip()
        )
        msg = (
            f"{clean_details}\n\n"
            "This race is no longer listed under Upcoming Entries. "
            "This may reflect a site update or race entries being drawn."
        )
        subject_line = f"{horse} 📰 Race Update"
        send_alert(msg, horse, subject_override=subject_line)

    previous_snapshot = current_snapshot.copy()
    entry_data = current_entry_data.copy()

# ✅ Scrape and alert for race entries
def check_entries():
    url = "https://eclipsetbpartners.com/stable/upcoming-races/entries/"
    print(f"📡 Checking Entries: {url}")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Entries page returned {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.find_all("tr"):
            raw = row.get_text(separator="|").strip()
            normalized = normalize_row_text(raw)

            for horse in tracked_horses:
                horse_key = horse.lower()
                if horse_key in normalized:
                    cache_key = f"ENTRY:{horse_key}::{normalized}"
                    if cache_key not in seen_entries:
                        seen_entries.add(cache_key)
                        save_entry(cache_key)

                        clean_lines = [
                            line.strip() for line in raw.replace("|", "\n").splitlines() if line.strip()
                        ]
                        if len(clean_lines) >= 7:
                            clean_lines[3] = f"Race #{clean_lines[3]}"
                            clean_lines[5] = f"Post Position #{clean_lines[5]}"
                        clean_details = "\n".join(clean_lines)

                        msg = f"\n{clean_details}"
                        subject = f"{horse} 🎯 Entry!"
                        send_alert(msg, horse, subject_override=subject)
    except Exception as e:
        print(f"⚠️ Error checking Entries page: {e}")

# ✅ Loop forever
while True:
    check_site()
    check_entries()
    print("🕐 Sleeping for 1 hour…")
    time.sleep(3600)
import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import os
import time

# ✅ Tracked horses
tracked_horses = {
    "Velocity", "Air Force Red", "Silversmith",
    "La Ville Lumiere", "Julia Street", "Toodles",
    "Cultural", "Ariri", "Needlepoint", "There Goes Harvard"
}

# ✅ Normalize helper
def normalize_row_text(raw):
    return " ".join(raw.lower().split())

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

# ✅ Twilio SMS Alert
def send_alert(message, horse, subject_override=None):
    try:
        twilio_sid = os.environ['TWILIO_SID']
        twilio_auth = os.environ['TWILIO_AUTH_TOKEN']
        messaging_sid = os.environ['TWILIO_FROM']  # This is your Messaging Service SID
        twilio_to = os.environ['TWILIO_TO']

        client = Client(twilio_sid, twilio_auth)
        sms = client.messages.create(
            body=message,
            messaging_service_sid=messaging_sid,
            to=twilio_to
        )
        print(f"📲 SMS alert sent for {horse}. SID: {sms.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")

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
        msg = f"🏇 {horse
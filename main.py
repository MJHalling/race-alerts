import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import smtplib
from email.message import EmailMessage
import os
import time

# ✅ Tracked horses (updated list)
tracked_horses = {
    "Velocity", "Air Force Red", "Silversmith",
    "La Ville Lumiere", "Julia Street", "Toodles",
    "Cultural", "Ariri", "Needlepoint", "Speed Shopper"
}

# ✅ Normalize helper to suppress duplicates
def normalize_row_text(raw):
    return " ".join(raw.lower().split())

# ✅ Twilio Setup
twilio_client = Client(
    os.environ['TWILIO_SID'],
    os.environ['TWILIO_AUTH_TOKEN']
)
FROM = os.environ['TWILIO_FROM']
TO = os.environ['TWILIO_TO']

# ✅ Email Setup
EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
EMAIL_TO = os.environ['EMAIL_TO'].split(',')

# ✅ Load/Save Entry Cache
def load_seen_entries():
    try:
        with open("seen_entries.txt", "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_entry(entry):
    with open("seen_entries.txt", "a") as f:
        f.write(entry + "\n")

seen_entries = load_seen_entries()
previous_snapshot = set()
entry_data = {}

def send_alert(message, horse, subject_override=None):
    subject = subject_override if subject_override else f"{horse} 🏇 Race Target!"
    try:
        twilio_client.messages.create(
            body=message,
            from_=FROM,
            to=TO
        )
        print("📲 Text sent via Twilio.")
    except Exception as e:
        print(f"⚠️ Twilio failed: {e}")
        try:
            email = EmailMessage()
            email['Subject'] = subject
            email['From'] = EMAIL_ADDRESS
            email['To'] = EMAIL_TO
            email.set_content(message)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(email)
            print("📬 Email alert sent instead.")
        except Exception as e2:
            print(f"❌ Failed to send email fallback: {e2}")

def check_site():
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
        except Exception as e:
            print(f"⚠️ Error on page {page_num}: {e}")

    for horse in previous_snapshot:
        if horse not in current_snapshot and horse in entry_data:
            removed_alerts.append((horse, entry_data[horse]))

    for horse, details in new_alerts:
        clean_details = details.replace("|", "\n").strip()
        clean_details = "\n".join(line.strip() for line in clean_details.splitlines() if line.strip())
        msg = f"🏇 {horse} Race Target!\n\n{clean_details}\n\nReply STOP to unsubscribe"
        send_alert(msg, horse)
        entry_data[horse] = details

    for horse, last_details in removed_alerts:
        clean_details = last_details.replace("|", "\n").strip()
        clean_details = "\n".join(line.strip() for line in clean_details.splitlines() if line.strip())
        msg = (
            f"📰 {horse} Race Update\n\n"
            f"{clean_details}\n\n"
            "This race is no longer listed under Upcoming Entries. "
            "This may reflect a draw, scratch, or site update."
        )
        subject_line = f"{horse} 📰 Race Update"
        send_alert(msg, horse, subject_override=subject_line)

    previous_snapshot = current_snapshot.copy()
    entry_data = current_entry_data.copy()

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

                        lines = [line.strip() for line in raw.replace("|", "\n").splitlines() if line.strip()]
                        date = lines[0] if lines else ""
                        track = next((l for l in lines if l not in [date, horse] and "Purse" not in l and "Jockey" not in l and "Race" not in l and "Post" not in l), "")

                        msg_lines = [
                            f"🎯 {horse} Race Entry!",
                            "",
                            date,
                            horse,
                            track,
                        ]

                        for keyword in ["Purse", "Jockey", "Race", "Post Position", "Post Time"]:
                            match = next((l for l in lines if keyword in l), None)
                            if match:
                                msg_lines.append(match)

                        msg_lines.append("")
                        msg_lines.append("Reply STOP to unsubscribe")
                        msg = "\n".join(msg_lines)

                        subject = f"{horse} 🎯 Entry – {track} {date}"
                        send_alert(msg, horse, subject_override=subject)
    except Exception as e:
        print(f"⚠️ Error checking Entries page: {e}")

while True:
    check_site()
    check_entries()
    time.sleep(3600)

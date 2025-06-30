import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import smtplib
from email.message import EmailMessage
import os
import time

# Tracked horse racing entries
tracked_horses = {
    "Velocity", "Air Force Red", "Silversmith",
    "La Ville Lumiere", "Julia Street", "Toodles",
    "Cultural", "Ariri"
}

# Twilio setup
twilio_client = Client(
    os.environ['TWILIO_SID'],
    os.environ['TWILIO_AUTH_TOKEN']
)
FROM = os.environ['TWILIO_FROM']
TO = os.environ['TWILIO_TO']

# Email setup
EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
EMAIL_TO = os.environ['EMAIL_TO'].split(',')

seen_entries = set()

def send_alert(message, horse):
    try:
        # Attempt Twilio SMS
        twilio_client.messages.create(
            body=message,
            from_=FROM,
            to=TO
        )
        print("📲 Text sent via Twilio.")
    except Exception as e:
        print(f"⚠️ Twilio failed: {e}")
        # Fallback to email
        try:
            email = EmailMessage()
            email['Subject'] = f"{horse} 🏇 Race Target!"
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
    base_url = "https://eclipsetbpartners.com/stable/upcoming-races/upcoming"
    new_alerts = []

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
                row_text = row.get_text(separator="|").strip()
                for horse in tracked_horses:
                    if horse in row_text and row_text not in seen_entries:
                        seen_entries.add(row_text)
                        new_alerts.append((horse, row_text))
        except Exception as e:
            print(f"⚠️ Error on page {page_num}: {e}")

    for horse, details in new_alerts:
        clean_details = details.replace("|", "\n").strip()
        clean_details = "\n".join(line.strip() for line in clean_details.splitlines() if line.strip())
        msg = f"🏇 {horse} Race Target!\n\n{clean_details}"
        print(f"📢 Alert:\n{msg}")
        send_alert(msg, horse)

# Check every hour
while True:
    check_site()
    time.sleep(3600)


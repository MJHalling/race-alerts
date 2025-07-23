import os
from twilio.rest import Client

def send_alert(message, horse):
    try:
        # Load environment variables
        twilio_sid = os.environ['TWILIO_SID']
        twilio_auth = os.environ['TWILIO_AUTH_TOKEN']
        messaging_sid = os.environ['TWILIO_FROM']  # Should be your MG SID
        twilio_to = os.environ['TWILIO_TO']

        # Diagnostic logs
        print("[DEBUG] Twilio credentials loaded:")
        print(f"TWILIO_SID: {twilio_sid}")
        print(f"TWILIO_AUTH_TOKEN: {twilio_auth[:6]}…")
        print(f"TWILIO_FROM (Messaging SID): {messaging_sid}")
        print(f"TWILIO_TO: {twilio_to}")

        # Explicit Twilio client setup
        client = Client(username=twilio_sid, password=twilio_auth)
        print(f"Client SID being used: {client.username}")

        # Send SMS using messaging_service_sid
        sms = client.messages.create(
            body=message,
            messaging_service_sid=messaging_sid,
            to=twilio_to
        )

        print(f"📲 SMS alert sent for {horse}. SID: {sms.sid}")

    except Exception as e:
        print(f"❌ Failed to send SMS: {e}")

# 🔍 Run test
if __name__ == "__main__":
    test_message = "✅ Manual test: Velocity enters Del Mar. Race # 2, Post # 6. Reply STOP to unsubscribe."
    test_horse = "Velocity"
    send_alert(test_message, test_horse)
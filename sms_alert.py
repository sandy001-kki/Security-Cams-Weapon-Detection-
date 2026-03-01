# ─────────────────────────────────────────────
# sms_alert.py — Twilio SMS alerts
# ─────────────────────────────────────────────

import threading
from config import (
    TWILIO_ENABLED, TWILIO_SID, TWILIO_AUTH,
    TWILIO_FROM, TWILIO_TO
)


def send_sms_alert(weapon_label, timestamp, camera_idx=0):
    if not TWILIO_ENABLED:
        return False
    try:
        from twilio.rest import Client
        client  = Client(TWILIO_SID, TWILIO_AUTH)
        message = (
            f"SECURITY ALERT!\n"
            f"Weapon: {weapon_label}\n"
            f"Camera: {camera_idx}\n"
            f"Time: {timestamp}"
        )
        for number in TWILIO_TO:
            client.messages.create(body=message, from_=TWILIO_FROM, to=number)
            print(f"[SMS] Alert sent to {number}")
        return True
    except Exception as e:
        print(f"[SMS ERROR] {e}")
        return False


def send_sms_async(weapon_label, timestamp, camera_idx=0):
    threading.Thread(
        target=send_sms_alert,
        args=(weapon_label, timestamp, camera_idx),
        daemon=True
    ).start()

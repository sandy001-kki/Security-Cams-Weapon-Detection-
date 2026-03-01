# ─────────────────────────────────────────────
# telegram_alert.py — Telegram bot alerts
# ─────────────────────────────────────────────

import threading
import requests
import os
from config import TELEGRAM_ENABLED, TELEGRAM_TOKEN, TELEGRAM_CHAT_IDS


def send_telegram_alert(weapon_label, snapshot_path, timestamp, camera_idx=0):
    if not TELEGRAM_ENABLED:
        return False
    try:
        message = (
            f"🚨 *WEAPON DETECTED*\n\n"
            f"Weapon : `{weapon_label}`\n"
            f"Camera : `{camera_idx}`\n"
            f"Time   : `{timestamp}`"
        )
        for chat_id in TELEGRAM_CHAT_IDS:
            # Send text message
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
                timeout=5
            )
            # Send photo
            if snapshot_path and os.path.exists(snapshot_path):
                with open(snapshot_path, "rb") as photo:
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                        data={"chat_id": chat_id, "caption": f"Person with {weapon_label}"},
                        files={"photo": photo},
                        timeout=10
                    )
            print(f"[TELEGRAM] Alert sent to chat {chat_id}")
        return True
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")
        return False


def send_telegram_async(weapon_label, snapshot_path, timestamp, camera_idx=0):
    threading.Thread(
        target=send_telegram_alert,
        args=(weapon_label, snapshot_path, timestamp, camera_idx),
        daemon=True
    ).start()

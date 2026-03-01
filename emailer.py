# ─────────────────────────────────────────────
# emailer.py — Email alerts + daily report
# ─────────────────────────────────────────────

import smtplib
import threading
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVERS, SMTP_HOST, SMTP_PORT


def _send(msg):
    """Internal helper to connect and send."""
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)


def send_weapon_alert(weapon_label, snapshot_path, timestamp, camera_idx=0):
    """Send weapon alert email with person photo to all receivers."""
    try:
        for receiver in EMAIL_RECEIVERS:
            msg = MIMEMultipart()
            msg["From"]    = EMAIL_SENDER
            msg["To"]      = receiver
            msg["Subject"] = f"🚨 WEAPON DETECTED: {weapon_label.upper()}"
            body = (
                f"⚠️ Security Alert!\n\n"
                f"Weapon  : {weapon_label}\n"
                f"Camera  : {camera_idx}\n"
                f"Time    : {timestamp}\n\n"
                f"Photo of the person carrying the weapon is attached."
            )
            msg.attach(MIMEText(body, "plain"))
            if snapshot_path and os.path.exists(snapshot_path):
                with open(snapshot_path, "rb") as f:
                    msg.attach(MIMEImage(f.read(), name=os.path.basename(snapshot_path)))
            _send(msg)
            print(f"[EMAIL] Alert sent to {receiver}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False


def send_daily_report(alerts):
    """Send daily summary email."""
    try:
        for receiver in EMAIL_RECEIVERS:
            msg = MIMEMultipart()
            msg["From"]    = EMAIL_SENDER
            msg["To"]      = receiver
            msg["Subject"] = f"📋 Daily Security Report — {datetime.now().strftime('%Y-%m-%d')}"

            if not alerts:
                body = "✅ All clear! No weapons detected in the last 24 hours."
            else:
                lines = [f"⚠️ {len(alerts)} weapon detection(s) in the last 24 hours:\n"]
                for row in alerts:
                    lines.append(f"  • {row[1]}  |  Camera {row[2]}  |  {row[3]}")
                body = "\n".join(lines)

            msg.attach(MIMEText(body, "plain"))
            _send(msg)
            print(f"[EMAIL] Daily report sent to {receiver}")
        return True
    except Exception as e:
        print(f"[EMAIL REPORT ERROR] {e}")
        return False


def send_weapon_alert_async(weapon_label, snapshot_path, timestamp, camera_idx=0):
    threading.Thread(
        target=send_weapon_alert,
        args=(weapon_label, snapshot_path, timestamp, camera_idx),
        daemon=True
    ).start()

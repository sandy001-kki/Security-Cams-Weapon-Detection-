# ─────────────────────────────────────────────
# scheduler.py — Hour-based schedule + daily report
# ─────────────────────────────────────────────

import threading
import time
from datetime import datetime
from config import (
    SCHEDULE_ENABLED, SCHEDULE_START_HOUR, SCHEDULE_END_HOUR,
    DAILY_REPORT_ENABLED, DAILY_REPORT_HOUR
)


def is_active_hour():
    """Returns True if current time is within the active schedule."""
    if not SCHEDULE_ENABLED:
        return True
    hour = datetime.now().hour
    if SCHEDULE_START_HOUR <= SCHEDULE_END_HOUR:
        return SCHEDULE_START_HOUR <= hour < SCHEDULE_END_HOUR
    else:
        # Overnight schedule e.g. 22:00 to 06:00
        return hour >= SCHEDULE_START_HOUR or hour < SCHEDULE_END_HOUR


def start_daily_report_thread(report_fn):
    """Runs daily report at configured hour every day."""
    if not DAILY_REPORT_ENABLED:
        return

    def _loop():
        last_sent_day = None
        while True:
            now = datetime.now()
            if now.hour == DAILY_REPORT_HOUR and now.day != last_sent_day:
                print("[SCHEDULER] Sending daily report...")
                report_fn()
                last_sent_day = now.day
            time.sleep(60)   # check every minute

    threading.Thread(target=_loop, daemon=True).start()
    print("[SCHEDULER] Daily report thread started.")

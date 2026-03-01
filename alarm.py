# ─────────────────────────────────────────────
# alarm.py — Sound alarm when weapon detected
# ─────────────────────────────────────────────

import threading
import time
from config import ALARM_ENABLED, ALARM_DURATION


def play_alarm():
    """Play a system beep alarm."""
    if not ALARM_ENABLED:
        return
    def _beep():
        end = time.time() + ALARM_DURATION
        while time.time() < end:
            try:
                import winsound
                winsound.Beep(1000, 500)   # 1000Hz for 500ms
            except ImportError:
                # Linux/Mac fallback
                print("\a", end="", flush=True)
                time.sleep(0.5)
    threading.Thread(target=_beep, daemon=True).start()
    print("[ALARM] Alarm triggered!")

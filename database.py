# ─────────────────────────────────────────────
# database.py — SQLite logging + daily report
# ─────────────────────────────────────────────

import sqlite3
from datetime import datetime, timedelta
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp  TEXT,
            camera     INTEGER,
            weapon     TEXT,
            snapshot   TEXT,
            video      TEXT,
            email_sent INTEGER,
            sms_sent   INTEGER,
            tg_sent    INTEGER
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] Initialized.")


def log_alert(timestamp, camera_idx, weapon, snapshot, video, email_sent, sms_sent, tg_sent):
    conn = sqlite3.connect(DB_PATH)
    conn.cursor().execute(
        """INSERT INTO alerts
           (timestamp, camera, weapon, snapshot, video, email_sent, sms_sent, tg_sent)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (timestamp, camera_idx, weapon, snapshot, video,
         int(email_sent), int(sms_sent), int(tg_sent))
    )
    conn.commit()
    conn.close()


def get_all_alerts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return rows


def get_daily_summary():
    """Get all alerts from the last 24 hours for the daily report."""
    since = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
    conn  = sqlite3.connect(DB_PATH)
    c     = conn.cursor()
    c.execute("SELECT * FROM alerts WHERE timestamp >= ? ORDER BY timestamp DESC", (since,))
    rows  = c.fetchall()
    conn.close()
    return rows


def print_all_alerts():
    """Print all alerts to terminal — run: python database.py"""
    rows = get_all_alerts()
    if not rows:
        print("No alerts logged yet.")
        return
    print(f"\n{'ID':<5} {'Time':<22} {'Cam':<5} {'Weapon':<12} {'Snapshot'}")
    print("-" * 70)
    for row in rows:
        print(f"{row[0]:<5} {row[1]:<22} {row[2]:<5} {row[3]:<12} {row[4]}")
    print(f"\nTotal alerts: {len(rows)}\n")


if __name__ == "__main__":
    print_all_alerts()

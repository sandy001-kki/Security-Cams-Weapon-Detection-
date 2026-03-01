# ─────────────────────────────────────────────
# config.py — All settings in one place
# ─────────────────────────────────────────────

# ── Email ─────────────────────────────────────
EMAIL_SENDER    = "email-0"
EMAIL_PASSWORD  = "password"
EMAIL_RECEIVERS   = [
    "email-1",
    "email-2",   # add as many as you want
]
SMTP_HOST         = "smtp.gmail.com"
SMTP_PORT         = 587

# ── SMS (Twilio) ──────────────────────────────
TWILIO_ENABLED    = False   # set True after adding credentials
TWILIO_SID        = "your_twilio_account_sid"
TWILIO_AUTH       = "your_twilio_auth_token"
TWILIO_FROM       = "+1xxxxxxxxxx"   # your Twilio number
TWILIO_TO         = [
    "+91xxxxxxxxxx",    # add recipient numbers
]

# ── Telegram ──────────────────────────────────
TELEGRAM_ENABLED  = False   # set True after adding credentials
TELEGRAM_TOKEN    = "your_bot_token"
TELEGRAM_CHAT_IDS = ["your_chat_id"]

# ── Roboflow ──────────────────────────────────
ROBOFLOW_API_KEY  = "api-key"
ROBOFLOW_MODEL    = "weapon-detection-f1lih/1"
ROBOFLOW_API_URL  = f"https://detect.roboflow.com/{ROBOFLOW_MODEL}"

# ── Camera ────────────────────────────────────
CAMERA_INDEXES    = [0]     # add more indexes for multiple cameras e.g. [0, 1]
FRAME_WIDTH       = 640
FRAME_HEIGHT      = 480
FRAME_FPS         = 30
AUTO_RECONNECT    = True    # auto-reconnect if camera disconnects
NIGHT_MODE        = False   # auto-brightness boost in low light

# ── Detection ─────────────────────────────────
CONFIDENCE          = 0.35
ALERT_COOLDOWN      = 30      # seconds between repeated alerts per weapon
MIN_DETECT_FRAMES   = 3       # weapon must appear in N frames before alert (reduces false alarms)
MOTION_DETECTION    = True    # only run Roboflow when motion detected (saves API calls)
MOTION_THRESHOLD    = 5000    # sensitivity — lower = more sensitive

# ── Video Clip ────────────────────────────────
SAVE_VIDEO_CLIP     = True    # save video clip when weapon detected
VIDEO_CLIP_SECONDS  = 10      # how many seconds to record

# ── Alarm Sound ───────────────────────────────
ALARM_ENABLED       = True    # play beep when weapon detected
ALARM_DURATION      = 3       # seconds

# ── Schedule (only run during these hours) ────
SCHEDULE_ENABLED    = False   # set True to limit hours
SCHEDULE_START_HOUR = 22      # 10 PM
SCHEDULE_END_HOUR   = 6       # 6 AM

# ── Daily Report ─────────────────────────────
DAILY_REPORT_ENABLED = True
DAILY_REPORT_HOUR    = 8      # send report at 8 AM every day

# ── Weapon classes ────────────────────────────
WEAPON_CLASSES = {"pistol", "knife", "rifle", "grenade", "missile"}

# ── Storage ───────────────────────────────────
SNAPSHOT_DIR  = "snapshots"
VIDEO_DIR     = "videos"
DB_PATH       = "security_log.db"

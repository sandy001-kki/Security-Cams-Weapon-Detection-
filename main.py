# ─────────────────────────────────────────────
# main.py — Entry point
# Run: python main.py
# Dashboard: http://localhost:5000
# ─────────────────────────────────────────────

import cv2
import time
import threading
from datetime import datetime
from ultralytics import YOLO

from config import (
    CAMERA_INDEXES, FRAME_WIDTH, FRAME_HEIGHT, FRAME_FPS,
    WEAPON_CLASSES, ALERT_COOLDOWN, AUTO_RECONNECT, NIGHT_MODE
)
from database        import init_db, log_alert, get_daily_summary
from emailer         import send_weapon_alert_async, send_daily_report
from sms_alert       import send_sms_async
from telegram_alert  import send_telegram_async
from detector        import set_frame, get_predictions, start_detection_thread, stop_detection
from snapshot        import save_person_snapshot, start_video_recording
from alarm           import play_alarm
from scheduler       import is_active_hour, start_daily_report_thread
from dashboard       import start_dashboard, set_dashboard_frame


# ─────────────────────────────────────────────
# NIGHT MODE — boost brightness in low light
# ─────────────────────────────────────────────
def apply_night_mode(frame):
    if not NIGHT_MODE:
        return frame
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg  = gray.mean()
    if avg < 80:   # dark scene
        alpha = 1.5 + (80 - avg) / 80
        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=20)
    return frame


# ─────────────────────────────────────────────
# SINGLE CAMERA LOOP
# ─────────────────────────────────────────────
def run_camera(camera_idx, person_model, face_cascade):
    last_alert_time  = {}
    latest_cam_frame = [None]

    def get_latest_frame():
        return latest_cam_frame[0]

    cap = None

    def open_camera():
        nonlocal cap
        c = cv2.VideoCapture(camera_idx)
        if c.isOpened():
            c.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
            c.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            c.set(cv2.CAP_PROP_FPS,          FRAME_FPS)
            print(f"[CAM {camera_idx}] Opened.")
        cap = c

    open_camera()

    window_name = f"Security Camera {camera_idx}"

    while True:
        if not cap or not cap.isOpened():
            if AUTO_RECONNECT:
                print(f"[CAM {camera_idx}] Disconnected — retrying in 3s...")
                time.sleep(3)
                open_camera()
                continue
            else:
                break

        ret, frame = cap.read()
        if not ret:
            if AUTO_RECONNECT:
                print(f"[CAM {camera_idx}] Frame error — reconnecting...")
                cap.release()
                time.sleep(2)
                open_camera()
                continue
            break

        # Night mode
        frame = apply_night_mode(frame)
        latest_cam_frame[0] = frame.copy()

        # Share with detection thread and dashboard
        set_frame(frame)
        set_dashboard_frame(camera_idx, frame)

        # Skip detection if outside schedule
        if not is_active_hour():
            display = frame.copy()
            cv2.putText(display, "SYSTEM INACTIVE (outside schedule)", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            cv2.imshow(window_name, display)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        display = frame.copy()
        gray    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        now     = time.time()

        # ── Face detection ───────────────────────
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
        for (fx, fy, fw, fh) in faces:
            cv2.rectangle(display, (fx, fy), (fx+fw, fy+fh), (0, 255, 0), 2)
            cv2.putText(display, "Face", (fx, fy-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # ── Person detection ─────────────────────
        person_results = person_model(frame, verbose=False)[0]
        person_boxes   = []
        for b in person_results.boxes:
            if person_model.names[int(b.cls[0])].lower() == "person":
                coords = [int(v) for v in b.xyxy[0].tolist()]
                person_boxes.append(coords)
                px1, py1, px2, py2 = coords
                cv2.rectangle(display, (px1, py1), (px2, py2), (0, 220, 220), 2)
                cv2.putText(display, "Person", (px1, py1-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 220), 2)

        # ── Weapon detections ────────────────────
        for pred in get_predictions():
            label = pred["class"].lower()
            conf  = pred["confidence"]
            cx, cy = pred["x"], pred["y"]
            bw, bh = pred["width"], pred["height"]
            x1, y1 = int(cx - bw/2), int(cy - bh/2)
            x2, y2 = int(cx + bw/2), int(cy + bh/2)

            cv2.rectangle(display, (x1, y1), (x2, y2), (255, 100, 0), 2)
            cv2.putText(display, f"{label} {conf:.2f}", (x1, y1-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 100, 0), 2)

            if label in WEAPON_CLASSES:
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(display, f"WEAPON: {label}", (x1, y1-14),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

                if (now - last_alert_time.get(label, 0)) > ALERT_COOLDOWN:
                    last_alert_time[label] = now
                    ts_str      = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ts_readable = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # 1. Save person photo
                    snapshot = save_person_snapshot(
                        frame, (x1, y1, x2, y2),
                        person_boxes, ts_str, label
                    )

                    # 2. Save video clip
                    video = start_video_recording(
                        get_latest_frame, ts_str, label
                    )

                    # 3. Alarm
                    play_alarm()

                    # 4. Send all alerts
                    send_weapon_alert_async(label, snapshot, ts_readable, camera_idx)
                    send_sms_async(label, ts_readable, camera_idx)
                    send_telegram_async(label, snapshot, ts_readable, camera_idx)

                    # 5. Log to database
                    log_alert(ts_readable, camera_idx, label, snapshot,
                              video or "", True, True, True)

        # Status overlay
        cv2.putText(display, f"CAM {camera_idx} | ACTIVE", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow(window_name, display)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    if cap:
        cap.release()
    cv2.destroyWindow(window_name)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    init_db()

    print("[INFO] Loading person detection model...")
    person_model = YOLO("yolov8n.pt")

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # Start background services
    start_detection_thread()
    start_dashboard()

    # Daily report function
    def daily_report():
        alerts = get_daily_summary()
        send_daily_report(alerts)

    start_daily_report_thread(daily_report)

    print(f"[INFO] Starting {len(CAMERA_INDEXES)} camera(s)...")
    print("[INFO] Dashboard → http://localhost:5000")
    print("[INFO] Press Q in any camera window to quit.")

    if len(CAMERA_INDEXES) == 1:
        # Single camera — run in main thread
        run_camera(CAMERA_INDEXES[0], person_model, face_cascade)
    else:
        # Multiple cameras — each in its own thread
        threads = []
        for idx in CAMERA_INDEXES:
            t = threading.Thread(
                target=run_camera,
                args=(idx, person_model, face_cascade),
                daemon=True
            )
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    stop_detection()
    cv2.destroyAllWindows()
    print("[INFO] System shut down.")


if __name__ == "__main__":
    main()

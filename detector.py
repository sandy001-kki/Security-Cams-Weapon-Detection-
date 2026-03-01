# ─────────────────────────────────────────────
# detector.py — Roboflow weapon detection thread
#               with motion detection + consecutive frame check
# ─────────────────────────────────────────────

import cv2
import base64
import requests
import threading
import time
import numpy as np
from config import (
    ROBOFLOW_API_URL, ROBOFLOW_API_KEY, CONFIDENCE,
    MOTION_DETECTION, MOTION_THRESHOLD, MIN_DETECT_FRAMES
)

# Shared state
latest_predictions  = []
predictions_lock    = threading.Lock()
latest_frame        = None
frame_lock          = threading.Lock()
detection_running   = True
prev_gray           = None

# Consecutive frame counter per weapon label
detect_counter      = {}


def set_frame(frame):
    global latest_frame
    with frame_lock:
        latest_frame = frame.copy()


def get_predictions():
    with predictions_lock:
        return list(latest_predictions)


def has_motion(gray_frame):
    """Returns True if significant motion detected vs previous frame."""
    global prev_gray
    if prev_gray is None:
        prev_gray = gray_frame
        return True
    diff  = cv2.absdiff(prev_gray, gray_frame)
    _, th = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    score = np.sum(th)
    prev_gray = gray_frame
    return score > MOTION_THRESHOLD


def roboflow_detection_thread():
    global latest_predictions, detection_running, detect_counter

    while detection_running:
        with frame_lock:
            if latest_frame is None:
                time.sleep(0.05)
                continue
            frame_copy = latest_frame.copy()

        # Skip API call if no motion detected
        if MOTION_DETECTION:
            gray = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2GRAY)
            if not has_motion(gray):
                time.sleep(0.1)
                continue

        try:
            _, img_encoded = cv2.imencode(".jpg", frame_copy, [cv2.IMWRITE_JPEG_QUALITY, 70])
            img_b64 = base64.b64encode(img_encoded).decode("utf-8")
            response = requests.post(
                ROBOFLOW_API_URL,
                params={"api_key": ROBOFLOW_API_KEY, "confidence": int(CONFIDENCE * 100)},
                data=img_b64,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5
            )
            preds = response.json().get("predictions", [])

            # Update consecutive detection counters
            detected_labels = {p["class"].lower() for p in preds}
            for label in detected_labels:
                detect_counter[label] = detect_counter.get(label, 0) + 1
            # Reset counter for labels not detected this frame
            for label in list(detect_counter.keys()):
                if label not in detected_labels:
                    detect_counter[label] = 0

            # Only pass through predictions that hit the MIN_DETECT_FRAMES threshold
            confirmed = [p for p in preds
                         if detect_counter.get(p["class"].lower(), 0) >= MIN_DETECT_FRAMES]

            with predictions_lock:
                latest_predictions = confirmed

        except Exception as e:
            print(f"[ROBOFLOW ERROR] {e}")

        time.sleep(0.3)


def start_detection_thread():
    t = threading.Thread(target=roboflow_detection_thread, daemon=True)
    t.start()
    print("[DETECTOR] Background detection thread started.")
    return t


def stop_detection():
    global detection_running
    detection_running = False

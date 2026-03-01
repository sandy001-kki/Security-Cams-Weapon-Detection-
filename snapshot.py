# ─────────────────────────────────────────────
# snapshot.py — Person photo + video clip capture
# ─────────────────────────────────────────────

import cv2
import os
import threading
import time
from datetime import datetime
from config import SNAPSHOT_DIR, VIDEO_DIR, SAVE_VIDEO_CLIP, VIDEO_CLIP_SECONDS

os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)


def save_person_snapshot(frame, weapon_box, person_boxes, timestamp_str, weapon_label):
    """Capture the full person carrying the weapon."""
    wx1, wy1, wx2, wy2 = weapon_box
    w_cx = (wx1 + wx2) / 2
    w_cy = (wy1 + wy2) / 2
    h, w = frame.shape[:2]

    best_person = None
    best_dist   = float("inf")

    for (px1, py1, px2, py2) in person_boxes:
        p_cx = (px1 + px2) / 2
        p_cy = (py1 + py2) / 2
        dist = ((w_cx - p_cx) ** 2 + (w_cy - p_cy) ** 2) ** 0.5
        if dist < best_dist:
            best_dist   = dist
            best_person = (px1, py1, px2, py2)

    if best_person:
        px1, py1, px2, py2 = best_person
        pad = 60
        cx1 = max(0, px1 - pad)
        cy1 = max(0, py1 - pad)
        cx2 = min(w, px2 + pad)
        cy2 = min(h, py2 + pad)
        print("[SNAPSHOT] Person found — capturing full body.")
    else:
        cx1 = max(0, wx1 - 250)
        cy1 = 0
        cx2 = min(w, wx2 + 250)
        cy2 = min(h, wy2 + 100)
        print("[SNAPSHOT] No person — capturing wide frame area.")

    cropped = frame[cy1:cy2, cx1:cx2]
    if cropped.size == 0:
        cropped = frame

    filename = f"{SNAPSHOT_DIR}/{weapon_label}_{timestamp_str}.jpg"
    cv2.imwrite(filename, cropped)
    print(f"[SNAPSHOT] Saved: {filename}")
    return filename


# Video clip recording
_recording       = False
_video_frames    = []
_video_lock      = threading.Lock()


def start_video_recording(frame_provider_fn, timestamp_str, weapon_label, fps=20):
    """Record a video clip for VIDEO_CLIP_SECONDS seconds."""
    if not SAVE_VIDEO_CLIP:
        return None

    filename = f"{VIDEO_DIR}/{weapon_label}_{timestamp_str}.avi"

    def record():
        global _recording
        _recording = True
        frames     = []
        start      = time.time()
        while time.time() - start < VIDEO_CLIP_SECONDS:
            frame = frame_provider_fn()
            if frame is not None:
                frames.append(frame.copy())
            time.sleep(1 / fps)
        _recording = False

        if frames:
            h, w = frames[0].shape[:2]
            out  = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*"XVID"), fps, (w, h))
            for f in frames:
                out.write(f)
            out.release()
            print(f"[VIDEO] Saved: {filename}")

    threading.Thread(target=record, daemon=True).start()
    return filename

# ─────────────────────────────────────────────
# dashboard.py — Flask web dashboard
# Auto-updates logs every 3 seconds without refresh
# Open browser at: http://localhost:5000
# ─────────────────────────────────────────────

from flask import Flask, Response, render_template_string, jsonify
import cv2
import threading
from database import get_all_alerts
from config import CAMERA_INDEXES

app = Flask(__name__)

_dashboard_frames = {}
_frame_lock       = threading.Lock()


def set_dashboard_frame(camera_idx, frame):
    with _frame_lock:
        _dashboard_frames[camera_idx] = frame.copy()


def generate_feed(camera_idx):
    import time
    while True:
        with _frame_lock:
            frame = _dashboard_frames.get(camera_idx)
        if frame is None:
            import numpy as np
            frame = (255 * __import__('numpy').ones((480, 640, 3), dtype='uint8')).astype('uint8')
        _, buf = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        time.sleep(0.05)


HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Security Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0f0f0f;
      color: #eee;
      font-family: 'Segoe UI', Arial, sans-serif;
      padding: 20px;
    }
    h1 { color: #ff3333; font-size: 26px; margin-bottom: 6px; }
    .subtitle { color: #666; font-size: 13px; margin-bottom: 24px; }

    .cameras {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 30px;
    }
    .cam-box {
      background: #1a1a1a;
      border: 1px solid #333;
      border-radius: 10px;
      padding: 12px;
    }
    .cam-box h2 {
      color: #aaa;
      font-size: 14px;
      margin-bottom: 8px;
    }
    .cam-box img {
      width: 480px;
      border-radius: 6px;
      display: block;
    }

    .log-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 10px;
    }
    .log-header h2 { color: #ccc; font-size: 18px; }
    .live-dot {
      width: 10px; height: 10px;
      background: #00ff88;
      border-radius: 50%;
      animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
    .live-label { color: #00ff88; font-size: 13px; }
    .count-label { color: #666; font-size: 13px; margin-left: auto; }

    table {
      width: 100%;
      border-collapse: collapse;
      background: #1a1a1a;
      border-radius: 10px;
      overflow: hidden;
    }
    th {
      background: #2a2a2a;
      padding: 12px 14px;
      text-align: left;
      color: #ff3333;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    td {
      padding: 10px 14px;
      border-bottom: 1px solid #222;
      font-size: 13px;
      color: #ccc;
    }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #222; }

    .badge {
      background: #ff3333;
      color: #fff;
      padding: 3px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: bold;
      text-transform: uppercase;
    }
    .badge.knife    { background: #ff6600; }
    .badge.pistol   { background: #cc0000; }
    .badge.rifle    { background: #990000; }
    .badge.grenade  { background: #cc3300; }
    .badge.missile  { background: #880000; }

    .new-row {
      animation: highlight 2s ease-out;
    }
    @keyframes highlight {
      0%   { background: #1a3a1a; }
      100% { background: transparent; }
    }

    #last-updated {
      color: #444;
      font-size: 12px;
      margin-top: 10px;
      text-align: right;
    }
  </style>
</head>
<body>

  <h1>🔴 Security Camera Dashboard</h1>
  <p class="subtitle">Weapon detection system — live monitoring</p>

  <div class="cameras">
    {% for idx in camera_indexes %}
    <div class="cam-box">
      <h2>📷 Camera {{ idx }}</h2>
      <img src="/feed/{{ idx }}" />
    </div>
    {% endfor %}
  </div>

  <div class="log-header">
    <h2>Alert Log</h2>
    <div class="live-dot"></div>
    <span class="live-label">LIVE</span>
    <span class="count-label" id="alert-count">Loading...</span>
  </div>

  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Time</th>
        <th>Camera</th>
        <th>Weapon</th>
        <th>Snapshot</th>
        <th>Email</th>
        <th>SMS</th>
        <th>Telegram</th>
      </tr>
    </thead>
    <tbody id="alert-table-body">
      <tr><td colspan="8" style="text-align:center;color:#555;">Loading alerts...</td></tr>
    </tbody>
  </table>
  <div id="last-updated"></div>

<script>
  let lastCount = 0;

  function loadAlerts() {
    fetch('/api/alerts')
      .then(res => res.json())
      .then(data => {
        const tbody = document.getElementById('alert-table-body');
        const isNew = data.length > lastCount;
        lastCount = data.length;

        document.getElementById('alert-count').textContent =
          `${data.length} total alert${data.length !== 1 ? 's' : ''}`;

        if (data.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#555;">No alerts yet.</td></tr>';
          return;
        }

        tbody.innerHTML = data.map((row, i) => `
          <tr class="${i === 0 && isNew ? 'new-row' : ''}">
            <td>${row.id}</td>
            <td>${row.timestamp}</td>
            <td>Cam ${row.camera}</td>
            <td><span class="badge ${row.weapon.toLowerCase()}">${row.weapon}</span></td>
            <td style="color:#555;font-size:11px;">${row.snapshot || '—'}</td>
            <td>${row.email_sent ? '✅' : '❌'}</td>
            <td>${row.sms_sent ? '✅' : '❌'}</td>
            <td>${row.tg_sent ? '✅' : '❌'}</td>
          </tr>
        `).join('');

        const now = new Date();
        document.getElementById('last-updated').textContent =
          `Last updated: ${now.toLocaleTimeString()}`;
      })
      .catch(err => console.error('Error fetching alerts:', err));
  }

  // Load immediately then every 3 seconds
  loadAlerts();
  setInterval(loadAlerts, 3000);
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML, camera_indexes=CAMERA_INDEXES)


@app.route("/feed/<int:camera_idx>")
def feed(camera_idx):
    return Response(
        generate_feed(camera_idx),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/api/alerts")
def api_alerts():
    alerts = get_all_alerts()
    return jsonify([{
        "id":        r[0],
        "timestamp": r[1],
        "camera":    r[2],
        "weapon":    r[3],
        "snapshot":  r[4],
        "video":     r[5],
        "email_sent": r[6],
        "sms_sent":   r[7],
        "tg_sent":    r[8],
    } for r in alerts])


def start_dashboard():
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False),
        daemon=True
    ).start()
    print("[DASHBOARD] Running at http://localhost:5000")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

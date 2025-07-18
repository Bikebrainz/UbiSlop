# r6s_input_tracer.py — World-Class Anti-Cheat Mouse Profiling + Screenshot + Overlay Watch

import time
import win32api
import win32con
import math
import json
import os
from datetime import datetime
from collections import deque
from PIL import ImageGrab
import ctypes
from ctypes import wintypes

ALERT_FILE = "r6s_alerts.json"
SNAPSHOT_DIR = "r6s_snapshots"
POLL_HZ = 120
SAMPLE_DURATION = 2
SAMPLE_SIZE = POLL_HZ * SAMPLE_DURATION
SPEED_THRESHOLD = 3600
SPEED_SPIKE_RATIO = 0.85
SPEED_BURST_LIMIT = 5
DISTANCE_THRESHOLD = 200

samples = deque(maxlen=SAMPLE_SIZE)
last_pos = win32api.GetCursorPos()
last_time = time.time()
user32 = ctypes.windll.user32
os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def log_alert(alert_type, data):
    alert = {
        "type": alert_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    alerts = []
    if os.path.exists(ALERT_FILE):
        try:
            with open(ALERT_FILE, "r") as f:
                alerts = json.load(f)
        except Exception:
            alerts = []
    alerts.append(alert)
    with open(ALERT_FILE, "w") as f:
        json.dump(alerts, f, indent=2)


def take_screenshot(trigger):
    path = os.path.join(SNAPSHOT_DIR, f"ss_{trigger}_{int(time.time())}.png")
    try:
        ImageGrab.grab().save(path)
        print(f"[SNAPSHOT] Saved: {path}")
    except Exception as e:
        print(f"[ERROR] Screenshot failed: {e}")


def overlay_check():
    suspicious = []
    def enum_proc(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if title and any(w in title.lower() for w in ["esp", "radar", "overlay"]):
                    suspicious.append(title)
        return True

    enum_windows = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(enum_windows(enum_proc), 0)
    return suspicious


def calculate_speed(p1, p2, t1, t2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dist = math.hypot(dx, dy)
    delta_t = max(t2 - t1, 1e-6)
    return dist / delta_t, dist


def profile_mouse():
    global last_pos, last_time
    curr_pos = win32api.GetCursorPos()
    curr_time = time.time()
    speed, distance = calculate_speed(last_pos, curr_pos, last_time, curr_time)
    samples.append(speed)

    if distance > DISTANCE_THRESHOLD:
        log_alert("lock_on_jump", {
            "distance": round(distance, 2),
            "speed": round(speed, 2),
            "timestamp": datetime.utcnow().isoformat()
        })
        take_screenshot("lockjump")
        print(f"[ALERT] Lock-on movement spike: {distance:.2f}px")

    if len(samples) == SAMPLE_SIZE:
        spikes = [s for s in samples if s > SPEED_THRESHOLD]
        ratio = len(spikes) / len(samples)

        if ratio > SPEED_SPIKE_RATIO or len(spikes) > SPEED_BURST_LIMIT:
            log_alert("macro_signature", {
                "avg_speed": round(sum(samples) / len(samples), 2),
                "max_speed": round(max(samples), 2),
                "ratio_above_threshold": round(ratio, 2),
                "spike_count": len(spikes),
                "interval": f"{SAMPLE_DURATION}s"
            })
            take_screenshot("macro")
            found = overlay_check()
            if found:
                log_alert("overlay_detected", {"titles": found})
            print(f"[ALERT] Macro-like pattern detected with {len(spikes)} spikes")
            samples.clear()

    last_pos = curr_pos
    last_time = curr_time


if __name__ == "__main__":
    print("[INFO] Input Tracer + Screenshot + Overlay Scanner Active")
    while True:
        profile_mouse()
        time.sleep(1 / POLL_HZ)

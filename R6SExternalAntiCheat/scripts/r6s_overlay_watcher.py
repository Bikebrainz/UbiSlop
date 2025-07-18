# r6s_overlay_watcher.py — Advanced Overlay ESP Detector with Auto-Close + Uploader

import ctypes
import time
import json
import os
import requests
from datetime import datetime
from PIL import ImageGrab
from ctypes import wintypes

ALERT_FILE = "r6s_alerts.json"
SNAPSHOT_DIR = "r6s_snapshots"
SCAN_INTERVAL = 5
UPLOAD_URL = "https://r6s-acs.example.com/api/submit"
API_KEY = "your-secure-api-key"

user32 = ctypes.windll.user32
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

EXCLUDED_TITLES = ["steam", "discord", "nvidia", "chrome", "edge"]
SUSPICIOUS_KEYWORDS = ["esp", "cheat", "overlay", "radar", "hack", "crosshair"]


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
    return alert


def upload_alert(alert, screenshot_path=None):
    try:
        payload = {
            "alert_type": alert["type"],
            "timestamp": alert["timestamp"],
            "data": alert["data"]
        }
        files = {}
        if screenshot_path and os.path.exists(screenshot_path):
            files["screenshot"] = open(screenshot_path, "rb")

        headers = {"Authorization": f"Bearer {API_KEY}"}
        res = requests.post(UPLOAD_URL, data={"json": json.dumps(payload)}, files=files, headers=headers)
        if res.status_code == 200:
            print("[UPLOAD] Alert sent to server.")
        else:
            print(f"[UPLOAD ERROR] Status: {res.status_code}")
    except Exception as e:
        print(f"[UPLOAD FAILED] {e}")


def take_screenshot(trigger):
    path = os.path.join(SNAPSHOT_DIR, f"overlay_{trigger}_{int(time.time())}.png")
    try:
        img = ImageGrab.grab()
        img.save(path)
        print(f"[SNAPSHOT] Saved: {path}")
        return path
    except Exception as e:
        print(f"[ERROR] Screenshot failed: {e}")
    return None


def get_window_details(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return None
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    title = buff.value.strip().lower()

    class_buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, class_buf, 256)
    class_name = class_buf.value.strip().lower()

    return title, class_name


def enum_overlay_windows():
    suspicious = []

    def callback(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            details = get_window_details(hwnd)
            if not details:
                return True

            title, class_name = details
            if any(skip in title for skip in EXCLUDED_TITLES):
                return True

            if any(keyword in title or keyword in class_name for keyword in SUSPICIOUS_KEYWORDS):
                user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
                suspicious.append({"title": title, "class": class_name})
        return True

    enum_func = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(enum_func(callback), 0)
    return suspicious


if __name__ == "__main__":
    print("[INFO] Overlay Watcher with Auto-Close + Uploader Running")
    while True:
        titles = enum_overlay_windows()
        if titles:
            alert = log_alert("overlay_detected", {"windows": titles})
            snap = take_screenshot("esp_overlay")
            upload_alert(alert, snap)
            print(f"[ALERT] Closed suspicious overlays: {titles}")
        time.sleep(SCAN_INTERVAL)

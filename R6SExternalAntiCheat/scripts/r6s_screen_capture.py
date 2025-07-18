# r6s_screen_capture_ml_ocr.py — Visual Anti-Cheat Sensor (Final Expansion Tier)

import pyautogui
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
import pytesseract
from collections import Counter
import json
import os
import time
import requests
from datetime import datetime
import hashlib

ALERT_FILE = "r6s_alerts.json"
SNAPSHOT_DIR = "r6s_snapshots"
SCAN_INTERVAL = 10
UPLOAD_URL = "https://r6s-acs.example.com/api/submit"
API_KEY = "your-secure-api-key"

TRIGGER_COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 0, 255)
]
COLOR_TOLERANCE = 30
PIXEL_THRESHOLD = 200
OCR_TERMS = ["enemy", "health", "armor", "esp", "radar", "wallhack", "distance", "name"]
ML_SCORE_THRESHOLD = 0.7
HASH_TRACKER = set()

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
    return alert


def upload_alert(alert, screenshot_path):
    try:
        payload = {
            "alert_type": alert["type"],
            "timestamp": alert["timestamp"],
            "data": alert["data"]
        }
        files = {"screenshot": open(screenshot_path, "rb")} if screenshot_path and os.path.exists(screenshot_path) else {}
        headers = {"Authorization": f"Bearer {API_KEY}"}
        res = requests.post(UPLOAD_URL, data={"json": json.dumps(payload)}, files=files, headers=headers)
        if res.status_code == 200:
            print("[UPLOAD] Screenshot uploaded.")
        else:
            print(f"[UPLOAD FAILED] Status {res.status_code}")
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")


def color_distance(c1, c2):
    return sum((a - b)**2 for a, b in zip(c1, c2)) ** 0.5


def detect_pixel_clusters(img):
    img = img.resize((640, 360))
    pixels = np.array(img).reshape(-1, 3)
    counts = Counter()
    for p in pixels:
        for trigger in TRIGGER_COLORS:
            if color_distance(tuple(p), trigger) < COLOR_TOLERANCE:
                counts[trigger] += 1
    return counts


def ocr_text_check(image):
    try:
        enhanced = ImageEnhance.Contrast(ImageOps.grayscale(image)).enhance(2.0)
        text = pytesseract.image_to_string(enhanced).lower()
        matches = [word for word in OCR_TERMS if word in text]
        return text, matches
    except Exception as e:
        print(f"[OCR ERROR] {e}")
        return "", []


def ml_score(counts):
    total = sum(counts.values())
    score = 0.0
    for color, count in counts.items():
        score += (count / total) * 1.0
    return round(score, 3)


def hash_image(img_path):
    try:
        with open(img_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None


def take_and_analyze():
    snap = pyautogui.screenshot()
    timestamp = int(time.time())
    snap_path = os.path.join(SNAPSHOT_DIR, f"visual_{timestamp}.png")
    snap.save(snap_path)
    print(f"[SNAPSHOT] Captured: {snap_path}")

    snap_hash = hash_image(snap_path)
    if snap_hash in HASH_TRACKER:
        print("[SKIP] Duplicate visual signature. Not reprocessing.")
        return
    HASH_TRACKER.add(snap_hash)

    counts = detect_pixel_clusters(snap)
    score = ml_score(counts)
    ocr_result, ocr_matches = ocr_text_check(snap)

    if score > ML_SCORE_THRESHOLD or ocr_matches:
        alert = log_alert("visual_esp_confirmed", {
            "pixel_clusters": dict(counts),
            "ml_score": score,
            "ocr_terms": ocr_matches,
            "ocr_excerpt": ocr_result[:250],
            "screenshot": os.path.basename(snap_path),
            "sha256": snap_hash
        })
        upload_alert(alert, snap_path)
        print(f"[ALERT] ESP DETECTED | Score: {score} | OCR: {ocr_matches}")
    else:
        print(f"[CHECK] Score={score}, No trigger met.")


if __name__ == "__main__":
    print("[INFO] Screen Capture ML+OCR (Elite Mode) Running")
    while True:
        take_and_analyze()
        time.sleep(SCAN_INTERVAL)

# r6s_guard_with_snapshot.py — Extended Guard with ESP-Trigger Screenshot

import ctypes
import psutil
import time
import json
import hashlib
import os
from datetime import datetime
from PIL import ImageGrab

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_ALL_ACCESS = 0x1F0FFF

ALERT_FILE = "r6s_alerts.json"
TARGET_PROCESS_NAME = "RainbowSix"
SCAN_INTERVAL = 10
MEM_HASH_REGIONS = [(0x00400000, 0x100000), (0x00500000, 0x100000)]
SNAPSHOT_DIR = "r6s_snapshots"

kernel32 = ctypes.windll.kernel32
previous_hashes = {}

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
    filename = os.path.join(SNAPSHOT_DIR, f"screenshot_{trigger}_{int(time.time())}.png")
    try:
        img = ImageGrab.grab()
        img.save(filename)
        print(f"[SNAPSHOT] Screenshot saved: {filename}")
    except Exception as e:
        print(f"[ERROR] Screenshot failed: {e}")


def hash_region(handle, base_addr, size):
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t(0)
    success = kernel32.ReadProcessMemory(handle, ctypes.c_void_p(base_addr), buffer, size, ctypes.byref(bytes_read))
    if success:
        return hashlib.sha256(buffer.raw).hexdigest()
    return None


def get_r6s_process():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if TARGET_PROCESS_NAME.lower() in proc.info['name'].lower():
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None


def check_external_access(target_pid):
    suspicious = []
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.pid == target_pid:
            continue
        try:
            h = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, target_pid)
            if h:
                suspicious.append({"pid": proc.pid, "name": proc.info['name']})
                kernel32.CloseHandle(h)
        except Exception:
            continue
    return suspicious


def diff_hashes(region, new_hash):
    global previous_hashes
    old_hash = previous_hashes.get(region)
    changed = old_hash is not None and old_hash != new_hash
    previous_hashes[region] = new_hash
    return changed


def scan():
    proc = get_r6s_process()
    if not proc:
        print("[INFO] RainbowSix not found.")
        return

    print(f"[INFO] Monitoring PID {proc.pid} ({proc.name()})")
    suspicious = check_external_access(proc.pid)
    for entry in suspicious:
        log_alert("memory_access", {
            "source_pid": entry['pid'],
            "source_name": entry['name'],
            "target_pid": proc.pid,
            "target_name": proc.name()
        })

    try:
        h = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, proc.pid)
        if not h:
            return
        for base, size in MEM_HASH_REGIONS:
            region_id = f"{hex(base)}:{size}"
            digest = hash_region(h, base, size)
            if digest:
                if diff_hashes(region_id, digest):
                    log_alert("memory_changed", {
                        "region": region_id,
                        "length": size,
                        "sha256": digest,
                        "pid": proc.pid
                    })
                    take_screenshot(trigger=region_id.replace(":", "_"))
                else:
                    print(f"[OK] Memory region {region_id} unchanged.")
        kernel32.CloseHandle(h)
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    print("[INFO] Starting R6S Guard Scanner with Screenshot Capture...")
    while True:
        scan()
        time.sleep(SCAN_INTERVAL)

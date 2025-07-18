# r6s_local_runner.py — Orchestrator-Level Anti-Cheat Supervisor (Full Build)

import subprocess
import threading
import os
import time
import tkinter as tk
from tkinter import messagebox
import signal
import sys

MODULES = [
    ("r6s_guard_with_snapshot.py", "Memory Guard"),
    ("r6s_input_tracer_with_snap_overlay.py", "Input Profiler + Overlay"),
    ("r6s_alert_viewer.py", "GUI Alert Monitor")
]

LOCAL_LOG_DIR = "r6s_logs"
MODULE_PROCESSES = {}
os.makedirs(LOCAL_LOG_DIR, exist_ok=True)


def start_module(module_path, label):
    def run():
        log_path = os.path.join(LOCAL_LOG_DIR, f"{os.path.splitext(module_path)[0]}.log")
        with open(log_path, "a") as log:
            proc = subprocess.Popen(["python", module_path], stdout=log, stderr=log)
            MODULE_PROCESSES[label] = proc
            proc.wait()
    threading.Thread(target=run, daemon=True).start()
    print(f"[LAUNCHED] {label}")


def start_gui():
    def shutdown_all():
        for label, proc in MODULE_PROCESSES.items():
            try:
                proc.terminate()
                print(f"[SHUTDOWN] {label}")
            except Exception:
                continue
        root.quit()

    root = tk.Tk()
    root.title("R6S Anti-Cheat Supervisor")
    root.geometry("400x300")
    root.configure(bg="#1e1e1e")

    tk.Label(root, text="Anti-Cheat Modules Running", font=("Segoe UI", 12, "bold"), bg="#1e1e1e", fg="white").pack(pady=10)
    for _, label in MODULES:
        tk.Label(root, text=f"✔ {label}", font=("Segoe UI", 10), bg="#1e1e1e", fg="#8aff8a").pack()

    tk.Button(root, text="Shutdown All", command=shutdown_all, bg="#333", fg="white", padx=10, pady=5).pack(pady=20)
    root.mainloop()


def signal_handler(sig, frame):
    print("[CTRL+C] Gracefully shutting down...")
    for label, proc in MODULE_PROCESSES.items():
        try:
            proc.terminate()
        except Exception:
            continue
    sys.exit(0)


if __name__ == "__main__":
    print("[BOOT] R6S Local Anti-Cheat Launching...")
    signal.signal(signal.SIGINT, signal_handler)
    for mod_path, label in MODULES:
        start_module(mod_path, label)
    time.sleep(1.5)
    start_gui()

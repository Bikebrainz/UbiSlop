# r6s_uploader_gui_tray.py — GUI & Tray Shell for Secure Uploader Agent

import threading
import subprocess
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw

SCRIPT_PATH = "r6s_uploader_agent.py"
CHECK_INTERVAL = 30
MONITOR_FILES = [SCRIPT_PATH, "r6s_alerts.json"]

agent_proc = None


def create_icon():
    image = Image.new("RGB", (64, 64), (30, 150, 60))
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 16, 48, 48), fill=(255, 255, 255))
    return image


def launch_agent():
    global agent_proc
    print("[TRAY] Launching uploader agent...")
    agent_proc = subprocess.Popen([sys.executable, SCRIPT_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_agent():
    global agent_proc
    if agent_proc:
        print("[TRAY] Stopping uploader agent...")
        agent_proc.terminate()
        agent_proc = None


def monitor_integrity():
    last_states = {}
    while True:
        for file in MONITOR_FILES:
            try:
                mtime = os.path.getmtime(file)
                if file not in last_states:
                    last_states[file] = mtime
                elif mtime != last_states[file]:
                    print(f"[SECURITY] File modified: {file}. Restarting agent.")
                    stop_agent()
                    launch_agent()
                    last_states[file] = mtime
            except Exception as e:
                print(f"[ERROR] Monitoring {file}: {e}")
        time.sleep(CHECK_INTERVAL)


def show_gui():
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Uploader Agent", "Uploader agent is now running in the background.")


def main():
    launch_agent()
    threading.Thread(target=monitor_integrity, daemon=True).start()
    threading.Thread(target=show_gui, daemon=True).start()

    icon = Icon("R6SUploader", icon=create_icon(), menu=Menu(
        MenuItem("Force Sync", lambda icon, item: subprocess.Popen([sys.executable, SCRIPT_PATH])),
        MenuItem("Restart Agent", lambda icon, item: (stop_agent(), time.sleep(1), launch_agent())),
        MenuItem("Quit", lambda icon, item: (stop_agent(), icon.stop()))
    ))
    icon.run()


if __name__ == "__main__":
    main()

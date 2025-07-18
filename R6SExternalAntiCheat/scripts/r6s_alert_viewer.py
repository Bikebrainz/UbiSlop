# r6s_alert_viewer.py — Elite GUI Alert Viewer for External Anti-Cheat

import json
import os
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime

ALERT_FILE = "r6s_alerts.json"
REFRESH_INTERVAL = 2000  # in milliseconds
MAX_ALERTS_DISPLAYED = 100

class AlertViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("R6S Anti-Cheat — Realtime Alert Monitor")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e1e")

        self.text = scrolledtext.ScrolledText(
            root,
            width=120,
            height=40,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff",
            font=("Consolas", 10),
            wrap=tk.WORD,
            borderwidth=0
        )
        self.text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.text.configure(state='disabled')

        self.last_loaded = ""
        self.last_alert_count = 0

        self.poll_alert_file()

    def poll_alert_file(self):
        if os.path.exists(ALERT_FILE):
            try:
                with open(ALERT_FILE, 'r') as f:
                    content = f.read()
                    if content != self.last_loaded:
                        self.last_loaded = content
                        alerts = json.loads(content)
                        self.update_display(alerts[-MAX_ALERTS_DISPLAYED:])
                        if len(alerts) > self.last_alert_count:
                            self.last_alert_count = len(alerts)
                            self.notify(alerts[-1])
            except Exception as e:
                print(f"[ERROR] Failed reading alert file: {e}")

        self.root.after(REFRESH_INTERVAL, self.poll_alert_file)

    def update_display(self, alerts):
        self.text.configure(state='normal')
        self.text.delete("1.0", tk.END)
        for alert in alerts:
            ts = alert.get("timestamp", datetime.utcnow().isoformat())
            tag = alert.get("type", "UNKNOWN").upper()
            data = json.dumps(alert.get("data", {}), indent=2)
            entry = f"[{ts}] {tag}\n{data}\n{'-'*80}\n"
            self.text.insert(tk.END, entry)
        self.text.configure(state='disabled')

    def notify(self, alert):
        atype = alert.get("type", "UNKNOWN").upper()
        msg = f"New alert: {atype}\n\nClick OK to acknowledge."
        self.root.bell()
        self.root.after(500, lambda: messagebox.showinfo("Anti-Cheat Alert", msg))

if __name__ == "__main__":
    root = tk.Tk()
    viewer = AlertViewer(root)
    root.mainloop()

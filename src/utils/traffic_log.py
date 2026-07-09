"""
Thread-safe in-memory ring buffer (with optional local file append) used for
both the general traffic log and the captured-credentials log. Everything
stays on the machine running the proxy -- there is no network export path
here by design.
"""
import json
import os
import threading
import time


class TrafficLog:
    def __init__(self, maxlen=500, log_path=None):
        self.lock = threading.Lock()
        self.entries = []
        self.maxlen = maxlen
        self.log_path = log_path
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def add(self, entry):
        entry = dict(entry)
        entry.setdefault("ts", time.time())
        with self.lock:
            self.entries.append(entry)
            if len(self.entries) > self.maxlen:
                self.entries = self.entries[-self.maxlen:]
        if self.log_path:
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
            except Exception as e:
                print(f"[TrafficLog] Failed to write {self.log_path}: {e}")

    def snapshot(self, limit=200):
        with self.lock:
            items = list(self.entries)
        return items[-limit:]

    def count(self):
        with self.lock:
            return len(self.entries)

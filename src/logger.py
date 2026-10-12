"""CSV history log and plain-text alert log."""
import csv
import os

HEADER = ["timestamp", "interface", "upload_KBps", "download_KBps", "upload_Mbps",
          "download_Mbps", "total_sent_MB", "total_received_MB", "utilization_percent",
          "status"]


class MonitorLogger:
    def __init__(self, history_path, alert_path):
        for p in (history_path, alert_path):
            os.makedirs(os.path.dirname(p), exist_ok=True)
        is_new = not os.path.exists(history_path) or os.path.getsize(history_path) == 0
        self._hist = open(history_path, "a", newline="", encoding="utf-8")
        self._csv = csv.writer(self._hist, lineterminator="\n")
        if is_new:
            self._csv.writerow(HEADER)
        self._alerts = open(alert_path, "a", encoding="utf-8")

    def log_reading(self, row):
        self._csv.writerow(row)
        self._hist.flush()

    def log_alert(self, timestamp, interface, status, message):
        self._alerts.write(f"[{timestamp}] [{interface}] {message}\n")
        self._alerts.flush()

    def close(self):
        self._hist.close()
        self._alerts.close()

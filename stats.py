"""Simple statistics tracker for the scanner"""
import json
import os
from datetime import datetime
from threading import Lock

STATS_FILE = "scanner_stats.json"

class StatsTracker:
    def __init__(self):
        self.lock = Lock()
        self._load_stats()

    def _load_stats(self):
        """Load stats from file"""
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r') as f:
                    self.stats = json.load(f)
            except Exception:
                self.stats = self._default_stats()
        else:
            self.stats = self._default_stats()

    def _default_stats(self):
        """Create default stats structure"""
        return {
            "total_scans": 0,
            "started_at": datetime.now().isoformat(),
            "last_scan": None
        }

    def _save_stats(self):
        """Save stats to file"""
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Error saving stats: {e}")

    def increment_scan(self):
        """Increment scan counter"""
        with self.lock:
            self.stats["total_scans"] += 1
            self.stats["last_scan"] = datetime.now().isoformat()
            self._save_stats()
            return self.stats["total_scans"]

    def get_stats(self):
        """Get current stats"""
        with self.lock:
            return self.stats.copy()

# Global instance
tracker = StatsTracker()

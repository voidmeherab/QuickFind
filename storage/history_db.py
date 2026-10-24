"""
QuickFind Launch History Database
Maintains usage frequency and recency data using SQLite.
"""

import os
import sqlite3
import time
from typing import Dict, Tuple
from config import get_user_data_dir

DB_PATH = os.path.join(get_user_data_dir(), "history.db")


class HistoryDB:
    """Stores application launch counts and timestamps to optimize search rankings."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Create the launch history table and indexes if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS launch_history (
                        app_id TEXT PRIMARY KEY,
                        launch_count INTEGER DEFAULT 0,
                        last_launched REAL DEFAULT 0
                    )
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_launch_count 
                    ON launch_history(launch_count DESC)
                """)
                conn.commit()
        except Exception as e:
            print(f"[QuickFind] History DB init error: {e}")

    def record_launch(self, app_id: str) -> None:
        """Increment the launch counter and update the last launch timestamp for an app."""
        if not app_id:
            return
        try:
            now = time.time()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO launch_history (app_id, launch_count, last_launched)
                    VALUES (?, 1, ?)
                    ON CONFLICT(app_id) DO UPDATE SET
                        launch_count = launch_count + 1,
                        last_launched = ?
                """, (app_id, now, now))
                conn.commit()
        except Exception as e:
            print(f"[QuickFind] Error recording launch for '{app_id}': {e}")

    def get_all_stats(self) -> Dict[str, Tuple[int, float]]:
        """Return a mapping of app_id -> (launch_count, last_launched)."""
        stats: Dict[str, Tuple[int, float]] = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT app_id, launch_count, last_launched FROM launch_history")
                for row in cursor.fetchall():
                    stats[row[0]] = (row[1], row[2])
        except Exception as e:
            print(f"[QuickFind] Error fetching launch stats: {e}")
        return stats

    def clear_history(self) -> None:
        """Clear all recorded launch history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM launch_history")
                conn.commit()
        except Exception as e:
            print(f"[QuickFind] Error clearing history: {e}")

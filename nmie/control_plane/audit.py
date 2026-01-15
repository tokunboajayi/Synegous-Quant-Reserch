from datetime import datetime
from typing import Optional
import sqlite3
from nmie.control_plane.queue import DB_PATH

class AuditLog:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def log_event(self, entity_type: str, entity_id: str, action: str, details: str = ""):
        """
        Log an immutable event.
        entity_type: RUN | JOB | SYSTEM
        """
        conn = sqlite3.connect(self.db_path)
        timestamp = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO audit (timestamp, entity_type, entity_id, action, details) VALUES (?, ?, ?, ?, ?)",
            (timestamp, entity_type, entity_id, action, details)
        )
        conn.commit()
        conn.close()
        print(f"[AUDIT] {timestamp} {entity_type}:{entity_id} {action} - {details}")

# Global instance
auditor = AuditLog()

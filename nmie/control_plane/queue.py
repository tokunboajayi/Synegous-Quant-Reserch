import sqlite3
import json
from typing import List, Optional
from datetime import datetime
from threading import Lock

from nmie.control_plane.jobs import Job, Run
from nmie.control_plane.state import JobStatus, RunStatus

DB_PATH = "nmie_control.db"

class PersistentQueue:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = Lock()
        self._init_db()
        
    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Runs table
            c.execute('''CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                status TEXT,
                created_at TEXT,
                data JSON
            )''')
            
            # Jobs table
            c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                run_id TEXT,
                type TEXT,
                status TEXT,
                created_at TEXT,
                finished_at TEXT,
                data JSON,
                FOREIGN KEY(run_id) REFERENCES runs(run_id)
            )''')
            
            # Audit table
            c.execute('''CREATE TABLE IF NOT EXISTS audit (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                entity_type TEXT,
                entity_id TEXT,
                action TEXT,
                details TEXT
            )''')
            
            conn.commit()
            conn.close()

    def create_run(self, run: Run):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO runs (run_id, status, created_at, data) VALUES (?, ?, ?, ?)",
                (run.run_id, run.status, run.created_at.isoformat(), run.json())
            )
            conn.commit()
            conn.close()
            
    def get_run(self, run_id: str) -> Optional[Run]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            row = conn.execute("SELECT data FROM runs WHERE run_id=?", (run_id,)).fetchone()
            conn.close()
            if row:
                return Run.parse_raw(row[0])
            return None

    def update_run_status(self, run_id: str, status: RunStatus, details: dict = None):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            # We need to read-modify-write data blob OR just update status col
            # Updating blob is safer for consistency
            row = conn.execute("SELECT data FROM runs WHERE run_id=?", (run_id,)).fetchone()
            if row:
                r = Run.parse_raw(row[0])
                r.status = status
                if details:
                    # Update other fields if present (e.g. gate decision)
                    for k, v in details.items():
                        setattr(r, k, v)
                
                conn.execute(
                    "UPDATE runs SET status=?, data=? WHERE run_id=?",
                    (status, r.json(), run_id)
                )
            conn.commit()
            conn.close()

    def add_job(self, job: Job):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO jobs (job_id, run_id, type, status, created_at, data) VALUES (?, ?, ?, ?, ?, ?)",
                (job.job_id, job.run_id, job.type, job.status, job.created_at.isoformat(), job.json())
            )
            conn.commit()
            conn.close()

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            row = conn.execute("SELECT data FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            conn.close()
            if row:
                return Job.parse_raw(row[0])
            return None

    def update_job(self, job_id: str, updates: dict):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            row = conn.execute("SELECT data FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if row:
                j = Job.parse_raw(row[0])
                for k, v in updates.items():
                    setattr(j, k, v)
                
                status_val = updates.get("status", j.status)
                finished_at_val = updates.get("finished_at")
                finished_str = finished_at_val.isoformat() if finished_at_val else None

                conn.execute(
                    "UPDATE jobs SET status=?, finished_at=?, data=? WHERE job_id=?",
                    (status_val, finished_str, j.json(), job_id)
                )
            conn.commit()
            conn.close()

    def fetch_pending_jobs(self) -> List[Job]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            # Simple FIFO: Created At ASC
            rows = conn.execute(
                "SELECT data FROM jobs WHERE status=? ORDER BY created_at ASC", 
                (JobStatus.QUEUED,)
            ).fetchall()
            conn.close()
            return [Job.parse_raw(r[0]) for r in rows]

    def list_jobs_for_run(self, run_id: str) -> List[Job]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            rows = conn.execute(
                "SELECT data FROM jobs WHERE run_id=? ORDER BY created_at ASC", 
                (run_id,)
            ).fetchall()
            conn.close()
            return [Job.parse_raw(r[0]) for r in rows]

    def list_runs(self) -> List[Run]:
         with self._lock:
            conn = sqlite3.connect(self.db_path)
            rows = conn.execute("SELECT data FROM runs ORDER BY created_at DESC LIMIT 50").fetchall()
            conn.close()
            return [Run.parse_raw(r[0]) for r in rows]

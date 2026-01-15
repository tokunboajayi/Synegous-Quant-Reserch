import sqlite3
import pandas as pd
from pathlib import Path
import os

print("=== DB DEBUG START ===")
try:
    conn = sqlite3.connect('nmie_control.db')
    runs = pd.read_sql("SELECT run_id, status, created_at FROM runs ORDER BY created_at DESC LIMIT 5", conn)
    print("\n[Latest Runs]")
    print(runs)

    if not runs.empty:
        latest_id = runs.iloc[0]['run_id']
        print(f"\n[Jobs for {latest_id}]")
        jobs = pd.read_sql(f"SELECT job_id, status, data FROM jobs WHERE run_id='{latest_id}'", conn)
        print(jobs)
        
        # Check artifact dir
        # Expected path per MNXConfig (we think)
        path1 = Path(f"/app/data/outputs/{latest_id}")
        print(f"\n[Artifact Check]")
        print(f"Path: {path1} -> Exists? {path1.exists()}")
        if path1.exists():
             print(f"Contents: {os.listdir(path1)}")
             
        # Check NMIE Config path if different
        from nmie.config import DATA_DIR
        path2 = DATA_DIR / "outputs" / latest_id
        print(f"Path (NMIE): {path2} -> Exists? {path2.exists()}")
        
except Exception as e:
    print(f"ERROR: {e}")
print("=== DB DEBUG END ===")

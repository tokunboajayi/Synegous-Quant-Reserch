import requests
import time
import sys
from pathlib import Path

# Config
BASE_URL = "http://localhost:8000"
DATA_DIR = Path("data/outputs")

def wait_for_server():
    print("Waiting for server...")
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/")
            return
        except:
            time.sleep(2)
    print("Server not up.")
    sys.exit(1)

def run_test():
    wait_for_server()
    
    # 1. Trigger Full MNX Run
    print("Triggering FULL_RUN_MNX_NMIE...")
    payload = {
        "job_type": "FULL_RUN_MNX_NMIE",
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "start_date": "2023-01-01",
        "end_date": "2023-01-30",
        "n_orders": 50,
        "mnx_enabled": True
    }
    
    resp = requests.post(f"{BASE_URL}/control/runs/create", json=payload)
    if resp.status_code != 200:
        print(f"Failed to create run: {resp.text}")
        sys.exit(1)
        
    run_id = resp.json()["run_id"]
    print(f"Run ID: {run_id}")
    
    # 2. Poll for Completion
    print("Polling for completion...")
    for _ in range(30): # Wait up to 60s
        status_resp = requests.get(f"{BASE_URL}/control/runs")
        runs = status_resp.json()
        my_run = next((r for r in runs if r['run_id'] == run_id), None)
        
        if my_run:
            status = my_run['status']
            print(f"Status: {status}")
            if status == "COMPLETED":
                break
            if status == "FAILED":
                print(f"Run Failed! Error: {my_run.get('error_msg', 'Unknown Error')}")
                # Also try to fetch jobs for this run to see which step failed
                try:
                    jobs_resp = requests.get(f"{BASE_URL}/control/runs/{run_id}/jobs")
                    jobs = jobs_resp.json()
                    for j in jobs:
                        print(f" - Job {j['type']}: {j['status']} {j.get('error_msg', '')}")
                except:
                    pass
                sys.exit(1)
        
        time.sleep(2)
    else:
        print("Timeout waiting for run completion.")
        sys.exit(1)
        
    # 3. Verify Artifacts
    print("Verifying Artifacts...")
    mnx_dir = DATA_DIR / run_id / "mnx"
    nmie_dir = DATA_DIR / run_id # NMIE saves to root of run currently? Or nmie_exec?
    # Based on logic, NMIE standard pipe saves to run_dir
    
    expected_mnx = [
        "mnx_bars.parquet",
        "mnx_features_mom.parquet", 
        "mnx_scores.parquet",
        "mnx_target_weights.json",
        "mnx_rebalance_basket.parquet"
    ]
    
    missing = []
    for f in expected_mnx:
        if not (mnx_dir / f).exists():
            missing.append(f"MNX/{f}")
            
    # Expected NMIE (partial check)
    if not (nmie_dir / "tca_summary.json").exists():
        missing.append("NMIE/tca_summary.json")
        
    if missing:
        print(f"FAILED. Missing artifacts: {missing}")
        sys.exit(1)
        
    print("SUCCESS: All artifacts generated.")
    
    # 4. Check Bridge Data
    print("Verifying Bridge Data...")
    # Read basket
    import pandas as pd
    basket = pd.read_parquet(mnx_dir / "mnx_rebalance_basket.parquet")
    print(f"Basket Size: {len(basket)}")
    if len(basket) == 0:
        print("Warning: Basket is empty (Low Volatility mock data?)")
        
    print("Smoke Test Passed!")

if __name__ == "__main__":
    run_test()

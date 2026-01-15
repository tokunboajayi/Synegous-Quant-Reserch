import requests
import json
from pathlib import Path

# Config
API_URL = "http://localhost:8000/control/runs/create"
INPUTS_DIR = Path("data/inputs")

def get_stooq_universe():
    """Scan data/inputs for available tickers."""
    tickers = []
    if not INPUTS_DIR.exists():
        print(f"Error: {INPUTS_DIR} does not exist.")
        return []

    for f in INPUTS_DIR.glob("*_us_d.csv"):
        # standard stooq filename: SYMBOL_us_d.csv
        symbol = f.name.replace("_us_d.csv", "").upper()
        tickers.append(symbol)
    
    return sorted(tickers)

def main():
    print("Scanning for Stooq data...")
    universe = get_stooq_universe()
    
    if not universe:
        print("No tickers found! Run fetch_stooq.py first.")
        return

    print(f"Found {len(universe)} tickers to train on: {universe[:5]} ...")

    payload = {
        "job_type": "FULL_RUN_MNX_NMIE",
        "tickers": universe,
        "start_date": "2018-01-01",  # 5 years of training/test
        "end_date": "2023-01-01",
        "mnx_enabled": True,
        "model_params": {
            "model_type": "LGBM",
            "iterations": 100
        }
    }

    print(f"Sending job request to {API_URL}...")
    try:
        resp = requests.post(API_URL, json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        print(f"SUCCESS! Run Created.")
        print(f"Run ID: {data['run_id']}")
        print(f"Status: {data['status']}")
        print("\nGo to Dashboard > Results Viewer to monitor progress.")
        
    except Exception as e:
        print(f"Failed to launch run: {e}")
        if 'resp' in locals():
            print(f"Response: {resp.text}")

if __name__ == "__main__":
    main()

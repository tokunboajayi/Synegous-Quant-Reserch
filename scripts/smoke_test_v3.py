"""
SMOKE TEST: NMIE v3++
Verifies:
1. Pipeline V2 Imports & Granular Methods
2. Sensitivity Matrix Generation
3. Gate Logic
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from nmie.tca.pipeline_v2 import TCAPipeline
from nmie.config import DATA_DIR

def run_smoke_test():
    print(">>> Starting Smoke Test...")
    
    # 1. Initialize Pipeline
    try:
        pipeline = TCAPipeline()
        print(f"[OK] Pipeline Optimized Init: {pipeline.run_id}")
    except Exception as e:
        print(f"[FAIL] Pipeline Init: {e}")
        return

    # 2. Run for single ticker, minimal orders
    try:
        # We assume SPY data exists from previous runs/baseline
        print(">>> Executing Run...")
        result = pipeline.run(tickers=["SPY"], n_orders_per_ticker=2)
        print(f"[OK] Run Complete. ID: {result['run_id']}")
    except Exception as e:
        print(f"[FAIL] Pipeline Run: {e}")
        return

    # 3. Verify Artifacts
    run_id = result['run_id']
    output_dir = DATA_DIR / "outputs" / run_id
    
    expected_files = [
        "tca_summary.json",
        "tca_orders.json", 
        "sensitivity_matrix.csv", # E-01
        "gate_decision.json",
        "simulator_sensitivity.json"
    ]
    
    print("\n>>> Verifying Artifacts...")
    all_ok = True
    for f in expected_files:
        p = output_dir / f
        if p.exists():
             print(f"[OK] Found {f}")
        else:
             print(f"[FAIL] Missing {f}")
             all_ok = False
             
    if all_ok:
        print("\n>>> SMOKE TEST PASSED <<<")
    else:
        print("\n>>> SMOKE TEST FAILED (Missing Artifacts) <<<")

if __name__ == "__main__":
    run_smoke_test()

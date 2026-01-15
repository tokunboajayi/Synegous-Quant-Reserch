from nmie.optimizer.anee_engine import ANEEEngine
from nmie.labeling.parent_orders import ParentOrderGenerator
from nmie.store.feature_store import FeatureStore
import polars as pl
import pandas as pd

def test_anee_simulation():
    # 1. Load Data (SPY 2025-12-01 from ingestion)
    # We need to simulate an order on this day.
    # Usually we generate order from T-1 stats, but here we just pick a slice of T.
    
    store = FeatureStore()
    df_bars = store.load_bars("SPY", "2025-12-01")
    if df_bars.is_empty():
        print("No market data found for SPY 2025-12-01. Run ingestion first.")
        return

    # 2. Define Parent Order (10:00 to 11:00)
    start_str = "2025-12-01 10:00:00"
    end_str = "2025-12-01 11:00:00"
    total_shares = 10000 # Small order
    
    parent_order = {
        "order_id": "TEST_001",
        "ticker": "SPY",
        "size_shares": total_shares,
        "start_time": pd.to_datetime(start_str),
        "end_time": pd.to_datetime(end_str)
    }
    
    # 3. Run Engine
    engine = ANEEEngine()
    result = engine.run_simulation(parent_order, df_bars)
    
    if result:
        print(f"ANEE Simulation Complete for {result.parent_id}")
        print(f"Avg Price: {result.avg_exec_price:.2f}")
        print(f"Arrival Price: {result.benchmark_price:.2f}")
        print(f"IS (bps): {result.implementation_shortfall_bps:.2f}")
        print("-" * 30)
        print("Execution Trace (Head):")
        print(result.details.head())
        print("Execution Trace (Tail):")
        print(result.details.tail())
        
        # Verify Completion
        executed = result.details["q_exec"].sum()
        print(f"Total Executed: {executed} / {total_shares}")
        
    else:
        print("Simulation returned None.")

if __name__ == "__main__":
    test_anee_simulation()

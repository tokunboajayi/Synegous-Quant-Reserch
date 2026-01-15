from nmie.counterfactual.evaluate_anee import compare_strategies, run_counterfactual_suite
from nmie.store.feature_store import FeatureStore
import pandas as pd

def test_counterfactual():
    store = FeatureStore()
    df_bars = store.load_bars("SPY", "2025-12-01")
    if df_bars.is_empty():
        print("No data for SPY 2025-12-01")
        return
        
    # Define 3 test orders
    orders = [
        {
            "order_id": "TEST_001",
            "ticker": "SPY",
            "size_shares": 5000,
            "start_time": pd.to_datetime("2025-12-01 10:00:00"),
            "end_time": pd.to_datetime("2025-12-01 11:00:00")
        },
        {
            "order_id": "TEST_002",
            "ticker": "SPY",
            "size_shares": 10000,
            "start_time": pd.to_datetime("2025-12-01 11:00:00"),
            "end_time": pd.to_datetime("2025-12-01 12:00:00")
        },
        {
            "order_id": "TEST_003",
            "ticker": "SPY",
            "size_shares": 8000,
            "start_time": pd.to_datetime("2025-12-01 14:00:00"),
            "end_time": pd.to_datetime("2025-12-01 15:00:00")
        },
    ]
    
    print("Running Counterfactual Suite...")
    results_df = run_counterfactual_suite(orders, df_bars)
    
    print(results_df)
    
    # Summary Stats
    print("\n--- Summary ---")
    print(f"Mean IS ANEE: {results_df['IS_ANEE'].mean():.2f} bps")
    print(f"Mean IS TWAP: {results_df['IS_TWAP'].mean():.2f} bps")
    print(f"Mean IS VWAP: {results_df['IS_VWAP'].mean():.2f} bps")
    print(f"Mean ANEE vs TWAP: {results_df['ANEE_vs_TWAP'].mean():.2f} bps")

if __name__ == "__main__":
    test_counterfactual()

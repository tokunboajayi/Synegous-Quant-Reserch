import argparse
import polars as pl
import pandas as pd
from pathlib import Path

from nmie.config import DATA_DIR
from nmie.store.feature_store import FeatureStore
from nmie.labeling.parent_orders import ParentOrderGenerator
from nmie.labeling.impact_labels import ImpactLabeler

def main():
    parser = argparse.ArgumentParser(description="Generate IS labels for parent orders")
    parser.add_argument("--ticker", type=str, default="SPY", help="Ticker to label")
    parser.add_argument("--date", type=str, required=True, help="Date to label (YYYY-MM-DD)")
    parser.add_argument("--n-orders", type=int, default=10, help="Number of orders to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    # Load market data
    store = FeatureStore()
    bars = store.load_bars(args.ticker, args.date)
    
    if bars.is_empty():
        print(f"No data for {args.ticker} on {args.date}")
        return
        
    print(f"Loaded {bars.height} bars for {args.ticker} on {args.date}")
    
    # Generate parent orders
    # Note: Parent orders for date T need T-1 stats for ADV
    # Here we generate orders for the provided date
    gen = ParentOrderGenerator(seed=args.seed)
    orders_df = gen.generate_orders(args.ticker, args.date, n_orders=args.n_orders)
    
    if orders_df.is_empty():
        print("No orders generated (missing history for ADV)")
        return
        
    print(f"Generated {orders_df.height} parent orders")
    
    # Convert to list of dicts
    orders = orders_df.to_dicts()
    
    # Label
    labeler = ImpactLabeler()
    labels_df = labeler.label_batch(orders, bars, policies=["TWAP", "VWAP", "POV"])
    
    print(f"Generated {len(labels_df)} labels")
    print(labels_df.head(10))
    
    # Save
    output_dir = DATA_DIR / "labels"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"impact_labels_{args.ticker}_{args.date}.parquet"
    
    labels_df.to_parquet(output_path)
    print(f"Saved to {output_path}")
    
    # Summary stats
    print("\n--- Label Summary ---")
    print(f"Mean IS (TWAP): {labels_df[labels_df['policy']=='TWAP']['is_bps'].mean():.2f} bps")
    print(f"Mean IS (VWAP): {labels_df[labels_df['policy']=='VWAP']['is_bps'].mean():.2f} bps")
    print(f"Mean IS (POV): {labels_df[labels_df['policy']=='POV']['is_bps'].mean():.2f} bps")

if __name__ == "__main__":
    main()

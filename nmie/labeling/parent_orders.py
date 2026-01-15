import random
import polars as pl
from datetime import datetime, timedelta
from typing import List, Dict
from nmie.store.feature_store import FeatureStore

class ParentOrderGenerator:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.store = FeatureStore()
        
    def generate_orders(self, ticker: str, date_str: str, n_orders: int = 5) -> pl.DataFrame:
        """
        Generates deterministic synthetic parent orders for a given ticker/day.
        """
        # 1. Get reference data (Prev Day ADV)
        # Reseed rng based on ticker+date to ensure consistent orders 
        # regardless of call order
        seed_str = f"{self.seed}_{ticker}_{date_str}"
        local_rng = random.Random(seed_str)
        
        stats = self.store.get_prev_day_stats(ticker, date_str)
        if not stats:
            # Fallback if no history (e.g. first day of ingestion): Skip
            print(f"Skipping {ticker} on {date_str}: No history for ADV.")
            return pl.DataFrame()
            
        adv = stats["volume"]
        
        orders = []
        
        # Market structure
        mkt_open = datetime.strptime(f"{date_str} 09:30:00", "%Y-%m-%d %H:%M:%S")
        mkt_close = datetime.strptime(f"{date_str} 16:00:00", "%Y-%m-%d %H:%M:%S")
        total_minutes = (mkt_close - mkt_open).seconds // 60
        
        for _ in range(n_orders):
            # Sample parameters
            # 1. Horizon (minutes)
            horizon_mins = local_rng.choice([30, 60, 120])
            
            # 2. Start Time
            # Must finish before close. Latest start = close - horizon
            latest_start_min = total_minutes - horizon_mins
            if latest_start_min <= 0:
                continue
                
            start_offset = local_rng.randint(0, latest_start_min)
            start_dt = mkt_open + timedelta(minutes=start_offset)
            end_dt = start_dt + timedelta(minutes=horizon_mins)
            
            # 3. Size (% of ADV)
            # 1%, 5%, 10% buckets with some noise
            pct_bucket = local_rng.choice([0.01, 0.05, 0.10])
            # Add small noise +/- 10% of the bucket value to avoid discrete artifacts
            noise = local_rng.uniform(0.9, 1.1) 
            target_frac = pct_bucket * noise
            
            size_shares = int(adv * target_frac)
            
            # 4. Side (Buy/Sell)
            side = local_rng.choice(["BUY", "SELL"])
            
            orders.append({
                "order_id": f"{ticker}_{date_str}_{len(orders)}",
                "ticker": ticker,
                "date": date_str,
                "start_time": start_dt,
                "end_time": end_dt,
                "horizon_mins": horizon_mins,
                "side": side,
                "size_shares": size_shares,
                "pct_adv": target_frac,
                "ref_adv": adv
            })
            
        if not orders:
            return pl.DataFrame()
            
        df = pl.DataFrame(orders)
        
        # Cast timestamps
        df = df.with_columns([
            pl.col("start_time").cast(pl.Datetime),
            pl.col("end_time").cast(pl.Datetime)
        ])
        
        return df

if __name__ == "__main__":
    # Test
    gen = ParentOrderGenerator()
    # Assuming we have data for 'SPY' on '2025-12-02' (requires '2025-12-01' exists)
    print("Testing Parent Order Generation...")
    
    # We need to ingest another day to have 'prev day' data
    # or just Mock the store for this specific unit test if we don't want to run ingestion
    # But let's assume we ran the ingestion for 2025-12-01 earlier.
    # Now lets try to generate orders for 2025-12-02 (which doesn't exist in data/raw yet? 
    # Wait, the Generator needs PREV day. So if I want orders for T, I need T-1.
    # If I only have T=2025-12-01, I can generate orders for T+1=2025-12-02 using T stats.)
    
    df = gen.generate_orders("SPY", "2025-12-02")
    if not df.is_empty():
        print(df)
    else:
        print("No orders generated (likely missing history).")

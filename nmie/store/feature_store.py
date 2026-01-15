import polars as pl
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from nmie.config import DATA_DIR

class FeatureStore:
    def __init__(self):
        self.bars_dir = DATA_DIR / "raw" / "bars"
    
    def _get_path(self, date_str: str) -> Path:
        return self.bars_dir / f"data_{date_str}.parquet"

    def load_bars(self, ticker: str, date_str: str) -> pl.DataFrame:
        """
        Loads 1-minute bars for a specific ticker and date.
        """
        path = self._get_path(date_str)
        if not path.exists():
            return pl.DataFrame()
        
        # We scan parquet for efficiency if files are huge, 
        # but daily files are small enough to read.
        # Filter for the specific ticker.
        try:
            df = pl.read_parquet(path)
            df = df.filter(pl.col("ticker") == ticker)
            return df
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return pl.DataFrame()

    def get_prev_day_stats(self, ticker: str, current_date_str: str) -> dict:
        """
        Returns stats (Volume, Close) from the previous available trading day.
        Used for calculating ADV and reference prices without lookahead.
        """
        # Find all available date files
        all_files = sorted(list(self.bars_dir.glob("data_*.parquet")))
        if not all_files:
            return {}
        
        # Extract dates
        dates = [f.stem.replace("data_", "") for f in all_files]
        dates.sort()
        
        try:
            curr_idx = dates.index(current_date_str)
        except ValueError:
            # If current date not found (maybe not ingested yet), 
            # we try to find the insertion point/most recent before it
            # For now, let's just return empty if exact date logic fails 
            # or implement a bisect if needed. 
            # Simpler: just filter for dates < current_date_str
            valid_dates = [d for d in dates if d < current_date_str]
            if not valid_dates:
                return {}
            prev_date = valid_dates[-1]
        else:
            if curr_idx == 0:
                return {} # No history
            prev_date = dates[curr_idx - 1]
            
        # Load previous day data
        df = self.load_bars(ticker, prev_date)
        if df.is_empty():
            return {}
            
        # Calculate stats
        total_vol = df["volume"].sum()
        last_close = df["close"].tail(1)[0]
        
        return {
            "date": prev_date,
            "volume": total_vol,
            "last_close": last_close
        }

    def get_market_hours(self) -> tuple:
        # Simplified: 9:30 - 16:00
        # In prod, read from calendar or data
        return (9, 30), (16, 0)

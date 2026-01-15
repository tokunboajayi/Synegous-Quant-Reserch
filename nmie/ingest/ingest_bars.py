import requests
import pandas as pd
import polars as pl
import time
from datetime import datetime, timedelta
from pathlib import Path
from nmie.config import POLYGON_API_KEY, DATA_DIR, START_DATE, END_DATE
from nmie.store.schemas import BAR_SCHEMA

class PolygonClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or POLYGON_API_KEY
        if not self.api_key:
            raise ValueError("POLYGON_API_KEY not found in environment or config.")
        self.base_url = "https://api.polygon.io"
    
    def fetch_bars(self, ticker: str, date: str, timeframe: int = 1, timespan: str = 'minute') -> pd.DataFrame:
        """
        Fetch intraday bars for a single ticker on a single day.
        """
        # Endpoint: /v2/aggs/ticker/{stocksTicker}/range/{multiplier}/{timespan}/{from}/{to}
        endpoint = f"/v2/aggs/ticker/{ticker}/range/{timeframe}/{timespan}/{date}/{date}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "limit": 50000,
            "apiKey": self.api_key
        }
        
        url = self.base_url + endpoint
        
        retries = 3
        delay = 1
        
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 429:
                    print(f"Rate limited for {ticker} on {date}. Retrying in 12s...")
                    time.sleep(12)
                    continue
                    
                response.raise_for_status()
                data = response.json()
                break
            except Exception as e:
                print(f"Error fetching {ticker} on {date}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    return pd.DataFrame()
        else:
             print(f"Failed to fetch {ticker} on {date} after retries.")
             return pd.DataFrame()

        if data.get("resultsCount", 0) == 0:
            # print(f"Warning: No results for {ticker} on {date}. Response: {data}")
            return pd.DataFrame()
            
        results = data.get("results", [])
        df = pd.DataFrame(results)
        
        # Rename columns to match schema
        # Polygon: t (timestamp), o, h, l, c, v (volume), vw (vwap), n (transactions)
        rename_map = {
            "t": "timestamp",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
            "vw": "vwap",
            "n": "trade_count"
        }
        df = df.rename(columns=rename_map)
        
        # Convert timestamp (ms) to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df["ticker"] = ticker
        
        return df

def ingest_range(tickers: list, start_date: str, end_date: str):
    """
    Orchestrates the download/ingestion of bar data for a list of tickers over a date range.
    Saves daily parquet files.
    """
    client = PolygonClient()
    
    # Generate date range
    dates = pd.bdate_range(start=start_date, end=end_date)
    
    # Store directory
    raw_dir = DATA_DIR / "raw" / "bars"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    for date_obj in dates:
        date_str = date_obj.strftime("%Y-%m-%d")
        daily_dfs = []
        
        print(f"Processing {date_str}...")
        
        for ticker in tickers:
            # Check if already exists to avoid re-downloading
            # (In a real system we'd have more robust incremental checks)
            
            try:
                df = client.fetch_bars(ticker, date_str)
                if not df.empty:
                    daily_dfs.append(df)
                time.sleep(0.02) # Rate limit padding just in case
            except Exception as e:
                print(f"Failed {ticker} {date_str}: {e}")
        
        if daily_dfs:
            combined_df = pd.concat(daily_dfs, ignore_index=True)
            
            # Convert to Polars for schema enforcement and save
            pl_df = pl.from_pandas(combined_df)
            
            # Cast types to match schema strictly
            pl_df = pl_df.with_columns([
                pl.col("timestamp").dt.cast_time_unit("ms"),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                pl.col("volume").cast(pl.Float64),
                pl.col("vwap").cast(pl.Float64),
                pl.col("trade_count").cast(pl.Float64),
                pl.col("ticker").cast(pl.Utf8)
            ])
            
            # Save partition
            output_path = raw_dir / f"data_{date_str}.parquet"
            pl_df.write_parquet(output_path)
            print(f"Saved {len(pl_df)} rows to {output_path}")
            
            # OPTIMIZATION A-01: Ingestion Manifest
            # We append to a manifest file (or overwrite daily entry)
            manifest_path = DATA_DIR / "raw" / "ingestion_manifest.json"
            manifest_entry = {
                "date": date_str,
                "timestamp": datetime.utcnow().isoformat(),
                "tickers": tickers,
                "row_counts": {t: len(pl_df.filter(pl.col("ticker")==t)) for t in tickers},
                "total_rows": len(pl_df),
                "status": "SUCCESS"
            }
            
            # Simple append-only log in JSON Lines format? Or load-update-save JSON?
            # JSON Lines is safer for concurrency/append.
            with open(manifest_path, "a") as f:
                import json
                f.write(json.dumps(manifest_entry) + "\n")

        else:
            print(f"No data for {date_str}")
            # Log failure to manifest
            manifest_path = DATA_DIR / "raw" / "ingestion_manifest.json"
            with open(manifest_path, "a") as f:
                import json
                f.write(json.dumps({
                    "date": date_str, 
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "NO_DATA"
                }) + "\n")

if __name__ == "__main__":
    from nmie.ingest.universe import get_universe
    universe = get_universe()
    # Test run for 1 ticker 1 day if run directly
    print(f"Testing ingestion for SPY on {START_DATE}")
    client = PolygonClient()
    # Use yesterday or specific date to ensure data exists
    test_date = "2023-01-03" 
    df = client.fetch_bars("SPY", test_date)
    print(df.head())
    print(df.info())

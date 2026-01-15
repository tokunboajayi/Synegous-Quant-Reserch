import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def ingest_daily_bars(tickers: list, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Ingest daily bars from Polygon (or Mock for now).
    Returns DataFrame with MultiIndex (ticker, date).
    """
    print(f"[MNX Ingest] Fetching {len(tickers)} tickers from {start_date} to {end_date}")
    
    dates = pd.date_range(start_date, end_date, freq='B')
    dfs = []
    
    from pathlib import Path
    INPUTS_DIR = Path("data/inputs")
    
    # 0. Fast Path: Parquet Cache
    # If the unified parquet exists, use it significantly faster
    cache_path = INPUTS_DIR / "mnx_inputs.parquet"
    if cache_path.exists():
        print(f"[MNX Ingest] Fast Path: Loading from {cache_path}")
        try:
            full_data = pd.read_parquet(cache_path)
            
            # Filter Date
            mask = (full_data["date"] >= start_date) & (full_data["date"] <= end_date)
            # Filter Tickers (only if in request)
            mask &= full_data["ticker"].isin(tickers)
            
            df = full_data.loc[mask].copy()
            
            # Handle missing tickers by filling with mock (optional)
            found_tickers = df["ticker"].unique()
            missing = set(tickers) - set(found_tickers)
            
            if missing:
                print(f"[MNX Ingest] Warning: {len(missing)} tickers not in cache (e.g. {list(missing)[:3]}).")
                # We could run the CSV/Mock loop for missing ones, but for now let's just use what we have
                # Or we can append mock data for them?
                # Let's simple return what we have, the pipeline handles missing data
            
            return df.set_index(["ticker", "date"])

        except Exception as e:
            print(f"[MNX Ingest] Error reading parquet cache: {e}. Falling back to CSVs.")

    for ticker in tickers:
        # Check for local CSV (Polish format from Stooq/User)
        
        if found_csv:
            print(f"[MNX Ingest] Found local CSV for {ticker}: {found_csv}")
            try:
                # Load Polish format: Data, Otwarcie, Najwyzszy, Najnizszy, Zamkniecie, Wolumen
                raw = pd.read_csv(found_csv)
                
                # Normalize columns
                raw = raw.rename(columns={
                    "Data": "date",
                    "Zamkniecie": "close",
                    "Wolumen": "volume",
                    "Date": "date",       # Support English too
                    "Close": "close",
                    "Volume": "volume"
                })
                
                # Parse Dates
                raw["date"] = pd.to_datetime(raw["date"])
                
                # Filter range
                mask = (raw["date"] >= start_date) & (raw["date"] <= end_date)
                df = raw.loc[mask].copy()
                
                if df.empty:
                    print(f"[MNX Ingest] Warning: CSV for {ticker} has no data in requested range. Using mock.")
                else:
                    df["ticker"] = ticker
                    df = df.set_index("date")
                    # Ensure reindexed to business days to fill gaps if needed (optional)
                    # For now just use available data
                    dfs.append(df[["close", "volume", "ticker"]])
                    continue
                    
            except Exception as e:
                print(f"[MNX Ingest] Error reading CSV {found_csv}: {e}. Falling back to mock.")

        # Fallback: Mock Data Generator
        df = pd.DataFrame(index=dates)
        returns = np.random.normal(0, 0.02, size=len(dates))
        price = 100 * np.exp(np.cumsum(returns))
        
        df['close'] = price
        df['volume'] = np.random.randint(100000, 5000000, size=len(dates))
        df['ticker'] = ticker
        dfs.append(df)
        
    full_df = pd.concat(dfs)
    return full_df.reset_index().rename(columns={'index': 'date'}).set_index(['ticker', 'date'])

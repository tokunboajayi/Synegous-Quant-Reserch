"""
Live Data Provider
Fetches and caches real-time market data from public APIs.
Primary provider: yfinance (Yahoo Finance).
"""
import yfinance as yf

import pandas as pd
import numpy as np
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("live_data")

class LiveDataProvider:
    """
    Centralized manager for fetching live market data.
    Uses yfinance for free, real-time-ish (15m delay) OHLCV data.
    """
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: Dict[str, pd.DataFrame] = {}

    def fetch_current_prices(self, tickers: List[str]) -> pd.DataFrame:
        """
        Fetch the most recent daily price data for a list of tickers.
        Useful for Market Regime Detection and quick validation.
        """
        logger.info(f"Fetching current prices for {len(tickers)} tickers...")
        
        try:
            # Download recent data (last 30 days to ensure enough for volatility calc)
            data = yf.download(tickers, period="1mo", interval="1d", group_by='ticker', progress=False)
            
            if data.empty:
                logger.warning("No data returned from yfinance")
                return pd.DataFrame()

            all_dfs = []
            for ticker in tickers:
                if ticker in data.columns.levels[0]:
                    df = data[ticker].copy()
                    df['ticker'] = ticker
                    df.reset_index(inplace=True)
                    df.columns = [c.lower() for c in df.columns]
                    all_dfs.append(df)
            
            if not all_dfs:
                return pd.DataFrame()
                
            combined = pd.concat(all_dfs, ignore_index=True)
            return combined

        except Exception as e:
            logger.error(f"Error fetching live prices: {e}")
            return pd.DataFrame()

    def get_backtest_data(self, tickers: List[str], start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetch historical data for a specific range to use in a backtest.
        """
        cache_key = f"{'_'.join(tickers)}_{start_date}_{end_date}"
        if cache_key in self.memory_cache:
            return self.memory_cache[cache_key]

        logger.info(f"Fetching historical data for backtest: {tickers} from {start_date}")
        
        try:
            data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', progress=False)
            
            if data.empty:
                return pd.DataFrame()

            all_dfs = []
            # Handle single vs multi ticker return format
            if len(tickers) == 1:
                df = data.copy()
                df['ticker'] = tickers[0]
                df.reset_index(inplace=True)
                df.columns = [c.lower() for c in df.columns]
                all_dfs.append(df)
            else:
                for ticker in tickers:
                    if ticker in data.columns.levels[0]:
                        df = data[ticker].copy()
                        df['ticker'] = ticker
                        df.reset_index(inplace=True)
                        df.columns = [c.lower() for c in df.columns]
                        all_dfs.append(df)
            
            if not all_dfs:
                return pd.DataFrame()

            combined = pd.concat(all_dfs, ignore_index=True)
            self.memory_cache[cache_key] = combined
            return combined

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return pd.DataFrame()

# Global Instance
live_provider = LiveDataProvider()

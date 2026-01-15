import pandas as pd
import numpy as np

def compute_momentum(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Calculate returns over window."""
    return prices.pct_change(window)

def compute_volatility(prices: pd.DataFrame, window: int) -> pd.DataFrame:
    """Calculate rolling volatility (annualized)."""
    return prices.pct_change(1).rolling(window).std() * np.sqrt(252)

def compute_relative_volume(volume: pd.DataFrame, window: int) -> pd.DataFrame:
    """Calculate volume relative to moving average."""
    return volume / volume.rolling(window).mean()

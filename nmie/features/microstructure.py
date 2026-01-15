import numpy as np
import polars as pl
from typing import List

def compute_features(bars: pl.DataFrame, lookback: int = 20) -> pl.DataFrame:
    """
    Computes microstructure features from 1-minute bar data.
    
    Features:
    - rolling_spread: Rolling mean of (high-low)/mid
    - rolling_volatility: Rolling std of returns
    - volume_imbalance: (Vol - RollingMean) / RollingStd
    - time_sin, time_cos: Intraday seasonality embeddings
    - vwap_deviation: (Close - VWAP) / VWAP
    """
    df = bars.clone()
    
    # Ensure sorted
    df = df.sort("timestamp")
    
    # Mid price
    df = df.with_columns([
        ((pl.col("high") + pl.col("low")) / 2).alias("mid")
    ])
    
    # Returns
    df = df.with_columns([
        (pl.col("close") / pl.col("close").shift(1) - 1).alias("return")
    ])
    
    # Rolling Spread (proxy for bid-ask spread)
    df = df.with_columns([
        ((pl.col("high") - pl.col("low")) / pl.col("mid"))
        .rolling_mean(window_size=lookback)
        .alias("rolling_spread")
    ])
    
    # Rolling Volatility
    df = df.with_columns([
        pl.col("return")
        .rolling_std(window_size=lookback)
        .alias("rolling_volatility")
    ])
    
    # Volume Imbalance (Z-score)
    df = df.with_columns([
        pl.col("volume").rolling_mean(window_size=lookback).alias("vol_mean"),
        pl.col("volume").rolling_std(window_size=lookback).alias("vol_std")
    ])
    df = df.with_columns([
        ((pl.col("volume") - pl.col("vol_mean")) / (pl.col("vol_std") + 1e-9))
        .alias("volume_imbalance")
    ])
    
    # VWAP Deviation
    df = df.with_columns([
        ((pl.col("close") - pl.col("vwap")) / (pl.col("vwap") + 1e-9))
        .alias("vwap_deviation")
    ])
    
    # Intraday Seasonality (Time of Day)
    # Extract hour and minute, convert to fraction of day
    df = df.with_columns([
        pl.col("timestamp").dt.hour().alias("hour"),
        pl.col("timestamp").dt.minute().alias("minute")
    ])
    df = df.with_columns([
        ((pl.col("hour") * 60 + pl.col("minute")) / (24 * 60) * 2 * np.pi).alias("time_rad")
    ])
    df = df.with_columns([
        pl.col("time_rad").sin().alias("time_sin"),
        pl.col("time_rad").cos().alias("time_cos")
    ])
    
    # Select final features
    feature_cols = [
        "timestamp", "ticker",
        "rolling_spread", "rolling_volatility", "volume_imbalance",
        "vwap_deviation", "time_sin", "time_cos"
    ]
    
    # Fill nulls from rolling window warmup
    df = df.with_columns([
        pl.col(c).fill_null(0) for c in feature_cols if c not in ["timestamp", "ticker"]
    ])
    
    return df.select([c for c in feature_cols if c in df.columns])

def aggregate_features_for_order(
    bars: pl.DataFrame, 
    start_time, 
    end_time,
    features_df: pl.DataFrame = None
) -> dict:
    """
    Aggregates features for a specific order horizon.
    Returns summary stats to use as model input.
    """
    import datetime
    
    # Handle timezone
    tz = bars["timestamp"].dtype.time_zone
    if tz == "UTC":
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=datetime.timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=datetime.timezone.utc)
    
    if features_df is None:
        features_df = compute_features(bars)
        
    horizon = features_df.filter(
        (pl.col("timestamp") >= start_time) & 
        (pl.col("timestamp") < end_time)
    )
    
    if horizon.height == 0:
        return {}
        
    return {
        "mean_spread": horizon["rolling_spread"].mean(),
        "max_spread": horizon["rolling_spread"].max(),
        "mean_volatility": horizon["rolling_volatility"].mean(),
        "max_volatility": horizon["rolling_volatility"].max(),
        "mean_vol_imbalance": horizon["volume_imbalance"].mean(),
        "mean_vwap_dev": horizon["vwap_deviation"].mean(),
        "time_sin": horizon["time_sin"].mean(),
        "time_cos": horizon["time_cos"].mean(),
        "horizon_bars": horizon.height
    }

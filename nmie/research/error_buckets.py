"""
Error Buckets
Failure mode bucketing by regime.
"""
import numpy as np
import pandas as pd
import polars as pl
from typing import List, Dict
from dataclasses import dataclass

from nmie.research.types import ErrorBucket

def bucket_by_volatility(
    results_df: pd.DataFrame,
    vol_column: str = "volatility",
    n_buckets: int = 5
) -> List[ErrorBucket]:
    """Bucket errors by volatility regime."""
    if vol_column not in results_df.columns or len(results_df) == 0:
        return []
        
    results_df = results_df.copy()
    results_df["vol_bucket"] = pd.qcut(
        results_df[vol_column], 
        q=n_buckets, 
        labels=[f"vol_q{i+1}" for i in range(n_buckets)],
        duplicates='drop'
    )
    
    buckets = []
    for bucket_name, group in results_df.groupby("vol_bucket", observed=True):
        is_col = "IS_ANEE" if "IS_ANEE" in group.columns else "is_anee"
        if is_col not in group.columns:
            continue
            
        buckets.append(ErrorBucket(
            bucket_name=str(bucket_name),
            n_orders=len(group),
            mean_is=float(group[is_col].mean()),
            p95_is=float(np.percentile(group[is_col], 95)),
            regime_tags=["volatility"]
        ))
        
    return sorted(buckets, key=lambda x: -x.mean_is)

def bucket_by_liquidity(
    results_df: pd.DataFrame,
    spread_column: str = "spread",
    n_buckets: int = 5
) -> List[ErrorBucket]:
    """Bucket errors by liquidity/spread regime."""
    if spread_column not in results_df.columns or len(results_df) == 0:
        return []
        
    results_df = results_df.copy()
    results_df["liq_bucket"] = pd.qcut(
        results_df[spread_column],
        q=n_buckets,
        labels=[f"spread_q{i+1}" for i in range(n_buckets)],
        duplicates='drop'
    )
    
    buckets = []
    for bucket_name, group in results_df.groupby("liq_bucket", observed=True):
        is_col = "IS_ANEE" if "IS_ANEE" in group.columns else "is_anee"
        if is_col not in group.columns:
            continue
            
        buckets.append(ErrorBucket(
            bucket_name=str(bucket_name),
            n_orders=len(group),
            mean_is=float(group[is_col].mean()),
            p95_is=float(np.percentile(group[is_col], 95)),
            regime_tags=["liquidity"]
        ))
        
    return sorted(buckets, key=lambda x: -x.mean_is)

def bucket_by_time_of_day(
    results_df: pd.DataFrame,
    time_column: str = "start_time"
) -> List[ErrorBucket]:
    """Bucket errors by time of day."""
    if time_column not in results_df.columns or len(results_df) == 0:
        return []
    
    results_df = results_df.copy()
    
    # Extract hour
    try:
        results_df["hour"] = pd.to_datetime(results_df[time_column]).dt.hour
    except:
        return []
    
    # Create buckets
    def classify_time(h):
        if h < 10:
            return "open_hour"
        elif h < 12:
            return "mid_morning"
        elif h < 14:
            return "midday"
        elif h < 15:
            return "mid_afternoon"
        else:
            return "close_hour"
    
    results_df["time_bucket"] = results_df["hour"].apply(classify_time)
    
    buckets = []
    for bucket_name, group in results_df.groupby("time_bucket"):
        is_col = "IS_ANEE" if "IS_ANEE" in group.columns else "is_anee"
        if is_col not in group.columns:
            continue
            
        buckets.append(ErrorBucket(
            bucket_name=str(bucket_name),
            n_orders=len(group),
            mean_is=float(group[is_col].mean()),
            p95_is=float(np.percentile(group[is_col], 95)),
            regime_tags=["time_of_day"]
        ))
        
    return sorted(buckets, key=lambda x: -x.mean_is)

def compute_all_error_buckets(
    results_df: pd.DataFrame
) -> List[ErrorBucket]:
    """Compute all error buckets and return worst ones."""
    all_buckets = []
    
    all_buckets.extend(bucket_by_volatility(results_df))
    all_buckets.extend(bucket_by_liquidity(results_df))
    all_buckets.extend(bucket_by_time_of_day(results_df))
    
    # Sort by worst mean IS
    sorted_buckets = sorted(all_buckets, key=lambda x: -x.mean_is)
    
    return sorted_buckets[:10]  # Top 10 worst buckets

def buckets_to_dataframe(buckets: List[ErrorBucket]) -> pd.DataFrame:
    """Convert error buckets to DataFrame."""
    if not buckets:
        return pd.DataFrame()
        
    return pd.DataFrame([
        {
            "bucket_name": b.bucket_name,
            "n_orders": b.n_orders,
            "mean_is": b.mean_is,
            "p95_is": b.p95_is,
            "regime_tags": ",".join(b.regime_tags)
        }
        for b in buckets
    ])

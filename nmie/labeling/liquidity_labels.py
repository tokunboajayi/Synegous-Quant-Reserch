import numpy as np
import polars as pl
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class LiquidityEvent:
    timestamp: str
    event_type: str  # 'spread_blowout', 'volume_collapse'
    severity: float  # Z-score or magnitude

def detect_liquidity_events(
    bars: pl.DataFrame,
    spread_threshold_z: float = 2.0,
    volume_threshold_pct: float = 0.3
) -> List[LiquidityEvent]:
    """
    Detects liquidity shock events from bar data.
    
    Events:
    - Spread blowout: (High-Low)/Mid > mean + threshold_z * std
    - Volume collapse: Volume < threshold_pct * rolling_mean
    """
    df = bars.clone().sort("timestamp")
    
    if df.height < 20:
        return []
        
    # Compute spread
    df = df.with_columns([
        ((pl.col("high") - pl.col("low")) / 
         ((pl.col("high") + pl.col("low")) / 2 + 1e-9)).alias("spread")
    ])
    
    # Rolling stats for spread
    df = df.with_columns([
        pl.col("spread").rolling_mean(window_size=20).alias("spread_mean"),
        pl.col("spread").rolling_std(window_size=20).alias("spread_std")
    ])
    
    # Rolling volume
    df = df.with_columns([
        pl.col("volume").rolling_mean(window_size=20).alias("vol_mean")
    ])
    
    # Z-score for spread
    df = df.with_columns([
        ((pl.col("spread") - pl.col("spread_mean")) / 
         (pl.col("spread_std") + 1e-9)).alias("spread_z")
    ])
    
    # Volume ratio
    df = df.with_columns([
        (pl.col("volume") / (pl.col("vol_mean") + 1e-9)).alias("vol_ratio")
    ])
    
    events = []
    
    # Detect spread blowouts
    blowouts = df.filter(pl.col("spread_z") > spread_threshold_z)
    for row in blowouts.iter_rows(named=True):
        events.append(LiquidityEvent(
            timestamp=str(row["timestamp"]),
            event_type="spread_blowout",
            severity=row["spread_z"]
        ))
        
    # Detect volume collapses
    collapses = df.filter(pl.col("vol_ratio") < volume_threshold_pct)
    for row in collapses.iter_rows(named=True):
        events.append(LiquidityEvent(
            timestamp=str(row["timestamp"]),
            event_type="volume_collapse",
            severity=1.0 - row["vol_ratio"]
        ))
        
    return events

def create_survival_labels(
    bars: pl.DataFrame,
    horizon_mins: int = 30
) -> pl.DataFrame:
    """
    Creates time-to-event labels for survival modeling.
    
    For each bar, labels:
    - time_to_event: Minutes until next liquidity event
    - event_occurred: 1 if event within horizon, 0 otherwise (censored)
    """
    df = bars.clone().sort("timestamp")
    
    # Detect events
    events = detect_liquidity_events(df)
    
    if len(events) == 0:
        # No events - all censored
        df = df.with_columns([
            pl.lit(horizon_mins).alias("time_to_event"),
            pl.lit(0).alias("event_occurred")
        ])
        return df.select(["timestamp", "time_to_event", "event_occurred"])
        
    # Get event timestamps
    event_times = sorted([e.timestamp for e in events])
    
    # For each bar, find time to next event
    labels = []
    timestamps = df["timestamp"].to_list()
    
    for i, ts in enumerate(timestamps):
        ts_str = str(ts)
        
        # Find next event after this bar
        future_events = [e for e in event_times if e > ts_str]
        
        if len(future_events) == 0:
            # No future events - censored at horizon
            labels.append({
                "timestamp": ts,
                "time_to_event": horizon_mins,
                "event_occurred": 0
            })
        else:
            # Time to next event (in bars/minutes)
            next_event_idx = None
            for j, ts_j in enumerate(timestamps[i:]):
                if str(ts_j) >= future_events[0]:
                    next_event_idx = j
                    break
                    
            if next_event_idx is not None and next_event_idx <= horizon_mins:
                labels.append({
                    "timestamp": ts,
                    "time_to_event": next_event_idx,
                    "event_occurred": 1
                })
            else:
                labels.append({
                    "timestamp": ts,
                    "time_to_event": horizon_mins,
                    "event_occurred": 0
                })
                
    return pl.DataFrame(labels)

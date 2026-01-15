"""
TCA - Regime Slicing
Performance analysis by market regime.
"""
import numpy as np
import polars as pl
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class RegimeType(Enum):
    HIGH_VOL = "high_volatility"
    LOW_VOL = "low_volatility"
    WIDE_SPREAD = "wide_spread"
    TIGHT_SPREAD = "tight_spread"
    HIGH_LIQUIDITY = "high_liquidity"
    LOW_LIQUIDITY = "low_liquidity"
    OPEN_HOUR = "open_hour"
    MIDDAY = "midday"
    CLOSE_HOUR = "close_hour"
    NORMAL = "normal"

@dataclass
class RegimeSlice:
    """Performance metrics for a regime slice."""
    regime: str
    n_orders: int
    mean_is_bps: float
    median_is_bps: float
    p90_is_bps: float
    p95_is_bps: float
    win_rate_vs_twap: float

def classify_volatility_regime(
    volatility: float,
    vol_p75: float
) -> RegimeType:
    """Classify high/low volatility."""
    if volatility >= vol_p75:
        return RegimeType.HIGH_VOL
    return RegimeType.LOW_VOL

def classify_spread_regime(
    spread: float,
    spread_p75: float
) -> RegimeType:
    """Classify wide/tight spread."""
    if spread >= spread_p75:
        return RegimeType.WIDE_SPREAD
    return RegimeType.TIGHT_SPREAD

def classify_liquidity_regime(
    volume: float,
    vol_p25: float
) -> RegimeType:
    """Classify high/low liquidity."""
    if volume <= vol_p25:
        return RegimeType.LOW_LIQUIDITY
    return RegimeType.HIGH_LIQUIDITY

def classify_time_regime(hour: int) -> RegimeType:
    """Classify by time of day."""
    if hour < 10:
        return RegimeType.OPEN_HOUR
    elif hour >= 15:
        return RegimeType.CLOSE_HOUR
    return RegimeType.MIDDAY

def compute_regime_slices(
    order_metrics: List[Dict],
    regime_features: List[Dict]
) -> List[RegimeSlice]:
    """
    Compute performance metrics by regime slice.
    
    order_metrics: [{"order_id": ..., "is_bps": ..., "is_twap_bps": ...}]
    regime_features: [{"order_id": ..., "volatility": ..., "spread": ..., "volume": ..., "hour": ...}]
    """
    if not order_metrics or not regime_features:
        return []
    
    # Build lookup
    features_by_id = {f["order_id"]: f for f in regime_features}
    
    # Compute thresholds
    vols = [f.get("volatility", 0) for f in regime_features]
    spreads = [f.get("spread", 0) for f in regime_features]
    volumes = [f.get("volume", 1e9) for f in regime_features]
    
    vol_p75 = np.percentile(vols, 75) if vols else 0
    spread_p75 = np.percentile(spreads, 75) if spreads else 0
    vol_p25 = np.percentile(volumes, 25) if volumes else 0
    
    # Group by regime
    regime_orders = {}
    
    for m in order_metrics:
        order_id = m.get("order_id")
        features = features_by_id.get(order_id, {})
        
        # Classify regimes
        vol_regime = classify_volatility_regime(
            features.get("volatility", 0), vol_p75
        )
        spread_regime = classify_spread_regime(
            features.get("spread", 0), spread_p75
        )
        liq_regime = classify_liquidity_regime(
            features.get("volume", 1e9), vol_p25
        )
        time_regime = classify_time_regime(
            features.get("hour", 12)
        )
        
        for regime in [vol_regime, spread_regime, liq_regime, time_regime]:
            key = regime.value
            if key not in regime_orders:
                regime_orders[key] = []
            regime_orders[key].append(m)
    
    # Compute slices
    slices = []
    for regime_name, orders in regime_orders.items():
        is_values = [o.get("is_bps", 0) for o in orders]
        twap_values = [o.get("is_twap_bps", 0) for o in orders]
        
        wins = sum(1 for i, t in zip(is_values, twap_values) if i < t)
        win_rate = wins / len(orders) if orders else 0
        
        slices.append(RegimeSlice(
            regime=regime_name,
            n_orders=len(orders),
            mean_is_bps=float(np.mean(is_values)) if is_values else 0,
            median_is_bps=float(np.median(is_values)) if is_values else 0,
            p90_is_bps=float(np.percentile(is_values, 90)) if is_values else 0,
            p95_is_bps=float(np.percentile(is_values, 95)) if is_values else 0,
            win_rate_vs_twap=win_rate
        ))
    
    return sorted(slices, key=lambda s: -s.n_orders)

def slices_to_csv_rows(slices: List[RegimeSlice]) -> List[Dict]:
    """Convert slices to CSV-friendly rows."""
    return [
        {
            "regime": s.regime,
            "n_orders": s.n_orders,
            "mean_is_bps": s.mean_is_bps,
            "median_is_bps": s.median_is_bps,
            "p90_is_bps": s.p90_is_bps,
            "p95_is_bps": s.p95_is_bps,
            "win_rate_vs_twap": s.win_rate_vs_twap
        }
        for s in slices
    ]

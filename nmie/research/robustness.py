"""
Robustness & Stress Testing
Regime slices and stability metrics.
"""
import numpy as np
import polars as pl
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class RegimeSlice:
    """Results for a specific regime."""
    regime: str
    n_orders: int
    mean_is_anee: float
    mean_is_twap: float
    delta_is: float
    p95_is_anee: float
    p95_is_twap: float

def classify_regime(
    volatility: float,
    spread: float,
    volume: float,
    vol_threshold: float = None,
    spread_threshold: float = None,
    volume_threshold: float = None
) -> str:
    """Classify market regime from features."""
    tags = []
    
    if vol_threshold and volatility > vol_threshold:
        tags.append("high_vol")
    if spread_threshold and spread > spread_threshold:
        tags.append("wide_spread")
    if volume_threshold and volume < volume_threshold:
        tags.append("low_volume")
        
    if not tags:
        return "normal"
    return "_".join(tags)

def compute_regime_slices(
    results_df: pl.DataFrame,
    features_df: pl.DataFrame
) -> List[RegimeSlice]:
    """
    Compute performance by regime slice.
    
    results_df: columns [order_id, is_anee, is_twap, ...]
    features_df: columns [order_id, volatility, spread, volume]
    """
    # Join results with features
    if results_df.is_empty() or features_df.is_empty():
        return []
        
    # Compute percentile thresholds
    vol_vals = features_df["volatility"].to_numpy() if "volatility" in features_df.columns else []
    spread_vals = features_df["spread"].to_numpy() if "spread" in features_df.columns else []
    volume_vals = features_df["volume"].to_numpy() if "volume" in features_df.columns else []
    
    vol_p75 = np.percentile(vol_vals, 75) if len(vol_vals) > 0 else None
    spread_p75 = np.percentile(spread_vals, 75) if len(spread_vals) > 0 else None
    volume_p25 = np.percentile(volume_vals, 25) if len(volume_vals) > 0 else None
    
    # Classify each order
    regimes = {}
    
    for row in results_df.iter_rows(named=True):
        order_id = row.get("order_id")
        is_anee = row.get("is_anee", row.get("IS_ANEE", 0))
        is_twap = row.get("is_twap", row.get("IS_TWAP", 0))
        
        # Get features for this order
        feat_row = features_df.filter(pl.col("order_id") == order_id)
        
        if feat_row.is_empty():
            regime = "unknown"
        else:
            feat = feat_row.to_dicts()[0]
            regime = classify_regime(
                feat.get("volatility", 0),
                feat.get("spread", 0),
                feat.get("volume", float("inf")),
                vol_p75, spread_p75, volume_p25
            )
            
        if regime not in regimes:
            regimes[regime] = {"is_anee": [], "is_twap": []}
        regimes[regime]["is_anee"].append(is_anee)
        regimes[regime]["is_twap"].append(is_twap)
        
    # Compute slice stats
    slices = []
    for regime, data in regimes.items():
        anee = np.array(data["is_anee"])
        twap = np.array(data["is_twap"])
        
        slices.append(RegimeSlice(
            regime=regime,
            n_orders=len(anee),
            mean_is_anee=np.mean(anee) if len(anee) > 0 else 0,
            mean_is_twap=np.mean(twap) if len(twap) > 0 else 0,
            delta_is=np.mean(twap) - np.mean(anee) if len(anee) > 0 else 0,
            p95_is_anee=np.percentile(anee, 95) if len(anee) > 0 else 0,
            p95_is_twap=np.percentile(twap, 95) if len(twap) > 0 else 0
        ))
        
    return slices

def stress_test_liquidity_shock(
    results_df: pl.DataFrame,
    features_df: pl.DataFrame,
    top_pct: float = 0.10
) -> RegimeSlice:
    """
    Test performance on liquidity shock days (top X% spread).
    """
    if features_df.is_empty() or "spread" not in features_df.columns:
        return RegimeSlice("liquidity_shock", 0, 0, 0, 0, 0, 0)
        
    spread_threshold = np.percentile(features_df["spread"].to_numpy(), 100 - top_pct * 100)
    
    shock_orders = features_df.filter(pl.col("spread") >= spread_threshold)["order_id"].to_list()
    
    shock_results = results_df.filter(pl.col("order_id").is_in(shock_orders))
    
    if shock_results.is_empty():
        return RegimeSlice("liquidity_shock", 0, 0, 0, 0, 0, 0)
        
    anee = shock_results["IS_ANEE"].to_numpy() if "IS_ANEE" in shock_results.columns else []
    twap = shock_results["IS_TWAP"].to_numpy() if "IS_TWAP" in shock_results.columns else []
    
    return RegimeSlice(
        regime="liquidity_shock",
        n_orders=len(anee),
        mean_is_anee=np.mean(anee) if len(anee) > 0 else 0,
        mean_is_twap=np.mean(twap) if len(twap) > 0 else 0,
        delta_is=np.mean(twap) - np.mean(anee) if len(anee) > 0 else 0,
        p95_is_anee=np.percentile(anee, 95) if len(anee) > 0 else 0,
        p95_is_twap=np.percentile(twap, 95) if len(twap) > 0 else 0
    )

def compute_fold_stability(
    fold_deltas: List[float]
) -> Dict[str, float]:
    """
    Compute stability metrics across folds.
    """
    if not fold_deltas:
        return {"std": 0, "worst": 0, "best": 0, "range": 0}
        
    arr = np.array(fold_deltas)
    
    return {
        "std": float(np.std(arr)),
        "worst": float(np.min(arr)),
        "best": float(np.max(arr)),
        "range": float(np.max(arr) - np.min(arr)),
        "mean": float(np.mean(arr))
    }

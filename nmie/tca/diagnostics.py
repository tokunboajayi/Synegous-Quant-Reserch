"""
TCA - Diagnostics
Failure buckets, constraint binding, intervention logs.
"""
import numpy as np
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class FailureBucket:
    """A bucket of similar failure modes."""
    bucket_name: str
    description: str
    n_orders: int
    mean_is_bps: float
    p95_is_bps: float
    common_traits: List[str]
    root_cause_hint: str

def identify_failure_buckets(
    order_diagnostics: List[Dict],
    is_threshold_bps: float = 10.0
) -> List[FailureBucket]:
    """
    Identify failure buckets from order diagnostics.
    
    order_diagnostics: [{"order_id", "is_bps", "cap_bound_pct", "spread_regime", 
                         "vol_regime", "time_regime", "pct_filled"}]
    """
    # Filter to high-cost orders
    failures = [d for d in order_diagnostics if d.get("is_bps", 0) >= is_threshold_bps]
    
    if not failures:
        return []
    
    buckets = []
    
    # Bucket by constraint binding
    cap_bound = [d for d in failures if d.get("cap_bound_pct", 0) > 0.3]
    if cap_bound:
        buckets.append(FailureBucket(
            bucket_name="capacity_constrained",
            description="Orders where participation cap frequently bound",
            n_orders=len(cap_bound),
            mean_is_bps=float(np.mean([d["is_bps"] for d in cap_bound])),
            p95_is_bps=float(np.percentile([d["is_bps"] for d in cap_bound], 95)),
            common_traits=["high_urgency", "low_liquidity"],
            root_cause_hint="Consider stretching horizon or reducing order size"
        ))
    
    # Bucket by wide spread
    wide_spread = [d for d in failures if d.get("spread_regime") == "wide_spread"]
    if wide_spread:
        buckets.append(FailureBucket(
            bucket_name="wide_spread_regime",
            description="Orders executed during wide spread conditions",
            n_orders=len(wide_spread),
            mean_is_bps=float(np.mean([d["is_bps"] for d in wide_spread])),
            p95_is_bps=float(np.percentile([d["is_bps"] for d in wide_spread], 95)),
            common_traits=["high_spread_cost", "illiquid_period"],
            root_cause_hint="Avoid execution during spread blowouts"
        ))
    
    # Bucket by high volatility
    high_vol = [d for d in failures if d.get("vol_regime") == "high_volatility"]
    if high_vol:
        buckets.append(FailureBucket(
            bucket_name="high_volatility",
            description="Orders executed during volatile conditions",
            n_orders=len(high_vol),
            mean_is_bps=float(np.mean([d["is_bps"] for d in high_vol])),
            p95_is_bps=float(np.percentile([d["is_bps"] for d in high_vol], 95)),
            common_traits=["timing_risk", "price_drift"],
            root_cause_hint="Use more aggressive pacing in volatile regimes"
        ))
    
    # Bucket by close hour
    close_hour = [d for d in failures if d.get("time_regime") == "close_hour"]
    if close_hour:
        buckets.append(FailureBucket(
            bucket_name="close_hour_pressure",
            description="Orders executed near market close",
            n_orders=len(close_hour),
            mean_is_bps=float(np.mean([d["is_bps"] for d in close_hour])),
            p95_is_bps=float(np.percentile([d["is_bps"] for d in close_hour], 95)),
            common_traits=["urgency", "completion_pressure"],
            root_cause_hint="Start execution earlier to avoid end-of-day rush"
        ))
    
    # Bucket by incomplete fills
    incomplete = [d for d in failures if d.get("pct_filled", 1) < 0.95]
    if incomplete:
        buckets.append(FailureBucket(
            bucket_name="incomplete_fills",
            description="Orders that did not fully complete",
            n_orders=len(incomplete),
            mean_is_bps=float(np.mean([d["is_bps"] for d in incomplete])),
            p95_is_bps=float(np.percentile([d["is_bps"] for d in incomplete], 95)),
            common_traits=["size_too_large", "horizon_too_short"],
            root_cause_hint="Increase participation limit or extend horizon"
        ))
    
    return sorted(buckets, key=lambda b: -b.mean_is_bps)[:10]

def compute_constraint_binding_stats(
    fills: List[Dict]
) -> Dict:
    """Compute constraint binding statistics."""
    if not fills:
        return {}
    
    n_total = len(fills)
    n_bound = sum(1 for f in fills if f.get("cap_bound", False))
    n_unfilled = sum(1 for f in fills if f.get("executed_qty", 0) == 0)
    
    return {
        "n_intervals": n_total,
        "n_cap_bound": n_bound,
        "n_unfilled": n_unfilled,
        "pct_cap_bound": n_bound / n_total if n_total > 0 else 0,
        "pct_unfilled": n_unfilled / n_total if n_total > 0 else 0
    }

def buckets_to_json(buckets: List[FailureBucket]) -> List[Dict]:
    """Convert buckets to JSON-friendly format."""
    return [
        {
            "bucket_name": b.bucket_name,
            "description": b.description,
            "n_orders": b.n_orders,
            "mean_is_bps": b.mean_is_bps,
            "p95_is_bps": b.p95_is_bps,
            "common_traits": b.common_traits,
            "root_cause_hint": b.root_cause_hint
        }
        for b in buckets
    ]

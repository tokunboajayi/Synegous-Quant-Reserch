"""
TCA - Cost Decomposition
Decompose IS into spread, timing, and impact components.
"""
import numpy as np
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class CostDecomposition:
    """Decomposed execution costs."""
    order_id: str
    total_is_bps: float
    spread_cost_bps: float
    timing_cost_bps: float
    impact_cost_bps: float
    # Additional
    arrival_price: float
    terminal_price: float
    avg_fill_price: float
    total_shares: float

def decompose_cost(
    order_id: str,
    fill_prices: np.ndarray,
    fill_quantities: np.ndarray,
    spreads: np.ndarray,
    arrival_price: float,
    terminal_price: float,
    side: str = "BUY"
) -> CostDecomposition:
    """
    Decompose execution cost into components.
    
    Components:
    - Spread: Direct cost of crossing the spread
    - Timing: Cost from price drift (arrival vs VWAP)
    - Impact: Residual (market impact proxy)
    
    For BUY:
    Total IS = (Avg Fill - Arrival) / Arrival * 10000
    Spread = sum(0.5 * spread_t * qty_t) / (total_qty * arrival)
    Timing = (Terminal - Arrival) / Arrival * 10000 (price drift)
    Impact = Total IS - Spread - Timing (residual)
    """
    total_qty = np.sum(fill_quantities)
    
    if total_qty <= 0 or arrival_price <= 0:
        return CostDecomposition(
            order_id=order_id,
            total_is_bps=0, spread_cost_bps=0,
            timing_cost_bps=0, impact_cost_bps=0,
            arrival_price=arrival_price, terminal_price=terminal_price,
            avg_fill_price=arrival_price, total_shares=0
        )
    
    # Avg fill price
    avg_fill = np.sum(fill_prices * fill_quantities) / total_qty
    
    # Total IS
    if side.upper() == "BUY":
        total_is = (avg_fill - arrival_price) / arrival_price * 10000
    else:
        total_is = (arrival_price - avg_fill) / arrival_price * 10000
    
    # Spread component
    spread_dollars = np.sum(0.5 * spreads * fill_quantities)
    spread_bps = spread_dollars / (total_qty * arrival_price) * 10000
    
    # Timing component (price drift)
    if side.upper() == "BUY":
        timing_bps = (terminal_price - arrival_price) / arrival_price * 10000
    else:
        timing_bps = (arrival_price - terminal_price) / arrival_price * 10000
    
    # Impact is residual
    impact_bps = total_is - spread_bps - timing_bps
    
    return CostDecomposition(
        order_id=order_id,
        total_is_bps=total_is,
        spread_cost_bps=spread_bps,
        timing_cost_bps=timing_bps,
        impact_cost_bps=impact_bps,
        arrival_price=arrival_price,
        terminal_price=terminal_price,
        avg_fill_price=avg_fill,
        total_shares=total_qty
    )

def aggregate_decompositions(
    decompositions: List[CostDecomposition]
) -> Dict[str, float]:
    """Aggregate cost decompositions across orders."""
    if not decompositions:
        return {}
    
    return {
        "mean_total_is_bps": float(np.mean([d.total_is_bps for d in decompositions])),
        "mean_spread_cost_bps": float(np.mean([d.spread_cost_bps for d in decompositions])),
        "mean_timing_cost_bps": float(np.mean([d.timing_cost_bps for d in decompositions])),
        "mean_impact_cost_bps": float(np.mean([d.impact_cost_bps for d in decompositions])),
        "pct_spread": float(np.mean([d.spread_cost_bps / max(d.total_is_bps, 0.01) for d in decompositions if d.total_is_bps > 0])) if any(d.total_is_bps > 0 for d in decompositions) else 0,
        "pct_timing": float(np.mean([d.timing_cost_bps / max(d.total_is_bps, 0.01) for d in decompositions if d.total_is_bps > 0])) if any(d.total_is_bps > 0 for d in decompositions) else 0,
        "pct_impact": float(np.mean([d.impact_cost_bps / max(d.total_is_bps, 0.01) for d in decompositions if d.total_is_bps > 0])) if any(d.total_is_bps > 0 for d in decompositions) else 0,
        "n_orders": len(decompositions)
    }

def decomposition_to_waterfall(d: CostDecomposition) -> List[Dict]:
    """Convert decomposition to waterfall chart data."""
    return [
        {"label": "Spread", "value": d.spread_cost_bps, "type": "cost"},
        {"label": "Timing", "value": d.timing_cost_bps, "type": "cost" if d.timing_cost_bps > 0 else "benefit"},
        {"label": "Impact", "value": d.impact_cost_bps, "type": "cost" if d.impact_cost_bps > 0 else "benefit"},
        {"label": "Total IS", "value": d.total_is_bps, "type": "total"}
    ]

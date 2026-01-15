"""
Execution Simulation - Metrics
IS, VWAP benchmark, adverse selection proxies.
"""
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ExecutionMetrics:
    """Comprehensive execution quality metrics."""
    # Core IS
    is_bps: float
    is_dollars: float
    
    # Benchmarks
    vwap_slippage_bps: float
    twap_slippage_bps: float
    
    # Distribution
    total_shares: float
    avg_fill_price: float
    arrival_price: float
    terminal_price: float
    
    # Adverse selection
    post_fill_move_5min_bps: float
    post_fill_move_20min_bps: float
    
    # Execution quality
    participation_rate: float
    pct_filled: float
    n_intervals: int

def compute_is_bps(
    avg_fill_price: float,
    arrival_price: float,
    side: str = "BUY"
) -> float:
    """
    Compute Implementation Shortfall in basis points.
    
    IS = (Fill Price - Arrival Price) / Arrival Price * 10000
    For sells, negate.
    """
    if arrival_price <= 0:
        return 0.0
        
    is_bps = (avg_fill_price - arrival_price) / arrival_price * 10000
    
    if side.upper() == "SELL":
        is_bps = -is_bps
        
    return is_bps

def compute_vwap_slippage(
    avg_fill_price: float,
    interval_vwap: float,
    side: str = "BUY"
) -> float:
    """Compute slippage vs VWAP benchmark in bps."""
    if interval_vwap <= 0:
        return 0.0
        
    slippage = (avg_fill_price - interval_vwap) / interval_vwap * 10000
    
    if side.upper() == "SELL":
        slippage = -slippage
        
    return slippage

def compute_adverse_selection(
    fill_price: float,
    future_prices: List[float],
    side: str = "BUY"
) -> float:
    """
    Compute adverse selection: price move after fill.
    Negative = adverse (market moved against us after fill).
    """
    if not future_prices or fill_price <= 0:
        return 0.0
        
    future_avg = np.mean(future_prices)
    move_bps = (future_avg - fill_price) / fill_price * 10000
    
    # For buy, positive move (price went up) is adverse
    # For sell, negative move (price went down) is adverse
    if side.upper() == "BUY":
        return -move_bps  # Negative = we paid more than hindsight optimal
    else:
        return move_bps

def compute_execution_metrics(
    fill_prices: np.ndarray,
    fill_quantities: np.ndarray,
    scheduled_quantities: np.ndarray,
    bar_volumes: np.ndarray,
    arrival_price: float,
    terminal_price: float,
    interval_vwaps: np.ndarray,
    future_prices_5min: List[float] = None,
    future_prices_20min: List[float] = None,
    side: str = "BUY"
) -> ExecutionMetrics:
    """Compute comprehensive execution metrics."""
    
    # Weighted average fill price
    total_shares = np.sum(fill_quantities)
    if total_shares > 0:
        avg_fill_price = np.sum(fill_prices * fill_quantities) / total_shares
    else:
        avg_fill_price = arrival_price
        
    # IS
    is_bps = compute_is_bps(avg_fill_price, arrival_price, side)
    is_dollars = (avg_fill_price - arrival_price) * total_shares
    if side.upper() == "SELL":
        is_dollars = -is_dollars
        
    # VWAP benchmark
    session_vwap = np.mean(interval_vwaps) if len(interval_vwaps) > 0 else avg_fill_price
    vwap_slippage = compute_vwap_slippage(avg_fill_price, session_vwap, side)
    
    # TWAP benchmark
    twap_price = np.mean(fill_prices) if len(fill_prices) > 0 else avg_fill_price
    twap_slippage = compute_vwap_slippage(avg_fill_price, twap_price, side)
    
    # Adverse selection
    post_5 = compute_adverse_selection(avg_fill_price, future_prices_5min or [], side)
    post_20 = compute_adverse_selection(avg_fill_price, future_prices_20min or [], side)
    
    # Participation
    total_volume = np.sum(bar_volumes)
    participation = total_shares / total_volume if total_volume > 0 else 0
    
    # Fill rate
    total_scheduled = np.sum(scheduled_quantities)
    pct_filled = total_shares / total_scheduled if total_scheduled > 0 else 0
    
    return ExecutionMetrics(
        is_bps=is_bps,
        is_dollars=is_dollars,
        vwap_slippage_bps=vwap_slippage,
        twap_slippage_bps=twap_slippage,
        total_shares=total_shares,
        avg_fill_price=avg_fill_price,
        arrival_price=arrival_price,
        terminal_price=terminal_price,
        post_fill_move_5min_bps=post_5,
        post_fill_move_20min_bps=post_20,
        participation_rate=participation,
        pct_filled=pct_filled,
        n_intervals=len(fill_prices)
    )

def aggregate_metrics(
    metrics_list: List[ExecutionMetrics]
) -> Dict[str, float]:
    """Aggregate metrics across orders."""
    if not metrics_list:
        return {}
        
    is_values = [m.is_bps for m in metrics_list]
    
    return {
        "mean_is_bps": float(np.mean(is_values)),
        "median_is_bps": float(np.median(is_values)),
        "p90_is_bps": float(np.percentile(is_values, 90)),
        "p95_is_bps": float(np.percentile(is_values, 95)),
        "std_is_bps": float(np.std(is_values)),
        "worst_is_bps": float(np.max(is_values)),
        "best_is_bps": float(np.min(is_values)),
        "mean_vwap_slip_bps": float(np.mean([m.vwap_slippage_bps for m in metrics_list])),
        "mean_pct_filled": float(np.mean([m.pct_filled for m in metrics_list])),
        "mean_participation": float(np.mean([m.participation_rate for m in metrics_list])),
        "n_orders": len(metrics_list)
    }

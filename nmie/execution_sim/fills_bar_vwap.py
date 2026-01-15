"""
SOFT Simulator - Bar VWAP Fill
Fills at bar VWAP with spread crossing.
This is the more forgiving simulator.
"""
import numpy as np
import polars as pl
from typing import List, Tuple, Optional
from dataclasses import dataclass

from nmie.execution_sim.constraints import (
    ExecutionConstraints, apply_participation_cap, validate_fill
)
from nmie.execution_sim.metrics import ExecutionMetrics, compute_execution_metrics
from nmie.execution_sim.fills_next_trade import FillRecord

class BarVwapFillSimulator:
    """
    SOFT Simulator: Fill at bar VWAP.
    
    For each scheduled slice at time t:
    1. Fill at bar VWAP
    2. Apply side-consistent spread crossing
    3. Enforce max participation cap
    """
    
    def __init__(self, constraints: ExecutionConstraints = None):
        self.constraints = constraints or ExecutionConstraints()
        self.name = "SOFT_BAR_VWAP"
        
    def simulate(
        self,
        schedule: np.ndarray,
        bars: pl.DataFrame,
        side: str = "BUY",
        arrival_price: float = None
    ) -> Tuple[List[FillRecord], ExecutionMetrics]:
        """
        Simulate execution using bar VWAP fills.
        
        Args:
            schedule: Array of quantities per interval
            bars: DataFrame with columns [timestamp, open, high, low, close, volume, vwap]
            side: BUY or SELL
            arrival_price: Decision price (default: first bar open)
            
        Returns:
            (fill_records, execution_metrics)
        """
        n_intervals = min(len(schedule), len(bars))
        
        if n_intervals == 0:
            return [], None
            
        # Use VWAP or mid as fill price
        if "vwap" in bars.columns:
            vwaps = bars["vwap"].to_numpy()[:n_intervals]
        else:
            highs = bars["high"].to_numpy()[:n_intervals]
            lows = bars["low"].to_numpy()[:n_intervals]
            vwaps = (highs + lows) / 2
            
        bar_volumes = bars["volume"].to_numpy()[:n_intervals]
        bar_highs = bars["high"].to_numpy()[:n_intervals]
        bar_lows = bars["low"].to_numpy()[:n_intervals]
        
        # Estimate spread from high-low
        spreads = (bar_highs - bar_lows) / ((bar_highs + bar_lows) / 2)
        spreads = np.clip(spreads, 0.0001, 0.01)
        
        if arrival_price is None:
            arrival_price = bars["open"].to_numpy()[0]
            
        terminal_price = bars["close"].to_numpy()[-1] if "close" in bars.columns else vwaps[-1]
        
        fills = []
        fill_prices = []
        fill_quantities = []
        scheduled_quantities = []
        
        for i in range(n_intervals):
            qty = schedule[i] if i < len(schedule) else 0
            
            # Apply participation cap
            executable, unfilled = apply_participation_cap(
                qty, bar_volumes[i], self.constraints
            )
            
            cap_bound = unfilled > 0
            
            # Get fill price with spread crossing
            base_price = vwaps[i]
            spread = spreads[i] * base_price
            
            if side.upper() == "BUY":
                fill_price = base_price + 0.5 * spread
            else:
                fill_price = base_price - 0.5 * spread
                
            spread_cost = 0.5 * spread * executable
            
            # Validate fill
            valid, reason = validate_fill(
                executable, fill_price, bar_volumes[i],
                bar_lows[i], bar_highs[i], self.constraints
            )
            
            if not valid:
                executable = 0
                
            timestamp = str(bars["timestamp"].to_numpy()[i]) if "timestamp" in bars.columns else f"t{i}"
            
            fills.append(FillRecord(
                interval=i,
                timestamp=timestamp,
                scheduled_qty=qty,
                executed_qty=executable,
                fill_price=fill_price if executable > 0 else 0,
                spread_cost=spread_cost if executable > 0 else 0,
                cap_bound=cap_bound,
                valid=valid,
                reason=reason
            ))
            
            if executable > 0:
                fill_prices.append(fill_price)
                fill_quantities.append(executable)
            scheduled_quantities.append(qty)
            
        # Compute metrics
        fill_prices_arr = np.array(fill_prices) if fill_prices else np.array([arrival_price])
        fill_quantities_arr = np.array(fill_quantities) if fill_quantities else np.array([0])
        scheduled_arr = np.array(scheduled_quantities)
        
        metrics = compute_execution_metrics(
            fill_prices=fill_prices_arr,
            fill_quantities=fill_quantities_arr,
            scheduled_quantities=scheduled_arr,
            bar_volumes=bar_volumes,
            arrival_price=arrival_price,
            terminal_price=terminal_price,
            interval_vwaps=vwaps,
            side=side
        )
        
        return fills, metrics
    
    def __repr__(self):
        return f"BarVwapFillSimulator(max_participation={self.constraints.max_participation_rate})"


def compare_simulators(
    schedule: np.ndarray,
    bars: pl.DataFrame,
    side: str = "BUY"
) -> dict:
    """
    Run both simulators and compare results.
    Detects simulation sensitivity.
    """
    from nmie.execution_sim.fills_next_trade import NextTradeFillSimulator
    
    hard_sim = NextTradeFillSimulator()
    soft_sim = BarVwapFillSimulator()
    
    _, hard_metrics = hard_sim.simulate(schedule, bars, side)
    _, soft_metrics = soft_sim.simulate(schedule, bars, side)
    
    if hard_metrics is None or soft_metrics is None:
        return {"error": "Simulation failed"}
    
    # Check if results diverge
    is_delta = soft_metrics.is_bps - hard_metrics.is_bps
    agrees = (hard_metrics.is_bps < 0) == (soft_metrics.is_bps < 0)  # Same sign
    
    return {
        "hard_is_bps": hard_metrics.is_bps,
        "soft_is_bps": soft_metrics.is_bps,
        "delta_is_bps": is_delta,
        "simulators_agree": agrees,
        "sensitivity_warning": abs(is_delta) > 2.0,  # >2bps difference is concerning
        "hard_pct_filled": hard_metrics.pct_filled,
        "soft_pct_filled": soft_metrics.pct_filled
    }

"""
HARD Simulator - Next-Trade Fill
Fills at actual next trade price with spread crossing.
This is the less gameable simulator.
"""
import numpy as np
import polars as pl
from typing import List, Tuple, Optional
from dataclasses import dataclass

from nmie.execution_sim.constraints import (
    ExecutionConstraints, apply_participation_cap, validate_fill
)
from nmie.execution_sim.metrics import ExecutionMetrics, compute_execution_metrics

@dataclass
class FillRecord:
    """Single fill record."""
    interval: int
    timestamp: str
    scheduled_qty: float
    executed_qty: float
    fill_price: float
    spread_cost: float
    cap_bound: bool
    valid: bool
    reason: str = ""

class NextTradeFillSimulator:
    """
    HARD Simulator: Fill at next actual trade price.
    
    For each scheduled slice at time t:
    1. Find the next real trade print at or after t
    2. Fill at that trade price
    3. Apply side-consistent spread crossing:
       - buy: price += 0.5 * spread_est
       - sell: price -= 0.5 * spread_est
    4. Enforce max participation cap
    """
    
    def __init__(self, constraints: ExecutionConstraints = None, use_spread_crossing: bool = True):
        self.constraints = constraints or ExecutionConstraints()
        self.use_spread_crossing = use_spread_crossing
        self.name = f"HARD_NEXT_TRADE(spread={use_spread_crossing})"
        
    def simulate(
        self,
        schedule: np.ndarray,
        bars: pl.DataFrame,
        side: str = "BUY",
        arrival_price: float = None
    ) -> Tuple[List[FillRecord], ExecutionMetrics]:
        """
        Simulate execution using next-trade fills.
        """
        n_intervals = min(len(schedule), len(bars))
        
        if n_intervals == 0:
            return [], None
            
        # Use open as proxy for "next trade" price
        if "close" in bars.columns:
            trade_prices = bars["close"].to_numpy()[:n_intervals]
        else:
            trade_prices = bars["open"].to_numpy()[:n_intervals]
            
        bar_volumes = bars["volume"].to_numpy()[:n_intervals]
        bar_highs = bars["high"].to_numpy()[:n_intervals]
        bar_lows = bars["low"].to_numpy()[:n_intervals]
        
        # Estimate spread from high-low
        spreads = (bar_highs - bar_lows) / ((bar_highs + bar_lows) / 2)
        spreads = np.clip(spreads, 0.0001, 0.01)  # Cap at 1%
        
        if arrival_price is None:
            arrival_price = bars["open"].to_numpy()[0]
            
        terminal_price = trade_prices[-1]
        
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
            base_price = trade_prices[i]
            
            if self.use_spread_crossing:
                spread = spreads[i] * base_price
                if side.upper() == "BUY":
                    fill_price = base_price + 0.5 * spread
                else:
                    fill_price = base_price - 0.5 * spread
            else:
                fill_price = base_price
                
            spread_cost = (0.5 * spreads[i] * base_price * executable) if self.use_spread_crossing else 0
                
            spread_cost = 0.5 * spread * executable
            
            # Validate fill
            valid, reason = validate_fill(
                executable, fill_price, bar_volumes[i],
                bar_lows[i], bar_highs[i], self.constraints
            )
            
            # If invalid, don't fill (but still record)
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
        
        vwaps = bars["vwap"].to_numpy()[:n_intervals] if "vwap" in bars.columns else trade_prices
        
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
        return f"NextTradeFillSimulator(max_participation={self.constraints.max_participation_rate})"

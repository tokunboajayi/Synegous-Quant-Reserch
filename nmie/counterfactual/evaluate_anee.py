import numpy as np
import pandas as pd
import polars as pl
from typing import Dict, List
from dataclasses import dataclass
import datetime

from nmie.optimizer.anee_engine import ANEEEngine, ExecutionResult
from nmie.optimizer.policies import TWAP, VWAP, POV
from nmie.store.feature_store import FeatureStore

@dataclass
class ComparisonResult:
    parent_id: str
    ticker: str
    total_shares: float
    arrival_price: float
    
    # IS in bps by strategy
    is_anee: float
    is_twap: float
    is_vwap: float
    is_pov: float
    
    # Delta (vs TWAP baseline)
    anee_vs_twap_bps: float

def run_baseline_simulation(parent_order: Dict, 
                             market_data: pl.DataFrame,
                             policy_name: str) -> ExecutionResult:
    """
    Runs a baseline execution simulation (TWAP/VWAP/POV).
    """
    ticker = parent_order["ticker"]
    total_shares = parent_order["size_shares"]
    
    start_ts = parent_order["start_time"]
    end_ts = parent_order["end_time"]
    
    # Timezone handling
    tz = market_data["timestamp"].dtype.time_zone
    if tz == "UTC":
        if start_ts.tzinfo is None:
            start_ts = start_ts.replace(tzinfo=datetime.timezone.utc)
        if end_ts.tzinfo is None:
            end_ts = end_ts.replace(tzinfo=datetime.timezone.utc)
    
    bars = market_data.filter(
        (pl.col("timestamp") >= start_ts) & 
        (pl.col("timestamp") < end_ts)
    ).sort("timestamp")
    
    if bars.height == 0:
        return None
        
    T = bars.height
    timestamps = bars["timestamp"].dt.strftime("%H:%M").to_list()
    volumes = bars["volume"].to_numpy()
    
    # Setup Policy
    if policy_name == "TWAP":
        pol = TWAP()
    elif policy_name == "VWAP":
        pol = VWAP(volumes)
    elif policy_name == "POV":
        pol = POV(participation_rate=0.10)
    else:
        raise ValueError(f"Unknown policy: {policy_name}")
        
    # Sim Loop
    arrival_price = bars["open"][0]
    rem_shares = total_shares
    
    executed_q = []
    realized_px = []
    
    for t in range(T):
        row = bars.row(t, named=True)
        
        if policy_name == "POV":
            q = pol.get_quantity(t, T, rem_shares, row["volume"])
        else:
            q = pol.get_quantity(t, T, rem_shares)
            
        # Cap at available volume
        max_bin_vol = 0.50 * row["volume"]
        q = min(q, max_bin_vol, rem_shares)
        
        # Impact Model (Simple)
        try:
            bar_vwap = row["vwap"]
        except:
            bar_vwap = row["close"]
            
        participation = q / (row["volume"] + 1e-9)
        impact_bps = 10 * (participation ** 0.5)
        exec_price = bar_vwap * (1 + impact_bps/10000)
        
        executed_q.append(q)
        realized_px.append(exec_price)
        rem_shares -= q
        
        if rem_shares <= 0:
            break
            
    # Pad
    while len(executed_q) < T:
        executed_q.append(0)
        realized_px.append(bars["close"][len(executed_q)-1])
        
    executed_q = np.array(executed_q)
    realized_px = np.array(realized_px)
    
    total_value = np.sum(executed_q * realized_px)
    avg_price = total_value / total_shares if total_shares > 0 else 0
    is_bps = (avg_price - arrival_price) / arrival_price * 10000
    
    return ExecutionResult(
        parent_id=parent_order.get("order_id", "unknown"),
        strategy=policy_name,
        intervals=timestamps,
        target_quantities=[],
        executed_quantities=executed_q.tolist(),
        realized_prices=realized_px.tolist(),
        benchmark_price=arrival_price,
        total_shares=total_shares,
        avg_exec_price=avg_price,
        implementation_shortfall_bps=is_bps,
        details=pd.DataFrame()
    )

def compare_strategies(parent_order: Dict, market_data: pl.DataFrame) -> ComparisonResult:
    """
    Runs ANEE and baselines, returns comparison metrics.
    """
    engine = ANEEEngine()
    
    # Run ANEE
    res_anee = engine.run_simulation(parent_order, market_data)
    
    # Run Baselines
    res_twap = run_baseline_simulation(parent_order, market_data, "TWAP")
    res_vwap = run_baseline_simulation(parent_order, market_data, "VWAP")
    res_pov = run_baseline_simulation(parent_order, market_data, "POV")
    
    is_anee = res_anee.implementation_shortfall_bps if res_anee else 0
    is_twap = res_twap.implementation_shortfall_bps if res_twap else 0
    is_vwap = res_vwap.implementation_shortfall_bps if res_vwap else 0
    is_pov = res_pov.implementation_shortfall_bps if res_pov else 0
    
    return ComparisonResult(
        parent_id=parent_order.get("order_id", ""),
        ticker=parent_order.get("ticker", ""),
        total_shares=parent_order.get("size_shares", 0),
        arrival_price=res_anee.benchmark_price if res_anee else 0,
        is_anee=is_anee,
        is_twap=is_twap,
        is_vwap=is_vwap,
        is_pov=is_pov,
        anee_vs_twap_bps=is_anee - is_twap
    )

def run_counterfactual_suite(orders: List[Dict], market_data: pl.DataFrame) -> pd.DataFrame:
    """
    Runs counterfactual evaluation across a batch of orders.
    """
    results = []
    for order in orders:
        comp = compare_strategies(order, market_data)
        results.append({
            "order_id": comp.parent_id,
            "ticker": comp.ticker,
            "shares": comp.total_shares,
            "arrival_px": comp.arrival_price,
            "IS_ANEE": comp.is_anee,
            "IS_TWAP": comp.is_twap,
            "IS_VWAP": comp.is_vwap,
            "IS_POV": comp.is_pov,
            "ANEE_vs_TWAP": comp.anee_vs_twap_bps
        })
        
    return pd.DataFrame(results)

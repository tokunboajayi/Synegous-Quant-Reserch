import numpy as np
import polars as pl
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional
import datetime

from nmie.store.feature_store import FeatureStore
from nmie.optimizer.policies import TWAP, VWAP, POV

@dataclass
class LabelResult:
    order_id: str
    ticker: str
    date: str
    side: str
    size_shares: float
    horizon_mins: int
    
    decision_price: float
    avg_exec_price: float
    is_bps: float
    
    # Adverse selection: price move after execution ends
    adverse_selection_bps: float
    
    # For distribution (if multiple simulations run)
    is_quantiles: Dict[str, float] = None

class ImpactLabeler:
    """
    Computes Implementation Shortfall labels from parent orders.
    """
    def __init__(self):
        self.store = FeatureStore()
        
    def compute_is(self, 
                   parent_order: Dict, 
                   bars: pl.DataFrame,
                   policy_name: str = "TWAP") -> Optional[LabelResult]:
        """
        Simulates execution of a parent order and computes IS.
        """
        ticker = parent_order["ticker"]
        total_shares = parent_order["size_shares"]
        side = parent_order.get("side", "BUY")
        
        start_ts = parent_order["start_time"]
        end_ts = parent_order["end_time"]
        
        # Timezone handling
        tz = bars["timestamp"].dtype.time_zone
        if tz == "UTC":
            if start_ts.tzinfo is None:
                start_ts = start_ts.replace(tzinfo=datetime.timezone.utc)
            if end_ts.tzinfo is None:
                end_ts = end_ts.replace(tzinfo=datetime.timezone.utc)
        
        # Filter bars for horizon
        horizon_bars = bars.filter(
            (pl.col("timestamp") >= start_ts) & 
            (pl.col("timestamp") < end_ts)
        ).sort("timestamp")
        
        if horizon_bars.height == 0:
            return None
            
        T = horizon_bars.height
        volumes = horizon_bars["volume"].to_numpy()
        
        # Decision Price = Mid at start (using open as proxy)
        decision_price = horizon_bars["open"][0]
        
        # Setup Policy
        if policy_name == "TWAP":
            pol = TWAP()
        elif policy_name == "VWAP":
            pol = VWAP(volumes)
        elif policy_name == "POV":
            pol = POV(participation_rate=0.10)
        else:
            pol = TWAP()
            
        # Simulate Execution
        rem_shares = total_shares
        executed_q = []
        exec_prices = []
        
        for t in range(T):
            row = horizon_bars.row(t, named=True)
            
            if policy_name == "POV":
                q = pol.get_quantity(t, T, rem_shares, row["volume"])
            else:
                q = pol.get_quantity(t, T, rem_shares)
                
            # Cap at 50% of bar volume
            max_bin = 0.50 * row["volume"]
            q = min(q, max_bin, rem_shares)
            
            # Execution price = VWAP + impact
            try:
                bar_vwap = row["vwap"]
            except:
                bar_vwap = row["close"]
                
            participation = q / (row["volume"] + 1e-9)
            impact_bps = 10 * (participation ** 0.5)  # Square root law
            
            if side == "BUY":
                exec_px = bar_vwap * (1 + impact_bps / 10000)
            else:
                exec_px = bar_vwap * (1 - impact_bps / 10000)
                
            executed_q.append(q)
            exec_prices.append(exec_px)
            rem_shares -= q
            
            if rem_shares <= 0:
                break
                
        # Avg Execution Price
        executed_q = np.array(executed_q)
        exec_prices = np.array(exec_prices)
        
        total_value = np.sum(executed_q * exec_prices)
        executed_total = np.sum(executed_q)
        
        if executed_total == 0:
            return None
            
        avg_exec_price = total_value / executed_total
        
        # IS = (AvgPx - DecisionPx) / DecisionPx * 10000
        # For BUY: positive IS = paid more than arrival (bad)
        # For SELL: positive IS = received less than arrival (bad)
        if side == "BUY":
            is_bps = (avg_exec_price - decision_price) / decision_price * 10000
        else:
            is_bps = (decision_price - avg_exec_price) / decision_price * 10000
            
        # Adverse Selection: Price move after execution
        # Look at price 5 mins after end (or end of day)
        # For simplicity, use last bar close vs decision
        post_bars = bars.filter(pl.col("timestamp") >= end_ts).sort("timestamp")
        if post_bars.height > 0:
            post_price = post_bars["close"][min(4, post_bars.height - 1)]
        else:
            post_price = horizon_bars["close"][-1]
            
        if side == "BUY":
            # If price went up after we bought, favorable (negative adverse selection)
            adverse_bps = (post_price - decision_price) / decision_price * 10000
        else:
            adverse_bps = (decision_price - post_price) / decision_price * 10000
            
        return LabelResult(
            order_id=parent_order.get("order_id", ""),
            ticker=ticker,
            date=parent_order.get("date", ""),
            side=side,
            size_shares=total_shares,
            horizon_mins=parent_order.get("horizon_mins", T),
            decision_price=decision_price,
            avg_exec_price=avg_exec_price,
            is_bps=is_bps,
            adverse_selection_bps=adverse_bps
        )
        
    def label_batch(self, 
                    orders: List[Dict], 
                    bars: pl.DataFrame,
                    policies: List[str] = ["TWAP", "VWAP"]) -> pd.DataFrame:
        """
        Labels a batch of orders with multiple policies.
        """
        results = []
        
        for order in orders:
            for policy in policies:
                label = self.compute_is(order, bars, policy)
                if label:
                    results.append({
                        "order_id": label.order_id,
                        "ticker": label.ticker,
                        "date": label.date,
                        "side": label.side,
                        "size_shares": label.size_shares,
                        "horizon_mins": label.horizon_mins,
                        "policy": policy,
                        "decision_price": label.decision_price,
                        "avg_exec_price": label.avg_exec_price,
                        "is_bps": label.is_bps,
                        "adverse_selection_bps": label.adverse_selection_bps
                    })
                    
        return pd.DataFrame(results)

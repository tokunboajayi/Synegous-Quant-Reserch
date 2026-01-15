import numpy as np
import pandas as pd
from typing import List, Dict, Any
from dataclasses import dataclass
import polars as pl
from tqdm import tqdm
import datetime
import pandas as pd

from nmie.optimizer.types import PlanningInput, MarketForecast, Schedule
from nmie.optimizer.cvx_planner import GlobalPlanner
from nmie.optimizer.neural_controller import LocalController, MarketState
from nmie.optimizer.trust_region import TrustRegion, TrustRegionConfig

@dataclass
class ExecutionResult:
    parent_id: str
    strategy: str # ANEE, TWAP, etc.
    intervals: List[str]
    target_quantities: List[float] # q* (if applicable)
    executed_quantities: List[float] # q_exec
    realized_prices: List[float]
    benchmark_price: float # Arrival Mid
    
    total_shares: float
    avg_exec_price: float
    implementation_shortfall_bps: float
    
    details: pd.DataFrame # Trace of state/actions

class ANEEEngine:
    def __init__(self):
        self.planner = GlobalPlanner()
        self.controller = LocalController()
        self.trust_region = TrustRegion(TrustRegionConfig())
        
    def run_simulation(self, 
                       parent_order: Dict, 
                       market_data: pl.DataFrame,
                       forecast_overrides: Dict = None) -> ExecutionResult:
        """
        Runs the full ANEE simulation for a single parent order.
        """
        # 1. Setup
        ticker = parent_order["ticker"]
        total_shares = parent_order["size_shares"]
        
        # Filter market data for the horizon
        # Convert pandas/python datetime to polars compatible
        # If market_data is read from parquet, it might be naive or UTC.
        # Let's ensure strict types.
        
        start_ts = parent_order["start_time"]
        end_ts = parent_order["end_time"]
        
        # Ensure start_ts/end_ts are localized if the DF is timezoned
        # Checking first timestamp of DF
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
            print(f"No bars found for {ticker} between {start_time} and {end_time}")
            return None

        T = bars.height
        timestamps = bars["timestamp"].dt.strftime("%H:%M").to_list()
        
        # 2. Build Forecast (Mock/Heuristic for now)
        # Using Realized as Forecast + Noise for realism in simulation?
        # Ideally we use T-1 stats.
        # For simplicity in this step, we use Realized but assume we knew it (Perfect Foresight) 
        # OR we use a simple smoothed profile.
        # Let's use Realized Volume for the Forecast Volume Profile (Perfect Volume Foresight) 
        # so we can purely test the Optimization logic, but impact params are heuristic.
        
        vol_forecast = bars["volume"].to_numpy()
        volatility_forecast = np.full(T, 0.005) # Dummy
        spread_forecast = np.full(T, 0.02) # Dummy
        
        # Heuristic Impact
        alpha = spread_forecast / 2
        beta = np.full(T, 1e-5) 
        
        forecast = MarketForecast(
            intervals=timestamps,
            expected_volume=vol_forecast,
            expected_volatility=volatility_forecast,
            expected_spread=spread_forecast,
            alpha=alpha,
            beta=beta
        )
        
        plan_input = PlanningInput(total_shares=total_shares, forecast=forecast)
        
        # 3. Global Plan
        schedule = self.planner.plan(plan_input)
        if not schedule.is_feasible:
            print("Global Planning Failed! Falling back to TWAP.")
            q_star = np.full(T, total_shares / T)
        else:
            q_star = schedule.quantities
            
        # 4. Simulation Loop
        executed_q = []
        realized_px = []
        history = []
        
        cum_exec = 0.0
        cum_plan = 0.0
        
        arrival_price = bars["open"][0]
        
        for t in range(T):
            row = bars.row(t, named=True)
            
            # Global Plan target for this step
            target_q = q_star[t]
            cum_plan += target_q
            
            # Observe State
            # Vol Ratio: Realized Vol vs Forecast (Here they are same 1.0)
            # Let's inject some noise to test controller
            current_vol = row["volume"]
            expected_vol = vol_forecast[t]
            vol_ratio = current_vol / (expected_vol + 1e-9)
            
            current_spread = 0.02 # Fixed for now
            expected_spread = spread_forecast[t]
            spread_ratio = current_spread / expected_spread
            
            # State
            state = MarketState(
                vol_ratio=vol_ratio,
                spread_ratio=spread_ratio,
                imbalance=0.0,
                progress_frac=cum_exec / total_shares,
                time_frac=t / T,
                deviation_pct=(cum_exec - cum_plan) / total_shares
            )
            
            # Controller Action
            alpha = self.controller.get_action(state)
            
            # Trust Region
            safe_q = self.trust_region.clip_quantity(
                target_q, alpha, cum_exec, cum_plan, total_shares
            )
            
            # Execution (Cap at available volume?)
            # In simulation we usually assume we can trade X% of bin.
            # Let's cap at 50% of bin volume to be realistic
            max_bin_vol = 0.50 * row["volume"]
            final_q = min(safe_q, max_bin_vol)
            
            # Final check: Don't overfill total order
            rem_shares = total_shares - cum_exec
            final_q = min(final_q, rem_shares)
            
            # Cost Sim
            # Price = VWAP + Impact
            # Impact ~ Beta * Q^2?  Or simply use VWAP + 1/2 Spread + perm impact
            # Simple slippage model: Mid + Alpha * (Q / Vol) * Volatility?
            # Let's uses: Realized Price = Bar VWAP + 0.1 * BasisPoints * (Q/V)^0.5
            
            try:
                bar_vwap = row["vwap"]
            except:
                bar_vwap = row["close"] # Fallback
            
            participation = final_q / (row["volume"] + 1e-9)
            impact_bps = 10 * (participation ** 0.5) # Square root law
            exec_price = bar_vwap * (1 + impact_bps/10000)
            
            executed_q.append(final_q)
            realized_px.append(exec_price)
            
            cum_exec += final_q
            
            history.append({
                "t": t,
                "timestamp": timestamps[t],
                "q_star": target_q,
                "alpha": alpha,
                "q_exec": final_q,
                "dev_pct": state.deviation_pct,
                "price": exec_price
            })
            
            if cum_exec >= total_shares:
                # Finished early
                break
                
        # Fill rest with 0 if finished early
        while len(executed_q) < T:
            executed_q.append(0)
            realized_px.append(bars["close"][len(executed_q)-1])
            
        # Calc Metrics
        executed_q = np.array(executed_q)
        realized_px = np.array(realized_px)
        
        total_value = np.sum(executed_q * realized_px)
        avg_price = total_value / total_shares if total_shares > 0 else 0
        
        # IS bps = (AvgPx - Arrival) / Arrival * 10000
        # Buy order: Higher is bad. 
        is_bps = (avg_price - arrival_price) / arrival_price * 10000
        
        return ExecutionResult(
            parent_id=parent_order.get("order_id", "unknown"),
            strategy="ANEE",
            intervals=timestamps,
            target_quantities=q_star.tolist(),
            executed_quantities=executed_q.tolist(),
            realized_prices=realized_px.tolist(),
            benchmark_price=arrival_price,
            total_shares=total_shares,
            avg_exec_price=avg_price,
            implementation_shortfall_bps=is_bps,
            details=pd.DataFrame(history)
        )

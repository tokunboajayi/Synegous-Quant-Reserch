import numpy as np
import pandas as pd
from nmie.optimizer.types import PlanningInput, MarketForecast
from nmie.optimizer.cvx_planner import GlobalPlanner

def test_planner():
    T = 60 # 60 minutes
    timestamps = [f"10:{i:02d}" for i in range(T)]
    
    # Mock Forecast
    # Volume Curve: U-shape
    t = np.linspace(-1, 1, T)
    vol_profile = 10000 * (t**2 + 0.5) # Higher at start/end
    
    # Volatility and Spread
    sigma = np.full(T, 0.01) # constant vol
    spread = np.full(T, 0.02)
    
    # Impact Params (Heuristic)
    # alpha ~ spread/2
    alpha = spread / 2
    # beta ~ 1e-5 (slope of impact)
    beta = np.full(T, 1e-4) # High impact cost
    
    forecast = MarketForecast(
        intervals=timestamps,
        expected_volume=vol_profile,
        expected_volatility=sigma,
        expected_spread=spread,
        alpha=alpha,
        beta=beta
    )
    
    # Input
    total_shares = 50000 # 5% of total volume roughly? 
    # Total Vol ~ 10000 * 1 * 60 ~ 600k. 50k is significant.
    
    inputs = PlanningInput(
        total_shares=total_shares,
        forecast=forecast,
        risk_aversion=1.0,
        smooth_penalty=10.0,
        max_participation=0.20
    )
    
    # Plan
    planner = GlobalPlanner()
    sched = planner.plan(inputs)
    
    print(f"Status: {sched.solver_status}")
    print(f"Feasible: {sched.is_feasible}")
    print(f"Total Scheduled: {np.sum(sched.quantities):.2f} / {total_shares}")
    
    if sched.is_feasible:
        # Check constraints
        q = sched.quantities
        max_q = 0.20 * vol_profile
        violations = q > max_q + 1e-5
        if np.any(violations):
            print("Constraint Violation: Participation Cap exceeded!")
        else:
            print("Constraints Satisfied.")
            
        print("Schedule Sample (First 5):", q[:5].astype(int))
        print("Schedule Sample (Last 5):", q[-5:].astype(int))

if __name__ == "__main__":
    test_planner()

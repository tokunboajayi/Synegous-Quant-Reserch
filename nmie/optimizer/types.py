from dataclasses import dataclass, field
from typing import List, Optional, Dict
import numpy as np
import pandas as pd

@dataclass
class MarketForecast:
    """
    Forecasted market parameters for the execution horizon.
    Each array should have length T (number of intervals).
    """
    intervals: List[str]          # Timestamps
    expected_volume: np.ndarray   # V_t
    expected_volatility: np.ndarray # sigma_t
    expected_spread: np.ndarray   # s_t
    
    # Impact Model Params (Implementation Shortfall = alpha * q + beta * q^2)
    alpha: np.ndarray             # Linear cost coef (half-spread + linear impact)
    beta: np.ndarray              # Quadratic cost coef (market impact)
    
    cliff_hazard: Optional[np.ndarray] = None # h_t (Prob of liquidity shock)
    
    @property
    def T(self) -> int:
        return len(self.intervals)

@dataclass
class PlanningInput:
    """
    Inputs required to run the Global Planner.
    """
    total_shares: float           # Q
    forecast: MarketForecast
    
    # Risk Preferences
    risk_aversion: float = 1.0    # lambda
    smooth_penalty: float = 0.1   # gamma
    
    # Constraints
    max_participation: float = 0.10 # 10% of volume

@dataclass
class Schedule:
    """
    The output of the planner.
    """
    intervals: List[str]
    quantities: np.ndarray        # q*_t
    
    # Diagnostics
    expected_cost: float
    expected_risk: float
    is_feasible: bool
    solver_status: str
    solve_time: float
    
    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({
            "interval": self.intervals,
            "quantity": self.quantities
        })

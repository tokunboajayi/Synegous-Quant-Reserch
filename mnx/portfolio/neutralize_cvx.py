import pandas as pd
import cvxpy as cp
import numpy as np

def neutralize_weights(scores: pd.Series, max_pos: float = 0.05) -> pd.Series:
    """
    Constructs a Dollar-Neutral, Gross-Leverage=1 portfolio using Convex Optimization.
    Objective: Maximize DotProduct(w, scores) - L2_Regularization
    Constraints:
      1. Sum(w) == 0 (Dollar Neutral)
      2. Sum(abs(w)) <= 1 (Gross Leverage)
      3. abs(w) <= max_pos (Concentration Limit)
    """
    n = len(scores)
    tickers = scores.index
    mu = scores.values
    
    # Fill NaN
    mu = np.nan_to_num(mu)
    
    # Define Variables
    w = cp.Variable(n)
    
    # Objective: Maximize expected score (alpha) - penalize large weights (diversification)
    # L2 regularization acts as a proxy for transaction costs/risk
    gamma = 0.5
    objective = cp.Maximize(mu @ w - gamma * cp.sum_squares(w))
    
    # Constraints
    constraints = [
        cp.sum(w) == 0,        # Dollar Neutral
        cp.norm(w, 1) <= 1.0,  # Gross Leverage <= 1.0
        cp.abs(w) <= max_pos   # Max Position Size
    ]
    
    # Solve
    try:
        prob = cp.Problem(objective, constraints)
        prob.solve(solver=cp.OSQP) # OSQP is usually installed/fast
        
        if w.value is None:
            print("[CVX] Solver failed/unbounded. Fallback to naive ranking.")
            raise ValueError("Solver Failed")
            
        optimal_weights = pd.Series(w.value, index=tickers)
        
        # Clean small noise
        optimal_weights[optimal_weights.abs() < 1e-4] = 0.0
        
        return optimal_weights
        
    except Exception as e:
        print(f"[CVX] Optimization Error: {e}. Fallback to naive deciles.")
        # Fallback: Naive Decile
        ranked = scores.rank(method='first', pct=True)
        weights = pd.Series(0.0, index=scores.index)
        long_mask = ranked > 0.9
        weights[long_mask] = 1.0 / long_mask.sum()
        short_mask = ranked < 0.1
        weights[short_mask] = -1.0 / short_mask.sum()
        return weights

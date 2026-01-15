import cvxpy as cp
import numpy as np
import time
from nmie.optimizer.types import PlanningInput, Schedule

class GlobalPlanner:
    """
    Layer A: Global Convex Planner.
    Solves for the optimal trajectory q* minimizing Expected Cost + Risk.
    """
    
    def plan(self, inputs: PlanningInput) -> Schedule:
        T = inputs.forecast.T
        if T == 0:
            raise ValueError("Forecast horizon cannot be 0")
            
        # --- Variables ---
        q = cp.Variable(T)
        
        # --- Parameters ---
        # Impact Model: Cost ~ alpha * q + beta * q^2
        # alpha ~ spread/2 + permanent impact
        # beta ~ temporary impact
        alpha = inputs.forecast.alpha
        beta = inputs.forecast.beta
        
        # Risk: sigma^2 * q^2 (Simplified variance of cost proxy)
        # Often risk is modeled as variance of residual position -> this is a simplified per-trade risk 
        # For true IS variance, we minimize sum(sigma_i^2 * x_i^2) where x is holding? 
        # Standard Almgren-Chriss formulation:
        # E[Cost] = sum(perm_imp * x_i + temp_imp * q_i^2)
        # Var[Cost] ~ sum(sigma^2 * x_i^2) (holding risk)
        
        # We will use the prompt's objective formulation:
        # sum(alpha*q + beta*q^2) + lambda * sum((sigma*q)^2) + gamma * sum((q_t - q_{t-1})^2)
        # Note: (sigma*q)^2 puts penalty on TRADING in volatile times vs HOLDING via volatile times.
        # This effectively interprets "Risk" as "Execution Risk" or slippage uncertainty.
        
        sigma = inputs.forecast.expected_volatility
        
        # --- Objective ---
        # 1. Expected Cost
        cost_term = alpha @ q + cp.sum(cp.multiply(beta, q**2))
        
        # 2. Risk Penalty (Execution Risk)
        # lambda * sum(sigma^2 * q^2)
        risk_term = inputs.risk_aversion * cp.sum(cp.multiply(sigma**2, q**2))
        
        # 3. Smoothing (Signal Stability)
        # gamma * sum((q_t - q_{t-1})^2)
        if T > 1:
            diff_q = q[1:] - q[:-1]
            smooth_term = inputs.smooth_penalty * cp.sum_squares(diff_q)
        else:
            smooth_term = 0
            
        objective = cp.Minimize(cost_term + risk_term + smooth_term)
        
        # --- Constraints ---
        constraints = []
        
        # 1. Completion
        constraints.append(cp.sum(q) == inputs.total_shares)
        
        # 2. No Selling (Long Only Execution for now)
        constraints.append(q >= 0)
        
        # 3. Participation Rate Constraint (q_t <= p_max * V_t)
        max_q = inputs.max_participation * inputs.forecast.expected_volume
        constraints.append(q <= max_q)
        
        # --- Solve ---
        start_time = time.time()
        problem = cp.Problem(objective, constraints)
        
        # Scaling issues can happen with finance numbers.
        # If shares are huge (1M), q^2 is 10^12. CVXPY usually handles this but good to watch.
        try:
            problem.solve(solver=cp.OSQP) # OSQP is good for quadratic
            if problem.status not in ["optimal", "optimal_inaccurate"]:
                # Try ECOS as backup
                problem.solve(solver=cp.ECOS)
        except Exception as e:
            print(f"Solver Error: {e}")
            
        elapsed = time.time() - start_time
        
        # --- Result Extraction ---
        if problem.status in ["optimal", "optimal_inaccurate"]:
            q_val = q.value
            # Clip small negatives (numerical noise)
            q_val = np.maximum(q_val, 0)
            
            # Re-normalize to ensure sum is exactly Q (correcting numerical drift)
            current_sum = np.sum(q_val)
            if current_sum > 0:
                q_val = q_val * (inputs.total_shares / current_sum)
                
            return Schedule(
                intervals=inputs.forecast.intervals,
                quantities=q_val,
                expected_cost=cost_term.value if cost_term.value else 0.0,
                expected_risk=risk_term.value if risk_term.value else 0.0,
                is_feasible=True,
                solver_status=problem.status,
                solve_time=elapsed
            )
        else:
            print(f"Optimization Failed: {problem.status}")
            return Schedule(
                intervals=inputs.forecast.intervals,
                quantities=np.zeros(T),
                expected_cost=0.0,
                expected_risk=0.0,
                is_feasible=False,
                solver_status=problem.status,
                solve_time=elapsed
            )

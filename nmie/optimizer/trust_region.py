from dataclasses import dataclass
import numpy as np

@dataclass
class TrustRegionConfig:
    max_deviation_pct: float = 0.20  # Max +/- 20% deviation from accumulated plan
    step_limit_pct: float = 0.50     # Max +/- 50% deviation in a single step (alpha in [0.5, 1.5])
    catchup_rate: float = 0.10       # How fast to correct deviation per step

class TrustRegion:
    """
    Enforces safety boundaries around the global reference plan.
    Ensures that the executed trajectory does not drift too far from q*.
    """
    def __init__(self, config: TrustRegionConfig):
        self.config = config
        
    def clip_quantity(self, 
                      planned_q: float, 
                      proposed_alpha: float,
                      cum_executed: float,
                      cum_planned: float,
                      total_shares: float) -> float:
        """
        Clips the proposed quantity to satisfy Trust Region constraints.
        
        Args:
            planned_q: The Q* for this single interval.
            proposed_alpha: The controller's multiplier (e.g. 1.2 x planned).
            cum_executed: Total shares executed so far (before this step).
            cum_planned: Total shares supposed to be executed so far (before this step).
            total_shares: Total parent order size.
            
        Returns:
            final_q: The safe quantity to execute.
        """
        # 1. Instantaneous Step Limit
        # Limit alpha to [1 - step_limit, 1 + step_limit]
        min_alpha = 1.0 - self.config.step_limit_pct
        max_alpha = 1.0 + self.config.step_limit_pct
        effective_alpha = np.clip(proposed_alpha, min_alpha, max_alpha)
        
        proposed_q = planned_q * effective_alpha
        
        # 2. Cumulative Deviation Limit (The "Cone" of safety)
        # |CumExec + q - (CumPlan + q*)| <= MaxDev * Total
        # Let's verify if proposed_q keeps us within bounds.
        
        allowed_drift = self.config.max_deviation_pct * total_shares
        
        current_drift = cum_executed - cum_planned
        future_drift = current_drift + (proposed_q - planned_q)
        
        if abs(future_drift) <= allowed_drift:
            return proposed_q
            
        # If violating, clip to boundary
        # If future_drift > allowed, we reduce q
        # Exec + q - (Plan + q*) = allowed
        # q = allowed + Plan + q* - Exec
        if future_drift > allowed_drift:
            # We are too far ahead (Aggressive) -> Slow down
            corrected_q = allowed_drift + (cum_planned + planned_q) - cum_executed
        else: # future_drift < -allowed_drift
            # We are too far behind (Passive) -> Speed up
            corrected_q = -allowed_drift + (cum_planned + planned_q) - cum_executed
            
        # Ensure non-negative
        corrected_q = max(0.0, corrected_q)
        
        # 3. Apply Catchup Logic (Soft constraint / Heuristic)
        # If we are behind, we might WANT to be faster than plan, 
        # but the controller might have said "slow down" due to bad spreads.
        # The Trust Region acts as a hard boundary.
        # If we are at the edge, we MUST correct. 
        # The logic above enforces the hard boundary.
        
        return corrected_q

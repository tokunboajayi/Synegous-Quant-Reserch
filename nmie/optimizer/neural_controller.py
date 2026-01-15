from dataclasses import dataclass
import numpy as np

@dataclass
class MarketState:
    """
    State observed by the Local Controller.
    """
    vol_ratio: float       # Realized Vol / Expected Vol
    spread_ratio: float    # Realized Spread / Expected Spread
    imbalance: float       # Order Book Imbalance (-1 to 1)
    
    # Execution Progress
    progress_frac: float   # Shares Executed / Total
    time_frac: float       # Time Elapsed / Total
    deviation_pct: float   # (Exec - Plan) / Total

class LocalController:
    """
    Layer B: Local Neural Controller (Tactical).
    Adaptation policy that outputs an aggression multiplier alpha_t.
    """
    def __init__(self):
        # In a real system, this would load a trained PyTorch model.
        # For this prototype, we implement the "Converged Policy" deterministically.
        pass
        
    def get_action(self, state: MarketState) -> float:
        """
        Determines execution speed multiplier alpha.
        alpha = 1.0 : Follow Global Plan exactly.
        alpha > 1.0 : Speed up (Aggressive).
        alpha < 1.0 : Slow down (Passive).
        """
        base_alpha = 1.0
        
        # --- Logic 1: Liquidity Opportunism ---
        # If Volume is high (vol_ratio > 1) and Spread is tight (spread_ratio < 1), 
        # we should take more liquidity.
        if state.vol_ratio > 1.1 and state.spread_ratio < 0.9:
            base_alpha += 0.2  # +20% aggression
        
        # --- Logic 2: Spread Aversion ---
        # If Spread is blown out, wait (unless urgent).
        if state.spread_ratio > 1.3:
            base_alpha -= 0.3 # -30% aggression
            
        # --- Logic 3: Catchup (Schedule Adherence) ---
        # If we are falling behind (deviation < 0), speed up slightly
        # If we are ahead (deviation > 0), slow down
        # Gain K_p
        k_p = 2.0 
        # Target deviation is 0. 
        # If deviation is -0.05 (-5%), correction is +0.10 (+10% alpha)
        correction = -1.0 * k_p * state.deviation_pct
        base_alpha += correction
        
        # --- Logic 4: Urgency at End ---
        # If time is running out (>90%) and we have shares left, panic!
        # (Though Global Planner handles the schedule 'shape', local shocks might leave us with dust)
        # We rely on Global Planner for the main curve, so this is just minor fix.
        
        # Clip to reasonable tactical bounds [0.0, 3.0]
        # (Trust Region will apply tighter clips)
        return float(np.clip(base_alpha, 0.0, 3.0))

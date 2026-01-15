from abc import ABC, abstractmethod
import numpy as np

class ExecutionPolicy(ABC):
    @abstractmethod
    def get_quantity(self, 
                     t_idx: int, 
                     total_intervals: int, 
                     rem_shares: float, 
                     market_volume: float = None) -> float:
        pass

class TWAP(ExecutionPolicy):
    def get_quantity(self, t_idx: int, total_intervals: int, rem_shares: float, market_volume: float = None) -> float:
        rem_intervals = total_intervals - t_idx
        if rem_intervals <= 0:
            return rem_shares
        return rem_shares / rem_intervals

class VWAP(ExecutionPolicy):
    def __init__(self, volume_profile: np.ndarray):
        self.profile = volume_profile / np.sum(volume_profile)
        
    def get_quantity(self, t_idx: int, total_intervals: int, rem_shares: float, market_volume: float = None) -> float:
        if t_idx >= len(self.profile):
            return rem_shares
            
        target_pct = self.profile[t_idx]
        rem_profile_sum = np.sum(self.profile[t_idx:])
        if rem_profile_sum == 0:
            return rem_shares
            
        normalized_target = target_pct / rem_profile_sum
        return rem_shares * normalized_target

class POV(ExecutionPolicy):
    def __init__(self, participation_rate: float):
        self.rate = participation_rate
        
    def get_quantity(self, t_idx: int, total_intervals: int, rem_shares: float, market_volume: float = None) -> float:
        if market_volume is None:
            raise ValueError("POV requires market_volume")
        
        qty = self.rate * market_volume
        return min(qty, rem_shares)


# =============================================================================
# HELPER FUNCTIONS - Generate static schedules as arrays
# =============================================================================

def twap_schedule(total_qty: float, n_intervals: int) -> np.ndarray:
    """Generate TWAP schedule - equal slices."""
    if n_intervals <= 0:
        return np.array([total_qty])
    return np.full(n_intervals, total_qty / n_intervals)

def vwap_schedule(total_qty: float, volume_profile: np.ndarray) -> np.ndarray:
    """Generate VWAP schedule - proportional to volume."""
    if len(volume_profile) == 0:
        return np.array([total_qty])
    total_vol = np.sum(volume_profile)
    if total_vol == 0:
        return twap_schedule(total_qty, len(volume_profile))
    return total_qty * (volume_profile / total_vol)

def pov_schedule(total_qty: float, volume_profile: np.ndarray, participation_rate: float = 0.1) -> np.ndarray:
    """Generate POV schedule - constant % of volume."""
    if len(volume_profile) == 0:
        return np.array([total_qty])
    
    raw_schedule = participation_rate * volume_profile
    
    # Scale to match total quantity
    raw_total = np.sum(raw_schedule)
    if raw_total == 0:
        return twap_schedule(total_qty, len(volume_profile))
    
    return total_qty * (raw_schedule / raw_total)

"""
Execution Simulation - Constraints
Participation caps and fill validation.
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ExecutionConstraints:
    """Constraints for realistic execution simulation."""
    max_participation_rate: float = 0.10  # Max 10% of bar volume
    min_fill_size: int = 1  # Minimum shares per fill
    max_bar_volume_cap: float = 0.25  # Max 25% of any single bar
    
def apply_participation_cap(
    scheduled_qty: float,
    bar_volume: float,
    constraints: ExecutionConstraints = None
) -> Tuple[float, float]:
    """
    Apply participation cap to scheduled quantity.
    
    Returns: (executable_qty, unfilled_qty)
    """
    if constraints is None:
        constraints = ExecutionConstraints()
        
    max_executable = bar_volume * constraints.max_participation_rate
    
    if scheduled_qty <= max_executable:
        return scheduled_qty, 0.0
    else:
        return max_executable, scheduled_qty - max_executable

def validate_fill(
    fill_qty: float,
    fill_price: float,
    bar_volume: float,
    bar_low: float,
    bar_high: float,
    constraints: ExecutionConstraints = None
) -> Tuple[bool, str]:
    """
    Validate that a fill is realistic.
    
    Returns: (is_valid, reason_if_invalid)
    """
    if constraints is None:
        constraints = ExecutionConstraints()
    
    # Check volume constraint
    if fill_qty > bar_volume * constraints.max_bar_volume_cap:
        return False, f"Fill exceeds {constraints.max_bar_volume_cap:.0%} of bar volume"
    
    # Check price in range
    if fill_price < bar_low or fill_price > bar_high:
        return False, f"Fill price {fill_price} outside bar range [{bar_low}, {bar_high}]"
    
    # Check minimum size
    if fill_qty < constraints.min_fill_size and fill_qty > 0:
        return False, f"Fill size {fill_qty} below minimum {constraints.min_fill_size}"
    
    return True, ""

def compute_participation_rate(
    executed_qty: float,
    bar_volume: float
) -> float:
    """Compute participation rate for a fill."""
    if bar_volume <= 0:
        return 0.0
    return min(1.0, executed_qty / bar_volume)

def get_unfilled_summary(
    scheduled: np.ndarray,
    executed: np.ndarray
) -> dict:
    """Summarize unfilled quantities."""
    total_scheduled = np.sum(scheduled)
    total_executed = np.sum(executed)
    unfilled = total_scheduled - total_executed
    
    n_intervals = len(scheduled)
    n_fully_filled = np.sum(executed >= scheduled * 0.99)
    n_partially_filled = np.sum((executed > 0) & (executed < scheduled * 0.99))
    n_unfilled = np.sum(executed == 0)
    
    return {
        "total_scheduled": float(total_scheduled),
        "total_executed": float(total_executed),
        "total_unfilled": float(unfilled),
        "pct_filled": float(total_executed / total_scheduled) if total_scheduled > 0 else 0,
        "n_intervals": n_intervals,
        "n_fully_filled": int(n_fully_filled),
        "n_partially_filled": int(n_partially_filled),
        "n_unfilled": int(n_unfilled),
        "pct_intervals_with_cap_binding": float(n_partially_filled / n_intervals) if n_intervals > 0 else 0
    }

"""
Research Analytics Engine - Core Types
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import date
from enum import Enum
import numpy as np

class GateDecision(Enum):
    PROMOTE = "PROMOTE"
    HOLD = "HOLD"
    REJECT = "REJECT"

@dataclass
class WalkForwardFold:
    """Single walk-forward fold."""
    fold_id: int
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    
    @property
    def train_days(self) -> int:
        return (self.train_end - self.train_start).days
    
    @property
    def test_days(self) -> int:
        return (self.test_end - self.test_start).days

@dataclass
class WalkForwardResult:
    """Results from a single fold."""
    fold_id: int
    n_orders: int
    mean_is_anee: float
    mean_is_twap: float
    delta_is: float
    p95_is_anee: float
    p95_is_twap: float
    win_rate: float

@dataclass
class SignificanceResult:
    """Statistical test results."""
    test_name: str
    statistic: float
    p_value: float
    ci_low: float
    ci_high: float
    is_significant: bool
    
@dataclass
class CalibrationResult:
    """Calibration metrics."""
    ece: float  # Expected Calibration Error
    brier: float
    coverage_p90: float
    coverage_p95: float
    reliability_bins: List[Dict[str, float]]

@dataclass
class DriftResult:
    """Feature drift metrics."""
    feature: str
    psi: float
    is_drifted: bool
    reference_mean: float
    current_mean: float

@dataclass
class AttributionResult:
    """Cost attribution breakdown."""
    order_id: str
    spread_cost_bps: float
    impact_cost_bps: float
    vol_cost_bps: float
    hazard_cost_bps: float
    total_is_bps: float

@dataclass
class ErrorBucket:
    """Failure mode bucket."""
    bucket_name: str
    n_orders: int
    mean_is: float
    p95_is: float
    regime_tags: List[str]

@dataclass
class LeaderboardEntry:
    """Policy comparison entry."""
    policy: str
    mean_is: float
    median_is: float
    p95_is: float
    win_rate_vs_twap: float
    rank: int

@dataclass
class GateResult:
    """Promotion gate decision."""
    run_id: str
    decision: GateDecision
    reasons: List[str]
    scores: Dict[str, float]
    thresholds: Dict[str, float]
    passed_checks: List[str]
    failed_checks: List[str]

@dataclass
class ResearchRun:
    """Complete research run output."""
    run_id: str
    timestamp: str
    universe: str
    data_source: str
    folds: List[WalkForwardResult]
    significance: Optional[SignificanceResult] = None
    calibration: Optional[CalibrationResult] = None
    drift: List[DriftResult] = field(default_factory=list)
    attribution: List[AttributionResult] = field(default_factory=list)
    error_buckets: List[ErrorBucket] = field(default_factory=list)
    leaderboard: List[LeaderboardEntry] = field(default_factory=list)
    gate: Optional[GateResult] = None

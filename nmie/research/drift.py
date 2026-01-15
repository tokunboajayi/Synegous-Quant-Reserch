"""
Feature Drift Detection
PSI calculation and drift monitoring.
"""
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

from nmie.research.types import DriftResult
from nmie.research.gates_config import GateConfig

def compute_psi(
    reference: np.ndarray,
    current: np.ndarray,
    n_bins: int = 10,
    epsilon: float = 1e-6
) -> float:
    """
    Population Stability Index (PSI).
    
    PSI < 0.1: No significant shift
    PSI 0.1-0.25: Moderate shift
    PSI > 0.25: Significant shift
    """
    if len(reference) == 0 or len(current) == 0:
        return 0.0
        
    # Compute bin edges from reference
    min_val = min(np.min(reference), np.min(current))
    max_val = max(np.max(reference), np.max(current))
    
    if min_val == max_val:
        return 0.0
        
    bin_edges = np.linspace(min_val, max_val, n_bins + 1)
    
    # Compute histograms
    ref_hist, _ = np.histogram(reference, bins=bin_edges)
    cur_hist, _ = np.histogram(current, bins=bin_edges)
    
    # Normalize to percentages
    ref_pct = ref_hist / len(reference) + epsilon
    cur_pct = cur_hist / len(current) + epsilon
    
    # PSI formula
    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    
    return psi

def detect_drift(
    feature_name: str,
    reference: np.ndarray,
    current: np.ndarray,
    psi_threshold: float = None
) -> DriftResult:
    """
    Detect drift for a single feature.
    """
    if psi_threshold is None:
        psi_threshold = GateConfig.MAX_PSI
        
    psi = compute_psi(reference, current)
    
    return DriftResult(
        feature=feature_name,
        psi=psi,
        is_drifted=(psi > psi_threshold),
        reference_mean=float(np.mean(reference)) if len(reference) > 0 else 0,
        current_mean=float(np.mean(current)) if len(current) > 0 else 0
    )

def compute_drift_timeline(
    feature_name: str,
    reference: np.ndarray,
    time_series: List[Tuple[str, np.ndarray]],
    psi_threshold: float = None
) -> List[Dict]:
    """
    Compute PSI over time for a feature.
    
    time_series: [(period_id, values), ...]
    
    Returns list of {period, psi, is_drifted}
    """
    if psi_threshold is None:
        psi_threshold = GateConfig.MAX_PSI
        
    timeline = []
    
    for period_id, values in time_series:
        psi = compute_psi(reference, values)
        timeline.append({
            "period": period_id,
            "feature": feature_name,
            "psi": psi,
            "is_drifted": psi > psi_threshold,
            "current_mean": float(np.mean(values)) if len(values) > 0 else 0
        })
        
    return timeline

def compute_all_features_drift(
    reference_features: Dict[str, np.ndarray],
    current_features: Dict[str, np.ndarray]
) -> List[DriftResult]:
    """
    Compute drift for all features.
    """
    results = []
    
    for feature_name in reference_features.keys():
        if feature_name not in current_features:
            continue
            
        result = detect_drift(
            feature_name,
            reference_features[feature_name],
            current_features[feature_name]
        )
        results.append(result)
        
    return results

def get_top_drifted_features(
    drift_results: List[DriftResult],
    top_n: int = 5
) -> List[DriftResult]:
    """Get features with highest PSI."""
    sorted_results = sorted(drift_results, key=lambda x: x.psi, reverse=True)
    return sorted_results[:top_n]

def compute_drift_breach_rate(drift_results: List[DriftResult]) -> float:
    """Compute fraction of features that drifted."""
    if not drift_results:
        return 0.0
    n_drifted = sum(1 for d in drift_results if d.is_drifted)
    return n_drifted / len(drift_results)

"""
Calibration Metrics
ECE, Brier, reliability, conformal coverage.
"""
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass

from nmie.research.types import CalibrationResult

def compute_ece(
    predicted_probs: np.ndarray,
    actual_outcomes: np.ndarray,
    n_bins: int = 10
) -> Tuple[float, List[Dict]]:
    """
    Expected Calibration Error.
    
    Returns: (ece, reliability_bins)
    """
    if len(predicted_probs) == 0:
        return 0.0, []
        
    bin_edges = np.linspace(0, 1, n_bins + 1)
    reliability_bins = []
    
    total_ece = 0.0
    total_samples = len(predicted_probs)
    
    for i in range(n_bins):
        low, high = bin_edges[i], bin_edges[i + 1]
        mask = (predicted_probs >= low) & (predicted_probs < high)
        
        if i == n_bins - 1:  # Include 1.0 in last bin
            mask = (predicted_probs >= low) & (predicted_probs <= high)
            
        n_in_bin = np.sum(mask)
        
        if n_in_bin > 0:
            avg_predicted = np.mean(predicted_probs[mask])
            avg_actual = np.mean(actual_outcomes[mask])
            bin_ece = np.abs(avg_predicted - avg_actual) * (n_in_bin / total_samples)
            total_ece += bin_ece
            
            reliability_bins.append({
                "bin_low": low,
                "bin_high": high,
                "n_samples": int(n_in_bin),
                "mean_predicted": float(avg_predicted),
                "mean_actual": float(avg_actual),
                "calibration_error": float(np.abs(avg_predicted - avg_actual))
            })
        else:
            reliability_bins.append({
                "bin_low": low,
                "bin_high": high,
                "n_samples": 0,
                "mean_predicted": 0.0,
                "mean_actual": 0.0,
                "calibration_error": 0.0
            })
            
    return total_ece, reliability_bins

def compute_brier_score(
    predicted_probs: np.ndarray,
    actual_outcomes: np.ndarray
) -> float:
    """
    Brier score for probability calibration.
    Lower is better.
    """
    if len(predicted_probs) == 0:
        return 0.0
    return np.mean((predicted_probs - actual_outcomes) ** 2)

def compute_quantile_coverage(
    predictions: np.ndarray,
    actuals: np.ndarray,
    quantile: float
) -> float:
    """
    Compute empirical coverage for a predicted quantile.
    
    predictions: predicted quantile values
    actuals: realized values
    quantile: target coverage (e.g., 0.90 for p90)
    
    Returns: empirical coverage rate
    """
    if len(predictions) == 0:
        return 0.0
        
    # For upper quantile: actual should be <= prediction
    covered = actuals <= predictions
    return np.mean(covered)

def compute_calibration(
    predicted_quantiles: Dict[str, np.ndarray],
    actuals: np.ndarray,
    predicted_probs: np.ndarray = None,
    actual_events: np.ndarray = None
) -> CalibrationResult:
    """
    Compute full calibration metrics.
    
    predicted_quantiles: {"p50": [...], "p90": [...], "p95": [...]}
    actuals: realized IS values
    predicted_probs: probability predictions (for ECE/Brier)
    actual_events: binary outcomes (for ECE/Brier)
    """
    # Quantile coverage
    coverage_p90 = 0.0
    coverage_p95 = 0.0
    
    if "p90" in predicted_quantiles:
        coverage_p90 = compute_quantile_coverage(
            predicted_quantiles["p90"], actuals, 0.90
        )
    if "p95" in predicted_quantiles:
        coverage_p95 = compute_quantile_coverage(
            predicted_quantiles["p95"], actuals, 0.95
        )
        
    # Probability calibration
    ece = 0.0
    brier = 0.0
    reliability_bins = []
    
    if predicted_probs is not None and actual_events is not None:
        ece, reliability_bins = compute_ece(predicted_probs, actual_events)
        brier = compute_brier_score(predicted_probs, actual_events)
        
    return CalibrationResult(
        ece=ece,
        brier=brier,
        coverage_p90=coverage_p90,
        coverage_p95=coverage_p95,
        reliability_bins=reliability_bins
    )

def split_conformal_calibration(
    cal_scores: np.ndarray,
    test_scores: np.ndarray,
    target_coverage: float = 0.90
) -> Tuple[float, np.ndarray]:
    """
    Split conformal prediction for calibrated intervals.
    
    cal_scores: conformity scores from calibration set
    test_scores: scores for test set
    target_coverage: desired coverage level
    
    Returns: (quantile_threshold, calibrated_predictions)
    """
    if len(cal_scores) == 0:
        return 0.0, test_scores
        
    # Compute quantile from calibration set
    n = len(cal_scores)
    q = np.ceil((n + 1) * target_coverage) / n
    q = min(q, 1.0)
    
    threshold = np.quantile(cal_scores, q)
    
    # Apply to test set
    return threshold, threshold * np.ones_like(test_scores)

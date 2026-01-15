"""
Statistical Significance Tests
Bootstrap and permutation tests for policy comparison.
"""
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

from nmie.research.types import SignificanceResult

def block_bootstrap_mean(
    data: np.ndarray,
    n_bootstrap: int = 1000,
    block_size: int = 5,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Block bootstrap for time series.
    Returns: (mean, ci_low, ci_high)
    """
    np.random.seed(seed)
    n = len(data)
    
    if n == 0:
        return 0.0, 0.0, 0.0
        
    n_blocks = max(1, n // block_size)
    
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        # Sample blocks with replacement
        block_starts = np.random.randint(0, max(1, n - block_size + 1), size=n_blocks)
        
        sample = []
        for start in block_starts:
            end = min(start + block_size, n)
            sample.extend(data[start:end])
            
        if sample:
            bootstrap_means.append(np.mean(sample))
            
    if not bootstrap_means:
        return np.mean(data), np.mean(data), np.mean(data)
        
    return (
        np.mean(bootstrap_means),
        np.percentile(bootstrap_means, 2.5),
        np.percentile(bootstrap_means, 97.5)
    )

def block_bootstrap_test(
    treatment: np.ndarray,
    control: np.ndarray,
    n_bootstrap: int = 1000,
    block_size: int = 5,
    seed: int = 42
) -> SignificanceResult:
    """
    Block bootstrap test for difference in means.
    H0: treatment mean <= control mean (no improvement)
    """
    np.random.seed(seed)
    
    observed_delta = np.mean(treatment) - np.mean(control)
    
    # Bootstrap the difference
    n = min(len(treatment), len(control))
    
    if n == 0:
        return SignificanceResult(
            test_name="block_bootstrap",
            statistic=0.0,
            p_value=1.0,
            ci_low=0.0,
            ci_high=0.0,
            is_significant=False
        )
    
    n_blocks = max(1, n // block_size)
    
    bootstrap_deltas = []
    
    for _ in range(n_bootstrap):
        block_starts = np.random.randint(0, max(1, n - block_size + 1), size=n_blocks)
        
        t_sample = []
        c_sample = []
        
        for start in block_starts:
            end = min(start + block_size, n)
            t_sample.extend(treatment[start:end])
            c_sample.extend(control[start:end])
            
        if t_sample and c_sample:
            delta = np.mean(t_sample) - np.mean(c_sample)
            bootstrap_deltas.append(delta)
            
    if not bootstrap_deltas:
        return SignificanceResult(
            test_name="block_bootstrap",
            statistic=observed_delta,
            p_value=1.0,
            ci_low=observed_delta,
            ci_high=observed_delta,
            is_significant=False
        )
    
    # One-sided p-value: P(delta <= 0)
    p_value = np.mean(np.array(bootstrap_deltas) <= 0)
    
    ci_low = np.percentile(bootstrap_deltas, 2.5)
    ci_high = np.percentile(bootstrap_deltas, 97.5)
    
    return SignificanceResult(
        test_name="block_bootstrap",
        statistic=observed_delta,
        p_value=p_value,
        ci_low=ci_low,
        ci_high=ci_high,
        is_significant=(p_value < 0.05)
    )

def permutation_test(
    treatment: np.ndarray,
    control: np.ndarray,
    n_permutations: int = 1000,
    seed: int = 42
) -> SignificanceResult:
    """
    Permutation test for difference in means.
    """
    np.random.seed(seed)
    
    observed_delta = np.mean(treatment) - np.mean(control)
    
    combined = np.concatenate([treatment, control])
    n_treatment = len(treatment)
    
    null_deltas = []
    
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_treatment = combined[:n_treatment]
        perm_control = combined[n_treatment:]
        
        delta = np.mean(perm_treatment) - np.mean(perm_control)
        null_deltas.append(delta)
        
    null_deltas = np.array(null_deltas)
    
    # Two-sided p-value
    p_value = np.mean(np.abs(null_deltas) >= np.abs(observed_delta))
    
    return SignificanceResult(
        test_name="permutation",
        statistic=observed_delta,
        p_value=p_value,
        ci_low=np.percentile(null_deltas, 2.5),
        ci_high=np.percentile(null_deltas, 97.5),
        is_significant=(p_value < 0.05)
    )

def compute_is_significance(
    is_anee: List[float],
    is_twap: List[float]
) -> SignificanceResult:
    """
    Compute significance of ANEE improvement over TWAP.
    Lower IS is better, so we test if ANEE IS < TWAP IS.
    """
    # For IS, improvement = TWAP - ANEE (positive = good)
    improvement = np.array(is_twap) - np.array(is_anee)
    
    return block_bootstrap_test(
        treatment=improvement,
        control=np.zeros_like(improvement)
    )

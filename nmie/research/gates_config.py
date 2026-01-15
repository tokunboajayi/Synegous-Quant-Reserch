"""
Promotion Gate Configuration v3
Configurable thresholds with minimum data requirements.
"""

# ============================================================================
# GATE THRESHOLDS v3
# ============================================================================

class GateConfig:
    """Configurable promotion gate thresholds."""
    
    # ========================================================================
    # DATA MINIMUMS (v3 - STOP BS WINS)
    # ========================================================================
    MIN_TOTAL_DAYS = 60         # Minimum total trading days
    MIN_TEST_DAYS = 20          # Minimum test days per fold
    MIN_TICKERS = 10            # Minimum tickers (or 4 ETFs + 6 mega caps)
    MIN_ORDERS = 500            # Minimum orders for credibility
    HARD_SIM_REQUIRED = True    # Must pass on HARD simulator
    
    # ========================================================================
    # PERFORMANCE THRESHOLDS
    # ========================================================================
    MIN_IS_IMPROVEMENT_BPS = 0.5        # Mean IS must improve by at least X bps
    MAX_P95_DEGRADATION_BPS = 2.0       # p95 IS cannot worsen by more than X bps
    MIN_WIN_RATE = 0.50                 # Must win at least 50% vs TWAP
    MIN_WIN_RATE_VS_VWAP = 0.45         # Must win 45% vs VWAP (harder baseline)
    
    # ========================================================================
    # STATISTICAL SIGNIFICANCE
    # ========================================================================
    P_VALUE_THRESHOLD = 0.05            # Block bootstrap p-value
    
    # ========================================================================
    # CALIBRATION THRESHOLDS
    # ========================================================================
    MIN_P90_COVERAGE = 0.85             # p90 quantile coverage
    MIN_P95_COVERAGE = 0.90             # p95 quantile coverage
    MAX_ECE = 0.10                      # Expected Calibration Error
    
    # ========================================================================
    # DRIFT THRESHOLDS
    # ========================================================================
    MAX_PSI = 0.25                      # PSI threshold for drift
    MAX_DRIFT_BREACH_RATE = 0.20        # Max % of features drifted
    
    # ========================================================================
    # STABILITY THRESHOLDS
    # ========================================================================
    MAX_FOLD_IS_STD = 3.0               # Max std in fold IS improvements
    MAX_WORST_FOLD_LOSS = -5.0          # Worst fold cannot lose more than X bps
    MIN_REGIMES_IMPROVED = 3            # Must improve in at least 3 regime slices
    
    # ========================================================================
    # SIMULATOR AGREEMENT
    # ========================================================================
    MAX_HARD_SOFT_DIVERGENCE_BPS = 3.0  # Max divergence between simulators
    
    # ========================================================================
    # CONTROLLER RISK
    # ========================================================================
    MAX_TAIL_RISK_INCREASE = 1.0        # Controller cannot increase p95 by more than X bps
    
    @classmethod
    def to_dict(cls) -> dict:
        return {
            # Data minimums
            "min_total_days": cls.MIN_TOTAL_DAYS,
            "min_test_days": cls.MIN_TEST_DAYS,
            "min_tickers": cls.MIN_TICKERS,
            "min_orders": cls.MIN_ORDERS,
            "hard_sim_required": cls.HARD_SIM_REQUIRED,
            # Performance
            "min_is_improvement_bps": cls.MIN_IS_IMPROVEMENT_BPS,
            "max_p95_degradation_bps": cls.MAX_P95_DEGRADATION_BPS,
            "min_win_rate": cls.MIN_WIN_RATE,
            "min_win_rate_vs_vwap": cls.MIN_WIN_RATE_VS_VWAP,
            # Significance
            "p_value_threshold": cls.P_VALUE_THRESHOLD,
            # Calibration
            "min_p90_coverage": cls.MIN_P90_COVERAGE,
            "min_p95_coverage": cls.MIN_P95_COVERAGE,
            "max_ece": cls.MAX_ECE,
            # Drift
            "max_psi": cls.MAX_PSI,
            "max_drift_breach_rate": cls.MAX_DRIFT_BREACH_RATE,
            # Stability
            "max_fold_is_std": cls.MAX_FOLD_IS_STD,
            "max_worst_fold_loss": cls.MAX_WORST_FOLD_LOSS,
            "min_regimes_improved": cls.MIN_REGIMES_IMPROVED,
            # Simulator
            "max_hard_soft_divergence_bps": cls.MAX_HARD_SOFT_DIVERGENCE_BPS,
            # Controller
            "max_tail_risk_increase": cls.MAX_TAIL_RISK_INCREASE
        }
    
    @classmethod
    def check_data_minimums(cls, n_days: int, n_tickers: int, n_orders: int) -> tuple:
        """
        Check if data meets minimum requirements.
        Returns: (meets_minimums: bool, reasons: list)
        """
        reasons = []
        
        if n_days < cls.MIN_TOTAL_DAYS:
            reasons.append(f"Only {n_days} days < minimum {cls.MIN_TOTAL_DAYS}")
        if n_tickers < cls.MIN_TICKERS:
            reasons.append(f"Only {n_tickers} tickers < minimum {cls.MIN_TICKERS}")
        if n_orders < cls.MIN_ORDERS:
            reasons.append(f"Only {n_orders} orders < minimum {cls.MIN_ORDERS}")
            
        return len(reasons) == 0, reasons

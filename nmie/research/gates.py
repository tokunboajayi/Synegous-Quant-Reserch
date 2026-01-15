"""
Promotion Gate Logic v3
Deterministic rubric with data minimum gates.
"""
from typing import List, Dict, Optional
from dataclasses import asdict

from nmie.research.types import (
    GateResult, GateDecision, WalkForwardResult,
    SignificanceResult, CalibrationResult, DriftResult
)
from nmie.research.gates_config import GateConfig
from nmie.research.artifacts import write_gate_decision

class PromotionGate:
    """
    v3 Promotion Gate with data minimums.
    
    PROMOTE only if ALL true:
    - Data meets minimums (days, tickers, orders)
    - Mean IS improvement vs VWAP >= threshold AND significant
    - p95 IS not worse than baseline by tolerance
    - Improvement holds in >= 3 regimes
    - HARD simulator agrees directionally with SOFT
    - Calibration within tolerance
    
    HOLD if:
    - Data below minimums (labeled "PIPELINE VALIDATION ONLY")
    - Mixed results
    
    REJECT if:
    - Worse on key metrics
    """
    
    def __init__(self, config: GateConfig = None):
        self.config = config or GateConfig()
        
    def evaluate(
        self,
        run_id: str,
        fold_results: List[WalkForwardResult],
        significance: Optional[SignificanceResult] = None,
        calibration: Optional[CalibrationResult] = None,
        drift_results: List[DriftResult] = None,
        tail_risk_delta: float = 0.0,
        # v3 additions
        n_days: int = 0,
        n_tickers: int = 0,
        n_orders: int = 0,
        hard_sim_agrees: bool = True,
        n_regimes_improved: int = 0
    ) -> GateResult:
        """Evaluate all gates and return decision."""
        passed = []
        failed = []
        scores = {}
        reasons = []
        
        # =====================================================================
        # 0. DATA MINIMUMS (v3 - CRITICAL)
        # =====================================================================
        meets_minimums, min_reasons = self.config.check_data_minimums(n_days, n_tickers, n_orders)
        scores["n_days"] = n_days
        scores["n_tickers"] = n_tickers
        scores["n_orders"] = n_orders
        
        is_validation_only = not meets_minimums
        
        if meets_minimums:
            passed.append("data_minimums")
        else:
            failed.append("data_minimums")
            reasons.extend(min_reasons)
            reasons.append("RUN LABELED: PIPELINE VALIDATION ONLY")
        
        # =====================================================================
        # 1. HARD SIMULATOR AGREEMENT (v3)
        # =====================================================================
        scores["hard_sim_agrees"] = hard_sim_agrees
        if self.config.HARD_SIM_REQUIRED:
            if hard_sim_agrees:
                passed.append("hard_simulator_agreement")
            else:
                failed.append("hard_simulator_agreement")
                reasons.append("SIMULATOR AGREEMENT FAILURE: Hard/Soft Divergence > 5bps")
        
        # =====================================================================
        # 2. PERFORMANCE GATE
        # =====================================================================
        mean_delta = sum(f.delta_is for f in fold_results) / len(fold_results) if fold_results else 0
        scores["mean_is_delta_bps"] = mean_delta
        
        if mean_delta >= self.config.MIN_IS_IMPROVEMENT_BPS:
            passed.append("mean_is_improvement")
        else:
            failed.append("mean_is_improvement")
            reasons.append(f"Mean IS improvement {mean_delta:.2f} bps < threshold {self.config.MIN_IS_IMPROVEMENT_BPS}")
        
        # =====================================================================
        # 3. TAIL RISK GATE
        # =====================================================================
        if fold_results:
            p95_deltas = [f.p95_is_anee - f.p95_is_twap for f in fold_results]
            mean_p95_delta = sum(p95_deltas) / len(p95_deltas)
            scores["mean_p95_delta_bps"] = mean_p95_delta
            
            if mean_p95_delta <= self.config.MAX_P95_DEGRADATION_BPS:
                passed.append("tail_risk")
            else:
                failed.append("tail_risk")
                reasons.append(f"p95 IS worsened by {mean_p95_delta:.2f} bps > tolerance")
        
        # =====================================================================
        # 4. WIN RATE GATE
        # =====================================================================
        if fold_results:
            avg_win_rate = sum(f.win_rate for f in fold_results) / len(fold_results)
            scores["win_rate"] = avg_win_rate
            
            if avg_win_rate >= self.config.MIN_WIN_RATE:
                passed.append("win_rate")
            else:
                failed.append("win_rate")
                reasons.append(f"Win rate {avg_win_rate:.1%} < threshold {self.config.MIN_WIN_RATE:.1%}")
        
        # =====================================================================
        # 5. SIGNIFICANCE GATE
        # =====================================================================
        if significance:
            scores["p_value"] = significance.p_value
            if significance.is_significant and significance.p_value < self.config.P_VALUE_THRESHOLD:
                passed.append("statistical_significance")
            else:
                failed.append("statistical_significance")
                reasons.append(f"Not statistically significant (p={significance.p_value:.3f})")
        else:
            failed.append("statistical_significance")
            reasons.append("No significance test performed")
        
        # =====================================================================
        # 6. REGIME CONSISTENCY (v3)
        # =====================================================================
        scores["n_regimes_improved"] = n_regimes_improved
        if n_regimes_improved >= self.config.MIN_REGIMES_IMPROVED:
            passed.append("regime_consistency")
        else:
            failed.append("regime_consistency")
            reasons.append(f"Improved in {n_regimes_improved} regimes < minimum {self.config.MIN_REGIMES_IMPROVED}")
        
        # =====================================================================
        # 7. CALIBRATION GATE
        # =====================================================================
        if calibration:
            scores["ece"] = calibration.ece
            scores["p90_coverage"] = calibration.coverage_p90
            
            cal_ok = True
            if calibration.ece > self.config.MAX_ECE:
                cal_ok = False
                reasons.append(f"ECE {calibration.ece:.3f} > threshold {self.config.MAX_ECE}")
                
            if cal_ok:
                passed.append("calibration")
            else:
                failed.append("calibration")
        
        # =====================================================================
        # DECISION
        # =====================================================================
        n_failed = len(failed)
        
        # If data minimums not met, always HOLD
        if is_validation_only:
            decision = GateDecision.HOLD
        # Core gates
        elif "mean_is_improvement" in failed or "hard_simulator_agreement" in failed:
            decision = GateDecision.REJECT
        elif n_failed == 0:
            decision = GateDecision.PROMOTE
        elif n_failed <= 2:
            decision = GateDecision.HOLD
        else:
            decision = GateDecision.REJECT
        
        reasons = reasons[:5]
        
        return GateResult(
            run_id=run_id,
            decision=decision,
            reasons=reasons,
            scores=scores,
            thresholds=self.config.to_dict(),
            passed_checks=passed,
            failed_checks=failed
        )
    
    def save_decision(self, run_id: str, result: GateResult) -> str:
        """Save gate decision to artifact."""
        data = {
            "run_id": result.run_id,
            "decision": result.decision.value,
            "is_validation_only": "data_minimums" in result.failed_checks,
            "reasons": result.reasons,
            "scores": result.scores,
            "thresholds": result.thresholds,
            "passed_checks": result.passed_checks,
            "failed_checks": result.failed_checks
        }
        path = write_gate_decision(run_id, data)
        return str(path)

"""
Cost Attribution
Decompose IS into spread, impact, volatility, hazard components.
"""
import numpy as np
from typing import List, Dict
from dataclasses import dataclass

from nmie.research.types import AttributionResult

def attribute_costs(
    order_id: str,
    quantities: np.ndarray,
    prices: np.ndarray,
    spreads: np.ndarray,
    volatilities: np.ndarray,
    hazards: np.ndarray = None,
    arrival_price: float = None,
    total_is_bps: float = None
) -> AttributionResult:
    """
    Decompose implementation shortfall into components.
    
    Approximate attribution:
    - spread_cost = sum(q_t * spread_t / 2) / total_value
    - vol_cost = sum(q_t * sigma_t * sqrt(dt)) / total_value
    - hazard_cost = sum(q_t * h_t * scaling) / total_value
    - impact_cost = residual
    """
    if len(quantities) == 0:
        return AttributionResult(
            order_id=order_id,
            spread_cost_bps=0, impact_cost_bps=0,
            vol_cost_bps=0, hazard_cost_bps=0, total_is_bps=0
        )
    
    total_shares = np.sum(quantities)
    avg_price = np.mean(prices) if len(prices) > 0 else 1
    total_value = total_shares * avg_price
    
    if total_value == 0:
        total_value = 1
    
    # Spread cost (half spread per share)
    spread_cost = np.sum(quantities * spreads / 2)
    spread_cost_bps = (spread_cost / total_value) * 10000
    
    # Volatility cost proxy
    dt = 1.0 / 390  # 1 minute in trading day
    vol_cost = np.sum(quantities * volatilities * np.sqrt(dt) * avg_price)
    vol_cost_bps = (vol_cost / total_value) * 10000
    
    # Hazard cost (if available)
    hazard_cost_bps = 0.0
    if hazards is not None and len(hazards) == len(quantities):
        hazard_scaling = 0.5  # Tunable parameter
        hazard_cost = np.sum(quantities * hazards * hazard_scaling * avg_price)
        hazard_cost_bps = (hazard_cost / total_value) * 10000
    
    # Impact cost = residual
    if total_is_bps is not None:
        impact_cost_bps = total_is_bps - spread_cost_bps - vol_cost_bps - hazard_cost_bps
    else:
        # Estimate using t^2 proxy
        impact_cost_bps = max(0, spread_cost_bps * 0.5)  # Rough estimate
    
    return AttributionResult(
        order_id=order_id,
        spread_cost_bps=float(spread_cost_bps),
        impact_cost_bps=float(impact_cost_bps),
        vol_cost_bps=float(vol_cost_bps),
        hazard_cost_bps=float(hazard_cost_bps),
        total_is_bps=float(total_is_bps if total_is_bps else 
                          spread_cost_bps + impact_cost_bps + vol_cost_bps + hazard_cost_bps)
    )

def compute_constraint_binding(
    planned_quantities: np.ndarray,
    max_participation: float,
    volumes: np.ndarray
) -> Dict[str, float]:
    """
    Analyze how often participation constraints bind.
    """
    max_allowed = max_participation * volumes
    
    n_binding = np.sum(planned_quantities >= max_allowed * 0.99)
    n_total = len(planned_quantities)
    
    binding_rate = n_binding / n_total if n_total > 0 else 0
    
    # Average excess demand
    excess = np.maximum(0, planned_quantities - max_allowed)
    avg_excess = np.mean(excess)
    
    return {
        "binding_rate": float(binding_rate),
        "n_binding_intervals": int(n_binding),
        "n_total_intervals": int(n_total),
        "avg_excess_shares": float(avg_excess)
    }

def summarize_controller_interventions(
    planned: np.ndarray,
    executed: np.ndarray,
    intervention_threshold: float = 0.05
) -> Dict:
    """
    Summarize when and how much controller deviated from plan.
    """
    if len(planned) == 0 or len(executed) == 0:
        return {"n_interventions": 0, "intervention_rate": 0, "avg_deviation": 0}
    
    deviations = np.abs(executed - planned) / (planned + 1e-9)
    interventions = deviations > intervention_threshold
    
    n_interventions = np.sum(interventions)
    
    return {
        "n_interventions": int(n_interventions),
        "intervention_rate": float(n_interventions / len(planned)),
        "avg_deviation": float(np.mean(deviations[interventions])) if n_interventions > 0 else 0,
        "max_deviation": float(np.max(deviations)) if len(deviations) > 0 else 0,
        "avg_abs_deviation": float(np.mean(np.abs(executed - planned)))
    }

def aggregate_attribution(
    attributions: List[AttributionResult]
) -> Dict[str, float]:
    """Aggregate attribution across orders."""
    if not attributions:
        return {}
    
    return {
        "mean_spread_cost_bps": float(np.mean([a.spread_cost_bps for a in attributions])),
        "mean_impact_cost_bps": float(np.mean([a.impact_cost_bps for a in attributions])),
        "mean_vol_cost_bps": float(np.mean([a.vol_cost_bps for a in attributions])),
        "mean_hazard_cost_bps": float(np.mean([a.hazard_cost_bps for a in attributions])),
        "mean_total_is_bps": float(np.mean([a.total_is_bps for a in attributions]))
    }

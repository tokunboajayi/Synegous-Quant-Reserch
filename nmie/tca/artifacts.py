"""
TCA - Artifacts
Standardized TCA output files.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from nmie.config import DATA_DIR

OUTPUTS_DIR = DATA_DIR / "outputs"

class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

def get_run_dir(run_id: str) -> Path:
    """Get run output directory."""
    run_dir = OUTPUTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir

def write_tca_summary(
    run_id: str,
    strategy_metrics: Dict[str, Dict]
) -> Path:
    """
    Write tca_summary.json with strategy comparison.
    
    strategy_metrics: {
        "TWAP": {"mean_is_bps": ..., "median_is_bps": ..., "p90": ..., "p95": ..., "win_rate": ...},
        "VWAP": {...},
        ...
    }
    """
    path = get_run_dir(run_id) / "tca_summary.json"
    
    data = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),
        "strategies": strategy_metrics
    }
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, cls=NumpyEncoder)
    
    return path

def write_tca_orders(
    run_id: str,
    orders: List[Dict]
) -> Path:
    """
    Write tca_orders.parquet with per-order metrics.
    """
    path = get_run_dir(run_id) / "tca_orders.parquet"
    df = pd.DataFrame(orders)
    df.to_parquet(path, index=False)
    return path

def write_regime_slices(
    run_id: str,
    slices: List[Dict]
) -> Path:
    """Write regime_slices.csv."""
    path = get_run_dir(run_id) / "regime_slices.csv"
    df = pd.DataFrame(slices)
    df.to_csv(path, index=False)
    return path

def write_simulator_sensitivity(
    run_id: str,
    sensitivity: Dict
) -> Path:
    """
    Write simulator_sensitivity.json.
    
    sensitivity: {
        "hard_mean_is": ...,
        "soft_mean_is": ...,
        "agrees": bool,
        "sensitivity_warning": bool,
        ...
    }
    """
    path = get_run_dir(run_id) / "simulator_sensitivity.json"
    
    with open(path, 'w') as f:
        json.dump(sensitivity, f, indent=2, cls=NumpyEncoder)
    
    return path

def write_executive_note(
    run_id: str,
    headline: str,
    summary: str,
    key_findings: List[str],
    recommendation: str,
    gate_decision: str
) -> Path:
    """Write executive_note.md (1-page memo)."""
    path = get_run_dir(run_id) / "executive_note.md"
    
    content = f"""# TCA Executive Summary

**Run ID:** {run_id}  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Headline
{headline}

## Summary
{summary}

## Key Findings
"""
    for i, finding in enumerate(key_findings, 1):
        content += f"{i}. {finding}\n"
    
    content += f"""
## Recommendation
{recommendation}

## Governance Decision
**{gate_decision}**
"""
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return path

def list_tca_artifacts(run_id: str) -> Dict[str, bool]:
    """Check which TCA artifacts exist."""
    run_dir = get_run_dir(run_id)
    
    required = [
        "tca_summary.json",
        "tca_orders.parquet",
        "regime_slices.csv",
        "simulator_sensitivity.json",
        "executive_note.md"
    ]
    
    return {name: (run_dir / name).exists() for name in required}

def get_missing_tca_artifacts(run_id: str) -> List[str]:
    """Get list of missing TCA artifacts."""
    available = list_tca_artifacts(run_id)
    return [name for name, exists in available.items() if not exists]

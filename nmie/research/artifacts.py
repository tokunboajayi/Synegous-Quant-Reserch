"""
Standardized Artifact Writer/Reader
All research outputs saved under data/outputs/{run_id}/
"""
import json
import os
from pathlib import Path
from datetime import datetime, date
from typing import Any, Dict, List, Optional
import pandas as pd
import polars as pl
from dataclasses import asdict, is_dataclass

# OUTPUTS_DIR = DATA_DIR / "outputs"
OUTPUTS_DIR = Path("/app/data/outputs")

def get_run_dir(run_id: str) -> Path:
    """Get directory for a run's artifacts."""
    run_dir = OUTPUTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir

def generate_run_id() -> str:
    """Generate unique run ID."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

class DateEncoder(json.JSONEncoder):
    """JSON encoder for dates and numpy types."""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if is_dataclass(obj):
            return asdict(obj)
        if hasattr(obj, 'value'):  # Enum
            return obj.value
        # Numpy types
        import numpy as np
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

# ============================================================================
# WRITERS
# ============================================================================

def write_json(run_id: str, filename: str, data: Any) -> Path:
    """Write JSON artifact."""
    run_dir = get_run_dir(run_id)
    path = run_dir / filename
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, cls=DateEncoder, indent=2)
    
    return path

def write_csv(run_id: str, filename: str, df: pd.DataFrame) -> Path:
    """Write CSV artifact."""
    run_dir = get_run_dir(run_id)
    path = run_dir / filename
    df.to_csv(path, index=False)
    return path

def write_parquet(run_id: str, filename: str, df: pl.DataFrame) -> Path:
    """Write Parquet artifact."""
    run_dir = get_run_dir(run_id)
    path = run_dir / filename
    df.write_parquet(path)
    return path

# ============================================================================
# READERS
# ============================================================================

def read_json(run_id: str, filename: str) -> Optional[Dict]:
    """Read JSON artifact."""
    path = get_run_dir(run_id) / filename
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding JSON artifact: {path}")
            return None

def read_csv(run_id: str, filename: str) -> Optional[pd.DataFrame]:
    """Read CSV artifact."""
    path = get_run_dir(run_id) / filename
    if not path.exists():
        return None
    return pd.read_csv(path)

def read_parquet(run_id: str, filename: str) -> Optional[pl.DataFrame]:
    """Read Parquet artifact."""
    path = get_run_dir(run_id) / filename
    if not path.exists():
        return None
    return pl.read_parquet(path)

# ============================================================================
# STANDARD ARTIFACT NAMES
# ============================================================================

ARTIFACT_NAMES = {
    "walkforward": "walkforward_results.json",
    "calibration": "calibration.json",
    "drift": "drift_timeline.json",
    "error_buckets": "error_buckets.csv",
    "attribution": "attribution.csv",
    "leaderboard": "leaderboard.json",
    "gate": "gate_decision.json",
    "summary": "research_summary.json",
}

def write_walkforward_results(run_id: str, results: List[Dict]) -> Path:
    """Write walk-forward results."""
    return write_json(run_id, ARTIFACT_NAMES["walkforward"], {
        "run_id": run_id,
        "n_folds": len(results),
        "folds": results
    })

def write_calibration(run_id: str, data: Dict) -> Path:
    """Write calibration report."""
    return write_json(run_id, ARTIFACT_NAMES["calibration"], data)

def write_drift_timeline(run_id: str, data: List[Dict]) -> Path:
    """Write drift timeline."""
    return write_json(run_id, ARTIFACT_NAMES["drift"], {
        "run_id": run_id,
        "features": data
    })

def write_error_buckets(run_id: str, df: pd.DataFrame) -> Path:
    """Write error buckets."""
    return write_csv(run_id, ARTIFACT_NAMES["error_buckets"], df)

def write_attribution(run_id: str, df: pd.DataFrame) -> Path:
    """Write cost attribution."""
    return write_csv(run_id, ARTIFACT_NAMES["attribution"], df)

def write_leaderboard(run_id: str, entries: List[Dict]) -> Path:
    """Write leaderboard."""
    return write_json(run_id, ARTIFACT_NAMES["leaderboard"], {
        "run_id": run_id,
        "entries": entries
    })

def write_gate_decision(run_id: str, decision: Dict) -> Path:
    """Write gate decision."""
    return write_json(run_id, ARTIFACT_NAMES["gate"], decision)

# ============================================================================
# ARTIFACT INDEX
# ============================================================================

def list_artifacts(run_id: str) -> Dict[str, bool]:
    """List available artifacts for a run."""
    run_dir = get_run_dir(run_id)
    
    available = {}
    for key, filename in ARTIFACT_NAMES.items():
        available[key] = (run_dir / filename).exists()
        
    return available

def get_missing_artifacts(run_id: str) -> List[str]:
    """Get list of missing artifacts."""
    available = list_artifacts(run_id)
    return [k for k, v in available.items() if not v]

def list_runs() -> List[str]:
    """List all run IDs."""
    if not OUTPUTS_DIR.exists():
        return []
    return [d.name for d in OUTPUTS_DIR.iterdir() if d.is_dir()]

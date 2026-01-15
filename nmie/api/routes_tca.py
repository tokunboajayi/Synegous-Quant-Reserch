"""
TCA API Routes
Transaction Cost Analysis endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import pandas as pd

from nmie.tca.artifacts import (
    get_run_dir, list_tca_artifacts, get_missing_tca_artifacts
)
from nmie.research.artifacts import read_json

router = APIRouter(prefix="/tca", tags=["TCA"])

@router.get("/runs/{run_id}/summary")
def get_tca_summary(run_id: str):
    """Get TCA summary with strategy comparison."""
    path = get_run_dir(run_id) / "tca_summary.json"
    if not path.exists():
        raise HTTPException(404, f"tca_summary.json not found for run {run_id}")
    
    import json
    with open(path) as f:
        return json.load(f)

@router.get("/runs/{run_id}/orders")
def get_tca_orders(run_id: str, limit: int = 100):
    """Get per-order TCA metrics."""
    path = get_run_dir(run_id) / "tca_orders.parquet"
    if not path.exists():
        raise HTTPException(404, f"tca_orders.parquet not found for run {run_id}")
    
    df = pd.read_parquet(path)
    return {"orders": df.head(limit).to_dict(orient="records")}

@router.get("/runs/{run_id}/order/{order_id}")
def get_order_playback(run_id: str, order_id: str):
    """Get playback data for a single order."""
    path = get_run_dir(run_id) / "tca_orders.parquet"
    if not path.exists():
        raise HTTPException(404, f"tca_orders.parquet not found")
    
    df = pd.read_parquet(path)
    order = df[df["order_id"] == order_id]
    
    if len(order) == 0:
        raise HTTPException(404, f"Order {order_id} not found")
    
    return order.to_dict(orient="records")[0]

@router.get("/runs/{run_id}/regimes")
def get_regime_slices(run_id: str):
    """Get regime slice analysis."""
    path = get_run_dir(run_id) / "regime_slices.csv"
    if not path.exists():
        raise HTTPException(404, f"regime_slices.csv not found")
    
    df = pd.read_csv(path)
    return {"regimes": df.to_dict(orient="records")}

@router.get("/runs/{run_id}/sensitivity")
def get_simulator_sensitivity(run_id: str):
    """Get simulator sensitivity analysis."""
    path = get_run_dir(run_id) / "simulator_sensitivity.json"
    if not path.exists():
        raise HTTPException(404, f"simulator_sensitivity.json not found")
    
    import json
    with open(path) as f:
        return json.load(f)

@router.get("/runs/{run_id}/executive")
def get_executive_note(run_id: str):
    """Get executive summary note."""
    path = get_run_dir(run_id) / "executive_note.md"
    if not path.exists():
        raise HTTPException(404, f"executive_note.md not found")
    
    with open(path, encoding='utf-8') as f:
        return {"content": f.read()}

@router.get("/runs/{run_id}/artifacts")
def get_tca_artifacts_status(run_id: str):
    """Check which TCA artifacts exist."""
    available = list_tca_artifacts(run_id)
    missing = get_missing_tca_artifacts(run_id)
    
    return {
        "run_id": run_id,
        "artifacts": available,
        "missing": missing,
        "complete": len(missing) == 0
    }

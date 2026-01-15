"""
Research API Routes
Serve research artifacts via REST endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional

from nmie.research.artifacts import (
    list_runs, list_artifacts, get_missing_artifacts,
    read_json, read_csv, ARTIFACT_NAMES
)

router = APIRouter(prefix="/research", tags=["Research Analytics"])

@router.get("/runs")
def get_runs():
    """List all research run IDs."""
    runs = list_runs()
    return {"runs": runs, "count": len(runs)}

@router.get("/runs/{run_id}")
def get_run_index(run_id: str):
    """Get artifact index for a run."""
    available = list_artifacts(run_id)
    missing = get_missing_artifacts(run_id)
    
    return {
        "run_id": run_id,
        "artifacts": available,
        "missing": missing
    }

@router.get("/runs/{run_id}/walkforward")
def get_walkforward(run_id: str):
    """Get walk-forward results."""
    data = read_json(run_id, ARTIFACT_NAMES["walkforward"])
    if data is None:
        raise HTTPException(404, f"walkforward_results.json not found for run {run_id}")
    return data

@router.get("/runs/{run_id}/calibration")
def get_calibration(run_id: str):
    """Get calibration report."""
    data = read_json(run_id, ARTIFACT_NAMES["calibration"])
    if data is None:
        raise HTTPException(404, f"calibration.json not found for run {run_id}")
    return data

@router.get("/runs/{run_id}/drift")
def get_drift(run_id: str):
    """Get drift timeline."""
    data = read_json(run_id, ARTIFACT_NAMES["drift"])
    if data is None:
        raise HTTPException(404, f"drift_timeline.json not found for run {run_id}")
    return data

@router.get("/runs/{run_id}/gates")
def get_gates(run_id: str):
    """Get promotion gate decision."""
    data = read_json(run_id, ARTIFACT_NAMES["gate"])
    if data is None:
        raise HTTPException(404, f"gate_decision.json not found for run {run_id}")
    return data

@router.get("/runs/{run_id}/leaderboard")
def get_leaderboard(run_id: str):
    """Get policy leaderboard."""
    data = read_json(run_id, ARTIFACT_NAMES["leaderboard"])
    if data is None:
        raise HTTPException(404, f"leaderboard.json not found for run {run_id}")
    return data

@router.get("/runs/{run_id}/diagnostics")
def get_diagnostics(run_id: str):
    """Get combined diagnostics."""
    walkforward = read_json(run_id, ARTIFACT_NAMES["walkforward"])
    calibration = read_json(run_id, ARTIFACT_NAMES["calibration"])
    gates = read_json(run_id, ARTIFACT_NAMES["gate"])
    leaderboard = read_json(run_id, ARTIFACT_NAMES["leaderboard"])
    
    return {
        "run_id": run_id,
        "walkforward": walkforward,
        "calibration": calibration,
        "gates": gates,
        "leaderboard": leaderboard
    }

@router.get("/runs/{run_id}/error_buckets")
def get_error_buckets(run_id: str):
    """Get error buckets."""
    df = read_csv(run_id, ARTIFACT_NAMES["error_buckets"])
    if df is None:
        raise HTTPException(404, f"error_buckets.csv not found for run {run_id}")
    return {"buckets": df.to_dict(orient="records")}

@router.get("/runs/{run_id}/attribution")
def get_attribution(run_id: str):
    """Get cost attribution."""
    df = read_csv(run_id, ARTIFACT_NAMES["attribution"])
    if df is None:
        raise HTTPException(404, f"attribution.csv not found for run {run_id}")
    return {"attribution": df.to_dict(orient="records")}

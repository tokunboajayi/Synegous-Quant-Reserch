"""
GraphDash API Routes
Graph-centered dashboard endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime

from nmie.research.artifacts import list_runs, read_json, ARTIFACT_NAMES, OUTPUTS_DIR
from nmie.tca.artifacts import list_tca_artifacts, get_run_dir

router = APIRouter(prefix="/graphdash", tags=["GraphDash"])

# Pipeline node definitions
PIPELINE_NODES = [
    {"id": "ingest", "label": "Data Ingest", "description": "Load market data from Polygon"},
    {"id": "features", "label": "Features", "description": "Compute microstructure features"},
    {"id": "schedules", "label": "Schedules", "description": "Generate execution schedules (TWAP/VWAP/CVX)"},
    {"id": "sim_hard", "label": "HARD Sim", "description": "Next-trade fill simulation"},
    {"id": "sim_soft", "label": "SOFT Sim", "description": "Bar VWAP fill simulation"},
    {"id": "tca", "label": "TCA", "description": "Transaction cost analysis"},
    {"id": "research", "label": "Research", "description": "Walk-forward evaluation"},
    {"id": "gate", "label": "Gate", "description": "Promotion decision"}
]

PIPELINE_EDGES = [
    {"source": "ingest", "target": "features"},
    {"source": "features", "target": "schedules"},
    {"source": "schedules", "target": "sim_hard"},
    {"source": "schedules", "target": "sim_soft"},
    {"source": "sim_hard", "target": "tca"},
    {"source": "sim_soft", "target": "tca"},
    {"source": "tca", "target": "research"},
    {"source": "research", "target": "gate"}
]

@router.get("/overview")
def get_overview():
    """Get pipeline overview with latest run status."""
    runs = list_runs()
    latest_run = runs[-1] if runs else None
    
    # Compute node statuses
    node_statuses = {}
    headline_metrics = {}
    
    if latest_run:
        tca_artifacts = list_tca_artifacts(latest_run)
        
        # Determine status of each node
        node_statuses = {
            "ingest": "complete",
            "features": "complete",
            "schedules": "complete",
            "sim_hard": "complete" if tca_artifacts.get("simulator_sensitivity.json") else "pending",
            "sim_soft": "complete" if tca_artifacts.get("simulator_sensitivity.json") else "pending",
            "tca": "complete" if tca_artifacts.get("tca_summary.json") else "pending",
            "research": "complete",
            "gate": "complete"
        }
        
        # Get gate decision
        gate = read_json(latest_run, ARTIFACT_NAMES["gate"])
        if gate:
            headline_metrics["gate_decision"] = gate.get("decision", "UNKNOWN")
            headline_metrics["is_validation_only"] = gate.get("is_validation_only", False)
    
    return {
        "pipeline": {
            "nodes": PIPELINE_NODES,
            "edges": PIPELINE_EDGES,
            "node_statuses": node_statuses
        },
        "latest_run_id": latest_run,
        "n_runs": len(runs),
        "headline_metrics": headline_metrics
    }

@router.get("/runs")
def get_runs():
    """List all runs with metadata."""
    runs = list_runs()
    
    run_info = []
    for run_id in runs:
        gate = read_json(run_id, ARTIFACT_NAMES["gate"])
        
        # Check for MNX Tuning Artifacts if Gate is missing
        gate_decision = None
        if gate:
            gate_decision = gate.get("decision")
        else:
            # Check for tuning params
            mnx_params_path = OUTPUTS_DIR / run_id / "mnx" / "mnx_best_params.json"
            if mnx_params_path.exists():
                gate_decision = "OPTIMIZED"
        
        info = {
            "run_id": run_id,
            "gate_decision": gate_decision,
            "is_validation_only": gate.get("is_validation_only", False) if gate else False,
            "n_days": gate.get("scores", {}).get("n_days", 0) if gate else 0,
            "n_tickers": gate.get("scores", {}).get("n_tickers", 0) if gate else 0,
            "n_orders": gate.get("scores", {}).get("n_orders", 0) if gate else 0
        }
        run_info.append(info)
    
    # Sort by run_id (descending)
    run_info.sort(key=lambda x: x["run_id"], reverse=True)
    
    return {"runs": run_info}

@router.get("/run/{run_id}/pipeline")
def get_run_pipeline(run_id: str):
    """Get pipeline status for a specific run."""
    tca_artifacts = list_tca_artifacts(run_id)
    
    from nmie.research.artifacts import list_artifacts
    research_artifacts = list_artifacts(run_id)
    
    # Combine artifacts
    all_artifacts = {**tca_artifacts, **research_artifacts}
    
    # Fetch Job Timings from DB
    from nmie.control_plane.queue import PersistentQueue
    from nmie.control_plane.state import JobType
    queue = PersistentQueue()
    jobs = queue.list_jobs_for_run(run_id)
    
    timings = {}
    node_map = {
        JobType.MNX_INGEST_DAILY: "mnx_ingest",
        JobType.MNX_BUILD_FEATURES: "mnx_features",
        JobType.MNX_TRAIN_RANKER: "mnx_ranker",
        JobType.MNX_GENERATE_BASKET: "mnx_basket",
        JobType.MNX_TO_NMIE_EXEC_SIM: "mnx_bridge",
        JobType.GENERATE_PARENT_ORDERS: "nmie_orders",
        JobType.BACKTEST_STRATEGIES: "nmie_sim"
    }
    
    for job in jobs:
        if job.type in node_map and job.finished_at:
            # Format: "2:07 PM (45s)"
            duration = (job.finished_at - job.started_at).total_seconds() if job.started_at else 0
            timings[node_map[job.type]] = {
                "timestamp": job.finished_at.strftime("%I:%M %p"),
                "duration": f"{duration:.1f}s"
            }

    return {
        "run_id": run_id,
        "nodes": PIPELINE_NODES,
        "edges": PIPELINE_EDGES,
        "artifacts": all_artifacts,
        "missing": [k for k, v in all_artifacts.items() if not v],
        "timings": timings
    }

@router.get("/run/{run_id}/tca/summary")
def get_run_tca_summary(run_id: str):
    """Get TCA summary for dashboard."""
    path = get_run_dir(run_id) / "tca_summary.json"
    
    if not path.exists():
        # Return placeholder
        return {
            "run_id": run_id,
            "strategies": {},
            "missing": True
        }
    
    import json
    with open(path) as f:
        return json.load(f)

@router.get("/run/{run_id}/tca/sensitivity")
def get_run_tca_sensitivity(run_id: str):
    """Get simulator sensitivity."""
    path = get_run_dir(run_id) / "simulator_sensitivity.json"
    if not path.exists():
        return {}
    
    import json
    with open(path) as f:
        return json.load(f)

@router.get("/run/{run_id}/tca/order/{order_id}")
def get_order_playback(run_id: str, order_id: str):
    """Get playback data for one order."""
    import pandas as pd
    
    path = get_run_dir(run_id) / "tca_orders.parquet"
    if not path.exists():
        raise HTTPException(404, "tca_orders.parquet not found")
    
    df = pd.read_parquet(path)
    order = df[df["order_id"] == order_id]
    
    if len(order) == 0:
        raise HTTPException(404, f"Order {order_id} not found")
    
    return order.to_dict(orient="records")[0]

@router.get("/run/{run_id}/tca/orders")
def get_run_orders(run_id: str, limit: int = 100):
    """List orders for a run (summary)."""
    import pandas as pd
    
    path = get_run_dir(run_id) / "tca_orders.parquet"
    if not path.exists():
        return {"orders": []}
    
    try:
        df = pd.read_parquet(path)
        # Select summary columns
        cols = ["order_id", "ticker", "side", "qty", "limit_price", "status", "fill_qty", "fill_avg_price"]
        available_cols = [c for c in cols if c in df.columns]
        
        summary = df[available_cols].head(limit).fillna(0).to_dict(orient="records")
        return {"orders": summary, "total_count": len(df)}
    except Exception as e:
        print(f"Error reading orders: {e}")
        return {"orders": []}

@router.get("/run/{run_id}/research")
def get_run_research(run_id: str):
    """Get research results for quant view."""
    gate = read_json(run_id, ARTIFACT_NAMES["gate"])
    calibration = read_json(run_id, ARTIFACT_NAMES["calibration"])
    leaderboard = read_json(run_id, ARTIFACT_NAMES["leaderboard"])
    
    return {
        "run_id": run_id,
        "gate": gate,
        "calibration": calibration,
        "leaderboard": leaderboard
    }

@router.get("/glossary")
def get_glossary():
    """Get glossary for layman tooltips."""
    from nmie.tca.explain import GLOSSARY
    return {"glossary": GLOSSARY}

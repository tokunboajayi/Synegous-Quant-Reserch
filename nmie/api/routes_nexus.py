"""
Nexus API Router
Endpoints for controlling and monitoring the autonomous orchestrator.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from nmie.research.nexus_engine import nexus_engine

router = APIRouter(prefix="/nexus", tags=["Synegious Nexus"])

@router.get("/status")
def get_nexus_status():
    """Get the current status of the Nexus orchestrator."""
    return {
        "status": nexus_engine.status,
        "current_stage": nexus_engine.current_stage,
        "progress": nexus_engine.progress,
        "has_last_run": bool(nexus_engine.last_run_results)
    }

@router.post("/run")
async def run_nexus_loop(background_tasks: BackgroundTasks):
    """Trigger the autonomous Nexus research loop in the background."""
    if nexus_engine.status == "RUNNING":
        raise HTTPException(status_code=400, detail="Nexus loop is already running")
    
    background_tasks.add_task(nexus_engine.run_autonomous_loop)
    return {"message": "Nexus autonomous loop started", "status": "RUNNING"}

@router.get("/results")
def get_nexus_results():
    """Get the results of the last successful Nexus run."""
    if not nexus_engine.last_run_results:
        raise HTTPException(status_code=404, detail="No Nexus results available")
    return nexus_engine.last_run_results

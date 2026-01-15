from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import os
import json

from nmie.control_plane.queue import PersistentQueue

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])
queue = PersistentQueue()

DATA_DIR = Path("/app/data/outputs")

@router.get("/{run_id}/index")
def get_artifacts_index(run_id: str):
    """List available artifacts for a run."""
    run_dir = DATA_DIR / run_id
    if not run_dir.exists():
        return {"artifacts": [], "status": "missing_dir"}
        
    files = [f.name for f in run_dir.glob("*") if f.is_file()]
    return {"artifacts": files, "run_id": run_id}

@router.get("/{run_id}/{filename}")
def get_artifact(run_id: str, filename: str):
    """Retrieve a specific artifact."""
    file_path = DATA_DIR / run_id / filename
    
    if not file_path.exists():
        raise HTTPException(404, f"Artifact {filename} not found")
        
    # Security check: ensure no path traversal
    if ".." in filename or "/" in filename:
         raise HTTPException(400, "Invalid filename")
         
    return FileResponse(file_path)

@router.get("/{run_id}/summary/tca")
def get_tca_summary(run_id: str):
    """Convenience endpoint for TCA summary."""
    path = DATA_DIR / run_id / "tca_summary.json"
    if not path.exists():
        raise HTTPException(404, "TCA Summary not found")
    with open(path) as f:
        return json.load(f)

# --- MNX MODULE ENDPOINTS ---

@router.get("/{run_id}/mnx/index")
def get_mnx_index(run_id: str):
    """List MNX-specific artifacts."""
    mnx_dir = DATA_DIR / run_id / "mnx"
    if not mnx_dir.exists():
        return {"artifacts": [], "status": "no_mnx_data"}
    
    files = [f.name for f in mnx_dir.glob("*") if f.is_file()]
    return {"artifacts": files, "run_id": run_id}

@router.get("/{run_id}/mnx/file/{filename}")
def get_mnx_file(run_id: str, filename: str):
    """Retrieve MNX artifact."""
    # Security: filename should be base name
    if "/" in filename or "\\" in filename:
        raise HTTPException(400, "Invalid filename")
        
    path = DATA_DIR / run_id / "mnx" / filename
    if not path.exists():
        raise HTTPException(404, "MNX Artifact not found")
        
    return FileResponse(path)

@router.get("/{run_id}/mnx/basket_summary")
def get_mnx_basket_preview(run_id: str):
    """Return head of basket parquet as JSON."""
    import pandas as pd
    path = DATA_DIR / run_id / "mnx" / "mnx_rebalance_basket.parquet"
    
    if not path.exists():
        return {"status": "missing", "data": []}
        
    try:
        df = pd.read_parquet(path)
        # Convert to records
        return {
            "status": "ok",
            "count": len(df),
            "preview": df.head(50).to_dict(orient="records"),
            "total_turnover": df['qty_delta'].abs().sum() if 'qty_delta' in df else 0
        }
    except Exception as e:
        raise HTTPException(500, f"Error reading basket: {str(e)}")

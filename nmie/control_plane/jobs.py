from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import uuid

from nmie.control_plane.state import JobStatus, JobType, RunStatus

class JobParams(BaseModel):
    # Common params
    tickers: List[str] = Field(default_factory=list)
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    bar_size: str = "1m"
    
    # Strategy specific
    strategies: List[str] = ["TWAP", "VWAP", "POV", "CVX"]
    participation_cap: float = 0.10
    
    # Order gen specific
    n_orders: int = 1000
    
    # Research specific
    model_params: Dict[str, Any] = {}
    
    # Control specific
    job_type: Optional[str] = None
    mnx_enabled: bool = False

class Job(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    type: JobType
    params: JobParams
    status: JobStatus = JobStatus.QUEUED
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    error_msg: Optional[str] = None
    logs_path: Optional[str] = None
    artifacts_path: Optional[str] = None

class Run(BaseModel):
    run_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    status: RunStatus = RunStatus.PENDING
    params: JobParams
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Track progress of child jobs
    jobs: List[str] = []  # list of job_ids
    
    gate_decision: Optional[str] = None # HOLD/PROMOTE
    gate_reason: Optional[str] = None

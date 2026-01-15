from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional

from nmie.control_plane.jobs import Job, JobParams, Run, JobType
from nmie.control_plane.queue import PersistentQueue
from nmie.control_plane.runner import JobRunner
from nmie.control_plane.state import RunStatus
from nmie.control_plane.audit import auditor

router = APIRouter(prefix="/control", tags=["Control Plane"])

# Singletons (should be initialized in server startup, but here for now)
queue = PersistentQueue()
runner = JobRunner(queue)
# runner.start() # MOVED TO LIFECYCLE EVENT

@router.post("/runs/create", response_model=Run)
def create_run(params: JobParams):
    """
    Create a new Run and enqueue a FULL_RUN job.
    """
    # 1. Create Run
    run = Run(params=params)
    queue.create_run(run)
    auditor.log_event("RUN", run.run_id, "CREATED", f"Params: {params.dict()}")
    
    # 2. Create Initial Job
    # Default to FULL_RUN if not specified
    t = params.job_type if params.job_type else JobType.FULL_RUN
    
    job = Job(
        run_id=run.run_id,
        type=t,
        params=params
    )
    queue.add_job(job)
    auditor.log_event("JOB", job.job_id, "ENQUEUED", f"Type: {JobType.FULL_RUN}")
    
    return run

@router.get("/runs", response_model=List[Run])
def list_runs():
    return queue.list_runs()

@router.get("/runs/{run_id}", response_model=Run)
def get_run(run_id: str):
    run = queue.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    # Refresh child jobs status? No, client should ask for details
    return run

@router.get("/runs/{run_id}/jobs", response_model=List[Job])
def list_run_jobs(run_id: str):
    return queue.list_jobs_for_run(run_id)

@router.post("/control/stop")
def stop_runner():
    runner.stop()
    return {"status": "stopped"}

@router.post("/control/start")
def start_runner():
    runner.start()
    return {"status": "started"}

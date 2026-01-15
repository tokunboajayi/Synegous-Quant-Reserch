import time
import threading
import traceback
from datetime import datetime
from pathlib import Path

from nmie.control_plane.queue import PersistentQueue
from nmie.control_plane.jobs import Job, JobParams, Run
from nmie.control_plane.state import JobStatus, JobType, RunStatus

# Import Data Plane Functions
# We assume these exist or will exist. Steps map to functions.
# from nmie.data_ingestion import ingest_data
# from nmie.features import compute_features
# ...

class JobRunner:
    def __init__(self, queue: PersistentQueue):
        self.queue = queue
        self.running = False
        self.worker_thread = None
        self._stop_event = threading.Event()

    def start(self):
        if self.running: return
        self.running = True
        self._stop_event.clear()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        print("JobRunner started.")

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("JobRunner stopped.")

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                jobs = self.queue.fetch_pending_jobs()
                if jobs:
                    # Pick first one
                    job = jobs[0]
                    self._execute_job(job)
                else:
                    time.sleep(1) # Poll interval
            except Exception as e:
                print(f"Runner Loop Error: {e}")
                traceback.print_exc()
                time.sleep(5)

    def _execute_job(self, job: Job):
        print(f"Starting Job {job.job_id} ({job.type})")
        
        # Update Status RUNNING
        self.queue.update_job(job.job_id, {"status": JobStatus.RUNNING, "started_at": datetime.utcnow()})
        
        # Ensure Parent Run is RUNNING
        self.queue.update_run_status(job.run_id, RunStatus.RUNNING)
        
        try:
            # VIRTUAL JOB: FULL_RUN
            if job.type == JobType.FULL_RUN:
                self._handle_full_run(job)
                # Mark itself complete immediately (it just spawned children)
                self.queue.update_job(job.job_id, {"status": JobStatus.COMPLETED, "finished_at": datetime.utcnow()})
                return

            # ACTUAL WORK
            result = self._dispatch_work(job)
            
            # Update Status COMPLETED
            self.queue.update_job(job.job_id, {
                "status": JobStatus.COMPLETED, 
                "finished_at": datetime.utcnow(),
                # "artifacts_path": ...
            })
            print(f"Job {job.job_id} COMPLETED")
            
            # Check if all jobs for this run are complete
            all_jobs = self.queue.list_jobs_for_run(job.run_id)
            if all(j.status == JobStatus.COMPLETED for j in all_jobs):
                 self.queue.update_run_status(job.run_id, RunStatus.COMPLETED)

        except Exception as e:
            err = str(e)
            print(f"Job {job.job_id} FAILED: {err}")
            traceback.print_exc()
            self.queue.update_job(job.job_id, {
                "status": JobStatus.FAILED, 
                "finished_at": datetime.utcnow(), 
                "error_msg": err
            })
            # Also fail the Run
            self.queue.update_run_status(job.run_id, RunStatus.FAILED)

    def _handle_full_run(self, parent_job: Job):
        """
        Orchestrate a sequence of jobs.
        Actually, we just enqueue them all in order? 
        Or we enqueue only the first?
        Better to enqueue all, relying on FIFO.
        """
        steps = [
            JobType.INGEST,
            JobType.BUILD_FEATURES,
            JobType.GENERATE_PARENT_ORDERS,
            JobType.BACKTEST_STRATEGIES, # Includes Sim Hard/Soft
            JobType.TCA_PIPELINE,
            JobType.RESEARCH_PIPELINE,
            JobType.GENERATE_REPORTS
        ]
        
        for step in steps:
            # Create child job
            child = Job(
                run_id=parent_job.run_id,
                type=step,
                params=parent_job.params
            )
            self.queue.add_job(child)
            
        print(f"Enqueued {len(steps)} steps for Run {parent_job.run_id}")
        self.queue.update_run_status(parent_job.run_id, RunStatus.RUNNING)


    def _dispatch_work(self, job: Job):
        """
        Map JobType to actual function calls.
        """
        from nmie.control_plane.logic import run_ingest, run_full_pipeline
        
        t = job.type
        p = job.params
        
        if t == JobType.INGEST:
            run_ingest(p.tickers, p.start_date, p.end_date)
            
        elif t == JobType.FULL_RUN:
            # We treat FULL_RUN as a single blocking call for now (Phase 1 fix)
            pass

        elif t == JobType.BACKTEST_STRATEGIES:
             run_full_pipeline(job.run_id, p)

        elif t == JobType.TCA_PIPELINE:
             pass
             
        elif t == JobType.GENERATE_REPORTS:
             pass

        # MNX Module Dispatch
        elif t == JobType.MNX_INGEST_DAILY:
            from nmie.control_plane.logic import mnx_run_ingest
            mnx_run_ingest(p, job.run_id)
            
        elif t == JobType.MNX_BUILD_FEATURES:
            from nmie.control_plane.logic import mnx_build_features
            mnx_build_features(p, job.run_id)
            
        elif t == JobType.MNX_TRAIN_RANKER:
            from nmie.control_plane.logic import mnx_train_ranker
            mnx_train_ranker(p, job.run_id)
            
        elif t == JobType.MNX_GENERATE_WEIGHTS:
            from nmie.control_plane.logic import mnx_generate_weights
            mnx_generate_weights(p, job.run_id)
            
        elif t == JobType.MNX_GENERATE_BASKET:
            from nmie.control_plane.logic import mnx_generate_basket
            mnx_generate_basket(p, job.run_id)

        elif t == JobType.MNX_TO_NMIE_EXEC_SIM:
            from nmie.control_plane.logic import mnx_bridge_to_nmie
            mnx_bridge_to_nmie(p, job.run_id)

        elif t == JobType.FULL_RUN_MNX_NMIE:
            # Orchestrator: Runs the full chain
            from nmie.control_plane.logic import run_full_mnx_nmie_pipeline
            run_full_mnx_nmie_pipeline(p, job.run_id)

        elif job.type == JobType.MNX_TUNE_MODEL:
            from nmie.control_plane.logic import mnx_tune_model
            mnx_tune_model(p, job.run_id)
        
        return True

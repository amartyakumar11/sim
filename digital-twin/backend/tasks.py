from celery import Celery
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any

# Import simulation function (black box as per contract)
try:
    from simulation.main import run_simulation
except ImportError:
    # Fallback for development when simulation isn't ready
    def run_simulation(runtime_config: dict) -> dict:
        """Placeholder simulation function for development"""
        import time
        time.sleep(5)  # Simulate work
        return {
            "run_id": runtime_config.get("run_id", "unknown"),
            "status": "completed",
            "events_count": 1000,
            "frames_count": 360,
            "summary": {
                "avg_wait_time": 5.2,
                "lost_swaps": 12,
                "charger_utilization": 0.75,
                "total_swaps": 988
            }
        }

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

celery_app = Celery('digital_twin')
celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'tasks.run_simulation_task': 'simulation_queue',
    }
)

# Job status storage (using Redis)
def _store_job_status(run_id: str, status: str, message: str = "", progress: float = None):
    """Store job status in Redis for tracking"""
    from redis import Redis
    
    redis_client = Redis.from_url(CELERY_BROKER_URL)
    
    job_data = {
        "run_id": run_id,
        "status": status,
        "message": message,
        "progress": progress,
        "updated_at": datetime.now().isoformat()
    }
    
    # Store with expiry of 7 days
    redis_client.setex(f"job_status:{run_id}", 7*24*3600, json.dumps(job_data))

def _get_job_status(run_id: str) -> Dict[str, Any]:
    """Get job status from Redis"""
    from redis import Redis
    
    redis_client = Redis.from_url(CELERY_BROKER_URL)
    data = redis_client.get(f"job_status:{run_id}")
    
    if not data:
        raise ValueError(f"Job {run_id} not found")
    
    job_data = json.loads(data)
    # Add created_at if not present (for backward compatibility)
    if "created_at" not in job_data:
        job_data["created_at"] = job_data.get("updated_at", datetime.now().isoformat())
    
    return job_data

@celery_app.task(bind=True)
def run_simulation_task(self, run_id: str, scenario_data: Dict[str, Any]):
    """
    Run a simulation scenario in the background.
    This task calls the simulation engine (black box) and handles results.
    """
    try:
        # Update status to running
        _store_job_status(run_id, "running", "Simulation in progress", 0.0)
        
        # Create data directory structure
        data_dir = f"/app/data/results/{run_id}"
        os.makedirs(data_dir, exist_ok=True)
        
        # Prepare runtime config for simulation engine
        runtime_config = {
            "run_id": run_id,
            "data_dir": data_dir,
            "city_config": scenario_data.get("city_config", {}),
            "interventions": scenario_data.get("interventions", {}),
            "simulation_duration": scenario_data.get("simulation_duration", 3600),
            "description": scenario_data.get("description", "")
        }
        
        # Update progress
        _store_job_status(run_id, "running", "Starting simulation engine", 0.1)
        
        # Call simulation engine (black box as per integration contract)
        simulation_result = run_simulation(runtime_config)
        
        # Update progress
        _store_job_status(run_id, "running", "Processing results", 0.9)
        
        # Prepare final result
        final_result = {
            "run_id": run_id,
            "status": "completed",
            "summary": simulation_result.get("summary", {}),
            "events_count": simulation_result.get("events_count", 0),
            "frames_count": simulation_result.get("frames_count", 0),
            "artifacts": {
                "events": f"{data_dir}/events.ndjson",
                "frames": f"{data_dir}/frames.ndjson", 
                "summary": f"{data_dir}/summary.json"
            }
        }
        
        # Store final result
        _store_job_status(run_id, "completed", "Simulation completed successfully", 1.0)
        
        # Store detailed result
        from redis import Redis
        redis_client = Redis.from_url(CELERY_BROKER_URL)
        redis_client.setex(f"job_result:{run_id}", 7*24*3600, json.dumps(final_result))
        
        return final_result
        
    except Exception as exc:
        error_msg = f"Simulation failed: {str(exc)}"
        _store_job_status(run_id, "failed", error_msg)
        raise self.retry(exc=exc, countdown=60, max_retries=2)

# Helper functions for API layer
def get_task_status(run_id: str) -> Dict[str, Any]:
    """Get task status for API endpoint"""
    return _get_job_status(run_id)

def get_task_result(run_id: str) -> Dict[str, Any]:
    """Get task result for API endpoint"""
    from redis import Redis
    
    redis_client = Redis.from_url(CELERY_BROKER_URL)
    result_data = redis_client.get(f"job_result:{run_id}")
    
    if not result_data:
        # Check if job exists but result not ready
        status = _get_job_status(run_id)
        if status["status"] != "completed":
            return status
        raise ValueError(f"Result for job {run_id} not found")
    
    return json.loads(result_data)
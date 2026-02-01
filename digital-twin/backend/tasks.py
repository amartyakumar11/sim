from celery import Celery
import os
import json
import uuid
from datetime import datetime, timedelta
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
)

# Job status storage (using Redis)
def _store_job_status(run_id: str, status: str, message: str = "", progress: float = None):
    """Store job status in Redis for tracking"""
    try:
        from redis import Redis
        
        redis_client = Redis.from_url(CELERY_BROKER_URL)
        
        # Get existing data to preserve created_at
        existing_data = None
        try:
            existing_raw = redis_client.get(f"job_status:{run_id}")
            if existing_raw:
                existing_data = json.loads(existing_raw)
        except Exception:
            pass
        
        current_time = datetime.now().isoformat()
        job_data = {
            "run_id": run_id,
            "status": status,
            "message": message,
            "progress": progress,
            "created_at": existing_data.get("created_at", current_time) if existing_data else current_time,
            "updated_at": current_time
        }
        
        # Store with expiry of 7 days
        redis_client.setex(f"job_status:{run_id}", 7*24*3600, json.dumps(job_data))
    except Exception as e:
        print(f"Error storing job status for {run_id}: {e}")
        # Don't fail the task if status storage fails

def _get_job_status(run_id: str) -> Dict[str, Any]:
    """Get job status from Redis"""
    try:
        from redis import Redis
        
        redis_client = Redis.from_url(CELERY_BROKER_URL)
        data = redis_client.get(f"job_status:{run_id}")
        
        if not data:
            raise ValueError(f"Job {run_id} not found")
        
        job_data = json.loads(data)
        # Ensure required fields are present
        current_time = datetime.now().isoformat()
        if "created_at" not in job_data:
            job_data["created_at"] = job_data.get("updated_at", current_time)
        if "updated_at" not in job_data:
            job_data["updated_at"] = current_time
            
        return job_data
    except ValueError:
        raise  # Re-raise "not found" errors
    except Exception as e:
        raise ValueError(f"Error retrieving job {run_id}: {str(e)}")

def create_job_status(run_id: str, description: str = ""):
    """Create initial job status when task is submitted"""
    _store_job_status(
        run_id=run_id, 
        status="submitted", 
        message=f"Task submitted for processing. {description}".strip(),
        progress=0.0
    )

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
        simulation_duration = scenario_data.get("simulation_duration", 3600)
        duration_minutes = scenario_data.get("duration_minutes", simulation_duration // 60)
        
        # Use seed from scenario or default to 42
        seed = scenario_data.get("seed", 42)
        
        # Use fixed start_time based on seed for determinism
        # This ensures same seed + same config = same results
        base_date = datetime(2026, 1, 1, 10, 0, 0)  # Fixed reference date
        start_time = base_date + timedelta(days=(seed % 365))
        
        runtime_config = {
            "run_id": run_id,
            "data_dir": data_dir,
            "seed": seed,
            "city": scenario_data.get("city_config", {}).get("city", "unknown"),
            "start_time": start_time,
            "end_time": start_time + timedelta(seconds=simulation_duration),
            "city_config": scenario_data.get("city_config", {}),
            "interventions": scenario_data.get("interventions", {}),
            "simulation_duration": simulation_duration,
            "duration_minutes": duration_minutes,  # Add this for ROI calculations
            "description": scenario_data.get("description", ""),
            "demand": {
                "base_demand_rate_per_min": scenario_data.get("base_demand_rate_per_min", 0.167)  # ~10 riders/hr default
            },
            # Financial parameters (pass through from scenario)
            "revenue_per_swap": scenario_data.get("revenue_per_swap", 50.0),
            "charger_energy_cost": scenario_data.get("charger_energy_cost", 500.0),
            "station_staff_cost": scenario_data.get("station_staff_cost", 2000.0),
            "battery_depreciation_cost": scenario_data.get("battery_depreciation_cost", 1000.0),
            "infra_maintenance_cost": scenario_data.get("infra_maintenance_cost", 500.0),
            "capital_cost": scenario_data.get("capital_cost", 100000.0)
        }
        
        # Update progress
        _store_job_status(run_id, "running", "Starting simulation engine", 0.1)
        
        # Call simulation engine (black box as per integration contract)
        mode = scenario_data.get("mode", "fake")
        simulation_result = run_simulation(runtime_config, mode=mode)
        
        # Update progress
        _store_job_status(run_id, "running", "Processing results", 0.9)
        
        # Extract result fields (simulation returns: metadata, kpis, timeseries, events)
        kpis = simulation_result.get("kpis", {})
        events = simulation_result.get("events", [])
        timeseries = simulation_result.get("timeseries", {})
        
        # Calculate counts
        events_count = len(events)
        frames_count = len(timeseries.get("wait_time", []))
        
        # Prepare final result (map kpis -> summary for API compatibility)
        # Map simulation KPI field names to API response field names
        summary = {
            "avg_wait_time": kpis.get("avg_wait_time"),
            "lost_swaps": kpis.get("lost_swaps"),
            "charger_utilization": kpis.get("charger_utilization", 0.0),  # Use actual charger utilization
            "swap_bay_utilization": kpis.get("swap_bay_utilization", 0.0),  # Add swap bay utilization
            "idle_inventory": kpis.get("idle_inventory"),
            "city_throughput": kpis.get("throughput"),  # Map throughput -> city_throughput
            "total_cost_impact": kpis.get("operational_cost"),  # Map operational_cost -> total_cost_impact
            "roi": kpis.get("roi"),
            "revenue": kpis.get("revenue"),
            "financials": kpis.get("financials")
        }
        
        final_result = {
            "run_id": run_id,
            "status": "completed",
            "summary": summary,
            "events_count": events_count,
            "frames_count": frames_count,
            "artifacts": {
                "events": f"{data_dir}/events.ndjson",
                "frames": f"{data_dir}/frames.ndjson", 
                "summary": f"{data_dir}/summary.json"
            },
            # Include timeline data for frontend visualization
            "station_timelines": simulation_result.get("station_timelines", {}),
            "zone_pressure": simulation_result.get("zone_pressure", []),
            "rider_traces": simulation_result.get("rider_traces", {}),
            "city_config": runtime_config.get("city_config", {})  # Include original city config
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
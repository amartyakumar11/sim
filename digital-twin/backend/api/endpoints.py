from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .models import (
    ScenarioRequest, 
    ScenarioResponse, 
    JobStatusResponse, 
    SimulationResult
)
from tasks import run_simulation_task, get_task_status, get_task_result

router = APIRouter(prefix="/api", tags=["simulation"])

@router.post("/scenarios/submit", response_model=ScenarioResponse)
async def submit_scenario(scenario: ScenarioRequest):
    """
    Submit a new simulation scenario for processing.
    Returns immediately with a run_id for tracking.
    """
    try:
        run_id = str(uuid.uuid4())
        
        # Submit to Celery for background processing
        task = run_simulation_task.delay(run_id, scenario.dict())
        
        return ScenarioResponse(
            run_id=run_id,
            status="submitted",
            message="Scenario submitted for processing"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{run_id}/status", response_model=JobStatusResponse)
async def get_job_status_endpoint(run_id: str):
    """
    Get the current status of a simulation job.
    """
    try:
        status_info = get_task_status(run_id)
        return JobStatusResponse(**status_info)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Job {run_id} not found")

@router.get("/jobs/{run_id}/result", response_model=SimulationResult)
async def get_job_result_endpoint(run_id: str):
    """
    Get the results of a completed simulation job.
    """
    try:
        result = get_task_result(run_id)
        if result["status"] != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Job {run_id} is not completed. Status: {result['status']}"
            )
        return SimulationResult(**result)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/jobs")
async def list_jobs():
    """
    List all simulation jobs with their basic info.
    """
    # TODO: Implement job listing from database/Redis
    return {"message": "Job listing not yet implemented"}

@router.delete("/jobs/{run_id}")
async def cancel_job(run_id: str):
    """
    Cancel a running simulation job.
    """
    # TODO: Implement job cancellation
    return {"message": f"Job {run_id} cancellation not yet implemented"}

@router.get("/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "digital-twin-api"
    }
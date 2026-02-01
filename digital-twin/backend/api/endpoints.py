from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, ValidationError
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .models import (
    ScenarioRequest, 
    ScenarioResponse, 
    JobStatusResponse, 
    SimulationResult,
    SimulationRequest,
    ScenarioComparisonRequest,
    NLToToonRequest,
)
from tasks import run_simulation_task, get_task_status, get_task_result, create_job_status
from nlp.nl_to_toon import translate_nl_to_toon
from nlp.toon_parser import ToonParseError

router = APIRouter(prefix="/api", tags=["simulation"])

def get_station_catalog(city: str) -> list[str]:
    """
    Get list of valid station IDs for a city.
    
    Args:
        city: City name
        
    Returns:
        List of station ID strings
        
    TODO: Replace with database lookup or city config lookup
    """
    # Default station catalog - can be extended with database lookup
    # For now, return common station IDs based on city
    default_stations = [
        "CP_01", "CP_02", "CP_03",
        "DWK_01", "DWK_02", "DWK_03",
        "INA_01", "INA_02", "INA_03",
        "st_001", "st_002", "st_003"
    ]
    
    # City-specific catalogs can be added here
    city_catalogs = {
        "Bangalore": ["CP_01", "DWK_03", "INA_02", "MG_01", "HSR_01"],
        "Delhi": ["CP_01", "DWK_01", "INA_01", "GK_01"],
        "Mumbai": ["CP_01", "DWK_02", "INA_03", "BKC_01"],
    }
    
    return city_catalogs.get(city, default_stations)

def validate_city_config(city_config: Dict[str, Any]) -> None:
    """Validate city configuration structure"""
    if not isinstance(city_config, dict):
        raise ValueError("city_config must be a dictionary")
    
    # Check for required fields
    if "zones" not in city_config:
        raise ValueError("city_config must contain 'zones'")
    if "stations" not in city_config:
        raise ValueError("city_config must contain 'stations'")
        
    zones = city_config["zones"]
    stations = city_config["stations"]
    
    if not isinstance(zones, list) or not zones:
        raise ValueError("zones must be a non-empty list")
        
    if not isinstance(stations, list) or not stations:
        raise ValueError("stations must be a non-empty list")
        
    # Validate each station
    for i, station in enumerate(stations):
        if not isinstance(station, dict):
            raise ValueError(f"Station {i} must be a dictionary")
        
        required_fields = ["station_id", "lat", "lon", "zone_id"]
        for field in required_fields:
            if field not in station:
                raise ValueError(f"Station {i} missing required field: {field}")
        
        # Validate latitude and longitude
        try:
            lat = float(station["lat"])
            lon = float(station["lon"])
            if not (-90 <= lat <= 90):
                raise ValueError(f"Station {i} latitude must be between -90 and 90")
            if not (-180 <= lon <= 180):
                raise ValueError(f"Station {i} longitude must be between -180 and 180")
        except (ValueError, TypeError):
            raise ValueError(f"Station {i} lat/lon must be valid numbers")
            
        # Validate zone_id exists in zones
        if station["zone_id"] not in zones:
            raise ValueError(f"Station {i} zone_id '{station['zone_id']}' not found in zones list")

@router.post("/scenarios/submit", response_model=ScenarioResponse)
async def submit_scenario(scenario: ScenarioRequest):
    """
    Submit a new simulation scenario for processing.
    Returns immediately with a run_id for tracking.
    """
    try:
        # Validate city configuration
        validate_city_config(scenario.city_config)
        
        run_id = str(uuid.uuid4())
        
        # Create initial job status
        create_job_status(run_id, scenario.description)
        
        # Submit to Celery for background processing
        task = run_simulation_task.delay(run_id, scenario.dict())
        
        return ScenarioResponse(
            run_id=run_id,
            status="submitted",
            message="Scenario submitted for processing"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Validation error: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario data: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to submit scenario: {str(e)}"
        )

@router.get("/jobs/{run_id}/status", response_model=JobStatusResponse)
async def get_job_status_endpoint(run_id: str):
    """
    Get the current status of a simulation job.
    """
    try:
        status_info = get_task_status(run_id)
        return JobStatusResponse(**status_info)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=f"Error retrieving job status: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@router.get("/jobs/{run_id}/result", response_model=SimulationResult)
async def get_job_result_endpoint(run_id: str):
    """
    Get the results of a completed simulation job.
    """
    try:
        result = get_task_result(run_id)
        if result["status"] != "completed":
            raise HTTPException(
                status_code=202,  # Accepted - processing not yet complete
                detail=f"Job {run_id} is not completed. Status: {result['status']}. Check /jobs/{run_id}/status for updates."
            )
        return SimulationResult(**result)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

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

@router.post("/run-simulation")
async def run_simulation_endpoint(request: SimulationRequest):
    """
    Run a single simulation with specified mode.
    
    Supports 'fake' mode (fast, UI-safe) and 'real' mode (full SimPy simulation).
    """
    try:
        # Validate mode
        mode = request.mode or "fake"
        if mode not in ("fake", "real"):
            raise HTTPException(
                status_code=400,
                detail="mode must be 'fake' or 'real'"
            )
        
        # Import simulation function
        from simulation.main import run_simulation
        
        # Prepare config with mode
        config = request.config.copy()
        config["mode"] = mode
        
        # Run simulation
        result = run_simulation(config, mode=mode)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {str(e)}"
        )

@router.post("/analytics/demand-heatmap")
async def get_demand_heatmap_endpoint(request: ScenarioRequest):
    """
    Generate demand heatmap data based on scenario configuration.
    
    Returns GeoJSON FeatureCollection with demand intensity per station.
    """
    try:
        from analytics.spatial import calculate_demand_heatmap
        return calculate_demand_heatmap(request.city_config, request.interventions)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Heatmap generation failed: {str(e)}"
        )

@router.post("/analytics/coverage")
async def get_coverage_analysis_endpoint(request: ScenarioRequest):
    """
    Analyze network coverage and return health metrics.
    """
    try:
        from analytics.coverage import get_network_health
        return get_network_health(request.city_config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Coverage analysis failed: {str(e)}"
        )

@router.post("/analytics/recommendations")
async def get_recommendations_endpoint(request: ScenarioRequest):
    """
    Suggest optimal locations for new stations.
    """
    try:
        from analytics.recommendations import get_station_recommendations
        return get_station_recommendations(request.city_config)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )

@router.post("/analytics/forecast")
async def get_forecast(request: ScenarioRequest):
    """
    Predict demand for a specific station based on simulation history.
    Requires 'description' field to contain 'station_id:ST_ID'.
    """
    try:
        # Extract station_id from description or auxiliary field in a real app
        # Heuristic: We'll parse it from description purely for MVP simplicity
        # Format "forecast_request:ST_123"
        desc = request.description
        if not desc or "forecast_request:" not in desc:
             raise HTTPException(status_code=400, detail="Description must be 'forecast_request:ST_ID'")
        
        station_id = desc.split(":")[1]
        
        # Get global simulation context (hacky singleton access for MVP)
        # In production this would be a proper service injection
        from simulation.engine import city_manager
        
        # Use helper from forecasting module
        from analytics.forecasting import generate_station_forecast
        
        # Determine current minute (mock or from timeline)
        # We need the max minute from the timeline to know "now"
        current_minute = 0
        if city_manager and city_manager.timelines:
             # Find max minute across all logs (approximate)
             # Or just use the last minute of the requested station
             s_log = city_manager.timelines.get(station_id)
             if s_log and s_log.get("states"):
                 current_minute = s_log["states"][-1]["minute"]
        
        return generate_station_forecast(station_id, current_minute, city_manager)
        
    except Exception as e:
        print(f"Forecast Error: {e}")
        # Return empty safe response instead of 500 to keep UI stable
        return {"forecast": [], "risk_level": "unknown", "error": str(e)}

@router.post("/run-scenarios")
async def run_scenarios_endpoint(request: ScenarioComparisonRequest):
    """
    Run baseline and scenario simulations with comparison and ranking.
    
    Supports 'fake' mode (fast, UI-safe) and 'real' mode (full SimPy simulation).
    """
    try:
        # Validate mode
        mode = request.mode or "fake"
        if mode not in ("fake", "real"):
            raise HTTPException(
                status_code=400,
                detail="mode must be 'fake' or 'real'"
            )
        
        # Import simulation function
        from simulation.main import run_scenarios
        
        # Run scenarios
        result = run_scenarios(
            base_config=request.base_config,
            scenario_configs=request.scenarios,
            weight_config=request.weights,
            mode=mode
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scenario comparison failed: {str(e)}"
        )

@router.post("/nl-to-toon")
async def nl_to_toon_endpoint(request: NLToToonRequest):
    """
    Translate natural language scenario to TOON DSL configuration.
    
    Stateless endpoint - no simulation triggering, no state storage.
    """
    try:
        city = request.city or "Bangalore"
        station_catalog = get_station_catalog(city)
        toon, raw_toon = translate_nl_to_toon(request.text, station_catalog, city)
        out = {"toon": toon}
        if not toon.get("stations"):
            out["raw_toon"] = raw_toon
        return out
    except ToonParseError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except RuntimeError as e:
        # Surface Gemini / NLP engine failures without leaking internals
        raise HTTPException(
            status_code=502,
            detail=f"NLP engine failure: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        )

@router.get("/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "digital-twin-api"
    }
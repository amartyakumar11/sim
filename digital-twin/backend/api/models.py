from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    SUBMITTED = "submitted"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScenarioRequest(BaseModel):
    """Request model for scenario submission"""
    description: str = Field(..., description="Human-readable description of the scenario")
    city_config: Dict[str, Any] = Field(..., description="Base city configuration")
    interventions: Dict[str, Any] = Field(default_factory=dict, description="Scenario interventions to apply")
    simulation_duration: int = Field(default=3600, description="Simulation duration in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Add 5 charging stations to downtown area",
                "city_config": {
                    "zones": ["downtown", "suburb_north", "suburb_south"],
                    "stations": [
                        {
                            "station_id": "st_001",
                            "lat": 40.7128,
                            "lon": -74.0060,
                            "chargers_total": 4,
                            "chargers_active": 4,
                            "zone_id": "downtown"
                        }
                    ]
                },
                "interventions": {
                    "add_stations": [
                        {
                            "station_id": "st_new_001",
                            "lat": 40.7150,
                            "lon": -74.0070,
                            "chargers_total": 6,
                            "zone_id": "downtown"
                        }
                    ]
                },
                "simulation_duration": 3600
            }
        }

class ScenarioResponse(BaseModel):
    """Response model for scenario submission"""
    run_id: str
    status: JobStatus
    message: str
    
class JobStatusResponse(BaseModel):
    """Response model for job status queries"""
    run_id: str
    status: JobStatus
    progress: Optional[float] = Field(None, ge=0.0, le=1.0, description="Progress from 0.0 to 1.0")
    message: str
    created_at: datetime
    updated_at: datetime
    
class ArtifactInfo(BaseModel):
    """Information about simulation artifacts"""
    events: str = Field(..., description="Path to events.ndjson file")
    frames: str = Field(..., description="Path to frames.ndjson file") 
    summary: str = Field(..., description="Path to summary.json file")

class KPISummary(BaseModel):
    """Key Performance Indicators summary"""
    avg_wait_time: Optional[float] = Field(None, description="Average wait time in minutes")
    lost_swaps: Optional[int] = Field(None, description="Number of lost swaps")
    charger_utilization: Optional[float] = Field(None, ge=0.0, le=1.0, description="Average charger utilization")
    idle_inventory: Optional[float] = Field(None, description="Average idle inventory percentage")
    city_throughput: Optional[int] = Field(None, description="Total successful swaps")
    total_cost_impact: Optional[float] = Field(None, description="Total operational cost impact")
    roi: Optional[float] = Field(None, description="Return on investment")

class SimulationResult(BaseModel):
    """Complete simulation result"""
    run_id: str
    status: JobStatus
    summary: KPISummary
    events_count: int = Field(..., description="Number of events logged")
    frames_count: int = Field(..., description="Number of frame snapshots generated")
    artifacts: ArtifactInfo = Field(..., description="Paths to simulation artifacts")
    
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
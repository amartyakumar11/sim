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

class SimulationRequest(BaseModel):
    """Request model for single simulation run"""
    config: Dict[str, Any] = Field(
        ...,
        description="Simulation configuration dictionary"
    )
    mode: Optional[str] = Field(
        default="fake",
        description="Simulation mode: 'fake' (fast, UI-safe) or 'real' (full SimPy simulation)"
    )

class ScenarioRequest(BaseModel):
    """Request model for scenario submission"""
    description: str = Field(
        ..., 
        min_length=1,
        max_length=500,
        description="Human-readable description of the scenario"
    )
    city_config: Dict[str, Any] = Field(
        ..., 
        description="Base city configuration with zones and stations"
    )
    interventions: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Scenario interventions to apply"
    )
    simulation_duration: int = Field(
        default=3600,
        ge=60,  # Minimum 1 minute
        le=86400,  # Maximum 24 hours 
        description="Simulation duration in seconds (60-86400)"
    )
    mode: Optional[str] = Field(
        default="fake",
        description="Simulation mode: 'fake' (fast, UI-safe) or 'real' (full SimPy simulation)"
    )

class ScenarioComparisonRequest(BaseModel):
    """Request model for scenario comparison"""
    base_config: Dict[str, Any] = Field(
        ...,
        description="Baseline simulation configuration"
    )
    scenarios: List[Dict[str, Any]] = Field(
        ...,
        description="List of scenario configuration dictionaries"
    )
    weights: Dict[str, float] = Field(
        ...,
        description="Weighting configuration for ranking"
    )
    mode: Optional[str] = Field(
        default="fake",
        description="Simulation mode: 'fake' (fast, UI-safe) or 'real' (full SimPy simulation)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "base_config": {
                    "seed": 42,
                    "city": "Delhi",
                    "start_time": "2026-01-01T00:00:00",
                    "end_time": "2026-01-01T06:00:00"
                },
                "scenarios": [
                    {"scenario_id": "scenario_1", "revenue_per_swap": 600.0}
                ],
                "weights": {
                    "avg_wait_time": 0.25,
                    "lost_swaps": 0.20,
                    "throughput": 0.20,
                    "roi": 0.35
                },
                "mode": "fake"
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


class NLToToonRequest(BaseModel):
    """Request model for NL → TOON translation"""
    text: str = Field(
        ...,
        description="Natural language scenario description to translate to TOON DSL"
    )
    city: Optional[str] = Field(
        default="Bangalore",
        description="City name providing context for station catalog"
    )

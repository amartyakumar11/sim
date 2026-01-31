#!/usr/bin/env python3
"""
Real Lucknow Simulation Runner

Connects the ACTUAL SimPy simulation engine to Lucknow city graph.
Runs a 2-hour simulation and generates authentic timeline data for the frontend.

Usage:
    python run_real_lucknow_simulation.py
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

# Add backend directory to path so we can import as package
# __file__ is inside backend/simulation
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from simulation.main import run_simulation

# Configuration
SEED = 42
START_TIME = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
END_TIME = START_TIME + timedelta(hours=2)
DEMAND_RATE = 50.0  # High demand for stress testing

# Directories
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "simulation_output"
FRONTEND_PUBLIC = SCRIPT_DIR.parent.parent / "frontend" / "public"
CITY_GRAPH_PATH = SCRIPT_DIR / "city_graph_lucknow.json"

def load_lucknow_graph() -> Dict[str, Any]:
    """Load the Lucknow city graph."""
    if not CITY_GRAPH_PATH.exists():
        raise FileNotFoundError(f"Lucknow city graph not found: {CITY_GRAPH_PATH}")
    
    with open(CITY_GRAPH_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_events_to_timelines(events: List[Dict], stations: List[Dict], start_time: datetime, end_time: datetime) -> Dict:
    """
    Process simulation events into per-minute station timelines.
    """
    print(f"Processing {len(events)} events into timelines...")
    
    # Initialize station state
    station_state = {
        s["station_id"]: {
            "queue": 0,
            "charging": 0,
            "inventory": s.get("inventory_initial", 10),
            "chargers": s.get("chargers_total", 4),
            "zone": s["zone_id"]
        }
        for s in stations
    }
    
    # Create result structure
    timelines = {
        sid: {
            "station_id": sid,
            "zone": state["zone"],
            "chargers": state["chargers"],
            "timeline": []
        }
        for sid, state in station_state.items()
    }
    
    zone_pressure = []
    rider_traces = {}
    recommendations = []
    
    # Convert string timestamps to datetime and strip timezone for comparison
    for event in events:
        if isinstance(event.get("timestamp"), str):
            dt = datetime.fromisoformat(event["timestamp"].replace('Z', '+00:00'))
            event["timestamp"] = dt.replace(tzinfo=None) # Make naive to match start_time
    
    # Sort events by time
    events.sort(key=lambda x: x["timestamp"])
    
    # Iterate minute by minute
    current_time = start_time
    event_idx = 0
    start_minute = int((start_time - start_time).total_seconds() / 60) # 0 relative
    # For frontend absolute minute (e.g. 600 for 10:00 AM)
    sim_start_minute = start_time.hour * 60 + start_time.minute
    
    total_minutes = int((end_time - start_time).total_seconds() / 60)
    
    for relative_minute in range(total_minutes + 1):
        minute_timestamp = start_time + timedelta(minutes=relative_minute)
        next_minute_timestamp = minute_timestamp + timedelta(minutes=1)
        absolute_minute = sim_start_minute + relative_minute
        
        # Process all events in this minute
        while event_idx < len(events) and events[event_idx]["timestamp"] < next_minute_timestamp:
            event = events[event_idx]
            event_type = event.get("event_type")
            if not event_type:
                # Try fallback or skip
                event_type = event.get("type", "unknown")
            
            sid = event.get("station_id")
            
            # Extract metrics from metadata or top level
            meta = event.get("metadata", {})
            
            if sid and sid in station_state:
                # Update station state based on events
                if "queue_length" in meta:
                    station_state[sid]["queue"] = meta["queue_length"]
                elif "queue_length" in event:
                    station_state[sid]["queue"] = event["queue_length"]
                
                if "inventory_level" in meta:
                    station_state[sid]["inventory"] = meta["inventory_level"]
                elif "inventory_level" in event:
                    station_state[sid]["inventory"] = event["inventory_level"]
                
                if "charging_count" in meta:
                    station_state[sid]["charging"] = meta["charging_count"]
                elif "charging_count" in event:
                    station_state[sid]["charging"] = event["charging_count"]
            
            # Capture rider traces
            rider_id = event.get("rider_id")
            if rider_id:
                if rider_id not in rider_traces:
                    rider_traces[rider_id] = {
                        "rider_id": rider_id,
                        "swap_stations": [],
                        "swap_minutes": [],
                        "status": "active"
                    }
                
                if event_type == "swap_complete":
                     rider_traces[rider_id]["swap_stations"].append(sid)
                     rider_traces[rider_id]["swap_minutes"].append(absolute_minute)
                
                elif event_type == "rider_redirect":
                    # Initialize redirections list if needed (for safety)
                    if "redirections" not in rider_traces[rider_id]:
                        rider_traces[rider_id]["redirections"] = []
                        
                    rider_traces[rider_id]["redirections"].append({
                        "minute": absolute_minute,
                        "from_station": sid,
                        "to_station": meta.get("target_station_id"),
                        "distance": meta.get("distance_deg", 0)
                    })
                
                elif event_type == "demand_gap":
                    recommendations.append({
                        "minute": absolute_minute,
                        "lat": meta.get("latitude"),
                        "lon": meta.get("longitude"),
                        "reason": "stockout_no_neighbor",
                        "rider_id": rider_id
                    })
            
            event_idx += 1
            
        # Record state for this minute
        for sid, state in station_state.items():
            timelines[sid]["timeline"].append({
                "minute": absolute_minute,
                "queue": state["queue"],
                "charging": state["charging"],
                "inventory": state["inventory"]
            })
            
    # Post-process zone pressure
    # ... logic similar to before but using real state ...
    
    return {
        "station_timelines": timelines,
        "zone_pressure": zone_pressure, # TODO: calculate from timelines
        "rider_traces": rider_traces,
        "recommendations": recommendations
    }

def main():
    print("="*60)
    print("REAL LUCKNOW SIMULATION (SimPy Engine)")
    print("="*60)
    
    city_graph = load_lucknow_graph()
    print(f"Loaded graph: {len(city_graph['stations'])} stations")
    
    # Sanitize station data to ensure validation passes
    for station in city_graph["stations"]:
        # Map inventory_initial to inventory_current if missing
        if "inventory_current" not in station:
            station["inventory_current"] = station.get("inventory_initial", 10)
        
        # Ensure capacity is sufficient
        if "inventory_capacity" not in station:
            station["inventory_capacity"] = int(station["inventory_current"] * 1.5)
        
        # Fix invalid capacity
        if station["inventory_current"] > station["inventory_capacity"]:
            station["inventory_capacity"] = int(station["inventory_current"] * 1.2)
            
        # Ensure chargers total is set
        if "chargers_total" not in station:
            station["chargers_total"] = station.get("swap_bays", 4)
    
    # Create configuration for real simulation (FLATTENED structure as expected by main.py)
    config = {
        # Metadata
        "run_id": f"lucknow_real_{int(datetime.now().timestamp())}",
        "city": "Lucknow",
        "seed": SEED,
        "description": "Real Lucknow Simulation Run",
        
        # Simulation Window
        "start_time": START_TIME.isoformat(),
        "end_time": END_TIME.isoformat(),
        
        # Graph & Topology
        "city_config": city_graph,
        "graph_path": str(CITY_GRAPH_PATH),
        
        # Demand
        "demand": {
            "base_demand_rate_per_min": DEMAND_RATE
        },
        
        # Costs (Flat)
        "revenue_per_swap": 50,
        "charger_energy_cost": 10,
        "station_staff_cost": 100,
        "battery_depreciation_cost": 5,
        "infra_maintenance_cost": 2,
        "capital_cost": 50000,
        "duration_minutes": 120
    }
    
    print("Running SimPy simulation...")
    try:
        results = run_simulation(config, mode="real")
        print("Simulation successful!")
        print(f"Generated {len(results['events'])} events")
        
        # Process outputs
        processed = process_events_to_timelines(
            results["events"], 
            city_graph["stations"],
            START_TIME,
            END_TIME
        )
        
        # Save to files
        OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        
        # Save timelines
        with open(OUTPUT_DIR / "station_timelines_lucknow.json", 'w') as f:
            json.dump(processed["station_timelines"], f)
            
        with open(OUTPUT_DIR / "rider_traces_lucknow.json", 'w') as f:
            json.dump(processed["rider_traces"], f)
            
        # Zone pressure (empty for now or calculated)
        with open(OUTPUT_DIR / "zone_pressure_lucknow.json", 'w') as f:
            json.dump(processed["zone_pressure"], f)
            
        # Recommendations
        print(f"Writing recommendations... Count: {len(processed['recommendations'])}")
        with open(OUTPUT_DIR / "station_recommendations_lucknow.json", 'w') as f:
            json.dump(processed["recommendations"], f)
        print("Done writing recommendations.")
            
        # Copy to frontend
        if FRONTEND_PUBLIC.exists():
            import shutil
            shutil.copy(OUTPUT_DIR / "station_timelines_lucknow.json", FRONTEND_PUBLIC)
            shutil.copy(OUTPUT_DIR / "rider_traces_lucknow.json", FRONTEND_PUBLIC)
            shutil.copy(OUTPUT_DIR / "zone_pressure_lucknow.json", FRONTEND_PUBLIC)
            shutil.copy(OUTPUT_DIR / "station_recommendations_lucknow.json", FRONTEND_PUBLIC)
            print("Copied files to frontend public directory")
            
    except Exception as e:
        print(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

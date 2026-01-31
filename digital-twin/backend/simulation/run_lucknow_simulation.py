#!/usr/bin/env python3
"""
Lucknow Simulation Runner

Runs a deterministic simulation for Lucknow city graph and generates
timeline outputs compatible with the frontend playback system.

Output files:
- station_timelines_lucknow.json: Per-minute station state for playback
- zone_pressure_lucknow.json: Zone pressure events over time
- rider_traces_lucknow.json: Rider journey traces

Usage:
    python run_lucknow_simulation.py
"""

import json
import random
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Configuration
SEED = 42
START_MINUTE = 600  # 10:00 AM
END_MINUTE = 720    # 12:00 PM (2 hours)
DEMAND_RATE_PER_MINUTE = 2.5  # Riders per minute across all stations

# Output directory
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "simulation_output"
FRONTEND_PUBLIC = SCRIPT_DIR.parent.parent / "frontend" / "public"

def load_lucknow_graph() -> Dict[str, Any]:
    """Load the Lucknow city graph."""
    graph_path = SCRIPT_DIR / "city_graph_lucknow.json"
    if not graph_path.exists():
        raise FileNotFoundError(f"Lucknow city graph not found: {graph_path}")
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def initialize_station_state(station: Dict) -> Dict:
    """Initialize station state from city graph data."""
    return {
        "station_id": station["station_id"],
        "zone_id": station["zone_id"],
        "chargers": station.get("chargers_total", 4),
        "swap_bays": station.get("swap_bays", 4),
        "inventory_capacity": station.get("inventory_capacity", 20),
        "inventory": station.get("inventory_initial", 10),
        "queue": 0,
        "charging": 0,
        "total_swaps": 0,
        "lost_swaps": 0
    }

def simulate_minute(
    stations: Dict[str, Dict],
    zones: Dict[str, Dict],
    minute: int,
    rng: random.Random,
    demand_rate: float
) -> Dict[str, Any]:
    """
    Simulate one minute of operations.
    
    This is a simplified simulation that:
    - Generates rider arrivals based on demand rate
    - Processes queues and swaps
    - Recharges batteries
    - Returns station states for this minute
    """
    events = []
    
    # Calculate arrivals for this minute
    station_ids = list(stations.keys())
    num_arrivals = rng.randint(int(demand_rate * 0.5), int(demand_rate * 1.5))
    
    # Generate arrivals to random stations
    for _ in range(num_arrivals):
        target_station_id = rng.choice(station_ids)
        station = stations[target_station_id]
        
        # Add to queue
        station["queue"] += 1
    
    # Process each station
    for station_id, station in stations.items():
        # Process charging (one battery charges every 3 minutes on average)
        if station["charging"] > 0 and rng.random() < 0.33:
            station["charging"] -= 1
            station["inventory"] = min(station["inventory"] + 1, station["inventory_capacity"])
        
        # Start charging empty bays
        empty_chargers = station["chargers"] - station["charging"]
        batteries_to_charge = min(empty_chargers, station["inventory_capacity"] - station["inventory"] - station["charging"])
        if batteries_to_charge > 0:
            station["charging"] += min(batteries_to_charge, rng.randint(0, 2))
        
        # Process swaps from queue
        while station["queue"] > 0 and station["inventory"] > 0:
            station["queue"] -= 1
            station["inventory"] -= 1
            station["total_swaps"] += 1
            
            # Start charging the returned battery
            if station["charging"] < station["chargers"]:
                station["charging"] += 1
        
        # Lost swaps (queue overflow or no inventory)
        if station["queue"] > station["swap_bays"] * 2:
            lost = station["queue"] - station["swap_bays"] * 2
            station["queue"] -= lost
            station["lost_swaps"] += lost
            events.append({
                "type": "lost_swap",
                "station_id": station_id,
                "minute": minute,
                "count": lost
            })
    
    return events

def run_simulation(city_graph: Dict) -> Dict[str, Any]:
    """
    Run the full simulation for Lucknow.
    
    Returns timeline data compatible with frontend playback.
    """
    rng = random.Random(SEED)
    
    # Initialize stations from city graph
    stations = {}
    for station_data in city_graph["stations"]:
        station_id = station_data["station_id"]
        stations[station_id] = initialize_station_state(station_data)
    
    # Build zone lookup
    zones = {zone["zone_id"]: zone for zone in city_graph["zones"]}
    
    # Station timelines: station_id -> { timeline: [...], zone, chargers }
    station_timelines = {
        station_id: {
            "station_id": station_id,
            "zone": stations[station_id]["zone_id"],
            "chargers": stations[station_id]["chargers"],
            "timeline": []
        }
        for station_id in stations
    }
    
    # Zone pressure events
    zone_pressure = []
    
    # Rider traces (simplified)
    rider_traces = {}
    rider_counter = 0
    
    print(f"Starting simulation: {len(stations)} stations, minutes {START_MINUTE}-{END_MINUTE}")
    
    # Run simulation minute by minute
    for minute in range(START_MINUTE, END_MINUTE + 1):
        # Vary demand by time of day (peak around 11 AM)
        hour = minute // 60
        if hour == 10:
            demand_mult = 1.0
        elif hour == 11:
            demand_mult = 1.5  # Peak hour
        else:
            demand_mult = 0.8
        
        current_demand = DEMAND_RATE_PER_MINUTE * demand_mult * len(stations) / 50
        
        # Simulate this minute
        events = simulate_minute(stations, zones, minute, rng, current_demand)
        
        # Record station states
        for station_id, station in stations.items():
            station_timelines[station_id]["timeline"].append({
                "minute": minute,
                "queue": station["queue"],
                "charging": station["charging"],
                "inventory": station["inventory"]
            })
        
        # Calculate zone pressure
        for zone_id, zone in zones.items():
            # Find stations in this zone
            zone_stations = [s for s in stations.values() if s["zone_id"] == zone_id]
            if zone_stations:
                avg_queue = sum(s["queue"] for s in zone_stations) / len(zone_stations)
                avg_inventory = sum(s["inventory"] for s in zone_stations) / len(zone_stations)
                
                pressure_score = avg_queue * 2 + (10 - avg_inventory)
                
                if pressure_score > 5:  # Only record significant pressure
                    drivers = []
                    if avg_queue > 2:
                        drivers.append("swap_congestion")
                    if avg_inventory < 3:
                        drivers.append("battery_stockout")
                    
                    zone_pressure.append({
                        "zone": zone_id,
                        "minute": minute,
                        "pressure_score": round(pressure_score, 1),
                        "drivers": drivers
                    })
        
        # Generate some rider traces (sample a few riders)
        if minute % 10 == 0 and rng.random() < 0.3:
            rider_id = f"R_{rider_counter:04d}"
            rider_counter += 1
            
            # Pick random stations for journey
            journey_stations = rng.sample(list(stations.keys()), min(3, len(stations)))
            swap_minutes = [minute + i * 5 for i in range(len(journey_stations))]
            
            rider_traces[rider_id] = {
                "rider_id": rider_id,
                "spawn_zone": stations[journey_stations[0]]["zone_id"],
                "spawn_minute": minute,
                "total_swaps": len(journey_stations),
                "swap_stations": journey_stations,
                "swap_minutes": swap_minutes,
                "end_state": "active" if rng.random() > 0.1 else "lost",
                "total_distance_km": round(rng.uniform(10, 50), 1)
            }
        
        # Progress indicator
        if minute % 30 == 0:
            print(f"  Minute {minute}: {sum(s['total_swaps'] for s in stations.values())} total swaps")
    
    # Calculate summary stats
    total_swaps = sum(s["total_swaps"] for s in stations.values())
    total_lost = sum(s["lost_swaps"] for s in stations.values())
    
    print(f"\nSimulation complete:")
    print(f"  Total swaps: {total_swaps}")
    print(f"  Lost swaps: {total_lost}")
    print(f"  Zone pressure events: {len(zone_pressure)}")
    print(f"  Rider traces: {len(rider_traces)}")
    
    return {
        "station_timelines": station_timelines,
        "zone_pressure": zone_pressure,
        "rider_traces": rider_traces,
        "summary": {
            "total_stations": len(stations),
            "total_zones": len(zones),
            "simulation_minutes": END_MINUTE - START_MINUTE + 1,
            "total_swaps": total_swaps,
            "lost_swaps": total_lost
        }
    }

def save_outputs(results: Dict[str, Any]) -> None:
    """Save simulation outputs to files."""
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Save to simulation output directory
    with open(OUTPUT_DIR / "station_timelines_lucknow.json", 'w', encoding='utf-8') as f:
        json.dump(results["station_timelines"], f, indent=2)
    
    with open(OUTPUT_DIR / "zone_pressure_lucknow.json", 'w', encoding='utf-8') as f:
        json.dump(results["zone_pressure"], f, indent=2)
    
    with open(OUTPUT_DIR / "rider_traces_lucknow.json", 'w', encoding='utf-8') as f:
        json.dump(results["rider_traces"], f, indent=2)
    
    with open(OUTPUT_DIR / "summary_lucknow.json", 'w', encoding='utf-8') as f:
        json.dump(results["summary"], f, indent=2)
    
    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    
    # Also copy to frontend public for immediate use
    if FRONTEND_PUBLIC.exists():
        with open(FRONTEND_PUBLIC / "station_timelines_lucknow.json", 'w', encoding='utf-8') as f:
            json.dump(results["station_timelines"], f, indent=2)
        
        with open(FRONTEND_PUBLIC / "zone_pressure_lucknow.json", 'w', encoding='utf-8') as f:
            json.dump(results["zone_pressure"], f, indent=2)
        
        with open(FRONTEND_PUBLIC / "rider_traces_lucknow.json", 'w', encoding='utf-8') as f:
            json.dump(results["rider_traces"], f, indent=2)
        
        print(f"Also copied to frontend: {FRONTEND_PUBLIC}")

def main():
    """Main entry point."""
    print("=" * 60)
    print("LUCKNOW SIMULATION RUNNER")
    print("=" * 60)
    print(f"Seed: {SEED}")
    print(f"Time range: {START_MINUTE//60}:{START_MINUTE%60:02d} - {END_MINUTE//60}:{END_MINUTE%60:02d}")
    print()
    
    # Load city graph
    city_graph = load_lucknow_graph()
    print(f"Loaded Lucknow graph: {city_graph['metadata']['total_stations']} stations, {city_graph['metadata']['total_zones']} zones")
    print()
    
    # Run simulation
    results = run_simulation(city_graph)
    
    # Save outputs
    save_outputs(results)
    
    print("\nDone! Refresh the frontend to see the simulation data.")

if __name__ == "__main__":
    main()

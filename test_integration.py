"""Test if backend integration is working with new simulation"""
import sys
sys.path.insert(0, 'd:/SIM/digital-twin/backend')

from datetime import datetime, timedelta
from simulation.main import run_simulation

# Simulate what tasks.py does
print("Testing integration flow...")
print("=" * 60)

scenario_data = {
    "description": "Test scenario",
    "city_config": {
        "stations": [
            {
                "station_id": "S1",
                "lat": 12.97,
                "lon": 77.59,
                "zone_id": "Z1",
                "chargers_total": 4,
                "chargers_active": 4
            }
        ]
    },
    "simulation_duration": 600,  # 10 minutes
    "mode": "real"
}

# Build runtime_config like tasks.py does
runtime_config = {
    "run_id": "test_integration_001",
    "data_dir": "./tmp_integration_test",
    "seed": 42,
    "city": scenario_data.get("city_config", {}).get("city", "unknown"),
    "start_time": datetime.now(),
    "end_time": datetime.now() + timedelta(seconds=scenario_data["simulation_duration"]),
    "city_config": scenario_data.get("city_config", {}),
    "interventions": scenario_data.get("interventions", {}),
    "simulation_duration": scenario_data["simulation_duration"],
    "description": scenario_data.get("description", ""),
    "demand": {
        "base_demand_rate_per_min": 0.5
    }
}

print("\n1. Calling run_simulation with runtime_config...")
simulation_result = run_simulation(runtime_config, mode="real")

print("\n2. Checking simulation_result structure...")
print(f"   Keys: {list(simulation_result.keys())}")

print("\n3. Checking if result has expected fields...")
has_metadata = "metadata" in simulation_result
has_kpis = "kpis" in simulation_result
has_events = "events" in simulation_result
has_timeseries = "timeseries" in simulation_result

print(f"   metadata: {has_metadata}")
print(f"   kpis: {has_kpis}")
print(f"   events: {has_events}")
print(f"   timeseries: {has_timeseries}")

if has_kpis:
    print("\n4. KPIs returned:")
    for key, value in simulation_result["kpis"].items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")

if has_events:
    print(f"\n5. Events count: {len(simulation_result['events'])}")
    rider_events = [e for e in simulation_result['events'] if e.get('rider_id') and e['event_type'] == 'rider_arrival']
    print(f"   Rider arrivals: {len(rider_events)}")

print("\n6. Checking what tasks.py expects to extract...")
print("   tasks.py tries to get:")
print(f"     - summary: {simulation_result.get('summary', 'NOT FOUND')}")
print(f"     - events_count: {simulation_result.get('events_count', 'NOT FOUND')}")
print(f"     - frames_count: {simulation_result.get('frames_count', 'NOT FOUND')}")

print("\n7. ISSUE FOUND!")
print("   tasks.py expects: simulation_result.get('summary', {})")
print("   but run_simulation returns: simulation_result['kpis']")
print("\n   This is a mismatch! tasks.py needs to be updated.")

print("\n" + "=" * 60)
print("INTEGRATION STATUS: PARTIAL")
print("=" * 60)
print("\nWhat works:")
print("  [OK] run_simulation() executes successfully")
print("  [OK] Returns kpis, metadata, events, timeseries")
print("\nWhat needs fixing:")
print("  [ISSUE] tasks.py line 159 expects result.get('summary')")
print("  [ISSUE] but run_simulation returns result['kpis']")
print("  [FIX] Update tasks.py to map kpis -> summary")

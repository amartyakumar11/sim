"""Trace execution with prints"""
import sys
from datetime import datetime
from simulation.main import build_real_simulation_config

raw_config = {
    "run_id": "trace_001",
    "seed": 1,
    "city": "Test",
    "start_time": datetime(2026, 1, 1, 10, 0, 0),
    "end_time": datetime(2026, 1, 1, 10, 5, 0),
    "city_config": {
        "stations": [
            {
                "station_id": "A",
                "lat": 12.97,
                "lon": 77.59,
                "swap_bays": 2,
                "swap_time_sec": 60,
                "inventory_current": 10
            }
        ]
    },
    "demand": {
        "base_demand_rate_per_min": 0.2
    }
}

print("Testing config adapter...")
try:
    normalized = build_real_simulation_config(raw_config)
    print("Config adapter SUCCESS")
    print(f"  Stations: {len(normalized['stations'])}")
    print(f"  Station 0:")
    for key, val in normalized['stations'][0].items():
        print(f"    {key}: {val}")
    print(f"  Demand rate: {normalized['demand']['base_demand_rate_per_min']}")
    print(f"  Duration: {normalized['simulation']['duration_minutes']} min")
except Exception as e:
    print(f"Config adapter FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nNow testing full simulation...")
from simulation.main import run_simulation

try:
    result = run_simulation(raw_config, mode="real")
    print(f"Simulation SUCCESS")
    print(f"  Events: {len(result['events'])}")
    print(f"  Throughput: {result['kpis']['throughput']}")
    print(f"  Lost: {result['kpis']['lost_swaps']}")
except Exception as e:
    print(f"Simulation FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

"""Minimal debug to understand flow"""
from datetime import datetime
from simulation.main import run_simulation

config = {
    "run_id": "simple_001",
    "seed": 1,
    "city": "Test",
    "start_time": datetime(2026, 1, 1, 10, 0, 0),
    "end_time": datetime(2026, 1, 1, 10, 5, 0),  # 5 minutes
    "city_config": {
        "stations": [
            {
                "station_id": "A",
                "lat": 12.97,
                "lon": 77.59,
                "swap_bays": 2,
                "swap_time_sec": 60,  # 1 min swap
                "inventory_current": 10
            }
        ]
    },
    "demand": {
        "base_demand_rate_per_min": 0.2  # ~1 rider per 5 min
    }
}

print("Running simulation...")
result = run_simulation(config, mode="real")

events = result['events']
print(f"\nGenerated {len(events)} events")

# Group by rider
from collections import defaultdict
by_rider = defaultdict(list)
for e in events:
    rider = e.get('rider_id') or 'system'
    by_rider[rider].append((e['timestamp'][:19], e['event_type']))

print("\nEvents by rider:")
for rider_id in sorted(by_rider.keys()):
    print(f"\n{rider_id}:")
    for ts, etype in by_rider[rider_id]:
        print(f"  {ts} | {etype}")

print(f"\nKPIs: wait={result['kpis']['avg_wait_time']:.2f}, util={result['kpis']['utilization']:.3f}, throughput={result['kpis']['throughput']}, lost={result['kpis']['lost_swaps']}")

"""Debug script to check event timing"""
from datetime import datetime
from simulation.main import run_simulation

config = {
    "run_id": "debug_001",
    "seed": 42,
    "city": "Test",
    "start_time": datetime(2026, 1, 1, 8, 0, 0),
    "end_time": datetime(2026, 1, 1, 8, 10, 0),  # 10 minutes only
    "city_config": {
        "stations": [
            {
                "station_id": "S1",
                "lat": 12.97,
                "lon": 77.59,
                "swap_bays": 1,  # Only 1 bay - should create congestion
                "swap_time_sec": 300,  # 5 min swap
                "inventory_current": 50
            }
        ]
    },
    "demand": {
        "base_demand_rate_per_min": 0.5  # ~5 riders in 10 min
    }
}

result = run_simulation(config, mode="real")

print(f"Total events: {len(result['events'])}")
print(f"\nFirst 20 events:")
for i, e in enumerate(result['events'][:20]):
    rider_id = e.get('rider_id') or 'None'
    station_id = e.get('station_id') or 'None'
    print(f"{i+1}. {e['timestamp'][:19]} | {e['event_type']:20s} | rider={rider_id:12s} | station={station_id}")

print(f"\nKPIs:")
print(f"  avg_wait_time: {result['kpis']['avg_wait_time']:.2f} min")
print(f"  utilization: {result['kpis']['utilization']:.3f}")
print(f"  throughput: {result['kpis']['throughput']}")
print(f"  lost_swaps: {result['kpis']['lost_swaps']}")

# Count event types
from collections import Counter
event_counts = Counter(e['event_type'] for e in result['events'])
print(f"\nEvent type counts:")
for event_type, count in sorted(event_counts.items()):
    print(f"  {event_type}: {count}")

"""
Simulation Adapter Layer for Digital Twin Simulation Platform.

Provides API-facing interface with fake mode for testing.
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List
import json
import tempfile
import os

# Conditional imports for real mode
try:
    from .simulation_engine import SimulationEngine
    from .event_logger import EventLogger
    SIMPY_AVAILABLE = True
except ImportError:
    SIMPY_AVAILABLE = False


def run_simulation(config: dict) -> dict:
    """
    Run simulation in fake or real mode.

    Args:
        config: Configuration dictionary containing:
            - "mode": str ("fake" or "real")
            - "seed": int (RNG seed for determinism)
            - "start_time": datetime (for real mode)
            - "end_time": datetime (for real mode)
            - "city": str
            - "stations": list[dict] (for real mode)
            - "demand_config": dict (for real mode)
            - "inventory_config": dict (for real mode)

    Returns:
        Dictionary matching the stable return schema:
        {
            "metadata": {...},
            "kpis": {...},
            "timeseries": {...},
            "events": [...]
        }
    """
    mode = config.get("mode", "fake")
    seed = config.get("seed", 42)
    city = config.get("city", "default")

    if mode == "fake":
        return _run_fake_simulation(config, seed, city)
    else:
        return _run_real_simulation(config, seed, city)


def _run_fake_simulation(config: dict, seed: int, city: str) -> dict:
    """
    Generate deterministic fake simulation results.

    Args:
        config: Configuration dictionary
        seed: RNG seed for determinism
        city: City identifier

    Returns:
        Schema-compliant fake results dictionary
    """
    rng = random.Random(seed)

    # Generate fake metadata
    start_time = config.get("start_time", datetime.now())
    end_time = config.get("end_time", datetime.now() + timedelta(hours=1))
    # Generate deterministic run_id using seeded RNG
    run_id = f"run_{seed}_{int(start_time.timestamp())}"

    # Generate fake KPIs
    num_arrivals = rng.randint(50, 200)
    num_completed = int(num_arrivals * rng.uniform(0.7, 0.95))
    num_lost = num_arrivals - num_completed

    avg_wait_time = rng.uniform(2.0, 15.0)
    utilization = rng.uniform(0.3, 0.9)
    throughput = num_completed
    cost_impact = rng.uniform(100.0, 1000.0)
    roi = rng.uniform(0.1, 0.5)

    # Generate fake timeseries
    duration_minutes = int((end_time - start_time).total_seconds() / 60.0)
    wait_times = [rng.uniform(1.0, 20.0) for _ in range(min(100, num_completed))]

    # Generate fake station timeseries
    station_ids = config.get("station_ids", ["station_1", "station_2", "station_3"])
    inventory_levels = {
        station_id: [rng.randint(5, 20) for _ in range(min(60, duration_minutes))]
        for station_id in station_ids
    }
    queue_lengths = {
        station_id: [rng.randint(0, 5) for _ in range(min(60, duration_minutes))]
        for station_id in station_ids
    }

    # Generate fake events
    events = []
    current_time = start_time
    event_types = [
        "rider_arrival", "queue_join", "swap_start", "swap_complete",
        "lost_swap", "charge_start", "charge_complete"
    ]

    for _ in range(min(200, num_arrivals * 2)):
        event_time = current_time + timedelta(
            minutes=rng.uniform(0, (end_time - start_time).total_seconds() / 60.0)
        )
        # Generate deterministic event_id using seeded RNG
        event_id = f"evt_{seed}_{len(events):06d}"
        events.append({
            "event_id": event_id,
            "timestamp": event_time.isoformat() + 'Z',
            "event_type": rng.choice(event_types),
            "station_id": rng.choice(station_ids) if rng.random() > 0.3 else None,
            "rider_id": f"rider_{rng.randint(1000, 9999)}" if rng.random() > 0.5 else None,
            "battery_id": None,
            "metadata": {}
        })

    # Sort events by timestamp
    events.sort(key=lambda x: x["timestamp"])

    return {
        "metadata": {
            "run_id": run_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "seed": seed,
            "city": city
        },
        "kpis": {
            "avg_wait_time": round(avg_wait_time, 2),
            "lost_swaps": num_lost,
            "utilization": round(utilization, 3),
            "throughput": throughput,
            "cost_impact": round(cost_impact, 2),
            "roi": round(roi, 3)
        },
        "timeseries": {
            "wait_time": wait_times,
            "inventory_levels": inventory_levels,
            "queue_lengths": queue_lengths
        },
        "events": events
    }


def _run_real_simulation(config: dict, seed: int, city: str) -> dict:
    """
    Run actual SimPy simulation.

    Args:
        config: Configuration dictionary
        seed: RNG seed for determinism
        city: City identifier

    Returns:
        Schema-compliant results dictionary
    """
    if not SIMPY_AVAILABLE:
        raise RuntimeError("SimPy not available - cannot run real simulation")

    start_time = config.get("start_time", datetime.now())
    end_time = config.get("end_time", datetime.now() + timedelta(hours=1))
    # Generate deterministic run_id
    run_id = f"run_{seed}_{int(start_time.timestamp())}"

    # Create temporary event log file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()

    try:
        # Initialize event logger
        event_logger = EventLogger(temp_file.name)

        # Prepare simulation config
        sim_config = {
            "seed": seed,
            "start_time": start_time,
            "end_time": end_time,
            "stations": config.get("stations", []),
            "demand_config": config.get("demand_config", {}),
            "inventory_config": config.get("inventory_config", {}),
            "event_logger": event_logger
        }

        # Run simulation
        engine = SimulationEngine(sim_config)
        kpi_snapshot = engine.run()

        # Close event logger
        event_logger.close()

        # Read events from log file
        events = []
        with open(temp_file.name, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file.name)
        except:
            pass

    # Return schema-compliant results
    # TODO: Calculate actual KPIs from snapshot
    # TODO: Generate timeseries from events
    return {
        "metadata": {
            "run_id": run_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "seed": seed,
            "city": city
        },
        "kpis": {
            "avg_wait_time": kpi_snapshot.get("average_wait_time", 0.0),
            "lost_swaps": kpi_snapshot.get("lost", 0),
            "utilization": 0.0,  # TODO: Calculate from snapshot
            "throughput": kpi_snapshot.get("completed", 0),
            "cost_impact": 0.0,  # TODO: Calculate from snapshot
            "roi": 0.0  # TODO: Calculate from snapshot
        },
        "timeseries": {
            "wait_time": [],
            "inventory_levels": {},
            "queue_lengths": {}
        },
        "events": events
    }

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


def build_real_simulation_config(raw_config: dict) -> dict:
    """
    Adapt user / API / Celery config into a Level 1 REAL simulation config.
    
    This function transforms raw incoming config into a complete, deterministic,
    validated configuration that is safe for SimPy and independent of frontend/Celery shape.
    
    Args:
        raw_config: Raw configuration from API/Celery/tests
        
    Returns:
        Normalized config dict with structure:
        {
            "metadata": {...},
            "simulation": {...},
            "stations": [...],
            "demand": {...},
            "routing": {...}
        }
        
    Raises:
        ValueError: On invalid or incomplete input
    """
    # 1️⃣ Extract and validate metadata
    metadata = {}
    
    if "run_id" not in raw_config:
        raise ValueError("run_id is required")
    metadata["run_id"] = raw_config["run_id"]
    
    metadata["city"] = raw_config.get("city", "unknown")
    
    if "seed" in raw_config:
        try:
            metadata["seed"] = int(raw_config["seed"])
        except (ValueError, TypeError):
            raise ValueError("seed must be an integer")
    else:
        metadata["seed"] = 42
    
    metadata["description"] = raw_config.get("description", "")
    
    # 2️⃣ Parse and normalize simulation window
    simulation = {}
    
    start_time = raw_config.get("start_time")
    end_time = raw_config.get("end_time")
    
    # Parse datetime strings if needed
    if isinstance(start_time, str):
        try:
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("start_time must be valid ISO 8601 datetime")
    
    if isinstance(end_time, str):
        try:
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("end_time must be valid ISO 8601 datetime")
    
    if start_time is None or end_time is None:
        raise ValueError("start_time and end_time are required")
    
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        raise ValueError("start_time and end_time must be datetime objects or ISO strings")
    
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")
    
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    
    if duration_minutes <= 0:
        raise ValueError("Simulation duration must be > 0")
    
    simulation["start_time"] = start_time
    simulation["end_time"] = end_time
    simulation["duration_minutes"] = duration_minutes
    
    # 3️⃣ Normalize stations
    raw_stations = raw_config.get("city_config", {}).get("stations")
    
    if not raw_stations or len(raw_stations) == 0:
        raise ValueError("At least one station is required")
    
    stations = []
    
    for idx, raw_station in enumerate(raw_stations):
        station = {}
        
        if "station_id" not in raw_station:
            raise ValueError(f"Station {idx}: station_id is required")
        station["station_id"] = raw_station["station_id"]
        
        station["zone_id"] = raw_station.get("zone_id", "Z1")
        
        # Coordinate normalization (handle both lat/lon and latitude/longitude)
        if "latitude" in raw_station:
            station["latitude"] = float(raw_station["latitude"])
        elif "lat" in raw_station:
            station["latitude"] = float(raw_station["lat"])
        else:
            raise ValueError(f"Station {idx}: latitude missing")
        
        if "longitude" in raw_station:
            station["longitude"] = float(raw_station["longitude"])
        elif "lon" in raw_station:
            station["longitude"] = float(raw_station["lon"])
        else:
            raise ValueError(f"Station {idx}: longitude missing")
        
        # Capacity
        swap_bays = raw_station.get("swap_bays", raw_station.get("chargers_total", 0))
        station["swap_bays"] = int(swap_bays)
        if station["swap_bays"] <= 0:
            raise ValueError(f"Station {idx}: swap_bays must be >= 1")
        
        # Queue
        station["queue_limit"] = int(raw_station.get("queue_limit", station["swap_bays"] * 3))
        
        # Inventory
        station["inventory_current"] = int(
            raw_station.get("inventory_current", station["swap_bays"] * 10)
        )
        station["inventory_capacity"] = int(
            raw_station.get("inventory_capacity", int(station["inventory_current"] * 1.5))
        )
        
        if station["inventory_current"] > station["inventory_capacity"]:
            raise ValueError(f"Station {idx}: inventory_current exceeds capacity")
        
        # Timing
        station["swap_time_sec"] = int(raw_station.get("swap_time_sec", 180))
        
        # Status
        station["status"] = raw_station.get("status", "up")
        
        # Costs
        costs = raw_station.get("costs", {})
        station["costs"] = {
            "fixed_cost_per_day": float(costs.get("fixed_cost_per_day", 0)),
            "energy_cost_per_swap": float(costs.get("energy_cost_per_swap", 0)),
            "lost_swap_penalty": float(costs.get("lost_swap_penalty", 0))
        }
        
        # Add chargers for compatibility
        station["chargers_total"] = int(raw_station.get("chargers_total", station["swap_bays"]))
        
        stations.append(station)
    
    # 4️⃣ Demand block
    raw_demand = raw_config.get("demand")
    
    if raw_demand is None:
        raise ValueError("Demand configuration is required")
    
    demand = {}
    
    if "base_demand_rate_per_min" not in raw_demand:
        raise ValueError("base_demand_rate_per_min is required in demand config")
    
    demand["base_demand_rate_per_min"] = float(raw_demand["base_demand_rate_per_min"])
    
    if demand["base_demand_rate_per_min"] <= 0:
        raise ValueError("Demand rate must be > 0")
    
    demand["model"] = "poisson"
    
    # 5️⃣ Routing block (fixed for Level 1)
    routing = {
        "strategy": "deterministic"
    }
    
    # 6️⃣ Final assembly
    real_config = {
        "metadata": metadata,
        "simulation": simulation,
        "stations": stations,
        "demand": demand,
        "routing": routing
    }
    
    return real_config

# Conditional imports for real mode
try:
    from .simulation_engine import SimulationEngine
    from .event_logger import EventLogger
    from .kpi_engine import KPIEngine
    from .roi_engine import ROIEngine
    SIMPY_AVAILABLE = True
except ImportError:
    SIMPY_AVAILABLE = False


def run_simulation(config: dict, mode: str = "fake") -> dict:
    """
    Run simulation in fake or real mode.

    Args:
        config: Configuration dictionary containing:
            - "seed": int (RNG seed for determinism)
            - "start_time": datetime (for real mode)
            - "end_time": datetime (for real mode)
            - "city": str
            - "stations": list[dict] (for real mode)
            - "demand_config": dict (for real mode)
            - "inventory_config": dict (for real mode)
        mode: Simulation mode - "fake" (fast, UI-safe) or "real" (full SimPy simulation)

    Returns:
        Dictionary matching the stable return schema:
        {
            "metadata": {...},
            "kpis": {...},
            "timeseries": {...},
            "events": [...]
        }
    """
    # Validate mode
    if mode not in ("fake", "real"):
        raise ValueError("mode must be 'fake' or 'real'")
    
    seed = config.get("seed", 42)
    city = config.get("city", "default")

    if mode == "fake":
        return _run_fake_simulation(config, seed, city)
    elif mode == "real":
        return _run_real_simulation(config, seed, city)
    else:
        raise ValueError("mode must be 'fake' or 'real'")


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

    results = {
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
            "idle_inventory": round(rng.uniform(5.0, 15.0), 2),
            "revenue": round(throughput * rng.uniform(10.0, 50.0), 2),
            "operational_cost": round(cost_impact, 2),
            "net_profit": round(throughput * rng.uniform(10.0, 50.0) - cost_impact, 2),
            "roi": round(roi, 3)
        },
        "timeseries": {
            "wait_time": wait_times,
            "inventory_levels": inventory_levels,
            "queue_lengths": queue_lengths
        },
        "events": events
    }

    # Write artifact files
    data_dir = config.get("data_dir", "./data/results")
    os.makedirs(data_dir, exist_ok=True)

    # Write summary.json
    summary_path = os.path.join(data_dir, "summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Write events.ndjson
    events_path = os.path.join(data_dir, "events.ndjson")
    with open(events_path, 'w', encoding='utf-8') as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

    # Write frames.ndjson
    frames_path = os.path.join(data_dir, "frames.ndjson")
    with open(frames_path, 'w', encoding='utf-8') as f:
        for index, wait_time_value in enumerate(wait_times):
            frame = {
                "t": index,
                "wait_time": wait_time_value
            }
            f.write(json.dumps(frame, ensure_ascii=False) + '\n')

    return results


def _run_real_simulation(config: dict, seed: int, city: str) -> dict:
    """
    Run actual SimPy simulation.

    Args:
        config: Configuration dictionary (raw from API/Celery)
        seed: RNG seed for determinism
        city: City identifier

    Returns:
        Schema-compliant results dictionary
    """
    if not SIMPY_AVAILABLE:
        raise RuntimeError("SimPy not available - cannot run real simulation")

    # Build normalized config using adapter
    normalized_config = build_real_simulation_config(config)
    
    # Extract normalized values
    metadata = normalized_config["metadata"]
    simulation = normalized_config["simulation"]
    stations_config = normalized_config["stations"]
    demand_config = normalized_config["demand"]
    
    start_time = simulation["start_time"]
    end_time = simulation["end_time"]
    run_id = metadata["run_id"]

    # Create temporary event log file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()

    try:
        # Initialize event logger
        event_logger = EventLogger(temp_file.name)

        # Initialize components for SimulationEngine
        from .inventory_manager import InventoryManager
        from .kpi_tracker import KPITracker
        from .network_graph import NetworkGraph
        from .routing import RoutingEngine
        from .station import Station
        from .station_process import StationProcess
        import simpy

        # Initialize inventory manager
        initial_inventory = {s["station_id"]: s["inventory_current"] for s in stations_config}
        inventory_manager = InventoryManager(
            initial_inventory=initial_inventory,
            refill_threshold=5,
            refill_amount=10,
            event_logger=event_logger
        )

        # Initialize KPI tracker
        kpi_tracker = KPITracker(event_logger)

        # Initialize network graph and routing
        network_graph = NetworkGraph()
        routing_engine = RoutingEngine(network_graph)

        # Initialize stations
        stations: Dict[str, StationProcess] = {}
        env = simpy.Environment()
        
        for station_config in stations_config:
            station_id = station_config["station_id"]
            
            # Create Station object
            station = Station(station_config, event_logger)
            network_graph.add_station(station)

            # Create StationProcess
            station_process = StationProcess(
                station_id=station_id,
                env=env,
                swap_bays_count=station_config["swap_bays"],
                chargers_count=station_config.get("chargers_total", station_config["swap_bays"]),
                inventory_manager=inventory_manager,
                event_logger=event_logger,
                swap_time_sec=station_config["swap_time_sec"],
                queue_limit=station_config["queue_limit"],
                simulation_start_time=start_time
            )
            stations[station_id] = station_process

        # Initialize demand generator
        demand_gen_config = {
            "rng_seed": metadata["seed"],
            "base_demand_rate_per_min": demand_config["base_demand_rate_per_min"]
        }
        station_list = [network_graph.get_station(sid) for sid in stations.keys()]
        from .demand_generator import DemandGenerator
        demand_generator = DemandGenerator(demand_gen_config, station_list, event_logger)

        # Create simulation engine
        engine = SimulationEngine(
            env=env,
            demand_generator=demand_generator,
            routing_engine=routing_engine,
            inventory_manager=inventory_manager,
            kpi_tracker=kpi_tracker,
            stations=stations,
            event_logger=event_logger,
            rng_seed=metadata["seed"]
        )

        # Run simulation
        engine.run(start_time, end_time)

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

    # Compute KPIs from events
    kpi_config = {
        "start_time": start_time,
        "end_time": end_time,
        "stations": stations_config
    }
    kpi_engine = KPIEngine(events, kpi_config)
    kpis = kpi_engine.compute()

    # Compute ROI from KPIs (simplified for Level 1)
    roi_config = {
        "revenue_per_swap": 500.0,  # Default value
        "charger_energy_cost": 100.0,
        "station_staff_cost": 200.0,
        "battery_depreciation_cost": 50.0,
        "infra_maintenance_cost": 50.0,
        "capital_cost": 10000.0
    }
    roi_engine = ROIEngine(kpis, roi_config)
    roi_metrics = roi_engine.compute()

    # Merge KPIs and ROI metrics
    final_kpis = {**kpis, **roi_metrics}

    # Generate minimal timeseries from events
    timeseries = _generate_timeseries_from_events(events, stations_config, start_time, end_time)

    # Write artifact files
    data_dir = config.get("data_dir", "./data/results")
    os.makedirs(data_dir, exist_ok=True)
    
    results = {
        "metadata": {
            "run_id": run_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "seed": metadata["seed"],
            "city": metadata["city"]
        },
        "kpis": final_kpis,
        "timeseries": timeseries,
        "events": events
    }
    
    # Write summary.json
    summary_path = os.path.join(data_dir, "summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Write events.ndjson
    events_path = os.path.join(data_dir, "events.ndjson")
    with open(events_path, 'w', encoding='utf-8') as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

    # Write frames.ndjson
    frames_path = os.path.join(data_dir, "frames.ndjson")
    with open(frames_path, 'w', encoding='utf-8') as f:
        for idx, wt in enumerate(timeseries.get("wait_time", [])):
            frame = {"t": idx, "wait_time": wt}
            f.write(json.dumps(frame, ensure_ascii=False) + '\n')

    return results


def _generate_timeseries_from_events(events: List[dict], stations_config: List[dict], start_time: datetime, end_time: datetime) -> dict:
    """
    Generate minimal timeseries from event log.
    
    Reconstructs queue lengths and inventory levels over time per station.
    """
    # Initialize state tracking
    station_ids = [s["station_id"] for s in stations_config]
    inventory_by_station = {s["station_id"]: s["inventory_current"] for s in stations_config}
    queue_by_station = {sid: 0 for sid in station_ids}
    
    # Time-series buckets (1-minute resolution)
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    inventory_series = {sid: [inventory_by_station[sid]] for sid in station_ids}
    queue_series = {sid: [0] for sid in station_ids}
    
    # Sort events by timestamp
    sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""))
    
    current_minute = 0
    for event in sorted_events:
        station_id = event.get("station_id")
        event_type = event.get("event_type")
        
        if not station_id or station_id not in station_ids:
            continue
        
        # Update state based on event type
        if event_type == "queue_join":
            queue_by_station[station_id] += 1
        elif event_type == "swap_start":
            # Rider left queue, started swap
            queue_by_station[station_id] = max(0, queue_by_station[station_id] - 1)
        elif event_type == "swap_complete":
            # Inventory was consumed during swap_start, not here
            pass
        elif event_type == "lost_swap":
            # Rider left queue
            queue_by_station[station_id] = max(0, queue_by_station[station_id] - 1)
        elif event_type == "charge_complete":
            # This is actually inventory consumption (misnamed in inventory_manager)
            inventory_by_station[station_id] = max(0, inventory_by_station[station_id] - 1)
    
    # Sample state at each minute
    for minute in range(1, min(duration_minutes, 60)):  # Limit to 60 samples
        for sid in station_ids:
            inventory_series[sid].append(inventory_by_station[sid])
            queue_series[sid].append(queue_by_station[sid])
    
    return {
        "wait_time": [],  # Not reconstructed from events (would need interpolation)
        "inventory_levels": inventory_series,
        "queue_lengths": queue_series
    }


def run_scenarios(base_config: dict, scenario_configs: List[dict], weight_config: dict, mode: str = "fake") -> dict:
    """
    Run baseline and scenario simulations, compute diffs, and rank scenarios.

    Args:
        base_config: Baseline simulation configuration dictionary
        scenario_configs: List of scenario configuration dictionaries
        weight_config: Weighting configuration for ranking:
            {
                "avg_wait_time": float,
                "lost_swaps": float,
                "throughput": float,
                "roi": float
            }
        mode: Simulation mode - "fake" (fast, UI-safe) or "real" (full SimPy simulation)

    Returns:
        Dictionary containing:
            - "baseline": baseline simulation result
            - "scenarios": list of scenario results with diff
            - "ranking": ranked list of scenarios

    Rules:
        - Must not change run_simulation()
        - Must not change fake mode
        - Must not touch schema of existing outputs
        - Must not write files
        - Must not call external services

    TODO: Add multi-city scenario support
    TODO: Add optimization loop integration
    TODO: Add scenario caching
    """
    # Validate mode
    if mode not in ("fake", "real"):
        raise ValueError("mode must be 'fake' or 'real'")
    from .scenario_manager import ScenarioManager
    from .scenario_diff import ScenarioDiff
    from .scenario_ranker import ScenarioRanker
    from .event_logger import EventLogger
    import tempfile
    import os

    # Create temporary event log file for scenario events
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()

    try:
        # Initialize event logger for scenario events
        event_logger = EventLogger(temp_file.name)

        # Initialize scenario manager
        scenario_manager = ScenarioManager(base_config, scenario_configs, event_logger)

        # Run all simulations with specified mode
        results = scenario_manager.run_all(mode=mode)

        # Compute diffs for each scenario
        diffs = []
        for scenario_result in results["scenarios"]:
            diff = ScenarioDiff(results["baseline"], scenario_result["result"])
            diff_result = diff.compute()
            diffs.append(diff_result)

            # Add diff to scenario result
            scenario_result["diff"] = diff_result

            # Log ranking event for each scenario
            if event_logger:
                event_logger.log_event(
                    event_type="station_selected",  # Using closest match - scenario_ranked not in schema
                    metadata={
                        "event_category": "scenario_ranked",
                        "scenario_id": scenario_result["scenario_id"]
                    }
                )

        # Rank scenarios
        scenario_ids = [s["scenario_id"] for s in results["scenarios"]]
        ranker = ScenarioRanker(diffs, weight_config)
        ranking = ranker.rank(scenario_ids)

        # Close event logger
        event_logger.close()

    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file.name)
        except:
            pass

    return {
        "baseline": results["baseline"],
        "scenarios": results["scenarios"],
        "ranking": ranking
    }

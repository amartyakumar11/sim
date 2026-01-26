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

        # Initialize components for SimulationEngine
        # Note: SimulationEngine requires individual components, not a config dict
        from .inventory_manager import InventoryManager
        from .kpi_tracker import KPITracker
        from .network_graph import NetworkGraph
        from .routing import RoutingEngine
        from .station import Station
        from .station_process import StationProcess
        import simpy

        # Initialize inventory manager
        inventory_config = config.get("inventory_config", {})
        inventory_manager = InventoryManager(
            initial_inventory=inventory_config.get("initial_inventory", {}),
            refill_threshold=inventory_config.get("refill_threshold", 5),
            refill_amount=inventory_config.get("refill_amount", 10),
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
        station_configs = config.get("stations", [])
        
        for station_config in station_configs:
            station_id = station_config.get("station_id")
            if station_id:
                # Create Station object
                station = Station(station_config, event_logger)
                network_graph.add_station(station)

                # Create StationProcess
                station_process = StationProcess(
                    station_id=station_id,
                    env=env,
                    swap_bays_count=station.swap_bays,
                    chargers_count=station.chargers_total,
                    inventory_manager=inventory_manager,
                    event_logger=event_logger
                )
                stations[station_id] = station_process

        # Initialize demand generator
        demand_config = config.get("demand_config", {})
        demand_config["rng_seed"] = seed
        station_list = [network_graph.get_station(sid) for sid in stations.keys()]
        from .demand_generator import DemandGenerator
        demand_generator = DemandGenerator(demand_config, station_list, event_logger)

        # Create simulation engine
        engine = SimulationEngine(
            demand_generator=demand_generator,
            routing_engine=routing_engine,
            inventory_manager=inventory_manager,
            kpi_tracker=kpi_tracker,
            stations=stations,
            event_logger=event_logger,
            rng_seed=seed
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
        "stations": config.get("stations", [])
    }
    kpi_engine = KPIEngine(events, kpi_config)
    kpis = kpi_engine.compute()

    # Compute ROI from KPIs
    roi_config = {
        "revenue_per_swap": config.get("revenue_per_swap", 0.0),
        "charger_energy_cost": config.get("charger_energy_cost", 0.0),
        "station_staff_cost": config.get("station_staff_cost", 0.0),
        "battery_depreciation_cost": config.get("battery_depreciation_cost", 0.0),
        "infra_maintenance_cost": config.get("infra_maintenance_cost", 0.0),
        "capital_cost": config.get("capital_cost", 0.0)
    }
    roi_engine = ROIEngine(kpis, roi_config)
    roi_metrics = roi_engine.compute()

    # Merge KPIs and ROI metrics
    final_kpis = {**kpis, **roi_metrics}

    # Return schema-compliant results
    # TODO: Generate timeseries from events
    return {
        "metadata": {
            "run_id": run_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "seed": seed,
            "city": city
        },
        "kpis": final_kpis,
        "timeseries": {
            "wait_time": [],
            "inventory_levels": {},
            "queue_lengths": {}
        },
        "events": events
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

"""
Simulation Engine for Digital Twin Simulation Platform.

Main simulation orchestrator that coordinates all components.
"""

from datetime import datetime, timedelta
from typing import Dict
import simpy
from .demand_generator import DemandGenerator
from .routing import RoutingEngine
from .inventory_manager import InventoryManager
from .kpi_tracker import KPITracker
from .station_process import StationProcess
from .rider import Rider
from .event_logger import EventLogger


class SimulationEngine:
    """
    Main simulation engine orchestrating all components.

    Coordinates demand generation, routing, station processes, and KPI tracking.
    """

    def __init__(self, config: dict):
        """
        Initialize simulation engine from configuration.

        Args:
            config: Configuration dictionary containing:
                - "seed": int (RNG seed)
                - "start_time": datetime
                - "end_time": datetime
                - "stations": list[dict] (station configs)
                - "demand_config": dict
                - "inventory_config": dict
                - "event_logger": EventLogger
        """
        self.seed = config.get("seed", 42)
        self.start_time = config.get("start_time")
        self.end_time = config.get("end_time")
        self.event_logger = config.get("event_logger")

        # Initialize SimPy environment
        self.env = simpy.Environment()

        # Initialize components
        self.inventory_manager = InventoryManager(
            initial_inventory=config.get("inventory_config", {}).get("initial_inventory", {}),
            refill_threshold=config.get("inventory_config", {}).get("refill_threshold", 5),
            refill_amount=config.get("inventory_config", {}).get("refill_amount", 10),
            event_logger=self.event_logger
        )

        # Initialize network graph and routing
        from .network_graph import NetworkGraph
        self.graph = NetworkGraph()
        self.routing_engine = RoutingEngine(self.graph)

        # Initialize stations
        self.stations: Dict[str, StationProcess] = {}
        for station_config in config.get("stations", []):
            station_id = station_config.get("station_id")
            if station_id:
                from .station import Station
                station = Station(station_config, self.event_logger)
                self.graph.add_station(station)

                station_process = StationProcess(
                    station_id=station_id,
                    env=self.env,
                    swap_bays_count=station.swap_bays,
                    chargers_count=station.chargers_total,
                    inventory=station.inventory_current,
                    inventory_manager=self.inventory_manager,
                    event_logger=self.event_logger
                )
                self.stations[station_id] = station_process

        # Initialize demand generator
        demand_config = config.get("demand_config", {})
        demand_config["rng_seed"] = self.seed
        station_list = [self.graph.get_station(sid) for sid in self.stations.keys()]
        self.demand_generator = DemandGenerator(
            demand_config,
            station_list,
            self.event_logger
        )

        # Initialize KPI tracker
        self.kpi_tracker = KPITracker(self.event_logger)

        # TODO: Add scenario configuration
        # TODO: Add time scaling factor
        # TODO: Add parallel execution support

    def run(self) -> dict:
        """
        Run the simulation.

        Returns:
            Dictionary containing KPI snapshot and events

        TODO: Add checkpoint/rollback support
        TODO: Add confidence band calculation
        """
        # Log simulation start
        self.event_logger.log_event(
            event_type="rider_arrival",  # Using closest match - simulation_started not in schema
            metadata={
                "simulation_start": self.start_time.isoformat(),
                "simulation_end": self.end_time.isoformat(),
                "seed": self.seed,
                "event_category": "simulation_started"
            }
        )

        # Schedule arrivals
        self._schedule_arrivals()

        # Calculate simulation duration in minutes
        duration_minutes = (self.end_time - self.start_time).total_seconds() / 60.0

        # Run simulation
        self.env.run(until=duration_minutes)

        # Log simulation completion
        self.event_logger.log_event(
            event_type="swap_complete",  # Using closest match - simulation_completed not in schema
            metadata={
                "simulation_duration": duration_minutes,
                "event_category": "simulation_completed"
            }
        )

        # Return KPI snapshot
        return self.kpi_tracker.snapshot()

    def _schedule_arrivals(self) -> None:
        """
        Schedule rider arrivals from demand generator.

        TODO: Add arrival rate throttling
        TODO: Add arrival batching
        """
        arrivals = self.demand_generator.generate_arrivals(self.start_time, self.end_time)

        for arrival in arrivals:
            # Calculate arrival time offset in simulation time
            arrival_offset = (arrival["timestamp"] - self.start_time).total_seconds() / 60.0

            # Route rider to station
            rider_location = arrival.get("metadata", {}).get("rider_location", (0.0, 0.0))
            if isinstance(rider_location, list):
                rider_location = tuple(rider_location[:2])

            try:
                target_station_id = self.routing_engine.select_best_station(rider_location)
            except ValueError:
                # No stations available - skip this arrival
                continue

            # Create rider
            patience_timeout = 30.0  # minutes - TODO: make configurable
            rider = Rider(
                rider_id=arrival["rider_id"],
                arrival_time=arrival["timestamp"],
                target_station_id=target_station_id,
                patience_timeout=patience_timeout,
                event_logger=self.event_logger
            )

            # Schedule arrival process
            self.env.process(self._process_rider_arrival(rider, arrival_offset))

            self.event_logger.log_event(
                event_type="rider_arrival",
                station_id=target_station_id,
                rider_id=rider.rider_id,
                metadata={"scheduled": True}
            )

    def _process_rider_arrival(self, rider: Rider, arrival_offset: float):
        """
        Process a rider arrival (internal SimPy process).

        Args:
            rider: Rider instance to process
            arrival_offset: Time offset in minutes from simulation start

        Yields:
            SimPy events

        TODO: Add arrival time jitter
        TODO: Add reroute logic on failure
        """
        # Wait until arrival time
        yield self.env.timeout(arrival_offset)

        self.kpi_tracker.record_arrival()

        # Log routing
        self.event_logger.log_event(
            event_type="station_selected",
            station_id=rider.target_station_id,
            rider_id=rider.rider_id
        )

        # Process rider at station
        if rider.target_station_id in self.stations:
            station = self.stations[rider.target_station_id]
            yield self.env.process(rider.process(self.env, station))

            # Convert simulation times to datetimes
            if rider.status.value == "served" and hasattr(rider, '_service_start_sim'):
                rider.start_service_time = self.start_time + timedelta(minutes=rider._service_start_sim)
                rider.end_service_time = self.start_time + timedelta(minutes=rider._service_end_sim)
                
                wait_time = (
                    (rider.start_service_time - rider.arrival_time).total_seconds() / 60.0
                    if rider.start_service_time and rider.arrival_time else 0.0
                )
                self.kpi_tracker.record_completion(wait_time)
            elif rider.status.value == "lost":
                self.kpi_tracker.record_lost()
            elif rider.status.value == "rerouted":
                # TODO: Handle reroute
                pass

    def snapshot(self) -> dict:
        """
        Create a snapshot of simulation engine state.

        Returns:
            Dictionary containing state of all components
        """
        return {
            "simulation_time": self.env.now,
            "kpi_snapshot": self.kpi_tracker.snapshot(),
            "inventory_snapshot": self.inventory_manager.snapshot(),
            "stations": {
                station_id: station.snapshot()
                for station_id, station in self.stations.items()
            }
        }

"""
Simulation Engine for Digital Twin Simulation Platform.

Main simulation orchestrator that coordinates all components.
"""

from datetime import datetime
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

    def __init__(
        self,
        env: simpy.Environment,
        demand_generator: DemandGenerator,
        routing_engine: RoutingEngine,
        inventory_manager: InventoryManager,
        kpi_tracker: KPITracker,
        stations: Dict[str, StationProcess],
        event_logger: EventLogger,
        rng_seed: int = 42
    ):
        """
        Initialize simulation engine.

        Args:
            env: SimPy environment (shared with all station processes)
            demand_generator: DemandGenerator instance
            routing_engine: RoutingEngine instance
            inventory_manager: InventoryManager instance
            kpi_tracker: KPITracker instance
            stations: Dictionary mapping station_id to StationProcess
            event_logger: EventLogger instance
            rng_seed: Random number generator seed for determinism
        """
        self.env = env
        self.demand_generator = demand_generator
        self.routing_engine = routing_engine
        self.inventory_manager = inventory_manager
        self.kpi_tracker = kpi_tracker
        self.stations = stations
        self.event_logger = event_logger
        self.simulation_start_time = None  # Set when run() is called

    def schedule_arrivals(self, start_time: datetime, end_time: datetime) -> None:
        """
        Schedule rider arrivals from demand generator.

        Args:
            start_time: Simulation start time
            end_time: Simulation end time
        """
        # Generate all arrivals for the simulation period
        arrivals = self.demand_generator.generate_arrivals(start_time, end_time)

        for arrival in arrivals:
            # Calculate arrival time in simulation minutes (relative to start_time)
            arrival_time = arrival["timestamp"]
            arrival_offset_minutes = (arrival_time - start_time).total_seconds() / 60.0
            
            # Create rider with arrival offset for timing calculations
            rider = Rider(
                rider_id=arrival["rider_id"],
                arrival_time=arrival_time,
                assigned_station_id=arrival["station_id"],
                event_logger=self.event_logger,
                arrival_offset_minutes=arrival_offset_minutes
            )

            # Schedule arrival process at the correct simulation time
            self.env.process(self._schedule_rider_at_time(rider, arrival_offset_minutes))

    def _schedule_rider_at_time(self, rider: Rider, arrival_time_minutes: float):
        """
        Schedule a rider to arrive at a specific simulation time.
        
        Args:
            rider: Rider instance
            arrival_time_minutes: Time offset in minutes from simulation start
            
        Yields:
            SimPy events
        """
        # Wait until the rider's arrival time
        print(f"[DEBUG] _schedule: Scheduling {rider.id} to arrive at {arrival_time_minutes:.2f} min")
        yield self.env.timeout(arrival_time_minutes)
        print(f"[DEBUG] _schedule: Arrived! env.now={self.env.now}")
        
        # Log rider arrival with simulation timestamp
        self.event_logger.log_event(
            event_type="rider_arrival",
            station_id=rider.assigned_station_id,
            rider_id=rider.id,
            metadata={"arrival_time": rider.arrival_time.isoformat()},
            timestamp=self.get_current_simtime_iso()
        )
        
        # Record arrival in KPI tracker
        self.kpi_tracker.record_arrival()
        
        # Process rider at assigned station
        print(f"[DEBUG] _schedule: Calling _process_rider_arrival")
        yield from self._process_rider_arrival(rider)
        print(f"[DEBUG] _schedule: _process_rider_arrival completed")
    
    def _process_rider_arrival(self, rider: Rider):
        """
        Process a rider arrival (internal SimPy process).

        Args:
            rider: Rider instance

        Yields:
            SimPy events
        """
        print(f"[DEBUG] Processing rider {rider.id} arrival at station {rider.assigned_station_id}")
        print(f"[DEBUG] Available stations: {list(self.stations.keys())}")
        
        if rider.assigned_station_id not in self.stations:
            # Station not found - mark rider as lost
            print(f"[DEBUG] Station {rider.assigned_station_id} not found!")
            rider.mark_lost()
            self.kpi_tracker.record_lost()
            return
        
        station = self.stations[rider.assigned_station_id]
        print(f"[DEBUG] Calling station.handle_rider for {rider.id}")
        
        # Hand rider to station for processing
        yield from station.handle_rider(rider)
        
        print(f"[DEBUG] Rider {rider.id} finished with status {rider.status.value}")

        # Track outcome
        if rider.status.value == "served":
            wait_time = (
                (rider.start_service_time - rider.arrival_time).total_seconds()
                if rider.start_service_time and rider.arrival_time else 0.0
            )
            self.kpi_tracker.record_completion(wait_time)
        elif rider.status.value == "lost":
            self.kpi_tracker.record_lost()

    def route_rider(self, rider: Rider) -> None:
        """
        Route a rider to a station using routing engine.

        Args:
            rider: Rider instance to route

        TODO: Implement routing logic
        TODO: Call RoutingEngine.select_best_station()
        TODO: Update rider.assigned_station_id
        TODO: Emit rider_routed event
        """
        # TODO: Get rider location (from arrival metadata)
        # TODO: Call routing_engine.select_best_station()
        # TODO: Update rider.assigned_station_id
        # TODO: Emit rider_routed event
        # TODO: Handle reroute if needed

        # Placeholder: use existing assigned_station_id
        # TODO: Implement actual routing logic
        self.event_logger.log_event(
            event_type="station_selected",
            station_id=rider.assigned_station_id,
            rider_id=rider.id
        )

    def run(self, start_time: datetime, end_time: datetime) -> dict:
        """
        Run the simulation.

        Args:
            start_time: Simulation start time
            end_time: Simulation end time

        Returns:
            Dictionary containing KPI snapshot
        """
        # Store simulation start time for timestamp calculations
        self.simulation_start_time = start_time
        
        # Schedule all arrivals upfront
        self.schedule_arrivals(start_time, end_time)

        # Calculate simulation duration in minutes
        duration_minutes = (end_time - start_time).total_seconds() / 60.0

        # Run SimPy environment until end time
        self.env.run(until=duration_minutes)

        # Return KPI snapshot
        return self.kpi_tracker.snapshot()
    
    def get_current_simtime_iso(self) -> str:
        """
        Get current simulation time as ISO 8601 string.
        
        Returns:
            ISO 8601 timestamp with 'Z' suffix
        """
        if self.simulation_start_time is None:
            return datetime.utcnow().isoformat() + 'Z'
        
        from datetime import timedelta
        current_sim_time = self.simulation_start_time + timedelta(minutes=self.env.now)
        return current_sim_time.isoformat() + 'Z'

    def snapshot(self) -> dict:
        """
        Create a snapshot of simulation engine state.

        Returns:
            Dictionary containing state of all components

        TODO: Include all component snapshots
        TODO: Include simulation progress
        """
        # TODO: Get snapshots from all components
        # TODO: Include simulation time
        # TODO: Include active riders
        # TODO: Return comprehensive state

        return {
            "simulation_time": self.env.now,
            "kpi_snapshot": self.kpi_tracker.snapshot(),
            "inventory_snapshot": self.inventory_manager.snapshot(),
            "stations": {
                station_id: station.snapshot()
                for station_id, station in self.stations.items()
            }
        }

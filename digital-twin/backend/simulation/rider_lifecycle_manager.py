"""
RiderLifecycleManager: Manages deterministic rider lifecycle simulation.

Handles per-minute timestep simulation with zone movement, battery drain,
swap triggers, and multi-swap journeys.

NO random decisions - fully deterministic based on state + seed.
"""

from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
import random

from .rider_entity import RiderEntity, RiderState
from .battery_entity import BatteryEntity, BatteryState
from .simulation_config import (
    BATTERY_FULL_RANGE_KM,
    BATTERY_SWAP_THRESHOLD_KM,
    BATTERY_CRITICAL_THRESHOLD_KM,
    KM_PER_MIN,
    MAX_ZONE_DWELL_MIN,
    ZONE_TYPE_PRIORITY,
    STATION_BATTERY_AVAILABLE_SCORE,
    STATION_QUEUE_PENALTY_PER_RIDER,
    STATION_ZONE_HOP_PENALTY
)
from .event_logger import EventLogger
from .network_graph import NetworkGraph


class RiderLifecycleManager:
    """
    Manages deterministic rider lifecycle simulation.
    
    Handles timestep-based simulation with zone movement, battery drain,
    and swap logic while preserving event schema.
    """
    
    def __init__(self, event_logger: EventLogger, rng_seed: int = 42):
        """
        Initialize lifecycle manager.
        
        Args:
            event_logger: EventLogger for logging events
            rng_seed: Random seed for deterministic decisions
        """
        self.event_logger = event_logger
        self.rng = random.Random(rng_seed)
        
        # Track riders and batteries created
        self.rider_counter = 0
        self.battery_counter = 0
    
    def initialize_rider(
        self,
        rider_id: str,
        spawn_zone: str,
        spawn_time: datetime,
        network_graph: NetworkGraph
    ) -> RiderEntity:
        """
        Initialize a new rider entity with full battery.
        
        Args:
            rider_id: Unique rider identifier
            spawn_zone: Zone where rider spawns
            spawn_time: Time rider enters simulation
            network_graph: Network graph for zone validation
            
        Returns:
            Initialized RiderEntity
        """
        # Create full battery for rider
        battery_id = f"BAT_RIDER_{rider_id}"
        battery = BatteryEntity(
            battery_id=battery_id,
            initial_station_id=spawn_zone,
            initial_state=BatteryState.IN_USE
        )
        # Set battery to full range
        battery.remaining_km = BATTERY_FULL_RANGE_KM
        battery.current_rider_id = rider_id
        
        # Create rider entity
        rider = RiderEntity(
            rider_id=rider_id,
            initial_battery_id=battery_id,
            spawn_time=spawn_time
        )
        rider.current_zone_id = spawn_zone
        rider.home_zone_id = spawn_zone
        rider.time_in_zone = 0
        rider.total_distance_km = 0
        rider.current_battery = battery
        rider.state = RiderState.ACTIVE
        
        # Emit rider_arrival event (SPAWN ONLY - no terminal events)
        self.event_logger.log_event(
            event_type="rider_arrival",
            station_id="SYSTEM",
            rider_id=rider_id,
            metadata={
                "zone_id": spawn_zone,
                "battery_id": battery_id,
                "battery_remaining_km": BATTERY_FULL_RANGE_KM
            },
            timestamp=spawn_time.isoformat() + 'Z'
        )
        
        return rider
    
    def simulate_rider_timestep(
        self,
        rider: RiderEntity,
        minute: int,
        simulation_start: datetime,
        network_graph: NetworkGraph,
        stations: Dict
    ) -> bool:
        """
        Simulate one minute for a rider.
        
        Args:
            rider: RiderEntity to simulate
            minute: Current minute offset from simulation start
            simulation_start: Simulation start datetime
            network_graph: NetworkGraph for zone/station lookup
            stations: Dict of station_id -> StationProcess
            
        Returns:
            True if rider still active, False if terminated
        """
        if rider.state != RiderState.ACTIVE:
            return False
        
        current_time = simulation_start + timedelta(minutes=minute)
        
        # 1. Drain battery
        self._drain_battery(rider)
        
        # 2. Increment time in zone
        rider.time_in_zone += 1
        
        # 3. Check if swap needed
        swap_needed, swap_critical = self._check_swap_needed(rider)
        
        if swap_needed:
            # Attempt swap
            station_id = self._select_station_for_swap(
                rider, network_graph, stations
            )
            
            if station_id is None:
                # No station available - terminate rider
                self.event_logger.log_event(
                    event_type="lost_swap",
                    station_id="NONE",
                    rider_id=rider.rider_id,
                    metadata={
                        "reason": "no_battery_available",
                        "end_zone": rider.current_zone_id,
                        "battery_remaining_km": rider.current_battery.remaining_km
                    },
                    timestamp=current_time.isoformat() + 'Z'
                )
                rider.deactivate()
                return False
            
            # Execute swap (station handles queue_join, swap_start, swap_complete)
            success = self._execute_swap(rider, station_id, stations[station_id], current_time)
            if not success:
                rider.deactivate()
                return False
        
        # 4. Zone movement decision (only if not in critical battery state)
        if not swap_critical and self._should_move_zone(rider):
            next_zone = self._select_next_zone(rider, network_graph)
            if next_zone:
                rider.current_zone_id = next_zone
                rider.time_in_zone = 0
                if next_zone not in rider.visited_stations:
                    rider.visited_stations.append(next_zone)
        
        return True
    
    def _drain_battery(self, rider: RiderEntity):
        """
        Drain battery for one minute of travel.
        
        Args:
            rider: RiderEntity whose battery to drain
        """
        rider.current_battery.remaining_km -= KM_PER_MIN
        rider.total_distance_km += KM_PER_MIN
        
        # Ensure battery doesn't go negative
        if rider.current_battery.remaining_km < 0:
            rider.current_battery.remaining_km = 0
    
    def _check_swap_needed(self, rider: RiderEntity) -> Tuple[bool, bool]:
        """
        Check if rider needs battery swap.
        
        Args:
            rider: RiderEntity to check
            
        Returns:
            Tuple of (swap_needed, swap_critical)
        """
        remaining = rider.current_battery.remaining_km
        swap_critical = remaining <= BATTERY_CRITICAL_THRESHOLD_KM
        swap_needed = remaining <= BATTERY_SWAP_THRESHOLD_KM
        return swap_needed, swap_critical
    
    def _should_move_zone(self, rider: RiderEntity) -> bool:
        """
        Deterministic decision: should rider move to new zone?
        
        Args:
            rider: RiderEntity to evaluate
            
        Returns:
            True if rider should move zones
        """
        # Force move if dwelling too long
        if rider.time_in_zone >= MAX_ZONE_DWELL_MIN:
            return True
        
        # Compute move score
        move_score = 0
        
        # +1 if battery healthy
        if rider.current_battery.remaining_km > BATTERY_SWAP_THRESHOLD_KM:
            move_score += 1
        
        # +1 if not at home
        if rider.current_zone_id != rider.home_zone_id:
            move_score += 1
        
        # Deterministic: move if score >= 2
        return move_score >= 2
    
    def _select_next_zone(
        self,
        rider: RiderEntity,
        network_graph: NetworkGraph
    ) -> Optional[str]:
        """
        Select next zone for rider to move to (deterministic).
        
        Args:
            rider: RiderEntity selecting zone
            network_graph: NetworkGraph for zone connectivity
            
        Returns:
            Next zone ID or None
        """
        # Get current zone's connected zones via station edges
        current_zone = rider.current_zone_id
        zones = network_graph.graph.graph.get("zones", {})
        
        if current_zone not in zones:
            return None
        
        # Get all reachable zones from current zone's stations
        reachable_zones = set()
        for station_id in zones[current_zone]["station_ids"]:
            if station_id in network_graph.graph.nodes():
                for neighbor_station in network_graph.graph.successors(station_id):
                    neighbor_zone = network_graph.graph.nodes[neighbor_station].get("zone_id")
                    if neighbor_zone and neighbor_zone != current_zone:
                        reachable_zones.add(neighbor_zone)
        
        if not reachable_zones:
            return None
        
        # Score zones deterministically
        zone_scores = []
        for zone_id in reachable_zones:
            zone_data = zones.get(zone_id, {})
            zone_type = zone_data.get("type", "unknown")
            priority = ZONE_TYPE_PRIORITY.get(zone_type, 0)
            
            # Prefer unvisited zones
            visit_penalty = rider.visited_stations.count(zone_id)
            
            score = priority - visit_penalty
            zone_scores.append((score, zone_id))
        
        # Sort by score (descending), then by zone_id (deterministic tiebreak)
        zone_scores.sort(key=lambda x: (-x[0], x[1]))
        
        return zone_scores[0][1] if zone_scores else None
    
    def _select_station_for_swap(
        self,
        rider: RiderEntity,
        network_graph: NetworkGraph,
        stations: Dict
    ) -> Optional[str]:
        """
        Select best station for battery swap (deterministic scoring).
        
        Args:
            rider: RiderEntity needing swap
            network_graph: NetworkGraph for station lookup
            stations: Dict of station_id -> StationProcess
            
        Returns:
            Station ID or None if no viable station
        """
        zones = network_graph.graph.graph.get("zones", {})
        current_zone = rider.current_zone_id
        
        # Get candidate stations: current zone + neighbors
        candidate_stations = []
        
        # Current zone stations (0 hops)
        if current_zone in zones:
            for station_id in zones[current_zone]["station_ids"]:
                candidate_stations.append((station_id, 0))
        
        # Neighboring zone stations (1 hop)
        for zone_id in zones.keys():
            if zone_id != current_zone:
                # Check if reachable from current zone
                for station_id in zones[current_zone].get("station_ids", []):
                    if station_id in network_graph.graph.nodes():
                        for neighbor in network_graph.graph.successors(station_id):
                            neighbor_zone = network_graph.graph.nodes[neighbor].get("zone_id")
                            if neighbor_zone == zone_id:
                                for target_station in zones[zone_id]["station_ids"]:
                                    candidate_stations.append((target_station, 1))
                                break
        
        # Score stations
        station_scores = []
        for station_id, zone_hops in candidate_stations:
            if station_id not in stations:
                continue
            
            station_process = stations[station_id]
            
            # Check battery availability via BatteryPool
            battery_available = station_process.battery_pool.get_available_count() > 0
            
            # Score calculation
            score = 0
            if battery_available:
                score += STATION_BATTERY_AVAILABLE_SCORE
            
            score -= STATION_QUEUE_PENALTY_PER_RIDER * station_process.current_queue_length
            score -= STATION_ZONE_HOP_PENALTY * zone_hops
            
            station_scores.append((score, station_id))
        
        if not station_scores:
            return None
        
        # Sort by score (descending), then by station_id (deterministic)
        station_scores.sort(key=lambda x: (-x[0], x[1]))
        
        return station_scores[0][1]
    
    def _execute_swap(
        self,
        rider: RiderEntity,
        station_id: str,
        station_process,
        current_time: datetime
    ) -> bool:
        """
        Execute battery swap at station.
        
        Args:
            rider: RiderEntity getting swap
            station_id: Station ID
            station_process: StationProcess instance
            current_time: Current simulation time
            
        Returns:
            True if swap succeeded, False otherwise
        """
        # Note: We cannot directly call station_process.handle_rider() in timestep mode
        # Instead, we directly interact with BatteryPool
        
        # Get available battery
        new_battery = station_process.battery_pool.get_available_battery()
        if not new_battery:
            return False
        
        # Log swap_start
        self.event_logger.log_event(
            event_type="swap_start",
            station_id=station_id,
            rider_id=rider.rider_id,
            metadata={"battery_remaining_km": rider.current_battery.remaining_km},
            timestamp=current_time.isoformat() + 'Z'
        )
        
        # Get rider's old battery
        old_battery_id = rider.current_battery.battery_id
        
        # Assign new battery
        assigned_battery = station_process.battery_pool.assign_battery_to_rider(
            rider.rider_id, current_time
        )
        
        if assigned_battery:
            # Update rider's battery
            rider.current_battery = assigned_battery
            assigned_battery.remaining_km = BATTERY_FULL_RANGE_KM
            
            # Return old battery (triggers charge events)
            station_process.battery_pool.return_battery(
                old_battery_id, rider.rider_id, current_time
            )
            
            # Log swap_complete
            self.event_logger.log_event(
                event_type="swap_complete",
                station_id=station_id,
                rider_id=rider.rider_id,
                metadata={
                    "new_battery_id": assigned_battery.battery_id,
                    "battery_remaining_km": BATTERY_FULL_RANGE_KM
                },
                timestamp=current_time.isoformat() + 'Z'
            )
            
            # Update rider state
            rider.complete_swap(assigned_battery.battery_id, current_time)
            
            return True
        
        return False

"""
Station Process for Digital Twin Simulation Platform.

Manages station operations using SimPy resources for swap bays and chargers.
"""

from typing import Optional
from datetime import datetime, timedelta
import simpy
from .rider import Rider
from .battery_pool import BatteryPool
from .rider_entity import RiderEntity
from .event_logger import EventLogger


class StationProcess:
    """
    Manages station operations and resource allocation.

    Uses SimPy Resources for swap bays and chargers.
    """

    def __init__(
        self,
        station_id: str,
        env: simpy.Environment,
        swap_bays_count: int,
        chargers_count: int,
        battery_pool: BatteryPool,
        event_logger: EventLogger,
        swap_time_sec: int = 180,
        queue_limit: int = None,
        simulation_start_time: Optional[datetime] = None
    ):
        """
        Initialize station process.

        Args:
            station_id: Station identifier
            env: SimPy environment
            swap_bays_count: Number of swap bays available
            chargers_count: Number of chargers available
            battery_pool: BatteryPool instance for battery management
            event_logger: EventLogger instance for logging events
            swap_time_sec: Time in seconds for a swap operation
            queue_limit: Maximum queue length (None = unlimited)
            simulation_start_time: Simulation start datetime (for timestamp calculation)
        """
        self.station_id = station_id
        self.env = env
        self.swap_bays = simpy.Resource(env, capacity=swap_bays_count)
        self.chargers = simpy.Resource(env, capacity=chargers_count)
        self.battery_pool = battery_pool
        self.event_logger = event_logger
        self.swap_time_sec = swap_time_sec
        self.queue_limit = queue_limit if queue_limit is not None else (swap_bays_count * 3)
        self.simulation_start_time = simulation_start_time
        
        # Track current queue length for capacity checks
        self.current_queue_length = 0
    
    def get_current_simtime_iso(self) -> str:
        """Get current simulation time as ISO 8601 string."""
        if self.simulation_start_time is None:
            return datetime.utcnow().isoformat() + 'Z'
        
        current_sim_time = self.simulation_start_time + timedelta(minutes=self.env.now)
        return current_sim_time.isoformat() + 'Z'

    def can_accept_rider(self) -> bool:
        """
        Check if station can accept a new rider.

        Returns:
            True if station can accept rider, False otherwise
        """
        # Check if queue is at capacity
        if self.current_queue_length >= self.queue_limit:
            return False
        
        return True

    def handle_rider(self, rider: Rider):
        """
        Handle a rider arrival at the station.

        Args:
            rider: Rider instance to handle

        Yields:
            SimPy events
        """
        print(f"[DEBUG] handle_rider called for {rider.id} at station {self.station_id}")
        print(f"[DEBUG] can_accept_rider: queue={self.current_queue_length}, limit={self.queue_limit}")
        
        # Check if station can accept rider
        if not self.can_accept_rider():
            # Reject rider - queue is full
            print(f"[DEBUG] Rejecting {rider.id} - queue full")
            self.event_logger.log_event(
                event_type="lost_swap",
                station_id=self.station_id,
                rider_id=rider.id,
                metadata={"reason": "queue_full"},
                timestamp=self.get_current_simtime_iso()
            )
            rider.mark_lost()
            # Must yield something even when rejecting
            yield self.env.timeout(0)
            return
        
        # Accept rider into queue
        self.current_queue_length += 1
        print(f"[DEBUG] Accepted {rider.id}, queue now = {self.current_queue_length}")
        
        # Process swap (this handles queue_join logging and waiting)
        print(f"[DEBUG] Calling process_swap for {rider.id}")
        yield from self.process_swap(rider)
        print(f"[DEBUG] process_swap completed for {rider.id}")
        
        # Rider has left (either served or lost due to stockout)
        self.current_queue_length = max(0, self.current_queue_length - 1)

    def process_swap(self, rider: Rider):
        """
        Process a battery swap operation for a rider.

        Args:
            rider: Rider instance to serve

        Yields:
            SimPy events
        """
        from datetime import timedelta
        
        print(f"[DEBUG] process_swap: env.now={self.env.now}, rider.arrival_offset={rider.arrival_offset_minutes}")
        print(f"[DEBUG] process_swap: logging queue_join for {rider.id}")
        # Log queue_join when rider enters the queue (before waiting for resource)
        simtime_iso = self.get_current_simtime_iso()
        print(f"[DEBUG] process_swap: simtime_iso={simtime_iso}")
        self.event_logger.log_event(
            event_type="queue_join",
            station_id=self.station_id,
            rider_id=rider.id,
            timestamp=simtime_iso
        )
        print(f"[DEBUG] process_swap: queue_join logged")
        
        # Wait for available swap bay resource
        print(f"[DEBUG] process_swap: requesting bay")
        bay_request = self.swap_bays.request()
        print(f"[DEBUG] process_swap: yielding for bay")
        yield bay_request
        print(f"[DEBUG] process_swap: got bay, env.now={self.env.now}")
        
        try:
            # Rider got swap bay - service starts now
            # Calculate absolute time: arrival_time + time waited
            wait_duration_minutes = self.env.now - rider.arrival_offset_minutes
            rider.start_service_time = rider.arrival_time + timedelta(minutes=wait_duration_minutes)
            print(f"[DEBUG] process_swap: calculated start_service_time, wait_duration={wait_duration_minutes:.2f}")

            # Emit swap_start event with simulation timestamp
            self.event_logger.log_event(
                event_type="swap_start",
                station_id=self.station_id,
                rider_id=rider.id,
                timestamp=self.get_current_simtime_iso()
            )
            print(f"[DEBUG] process_swap: swap_start logged")

            # Check battery availability via BatteryPool
            available_battery = self.battery_pool.get_available_battery()
            if not available_battery:
                # Battery stockout - cannot serve rider
                print(f"[DEBUG] process_swap: battery stockout!")
                self.event_logger.log_event(
                    event_type="inventory_stockout",
                    station_id=self.station_id,
                    rider_id=rider.id,
                    timestamp=self.get_current_simtime_iso()
                )
                rider.mark_lost()
                return
            
            # Get rider's old battery (if exists)
            old_battery_id = getattr(rider, 'current_battery_id', None)
            
            # Assign new battery to rider
            swap_time = self.simulation_start_time + timedelta(minutes=self.env.now) if self.simulation_start_time else datetime.utcnow()
            new_battery = self.battery_pool.assign_battery_to_rider(rider.id, swap_time)
            
            # Update rider's battery tracking
            rider.current_battery_id = new_battery.battery_id if new_battery else None
            
            # Return old battery to pool (if exists)
            if old_battery_id:
                self.battery_pool.return_battery(old_battery_id, rider.id, swap_time)
            
            print(f"[DEBUG] process_swap: inventory consumed, starting swap")
            # Perform swap (takes swap_time_sec seconds of simulated time)
            # Convert seconds to minutes for SimPy
            swap_time_minutes = self.swap_time_sec / 60.0
            yield self.env.timeout(swap_time_minutes)
            print(f"[DEBUG] process_swap: swap timeout complete, env.now={self.env.now}")
            
            # Swap complete
            rider.end_service_time = rider.start_service_time + timedelta(seconds=self.swap_time_sec)
            rider.status = rider.status.__class__.SERVED
            
            self.event_logger.log_event(
                event_type="swap_complete",
                station_id=self.station_id,
                rider_id=rider.id,
                timestamp=self.get_current_simtime_iso()
            )
            print(f"[DEBUG] process_swap: swap_complete logged, rider status={rider.status.value}")
        finally:
            # Release swap bay
            self.swap_bays.release(bay_request)
            print(f"[DEBUG] process_swap: released bay")

    def snapshot(self) -> dict:
        """
        Create a snapshot of station process state.

        Returns:
            Dictionary containing station process attributes

        TODO: Include resource utilization
        TODO: Include queue length
        TODO: Include current riders being served
        """
        # TODO: Calculate swap bay utilization
        # TODO: Calculate charger utilization
        # TODO: Get queue length
        # TODO: Get current service count

        return {
            "station_id": self.station_id,
            "swap_bays_capacity": self.swap_bays.capacity,
            "swap_bays_available": self.swap_bays.capacity - len(self.swap_bays.queue),
            "chargers_capacity": self.chargers.capacity,
            "chargers_available": self.chargers.capacity - len(self.chargers.queue)
        }

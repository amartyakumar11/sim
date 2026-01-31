"""
BatteryPool: Manages battery availability and assignment per station.

Replaces simple inventory count logic with entity tracking.
Integrates into existing swap flow using existing event types.
"""

from typing import Dict, List, Optional
from datetime import datetime
from .battery_entity import BatteryEntity, BatteryState
from .event_logger import EventLogger


class BatteryPool:
    """
    Manages battery entities for a single station.
    
    Tracks available, in-use, charging, and depleted batteries.
    Replaces InventoryManager's integer count with entity tracking.
    """
    
    def __init__(
        self,
        station_id: str,
        initial_battery_count: int,
        event_logger: EventLogger
    ):
        """
        Initialize battery pool for a station.
        
        Args:
            station_id: Station this pool belongs to
            initial_battery_count: Number of batteries to create
            event_logger: EventLogger for logging events
        """
        self.station_id = station_id
        self.event_logger = event_logger
        
        # Create initial batteries
        self.batteries: Dict[str, BatteryEntity] = {}
        for i in range(initial_battery_count):
            battery_id = f"BAT_{station_id}_{i:04d}"
            battery = BatteryEntity(
                battery_id=battery_id,
                initial_station_id=station_id,
                initial_state=BatteryState.AVAILABLE
            )
            self.batteries[battery_id] = battery
    
    def get_available_count(self) -> int:
        """
        Get count of available batteries at this station.
        
        Returns:
            Number of batteries in AVAILABLE state
        """
        return sum(
            1 for battery in self.batteries.values()
            if battery.state == BatteryState.AVAILABLE 
            and battery.current_station_id == self.station_id
        )
    
    def get_available_battery(self) -> Optional[BatteryEntity]:
        """
        Get an available battery for assignment.
        
        Returns:
            BatteryEntity in AVAILABLE state, or None if none available
        """
        for battery in self.batteries.values():
            if (battery.state == BatteryState.AVAILABLE and 
                battery.current_station_id == self.station_id):
                return battery
        return None
    
    def assign_battery_to_rider(
        self, 
        rider_id: str, 
        swap_time: datetime
    ) -> Optional[BatteryEntity]:
        """
        Assign an available battery to a rider during swap.
        
        Args:
            rider_id: Rider receiving battery
            swap_time: Time of swap
            
        Returns:
            Assigned BatteryEntity, or None if no batteries available
        """
        battery = self.get_available_battery()
        if not battery:
            return None
        
        battery.assign_to_rider(rider_id, swap_time)
        return battery
    
    def return_battery(
        self,
        battery_id: str,
        rider_id: str,
        return_time: datetime
    ):
        """
        Return a battery to the station (rider dropped it off during swap).
        
        Args:
            battery_id: Battery being returned
            rider_id: Rider who had the battery
            return_time: Time of return
        """
        if battery_id not in self.batteries:
            # Battery not from this pool - add it
            battery = BatteryEntity(
                battery_id=battery_id,
                initial_station_id=self.station_id,
                initial_state=BatteryState.DEPLETED
            )
            self.batteries[battery_id] = battery
        else:
            battery = self.batteries[battery_id]
        
        battery.return_to_station(self.station_id, return_time)
        
        # Immediately start charging (simplified - instant transition)
        battery.start_charging(return_time)
        
        # Log charge_start event (using existing event type)
        self.event_logger.log_event(
            event_type="charge_start",
            station_id=self.station_id,
            battery_id=battery_id,
            metadata={"rider_id": rider_id}
        )
        
        # Complete charging immediately (Level-2 simplification - no charging time yet)
        battery.complete_charging(return_time)
        
        # Log charge_complete event (using existing event type)
        self.event_logger.log_event(
            event_type="charge_complete",
            station_id=self.station_id,
            battery_id=battery_id,
            metadata={"charge_duration_sec": 0}  # Instant for now
        )
    
    def snapshot(self) -> dict:
        """
        Get snapshot of pool state.
        
        Returns:
            Dictionary with battery counts by state
        """
        state_counts = {state.value: 0 for state in BatteryState}
        
        for battery in self.batteries.values():
            if battery.current_station_id == self.station_id:
                state_counts[battery.state.value] += 1
        
        return {
            "station_id": self.station_id,
            "total_batteries": len(self.batteries),
            "available": state_counts[BatteryState.AVAILABLE.value],
            "in_use": state_counts[BatteryState.IN_USE.value],
            "charging": state_counts[BatteryState.CHARGING.value],
            "depleted": state_counts[BatteryState.DEPLETED.value]
        }

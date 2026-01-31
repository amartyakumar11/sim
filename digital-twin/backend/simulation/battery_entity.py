"""
BatteryEntity: Pure state object tracking battery lifecycle.

NO physics simulation, NO charging curves, NO temperature models.
Just state tracking for battery assignment and availability.
"""

from datetime import datetime
from typing import Optional
from enum import Enum


class BatteryState(Enum):
    """Battery lifecycle states."""
    AVAILABLE = "available"     # Ready for assignment
    IN_USE = "in_use"          # Assigned to a rider
    CHARGING = "charging"       # Being charged at station
    DEPLETED = "depleted"       # Needs charging before use


class BatteryEntity:
    """
    Pure state object representing a battery.
    
    Tracks battery location, state, and assignment history.
    Does NOT simulate charging physics - just state transitions.
    """
    
    def __init__(
        self,
        battery_id: str,
        initial_station_id: str,
        initial_state: BatteryState = BatteryState.AVAILABLE
    ):
        """
        Initialize a battery entity.
        
        Args:
            battery_id: Unique battery identifier
            initial_station_id: Station where battery starts
            initial_state: Initial battery state
        """
        self.battery_id = battery_id
        self.state = initial_state
        self.current_station_id = initial_station_id
        self.current_rider_id: Optional[str] = None
        
        # Lifecycle tracking
        self.total_swaps = 0
        self.total_charges = 0
        self.last_swap_time: Optional[datetime] = None
        self.last_charge_time: Optional[datetime] = None
        
        # Battery range tracking (for Level-2 lifecycle)
        self.remaining_km: float = 0.0  # Set externally based on usage
        
    def assign_to_rider(self, rider_id: str, swap_time: datetime):
        """
        Assign battery to a rider (during swap).
        
        Args:
            rider_id: Rider receiving this battery
            swap_time: Time of swap
        """
        self.state = BatteryState.IN_USE
        self.current_rider_id = rider_id
        self.total_swaps += 1
        self.last_swap_time = swap_time
    
    def return_to_station(self, station_id: str, return_time: datetime):
        """
        Return battery to station (rider dropped it off).
        
        Args:
            station_id: Station where battery is returned
            return_time: Time of return
        """
        self.current_station_id = station_id
        self.current_rider_id = None
        self.state = BatteryState.DEPLETED  # Needs charging
    
    def start_charging(self, charge_start_time: datetime):
        """
        Start charging battery.
        
        Args:
            charge_start_time: When charging started
        """
        self.state = BatteryState.CHARGING
    
    def complete_charging(self, charge_complete_time: datetime):
        """
        Complete charging battery.
        
        Args:
            charge_complete_time: When charging completed
        """
        self.state = BatteryState.AVAILABLE
        self.total_charges += 1
        self.last_charge_time = charge_complete_time
    
    def snapshot(self) -> dict:
        """
        Get current state snapshot.
        
        Returns:
            Dictionary with battery state
        """
        return {
            "battery_id": self.battery_id,
            "state": self.state.value,
            "current_station_id": self.current_station_id,
            "current_rider_id": self.current_rider_id,
            "total_swaps": self.total_swaps,
            "total_charges": self.total_charges,
            "last_swap_time": self.last_swap_time.isoformat() if self.last_swap_time else None,
            "last_charge_time": self.last_charge_time.isoformat() if self.last_charge_time else None
        }

"""
RiderEntity: Pure state object tracking rider lifecycle across simulation.

NO SimPy, NO events, NO routing logic.
Just state tracking for persistent riders across swaps.
"""

from datetime import datetime
from typing import Optional
from enum import Enum


class RiderState(Enum):
    """Rider lifecycle states."""
    ACTIVE = "active"           # Rider exists and may need swaps
    AT_STATION = "at_station"   # Currently at a station
    SWAPPING = "swapping"       # Battery swap in progress
    INACTIVE = "inactive"       # No longer in simulation


class RiderEntity:
    """
    Pure state object representing a persistent rider.
    
    Tracks rider lifecycle, battery ownership, and station visits.
    Does NOT handle SimPy events or routing - those remain in Rider class.
    """
    
    def __init__(
        self,
        rider_id: str,
        initial_battery_id: Optional[str] = None,
        spawn_time: Optional[datetime] = None
    ):
        """
        Initialize a rider entity.
        
        Args:
            rider_id: Unique rider identifier
            initial_battery_id: ID of battery rider starts with (if any)
            spawn_time: When rider entered simulation
        """
        self.rider_id = rider_id
        self.state = RiderState.ACTIVE
        self.current_battery_id = initial_battery_id
        self.spawn_time = spawn_time or datetime.utcnow()
        
        # Lifecycle tracking
        self.total_swaps = 0
        self.visited_stations = []  # List of station_ids
        self.last_swap_time: Optional[datetime] = None
        
        # Current state
        self.current_station_id: Optional[str] = None
        
        # Zone tracking (for Level-2 lifecycle)
        self.current_zone_id: Optional[str] = None
        self.home_zone_id: Optional[str] = None
        self.time_in_zone: int = 0  # Minutes in current zone
        
        # Battery reference (for Level-2 lifecycle)
        self.current_battery = None  # Will hold BatteryEntity reference
        
        # Distance tracking
        self.total_distance_km: float = 0.0
        
    def arrive_at_station(self, station_id: str, arrival_time: datetime):
        """
        Mark rider as arriving at a station.
        
        Args:
            station_id: Station the rider arrived at
            arrival_time: Time of arrival
        """
        self.state = RiderState.AT_STATION
        self.current_station_id = station_id
        if station_id not in self.visited_stations:
            self.visited_stations.append(station_id)
    
    def start_swap(self):
        """Mark rider as starting a battery swap."""
        self.state = RiderState.SWAPPING
    
    def complete_swap(self, new_battery_id: str, swap_time: datetime):
        """
        Mark rider as completing a battery swap.
        
        Args:
            new_battery_id: ID of the new battery received
            swap_time: Time swap completed
        """
        self.current_battery_id = new_battery_id
        self.total_swaps += 1
        self.last_swap_time = swap_time
        self.state = RiderState.ACTIVE
    
    def leave_station(self):
        """Mark rider as leaving station."""
        self.current_station_id = None
        self.state = RiderState.ACTIVE
    
    def deactivate(self):
        """Mark rider as no longer active in simulation."""
        self.state = RiderState.INACTIVE
    
    def snapshot(self) -> dict:
        """
        Get current state snapshot.
        
        Returns:
            Dictionary with rider state
        """
        return {
            "rider_id": self.rider_id,
            "state": self.state.value,
            "current_battery_id": self.current_battery_id,
            "current_station_id": self.current_station_id,
            "total_swaps": self.total_swaps,
            "visited_stations": self.visited_stations.copy(),
            "spawn_time": self.spawn_time.isoformat() if self.spawn_time else None,
            "last_swap_time": self.last_swap_time.isoformat() if self.last_swap_time else None
        }

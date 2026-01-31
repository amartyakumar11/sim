"""
KPI Engine for Digital Twin Simulation Platform.

Computes operational KPIs from simulation event logs.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple


class KPIEngine:
    """
    Computes key performance indicators from event logs.

    All KPIs are derived strictly from event logs and are deterministic.
    """

    def __init__(self, events: List[dict], config: dict):
        """
        Initialize KPI engine with events and configuration.

        Args:
            events: List of event dictionaries from simulation
            config: Configuration dictionary containing:
                - "start_time": datetime
                - "end_time": datetime
                - "stations": list[dict] (station configs with swap_bays)
        """
        self.events = events
        self.config = config
        self.start_time = config.get("start_time")
        self.end_time = config.get("end_time")
        self.stations = config.get("stations", [])

        # Build station lookup for swap_bays count
        self.station_swap_bays: Dict[str, int] = {}
        for station in self.stations:
            station_id = station.get("station_id")
            if station_id:
                self.station_swap_bays[station_id] = station.get("swap_bays", 1)

        # TODO: Add caching for computed KPIs
        # TODO: Add validation for event structure

    def compute(self) -> dict:
        """
        Compute all KPIs from event logs.

        Returns:
            Dictionary containing all computed KPIs:
                - avg_wait_time: float
                - lost_swaps: int
                - utilization: float
                - throughput: int
                - idle_inventory: float
        """
        avg_wait_time = self._compute_avg_wait_time()
        lost_swaps = self._compute_lost_swaps()
        throughput = self._compute_throughput()
        utilization = self._compute_utilization()
        idle_inventory = self._compute_idle_inventory()
        financials = self._compute_financials()

        return {
            "revenue": financials.get("total_revenue", 0.0),
            "avg_wait_time": avg_wait_time,
            "lost_swaps": lost_swaps,
            "utilization": utilization,
            "throughput": throughput,
            "idle_inventory": idle_inventory,
            "financials": financials
        }

    def _compute_avg_wait_time(self) -> float:
        """
        Compute average wait time from queue_join to swap_start.

        Returns:
            Average wait time in minutes
        """
        # Track wait times per rider
        rider_wait_starts: Dict[str, datetime] = {}
        wait_times: List[float] = []

        for event in self.events:
            event_type = event.get("event_type")
            rider_id = event.get("rider_id")
            timestamp_str = event.get("timestamp")

            if not timestamp_str or not rider_id:
                continue

            try:
                # Parse timestamp (handle both timezone-aware and naive)
                if timestamp_str.endswith('Z'):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
                
                # Make timezone-naive for comparison if start_time is naive
                if timestamp.tzinfo is not None and self.start_time.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=None)
            except (ValueError, AttributeError):
                continue

            if event_type == "queue_join":
                # Rider started waiting
                rider_wait_starts[rider_id] = timestamp
            elif event_type == "swap_start":
                # Rider got service - calculate wait time
                if rider_id in rider_wait_starts:
                    wait_duration = (timestamp - rider_wait_starts[rider_id]).total_seconds() / 60.0
                    if wait_duration >= 0:
                        wait_times.append(wait_duration)
                    # Remove from tracking
                    del rider_wait_starts[rider_id]

        if not wait_times:
            return 0.0

        return sum(wait_times) / len(wait_times)

    def _compute_lost_swaps(self) -> int:
        """
        Compute count of lost swaps (inventory stockout or timeout).

        Returns:
            Count of lost swaps
        """
        lost_count = 0

        for event in self.events:
            event_type = event.get("event_type")
            metadata = event.get("metadata", {})

            if event_type == "lost_swap":
                # Check if it's due to inventory stockout or timeout
                abandonment_reason = metadata.get("abandonment_reason", "")
                if abandonment_reason in {"inventory_stockout", "patience_timeout", "timeout"}:
                    lost_count += 1
            elif event_type == "inventory_stockout":
                # Also count inventory stockout events as lost swaps
                lost_count += 1

        return lost_count

    def _compute_throughput(self) -> int:
        """
        Compute throughput as count of completed swaps.

        Returns:
            Count of swap_complete events
        """
        throughput = 0

        for event in self.events:
            if event.get("event_type") == "swap_complete":
                throughput += 1

        return throughput

    def _compute_utilization(self) -> float:
        """
        Compute utilization as total busy time / (swap_bays × total_time).

        Returns:
            Utilization value between 0.0 and 1.0
        """
        if not self.start_time or not self.end_time:
            return 0.0

        total_sim_time = (self.end_time - self.start_time).total_seconds() / 60.0  # minutes
        if total_sim_time <= 0:
            return 0.0

        # Track swap operations per station
        station_swap_starts: Dict[Tuple[str, str], datetime] = {}  # (station_id, rider_id) -> start_time
        station_busy_time: Dict[str, float] = {}  # station_id -> total busy minutes

        for event in self.events:
            event_type = event.get("event_type")
            station_id = event.get("station_id")
            rider_id = event.get("rider_id")
            timestamp_str = event.get("timestamp")

            if not station_id or not rider_id or not timestamp_str:
                continue

            try:
                # Parse timestamp (handle both timezone-aware and naive)
                if timestamp_str.endswith('Z'):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
                
                # Make timezone-naive for comparison if start_time is naive
                if timestamp.tzinfo is not None and self.start_time.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=None)
            except (ValueError, AttributeError):
                continue

            key = (station_id, rider_id)

            if event_type == "swap_start":
                station_swap_starts[key] = timestamp
            elif event_type == "swap_complete":
                if key in station_swap_starts:
                    duration = (timestamp - station_swap_starts[key]).total_seconds() / 60.0
                    if duration > 0:
                        station_busy_time[station_id] = station_busy_time.get(station_id, 0.0) + duration
                    del station_swap_starts[key]

        # Calculate total swap bay capacity × time
        total_capacity_minutes = 0.0
        for station_id, swap_bays in self.station_swap_bays.items():
            total_capacity_minutes += swap_bays * total_sim_time

        if total_capacity_minutes <= 0:
            return 0.0

        # Sum all busy time
        total_busy_time = sum(station_busy_time.values())

        return total_busy_time / total_capacity_minutes

    def _compute_idle_inventory(self) -> float:
        """
        Compute time-weighted average of idle inventory.

        Returns:
            Average idle inventory count
        """
        if not self.start_time or not self.end_time:
            return 0.0

        total_sim_time = (self.end_time - self.start_time).total_seconds() / 60.0  # minutes
        if total_sim_time <= 0:
            return 0.0

        # Track inventory changes per station
        station_inventory: Dict[str, int] = {}
        station_inventory_time: Dict[str, float] = {}  # station_id -> last_change_time
        station_idle_sum: Dict[str, float] = {}  # station_id -> sum of (idle_count × duration)

        # Initialize from station configs
        for station in self.stations:
            station_id = station.get("station_id")
            if station_id:
                station_inventory[station_id] = station.get("inventory_current", 0)
                station_inventory_time[station_id] = 0.0
                station_idle_sum[station_id] = 0.0

        # Process events chronologically
        sorted_events = sorted(self.events, key=lambda e: e.get("timestamp", ""))

        for event in sorted_events:
            event_type = event.get("event_type")
            station_id = event.get("station_id")
            timestamp_str = event.get("timestamp")
            metadata = event.get("metadata", {})

            if not station_id or not timestamp_str:
                continue

            try:
                # Parse timestamp (handle both timezone-aware and naive)
                if timestamp_str.endswith('Z'):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
                
                # Make start_time timezone-aware if timestamp is timezone-aware
                start_time = self.start_time
                if timestamp.tzinfo is not None and start_time.tzinfo is None:
                    # Make start_time timezone-naive for comparison
                    timestamp = timestamp.replace(tzinfo=None)
                
                current_time_minutes = (timestamp - start_time).total_seconds() / 60.0
            except (ValueError, AttributeError):
                continue

            if station_id not in station_inventory:
                continue

            # Update idle sum for time since last change
            last_time = station_inventory_time[station_id]
            duration = current_time_minutes - last_time
            current_inventory = station_inventory[station_id]
            station_idle_sum[station_id] += current_inventory * duration
            station_inventory_time[station_id] = current_time_minutes

            # Update inventory based on event
            if event_type == "swap_start":
                # Battery consumed
                station_inventory[station_id] = max(0, station_inventory[station_id] - 1)
            elif event_type == "charge_complete":
                # Battery added back
                station_inventory[station_id] = station_inventory[station_id] + 1
            elif event_type == "replenishment_complete":
                # Replenishment adds batteries
                replenishment_amount = metadata.get("replenishment_amount", 0)
                station_inventory[station_id] = station_inventory[station_id] + replenishment_amount

        # Finalize: add remaining time
        final_time_minutes = (self.end_time - self.start_time).total_seconds() / 60.0
        for station_id in station_inventory:
            last_time = station_inventory_time[station_id]
            duration = final_time_minutes - last_time
            current_inventory = station_inventory[station_id]
            station_idle_sum[station_id] += current_inventory * duration

        # Calculate average
        total_idle_sum = sum(station_idle_sum.values())
        return total_idle_sum / total_sim_time if total_sim_time > 0 else 0.0



    def _compute_financials(self) -> dict:
        """
        Compute financial metrics from swap events.
        
        Returns:
            Dictionary containing financial aggregates
        """
        total_revenue = 0.0
        primary_swaps = 0
        secondary_swaps = 0
        total_penalties = 0.0
        total_service_charges = 0.0
        
        for event in self.events:
            if event.get("event_type") == "swap_complete":
                # Check for financials in metadata
                metadata = event.get("metadata", {})
                fin = metadata.get("financials", {})
                
                # Sum up revenue elements
                total_revenue += fin.get("revenue", 0.0)
                
                # Count swap types
                if fin.get("type") == "primary":
                    primary_swaps += 1
                elif fin.get("type") == "secondary":
                    secondary_swaps += 1
                
                total_penalties += fin.get("penalty", 0.0)
                total_service_charges += fin.get("service_charge", 0.0)
                
        return {
            "total_revenue": total_revenue,
            "primary_swaps": primary_swaps,
            "secondary_swaps": secondary_swaps,
            "total_penalties": total_penalties,
            "total_service_charges": total_service_charges
        }

    def snapshot(self) -> dict:
        """
        Create a snapshot of computed KPIs.

        Returns:
            Dictionary containing all KPIs
        """
        return self.compute()

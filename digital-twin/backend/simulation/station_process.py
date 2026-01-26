"""
Station Process for Digital Twin Simulation Platform.

Manages station operations using SimPy resources for swap bays and chargers.
"""

from typing import Optional
import simpy
from .rider import Rider, RiderStatus
from .inventory_manager import InventoryManager
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
        inventory: int,
        inventory_manager: InventoryManager,
        event_logger: EventLogger
    ):
        """
        Initialize station process.

        Args:
            station_id: Station identifier
            env: SimPy environment
            swap_bays_count: Number of swap bays available
            chargers_count: Number of chargers available
            inventory: Initial battery inventory count
            inventory_manager: InventoryManager instance
            event_logger: EventLogger instance for logging events
        """
        self.station_id = station_id
        self.env = env
        self.swap_bays = simpy.Resource(env, capacity=swap_bays_count)
        self.chargers = simpy.Resource(env, capacity=chargers_count)
        self.inventory = inventory
        self.inventory_manager = inventory_manager
        self.event_logger = event_logger

        # TODO: Add priority queue for riders
        # TODO: Add fairness policies
        # TODO: Add service time distributions

    def request_swap(self, rider: Rider) -> simpy.events.Process:
        """
        Request a swap operation for a rider.

        Args:
            rider: Rider instance requesting swap

        Returns:
            SimPy process for swap operation

        TODO: Add queue priority logic
        TODO: Add fairness policies
        """
        return self.env.process(self._process_swap(rider, self.env))

    def _process_swap(self, rider: Rider, env: simpy.Environment):
        """
        Process a battery swap operation for a rider.

        Args:
            rider: Rider instance to serve
            env: SimPy environment

        Yields:
            SimPy events

        TODO: Add service time variation
        TODO: Add failure handling
        """
        # Check inventory availability
        if self.inventory <= 0:
            rider.status = RiderStatus.LOST
            self.event_logger.log_event(
                event_type="inventory_stockout",
                station_id=self.station_id,
                rider_id=rider.rider_id,
                metadata={"queue_length": len(self.swap_bays.queue)}
            )
            return

        # Consume battery from inventory
        if not self.inventory_manager.consume(self.station_id):
            rider.status = RiderStatus.LOST
            self.event_logger.log_event(
                event_type="inventory_stockout",
                station_id=self.station_id,
                rider_id=rider.rider_id
            )
            return

        self.inventory -= 1

        # Log swap start
        self.event_logger.log_event(
            event_type="swap_start",
            station_id=self.station_id,
            rider_id=rider.rider_id,
            metadata={
                "inventory": self.inventory,
                "queue_length": len(self.swap_bays.queue)
            }
        )

        # Process swap (simulate service time)
        # TODO: Use configurable service time distribution
        service_time = 5.0  # minutes - placeholder
        yield env.timeout(service_time)

        # Log swap completion
        self.event_logger.log_event(
            event_type="swap_complete",
            station_id=self.station_id,
            rider_id=rider.rider_id,
            metadata={"inventory": self.inventory}
        )

        # Trigger battery charging for the consumed battery
        env.process(self._charge_battery(env))

    def _charge_battery(self, env: simpy.Environment):
        """
        Charge a battery using a charger.

        Args:
            env: SimPy environment

        Yields:
            SimPy events

        TODO: Add charging time variation
        TODO: Add charger failure handling
        """
        # Request charger
        with self.chargers.request() as charger_request:
            yield charger_request

            self.event_logger.log_event(
                event_type="charge_start",
                station_id=self.station_id,
                metadata={
                    "chargers_available": self.chargers.capacity - len(self.chargers.queue),
                    "inventory": self.inventory
                }
            )

            # Charge battery (simulate charge time)
            # TODO: Use configurable charge time distribution
            charge_time = 30.0  # minutes - placeholder
            yield env.timeout(charge_time)

            # Battery charged - add back to inventory
            self.inventory += 1
            self.event_logger.log_event(
                event_type="charge_complete",
                station_id=self.station_id,
                metadata={"inventory": self.inventory}
            )

    def snapshot(self) -> dict:
        """
        Create a snapshot of station process state.

        Returns:
            Dictionary containing station process attributes
        """
        return {
            "station_id": self.station_id,
            "swap_bays_capacity": self.swap_bays.capacity,
            "swap_bays_available": self.swap_bays.capacity - len(self.swap_bays.queue),
            "swap_bays_in_use": self.swap_bays.capacity - self.swap_bays.count,
            "chargers_capacity": self.chargers.capacity,
            "chargers_available": self.chargers.capacity - len(self.chargers.queue),
            "chargers_in_use": self.chargers.capacity - self.chargers.count,
            "inventory": self.inventory,
            "queue_length": len(self.swap_bays.queue)
        }

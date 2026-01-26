"""
Rider model for Digital Twin Simulation Platform.

Represents a rider in the battery swap network simulation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
import simpy
from .event_logger import EventLogger


class RiderStatus(Enum):
    """Rider status enumeration."""
    WAITING = "waiting"
    SERVED = "served"
    LOST = "lost"
    REROUTED = "rerouted"


class Rider:
    """
    Represents a rider requesting battery swap service.

    Tracks rider state and emits events through EventLogger.
    """

    def __init__(
        self,
        rider_id: str,
        arrival_time: datetime,
        target_station_id: str,
        patience_timeout: float,
        event_logger: EventLogger
    ):
        """
        Initialize a rider.

        Args:
            rider_id: Unique rider identifier
            arrival_time: Time when rider arrived
            target_station_id: Station assigned to serve this rider
            patience_timeout: Maximum wait time in minutes before abandonment
            event_logger: EventLogger instance for logging events
        """
        self.rider_id = rider_id
        self.arrival_time = arrival_time
        self.target_station_id = target_station_id
        self.patience_timeout = patience_timeout
        self.status = RiderStatus.WAITING
        self.event_logger = event_logger
        self.start_service_time: Optional[datetime] = None
        self.end_service_time: Optional[datetime] = None

        # TODO: Add abandonment threshold configuration
        # TODO: Add reroute eligibility flags

    def process(self, env: simpy.Environment, station_process):
        """
        Process rider lifecycle through the simulation.

        Args:
            env: SimPy environment
            station_process: StationProcess instance to request service from

        Yields:
            SimPy events

        TODO: Add priority queue support
        TODO: Add dynamic reroute logic
        TODO: Add abandonment reason tracking
        """
        # Log rider arrival
        self.event_logger.log_event(
            event_type="rider_arrival",
            station_id=self.target_station_id,
            rider_id=self.rider_id,
            metadata={"arrival_time": self.arrival_time.isoformat()}
        )

        # Request swap bay with patience timeout
        wait_start_time = env.now
        self.event_logger.log_event(
            event_type="queue_join",
            station_id=self.target_station_id,
            rider_id=self.rider_id,
            metadata={"queue_length": len(station_process.swap_bays.queue)}
        )

        # Request swap bay with timeout
        with station_process.swap_bays.request() as bay_request:
            # Wait for bay or timeout
            timeout_event = env.timeout(self.patience_timeout)
            result = yield bay_request | timeout_event

            if timeout_event in result:
                # Patience exceeded - rider abandons
                self.status = RiderStatus.LOST
                wait_time_minutes = env.now - wait_start_time
                self.event_logger.log_event(
                    event_type="lost_swap",
                    station_id=self.target_station_id,
                    rider_id=self.rider_id,
                    metadata={"abandonment_reason": "patience_timeout", "wait_time": wait_time_minutes}
                )
                return

            # Got swap bay - process swap
            # Store simulation time for datetime conversion
            self._service_start_sim = env.now
            yield env.process(station_process._process_swap(self, env))

            if self.status != RiderStatus.LOST:
                self.status = RiderStatus.SERVED
                self._service_end_sim = env.now
                # swap_complete event is logged in station_process._process_swap

    def snapshot(self) -> dict:
        """
        Create a snapshot of rider state.

        Returns:
            Dictionary containing rider attributes
        """
        return {
            "rider_id": self.rider_id,
            "arrival_time": self.arrival_time.isoformat(),
            "target_station_id": self.target_station_id,
            "start_service_time": (
                self.start_service_time.isoformat()
                if self.start_service_time else None
            ),
            "end_service_time": (
                self.end_service_time.isoformat()
                if self.end_service_time else None
            ),
            "status": self.status.value
        }

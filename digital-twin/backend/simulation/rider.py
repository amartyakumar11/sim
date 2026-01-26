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
        assigned_station_id: str,
        event_logger: EventLogger
    ):
        """
        Initialize a rider.

        Args:
            rider_id: Unique rider identifier
            arrival_time: Time when rider arrived
            assigned_station_id: Station assigned to serve this rider
            event_logger: EventLogger instance for logging events
        """
        self.id = rider_id
        self.arrival_time = arrival_time
        self.assigned_station_id = assigned_station_id
        self.start_service_time: Optional[datetime] = None
        self.end_service_time: Optional[datetime] = None
        self.status = RiderStatus.WAITING
        self.event_logger = event_logger

        # TODO: Add timeout configuration
        # TODO: Add abandonment threshold
        # TODO: Add reroute eligibility flags

        # Log rider creation
        self.event_logger.log_event(
            event_type="rider_arrival",
            station_id=assigned_station_id,
            rider_id=rider_id,
            metadata={"arrival_time": arrival_time.isoformat()}
        )

    def wait(self, env: simpy.Environment):
        """
        Simulate rider waiting in queue.

        Args:
            env: SimPy environment

        Yields:
            SimPy events (placeholder)

        TODO: Implement actual queue waiting logic
        TODO: Add timeout handling
        TODO: Add abandonment logic (if wait time exceeds threshold)
        TODO: Emit queue_join event
        TODO: Track wait start time
        """
        # TODO: Log queue_join event
        # TODO: Wait for service availability
        # TODO: Check timeout periodically
        # TODO: Handle abandonment if timeout exceeded
        # TODO: Yield to SimPy environment

        self.event_logger.log_event(
            event_type="queue_join",
            station_id=self.assigned_station_id,
            rider_id=self.id
        )

        # Placeholder: yield immediately (no actual waiting yet)
        yield env.timeout(0)

    def serve(self, env: simpy.Environment):
        """
        Simulate rider being served (battery swap).

        Args:
            env: SimPy environment

        Yields:
            SimPy events (placeholder)

        TODO: Implement actual service logic
        TODO: Track service start time
        TODO: Wait for swap completion
        TODO: Track service end time
        TODO: Update status to SERVED
        TODO: Emit rider_served event
        """
        # TODO: Record start_service_time
        # TODO: Wait for swap operation to complete
        # TODO: Record end_service_time
        # TODO: Calculate service duration
        # TODO: Update status to SERVED
        # TODO: Yield to SimPy environment

        self.start_service_time = datetime.fromtimestamp(env.now)
        # Placeholder: yield immediately (no actual service time yet)
        yield env.timeout(0)
        self.end_service_time = datetime.fromtimestamp(env.now)
        self.status = RiderStatus.SERVED

        self.event_logger.log_event(
            event_type="swap_complete",
            station_id=self.assigned_station_id,
            rider_id=self.id,
            metadata={
                "service_duration": (
                    (self.end_service_time - self.start_service_time).total_seconds()
                    if self.start_service_time and self.end_service_time
                    else 0
                )
            }
        )

    def mark_lost(self):
        """
        Mark rider as lost (abandoned or timed out).

        TODO: Implement abandonment logic
        TODO: Track abandonment reason
        TODO: Emit rider_lost event
        """
        # TODO: Determine abandonment reason (timeout, queue too long, etc.)
        # TODO: Update status to LOST
        # TODO: Record abandonment metrics

        self.status = RiderStatus.LOST
        self.event_logger.log_event(
            event_type="lost_swap",
            station_id=self.assigned_station_id,
            rider_id=self.id,
            metadata={"abandonment_reason": "timeout"}
        )

    def mark_rerouted(self, new_station_id: str):
        """
        Mark rider as rerouted to a different station.

        Args:
            new_station_id: New station identifier

        TODO: Implement reroute logic
        TODO: Update assigned_station_id
        TODO: Track reroute reason
        TODO: Emit rider_rerouted event
        """
        # TODO: Validate new_station_id exists
        # TODO: Update assigned_station_id
        # TODO: Update status to REROUTED
        # TODO: Record reroute metrics

        old_station_id = self.assigned_station_id
        self.assigned_station_id = new_station_id
        self.status = RiderStatus.REROUTED

        self.event_logger.log_event(
            event_type="reroute",
            station_id=new_station_id,
            rider_id=self.id,
            metadata={
                "old_station_id": old_station_id,
                "new_station_id": new_station_id
            }
        )

    def snapshot(self) -> dict:
        """
        Create a snapshot of rider state.

        Returns:
            Dictionary containing rider attributes

        TODO: Include all state information
        TODO: Calculate derived metrics (wait time, service time)
        """
        # TODO: Calculate wait_time if served
        # TODO: Calculate service_time if completed
        # TODO: Include all status information

        return {
            "rider_id": self.id,
            "arrival_time": self.arrival_time.isoformat(),
            "assigned_station_id": self.assigned_station_id,
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

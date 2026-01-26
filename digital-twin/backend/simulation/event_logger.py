"""
Event Logger for Digital Twin Simulation Platform.

Writes events in NDJSON format matching backend/schemas/event_log_schema.json.
"""

import json
import uuid
from datetime import datetime
from typing import Optional


class EventLogger:
    """
    Event logger that writes events in NDJSON format.

    Validates event types and ensures all events match the event log schema.
    """

    # Allowed event types - DO NOT MODIFY without updating schema
    ALLOWED_EVENT_TYPES = {
        "rider_arrival",
        "station_selected",
        "reroute",
        "queue_join",
        "queue_leave",
        "swap_start",
        "swap_complete",
        "lost_swap",
        "charge_start",
        "charge_complete",
        "inventory_stockout",
        "replenishment_trigger",
        "replenishment_complete",
        "charger_failure",
        "charger_repair",
        "station_down",
        "station_up",
    }

    def __init__(self, output_path: str):
        """
        Initialize the event logger.

        Args:
            output_path: Path to the output file where events will be written (NDJSON format)
        """
        self.output_path = output_path
        self.file_handle = open(output_path, 'w', encoding='utf-8')

    def log_event(
        self,
        event_type: str,
        station_id: Optional[str] = None,
        rider_id: Optional[str] = None,
        battery_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """
        Log an event to the output file in NDJSON format.

        Args:
            event_type: Type of event (must be in ALLOWED_EVENT_TYPES)
            station_id: Optional station identifier
            rider_id: Optional rider identifier
            battery_id: Optional battery identifier
            metadata: Optional dictionary with additional event data

        Raises:
            ValueError: If event_type is not in the allowed list
        """
        # Validate event type
        if event_type not in self.ALLOWED_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{event_type}'. "
                f"Must be one of: {sorted(self.ALLOWED_EVENT_TYPES)}"
            )

        # Generate event_id as UUID
        event_id = str(uuid.uuid4())

        # Generate ISO 8601 timestamp
        timestamp = datetime.utcnow().isoformat() + 'Z'

        # Build event object matching schema
        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "station_id": station_id,
            "rider_id": rider_id,
            "battery_id": battery_id,
            "metadata": metadata or {}
        }

        # Write as NDJSON (one JSON object per line)
        json_line = json.dumps(event, ensure_ascii=False)
        self.file_handle.write(json_line + '\n')
        self.file_handle.flush()  # Ensure immediate write

    def close(self):
        """Close the event log file."""
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.close()

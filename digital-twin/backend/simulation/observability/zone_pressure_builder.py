"""
Zone Pressure Builder: Compute zone-level pressure signals from events.

Pure function - no side effects, deterministic output from events.
NO ML, NO clustering - just deterministic aggregation.
"""

from typing import Dict, List
from collections import defaultdict
from datetime import datetime


def build_zone_pressure(events: List[dict], city_graph: dict) -> List[dict]:
    """
    Compute zone-level pressure scores per minute.
    
    Pressure score = count of:
    - swap_start events (active demand)
    - lost_swap events (unmet demand)
    - queue_join with low_battery metadata (battery starvation)
    
    Args:
        events: List of event dictionaries from events.ndjson
        city_graph: City graph topology (for station → zone mapping)
        
    Returns:
        List of zone pressure records, sorted by (zone, minute)
        
    Assumptions:
        - Events have timestamps in ISO 8601 format
        - Station IDs map to zones via city_graph
        - Pressure = simple event count, no weighting
    """
    # Build station ID to zone mapping
    station_to_zone = {}
    for zone_id, zone_data in city_graph.get("zones", {}).items():
        for station_id in zone_data.get("station_ids", []):
            station_to_zone[station_id] = zone_id
    
    # Track zone pressure by (zone, minute)
    zone_minute_events = defaultdict(lambda: defaultdict(list))
    
    for event in events:
        station_id = event.get("station_id")
        event_type = event.get("event_type")
        timestamp_str = event.get("timestamp")
        metadata = event.get("metadata", {})
        
        # Skip system events
        if station_id in ("SYSTEM", "NONE", None):
            continue
        
        # Map station to zone
        zone_id = station_to_zone.get(station_id)
        if not zone_id:
            continue
        
        # Parse timestamp to minute offset
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            minute_offset = dt.hour * 60 + dt.minute
        except Exception:
            continue
        
        # Track pressure-contributing events
        if event_type in ("swap_start", "lost_swap"):
            zone_minute_events[zone_id][minute_offset].append(event_type)
        elif event_type == "queue_join" and "low_battery" in metadata.get("reason", ""):
            zone_minute_events[zone_id][minute_offset].append("battery_starvation")
    
    # Compute pressure scores
    pressure_records = []
    
    for zone_id, minute_data in zone_minute_events.items():
        for minute, event_types in minute_data.items():
            # Calculate pressure score
            pressure_score = len(event_types)
            
            # Identify drivers (unique event types)
            drivers = []
            if "swap_start" in event_types:
                drivers.append("swap_congestion")
            if "lost_swap" in event_types:
                drivers.append("battery_stockout")
            if "battery_starvation" in event_types:
                drivers.append("battery_starvation")
            
            pressure_records.append({
                "zone": zone_id,
                "minute": minute,
                "pressure_score": pressure_score,
                "drivers": drivers
            })
    
    # Sort by zone, then minute (deterministic)
    pressure_records.sort(key=lambda r: (r["zone"], r["minute"]))
    
    return pressure_records

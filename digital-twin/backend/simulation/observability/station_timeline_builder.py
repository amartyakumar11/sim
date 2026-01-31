"""
Station Timeline Builder: Aggregate station-level metrics and pressure windows.

Pure function - no side effects, deterministic output from events.
"""

from typing import Dict, List
from collections import defaultdict
from datetime import datetime


def build_station_timelines(events: List[dict], city_graph: dict) -> Dict[str, dict]:
    """
    Build station timelines with swap counts and pressure windows.
    
    Aggregates per station:
    - Total swaps completed
    - Lost swaps (stockouts)
    - Minute-wise swap density
    - Pressure windows (10-min intervals exceeding median density)
    
    Args:
        events: List of event dictionaries from events.ndjson
        city_graph: City graph topology (for station → zone mapping)
        
    Returns:
        Dictionary mapping station_id to timeline summary
        
    Assumptions:
        - swap_start events indicate swap attempts
        - lost_swap events indicate failures
        - Timestamps are ISO 8601 format
        - Pressure window = 10-min interval with swap_start > median
    """
    station_timelines = {}
    
    # Build station ID to zone mapping
    station_to_zone = {}
    for zone_id, zone_data in city_graph.get("zones", {}).items():
        for station_id in zone_data.get("station_ids", []):
            station_to_zone[station_id] = zone_id
    
    # Group events by station
    events_by_station = defaultdict(list)
    for event in events:
        station_id = event.get("station_id")
        if station_id and station_id != "SYSTEM" and station_id != "NONE":
            events_by_station[station_id].append(event)
    
    # Process each station
    for station_id, station_events in events_by_station.items():
        timeline = {
            "station_id": station_id,
            "swaps_total": 0,
            "lost_swaps": 0,
            "pressure_windows": []
        }
        
        # Add zone if available
        if station_id in station_to_zone:
            timeline["zone"] = station_to_zone[station_id]
        
        # Track swap_start events by minute for density
        swap_starts_by_minute = defaultdict(int)
        
        for event in station_events:
            event_type = event.get("event_type")
            timestamp_str = event.get("timestamp")
            
            # Count swap completions
            if event_type == "swap_complete":
                timeline["swaps_total"] += 1
            
            # Count lost swaps
            elif event_type == "lost_swap":
                timeline["lost_swaps"] += 1
            
            # Track swap_start density
            elif event_type == "swap_start" and timestamp_str:
                try:
                    # Parse timestamp to get minute offset
                    # Simplified: extract minute from ISO timestamp
                    # This assumes simulation_start is known, but we'll approximate
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    minute_offset = dt.hour * 60 + dt.minute
                    swap_starts_by_minute[minute_offset] += 1
                except Exception:
                    pass
        
        # Detect pressure windows (10-min intervals above median)
        if swap_starts_by_minute:
            # Calculate median swap_start density
            densities = list(swap_starts_by_minute.values())
            densities.sort()
            median_density = densities[len(densities) // 2] if densities else 0
            
            # Find 10-minute windows above median
            # Group consecutive high-density minutes
            high_pressure_minutes = sorted([
                minute for minute, count in swap_starts_by_minute.items()
                if count > median_density
            ])
            
            # Group into 10-minute windows
            if high_pressure_minutes:
                windows = []
                start_min = high_pressure_minutes[0]
                end_min = high_pressure_minutes[0]
                
                for minute in high_pressure_minutes[1:]:
                    if minute <= end_min + 10:
                        end_min = minute
                    else:
                        # Close previous window
                        if end_min - start_min >= 10:
                            windows.append({
                                "start_minute": start_min,
                                "end_minute": end_min,
                                "reason": "swap_congestion"
                            })
                        start_min = minute
                        end_min = minute
                
                # Close final window
                if end_min - start_min >= 10:
                    windows.append({
                        "start_minute": start_min,
                        "end_minute": end_min,
                        "reason": "swap_congestion"
                    })
                
                timeline["pressure_windows"] = windows
        
        station_timelines[station_id] = timeline
    
    return station_timelines

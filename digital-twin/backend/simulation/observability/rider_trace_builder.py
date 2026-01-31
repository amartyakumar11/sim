"""
Rider Trace Builder: Reconstruct individual rider journeys from event logs.

Pure function - no side effects, deterministic output from events.
"""

from typing import Dict, List, Optional


def build_rider_traces(events: List[dict], city_graph: dict) -> Dict[str, dict]:
    """
    Reconstruct rider journeys from event logs.
    
    Groups events by rider_id and extracts:
    - Spawn zone (from rider_arrival)
    - Total swaps (count of swap_complete)
    - Swap stations visited (ordered list)
    - Total distance (if battery metadata present)
    - End state (active or lost)
    
    Args:
        events: List of event dictionaries from events.ndjson
        city_graph: City graph topology (for station → zone mapping)
        
    Returns:
        Dictionary mapping rider_id to journey summary
        
    Assumptions:
        - rider_arrival event contains spawn zone in metadata
        - swap_complete events indicate successful swaps
        - lost_swap events indicate rider termination
        - If no lost_swap, rider is considered active at end
    """
    rider_traces = {}
    
    # Build station ID to zone mapping
    station_to_zone = {}
    for zone_id, zone_data in city_graph.get("zones", {}).items():
        for station_id in zone_data.get("station_ids", []):
            station_to_zone[station_id] = zone_id
    
    # Group events by rider
    events_by_rider = {}
    for event in events:
        rider_id = event.get("rider_id")
        if not rider_id:
            continue
        
        if rider_id not in events_by_rider:
            events_by_rider[rider_id] = []
        events_by_rider[rider_id].append(event)
    
    # Process each rider's events
    for rider_id, rider_events in events_by_rider.items():
        # Sort by timestamp for deterministic ordering
        rider_events_sorted = sorted(rider_events, key=lambda e: e.get("timestamp", ""))
        
        trace = {
            "rider_id": rider_id,
            "end_state": "active"  # Default, unless lost_swap found
        }
        
        swap_stations = []
        total_swaps = 0
        spawn_zone = None
        total_distance_km = None
        
        for event in rider_events_sorted:
            event_type = event.get("event_type")
            station_id = event.get("station_id")
            metadata = event.get("metadata", {})
            
            # Extract spawn zone from rider_arrival
            if event_type == "rider_arrival" and not spawn_zone:
                spawn_zone = metadata.get("zone_id")
                if not spawn_zone and station_id != "SYSTEM":
                    # Fallback: infer zone from station
                    spawn_zone = station_to_zone.get(station_id)
            
            # Count swaps from swap_complete
            elif event_type == "swap_complete":
                total_swaps += 1
                if station_id and station_id not in swap_stations:
                    swap_stations.append(station_id)
            
            # Mark as lost if lost_swap event
            elif event_type == "lost_swap":
                trace["end_state"] = "lost"
            
            # Extract distance if available
            if "total_distance_km" in metadata:
                total_distance_km = metadata["total_distance_km"]
        
        # Populate trace
        if spawn_zone:
            trace["spawn_zone"] = spawn_zone
        
        trace["total_swaps"] = total_swaps
        
        if swap_stations:
            trace["swap_stations"] = swap_stations
        
        if total_distance_km is not None:
            trace["total_distance_km"] = total_distance_km
        
        rider_traces[rider_id] = trace
    
    return rider_traces

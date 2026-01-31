"""
Run Narrative Builder: Generate deterministic factual narrative from observability data.

Pure function - no LLM, no speculation, just facts from data.
"""

from typing import Dict, List


def build_run_narrative(
    rider_traces: Dict[str, dict],
    station_timelines: Dict[str, dict],
    zone_pressure: List[dict]
) -> str:
    """
    Generate deterministic, factual narrative about simulation run.
    
    Identifies:
    - Top pressure zone (highest total pressure score)
    - Most stressed station (most lost swaps)
    - Example affected riders
    
    Args:
        rider_traces: Output from build_rider_traces()
        station_timelines: Output from build_station_timelines()
        zone_pressure: Output from build_zone_pressure()
        
    Returns:
        Single-paragraph factual narrative
        
    Assumptions:
        - NO LLM, NO adjectives, NO speculation
        - Deterministic facts only
        - If no pressure detected, state that
    """
    lines = []
    
    # 1. Identify top pressure zone
    zone_totals = {}
    for record in zone_pressure:
        zone = record["zone"]
        score = record["pressure_score"]
        zone_totals[zone] = zone_totals.get(zone, 0) + score
    
    if zone_totals:
        top_zone = max(zone_totals.items(), key=lambda x: (x[1], x[0]))
        top_zone_id, top_zone_score = top_zone
        
        # Find pressure window for top zone
        zone_records = [r for r in zone_pressure if r["zone"] == top_zone_id]
        if zone_records:
            zone_records.sort(key=lambda r: r["minute"])
            start_min = zone_records[0]["minute"]
            end_min = zone_records[-1]["minute"]
            
            # Identify drivers
            all_drivers = set()
            for r in zone_records:
                all_drivers.update(r["drivers"])
            drivers_str = ", ".join(sorted(all_drivers))
            
            lines.append(
                f"Between minute {start_min} and {end_min}, zone {top_zone_id} "
                f"experienced sustained pressure (total score: {top_zone_score}) "
                f"driven by {drivers_str}."
            )
    else:
        lines.append("No significant zone pressure detected during simulation.")
    
    # 2. Identify most stressed station
    station_stress = [(sid, data["lost_swaps"]) for sid, data in station_timelines.items()]
    station_stress.sort(key=lambda x: (-x[1], x[0]))
    
    if station_stress and station_stress[0][1] > 0:
        stressed_station, lost_count = station_stress[0]
        station_data = station_timelines[stressed_station]
        
        # Find pressure window if exists
        pressure_windows = station_data.get("pressure_windows", [])
        if pressure_windows:
            window = pressure_windows[0]
            lines.append(
                f"Station {stressed_station} recorded {lost_count} lost swaps "
                f"during window minute {window['start_minute']}-{window['end_minute']}."
            )
        else:
            lines.append(
                f"Station {stressed_station} recorded {lost_count} lost swaps."
            )
    
    # 3. Identify example affected riders
    multi_swap_riders = [
        (rid, trace["total_swaps"])
        for rid, trace in rider_traces.items()
        if trace["total_swaps"] > 1
    ]
    multi_swap_riders.sort(key=lambda x: (-x[1], x[0]))
    
    if multi_swap_riders:
        # Mention top 2 multi-swap riders
        example_riders = multi_swap_riders[:2]
        rider_ids = [r[0] for r in example_riders]
        
        if len(rider_ids) == 1:
            lines.append(f"Rider {rider_ids[0]} required multiple swaps.")
        else:
            lines.append(f"Riders {' and '.join(rider_ids)} required multiple swaps.")
    
    # 4. Lost riders summary
    lost_riders = [rid for rid, trace in rider_traces.items() if trace["end_state"] == "lost"]
    if lost_riders:
        lines.append(f"{len(lost_riders)} riders were lost due to battery unavailability.")
    
    # Join all lines into narrative
    if not lines:
        return "Simulation completed without notable pressure events."
    
    return " ".join(lines)

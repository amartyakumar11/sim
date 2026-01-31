from typing import Dict, Any, List

def calculate_demand_heatmap(city_config: Dict[str, Any], interventions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate demand intensity for each station based on configuration and interventions.
    
    Args:
        city_config: City configuration including stations list
        interventions: Active interventions including demand multipliers
        
    Returns:
        GeoJSON FeatureCollection of points with 'intensity' property
    """
    stations = city_config.get("stations", [])
    
    # Extract multipliers
    global_mult = float(interventions.get("demand_multiplier", 1.0))
    zone_mults = interventions.get("zone_demand_multipliers", {})
    
    features = []
    
    for station in stations:
        station_id = station.get("station_id")
        zone_id = station.get("zone_id", "unknown")
        lat = station.get("lat") or station.get("latitude")
        lon = station.get("lon") or station.get("longitude")
        
        # Calculate intensity
        # Base weight is 1.0, modified by zone multiplier
        zone_mult = float(zone_mults.get(zone_id, 1.0))
        
        # Final intensity = Global * Zone
        # We don't need absolute poisson rates here, just relative weights for the heatmap
        intensity = global_mult * zone_mult
        
        features.append({
            "type": "Feature",
            "properties": {
                "station_id": station_id,
                "zone_id": zone_id,
                "intensity": intensity,
                "weight": intensity  # Alias for heatmap libraries
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        })
        
    return {
        "type": "FeatureCollection",
        "features": features
    }

#!/usr/bin/env python3
"""
Lucknow City Graph Enrichment Pipeline

Converts lucknow_stations.json (lat/lon only) into a full city graph
compatible with the simulation framework.

DETERMINISTIC - NO RANDOMNESS - OFFLINE PREPROCESSING
"""

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

# =========================================================================
# CONFIGURATION CONSTANTS
# =========================================================================

GRID_SIZE_KM = 1.5  # 1.5 km × 1.5 km grid cells for zone construction

# Zone type thresholds based on station density
ZONE_TYPE_THRESHOLDS = {
    "commercial": 8,    # >= 8 stations
    "business": 4,      # 4-7 stations
    "residential": 2,   # 2-3 stations
    "industrial": 1     # 1 station
}

# Station capacity rules by zone type
CAPACITY_RULES = {
    "commercial": {
        "swap_bays": 16,
        "chargers_total": 20,
        "swap_time_sec": 180,
        "fixed_cost_per_day": 12000,
        "traffic_factor": 1.4
    },
    "business": {
        "swap_bays": 12,
        "chargers_total": 16,
        "swap_time_sec": 210,
        "fixed_cost_per_day": 9000,
        "traffic_factor": 1.3
    },
    "residential": {
        "swap_bays": 8,
        "chargers_total": 10,
        "swap_time_sec": 240,
        "fixed_cost_per_day": 6000,
        "traffic_factor": 1.1
    },
    "industrial": {
        "swap_bays": 6,
        "chargers_total": 6,
        "swap_time_sec": 300,
        "fixed_cost_per_day": 4000,
        "traffic_factor": 1.0
    }
}

# Cost model constants
ENERGY_COST_PER_CHARGE = 45
LOST_SWAP_PENALTY = 120

# =========================================================================
# UTILITY FUNCTIONS
# =========================================================================

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two lat/lon points in kilometers."""
    R = 6371  # Earth's radius in km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def lat_lon_to_grid_cell(lat: float, lon: float, min_lat: float, min_lon: float) -> Tuple[int, int]:
    """Convert lat/lon to grid cell indices based on GRID_SIZE_KM."""
    # Approximate: 1 degree latitude ≈ 111 km
    # 1 degree longitude ≈ 111 * cos(lat) km
    
    km_per_lat_deg = 111.0
    km_per_lon_deg = 111.0 * math.cos(math.radians(lat))
    
    lat_offset_km = (lat - min_lat) * km_per_lat_deg
    lon_offset_km = (lon - min_lon) * km_per_lon_deg
    
    grid_row = int(lat_offset_km // GRID_SIZE_KM)
    grid_col = int(lon_offset_km // GRID_SIZE_KM)
    
    return (grid_row, grid_col)


def determine_zone_type(station_count: int) -> str:
    """Determine zone type based on station density."""
    if station_count >= ZONE_TYPE_THRESHOLDS["commercial"]:
        return "commercial"
    elif station_count >= ZONE_TYPE_THRESHOLDS["business"]:
        return "business"
    elif station_count >= ZONE_TYPE_THRESHOLDS["residential"]:
        return "residential"
    else:
        return "industrial"


def compute_centroid(stations: List[Dict]) -> Tuple[float, float]:
    """Compute centroid of a list of stations."""
    if not stations:
        return (0.0, 0.0)
    
    total_lat = sum(s["latitude"] for s in stations)
    total_lon = sum(s["longitude"] for s in stations)
    n = len(stations)
    
    return (total_lat / n, total_lon / n)


# =========================================================================
# MAIN ENRICHMENT PIPELINE
# =========================================================================

def load_input_stations(input_path: Path) -> List[Dict]:
    """Load and validate input station data."""
    with open(input_path, 'r', encoding='utf-8') as f:
        stations = json.load(f)
    
    # Validate structure
    for i, station in enumerate(stations):
        if "latitude" not in station or "longitude" not in station:
            raise ValueError(f"Station at index {i} missing latitude/longitude")
    
    return stations


def step1_assign_station_ids(stations: List[Dict]) -> List[Dict]:
    """
    STEP 1: Assign deterministic station IDs.
    Sort by (lat + lon) to ensure reproducibility, then assign LKO_ST_XXX.
    """
    # Sort deterministically by lat + lon
    sorted_stations = sorted(
        stations,
        key=lambda s: (s["latitude"] + s["longitude"], s["latitude"], s["longitude"])
    )
    
    enriched = []
    for idx, station in enumerate(sorted_stations):
        enriched.append({
            "original_id": station.get("id", f"UNKNOWN_{idx}"),
            "station_id": f"LKO_ST_{idx:03d}",
            "latitude": station["latitude"],
            "longitude": station["longitude"]
        })
    
    return enriched


def step2_construct_zones(stations: List[Dict]) -> Tuple[Dict[str, Dict], List[Dict]]:
    """
    STEP 2: Grid-based zone construction.
    Partition stations into 1.5km × 1.5km grid cells.
    """
    if not stations:
        return {}, stations
    
    # Find bounding box
    min_lat = min(s["latitude"] for s in stations)
    max_lat = max(s["latitude"] for s in stations)
    min_lon = min(s["longitude"] for s in stations)
    max_lon = max(s["longitude"] for s in stations)
    
    # Assign each station to a grid cell
    grid_cells: Dict[Tuple[int, int], List[Dict]] = {}
    
    for station in stations:
        cell = lat_lon_to_grid_cell(station["latitude"], station["longitude"], min_lat, min_lon)
        if cell not in grid_cells:
            grid_cells[cell] = []
        grid_cells[cell].append(station)
    
    # Sort grid cells deterministically for consistent zone IDs
    sorted_cells = sorted(grid_cells.keys())
    
    # Create zones
    zones = {}
    stations_with_zones = []
    
    for zone_idx, cell in enumerate(sorted_cells):
        zone_id = f"LKO_ZONE_{zone_idx + 1:02d}"
        cell_stations = grid_cells[cell]
        station_count = len(cell_stations)
        zone_type = determine_zone_type(station_count)
        centroid = compute_centroid(cell_stations)
        
        zones[zone_id] = {
            "zone_id": zone_id,
            "zone_type": zone_type,
            "station_count": station_count,
            "centroid_lat": centroid[0],
            "centroid_lon": centroid[1],
            "grid_cell": cell,
            "description": f"{zone_type.capitalize()} zone with {station_count} station(s)"
        }
        
        # Assign zone to each station
        for station in cell_stations:
            station_copy = station.copy()
            station_copy["zone_id"] = zone_id
            station_copy["zone_type"] = zone_type
            stations_with_zones.append(station_copy)
    
    return zones, stations_with_zones


def step3_derive_station_capacities(stations: List[Dict]) -> List[Dict]:
    """
    STEP 3: Derive operational parameters based on zone type.
    """
    enriched = []
    
    for station in stations:
        zone_type = station["zone_type"]
        rules = CAPACITY_RULES[zone_type]
        
        swap_bays = rules["swap_bays"]
        inventory_capacity = swap_bays * 2
        inventory_initial = int(inventory_capacity * 0.7)
        
        enriched_station = {
            "station_id": station["station_id"],
            "original_id": station["original_id"],
            "zone_id": station["zone_id"],
            "latitude": station["latitude"],
            "longitude": station["longitude"],
            "swap_bays": swap_bays,
            "chargers_total": rules["chargers_total"],
            "inventory_capacity": inventory_capacity,
            "inventory_initial": inventory_initial,
            "swap_time_sec": rules["swap_time_sec"],
            "queue_limit": swap_bays * 2,
            "status": "up"
        }
        
        enriched.append(enriched_station)
    
    return enriched


def step4_add_cost_model(zones: Dict[str, Dict]) -> Dict[str, Dict]:
    """
    STEP 4: Add cost model to zones.
    """
    for zone_id, zone in zones.items():
        zone_type = zone["zone_type"]
        rules = CAPACITY_RULES[zone_type]
        
        zone["cost_model"] = {
            "fixed_cost_per_day": rules["fixed_cost_per_day"],
            "energy_cost_per_charge": ENERGY_COST_PER_CHARGE,
            "lost_swap_penalty": LOST_SWAP_PENALTY
        }
    
    return zones


def step5_build_graph_edges(stations: List[Dict], zones: Dict[str, Dict]) -> List[Dict]:
    """
    STEP 5: Build directed edges.
    - Fully connect stations INSIDE the same zone
    - Connect each zone to its 2 nearest neighboring zones (centroid distance)
    """
    edges = []
    
    # Group stations by zone
    stations_by_zone: Dict[str, List[Dict]] = {}
    for station in stations:
        zone_id = station["zone_id"]
        if zone_id not in stations_by_zone:
            stations_by_zone[zone_id] = []
        stations_by_zone[zone_id].append(station)
    
    # INTRA-ZONE edges: fully connect within each zone
    for zone_id, zone_stations in stations_by_zone.items():
        zone_type = zones[zone_id]["zone_type"]
        traffic_factor = CAPACITY_RULES[zone_type]["traffic_factor"]
        
        for i, s1 in enumerate(zone_stations):
            for j, s2 in enumerate(zone_stations):
                if i != j:
                    distance_km = haversine_km(
                        s1["latitude"], s1["longitude"],
                        s2["latitude"], s2["longitude"]
                    )
                    base_travel_time_min = distance_km / 0.5  # 30 km/h average
                    
                    edges.append({
                        "from_station_id": s1["station_id"],
                        "to_station_id": s2["station_id"],
                        "distance_km": round(distance_km, 3),
                        "base_travel_time_min": round(base_travel_time_min, 2),
                        "traffic_factor": traffic_factor,
                        "edge_type": "intra_zone"
                    })
    
    # INTER-ZONE edges: connect each zone to 2 nearest neighbors
    zone_ids = sorted(zones.keys())
    zone_distances: Dict[Tuple[str, str], float] = {}
    
    for i, z1_id in enumerate(zone_ids):
        z1 = zones[z1_id]
        distances_to_others = []
        
        for z2_id in zone_ids:
            if z1_id == z2_id:
                continue
            
            z2 = zones[z2_id]
            dist = haversine_km(
                z1["centroid_lat"], z1["centroid_lon"],
                z2["centroid_lat"], z2["centroid_lon"]
            )
            distances_to_others.append((z2_id, dist))
        
        # Sort and take 2 nearest
        distances_to_others.sort(key=lambda x: x[1])
        nearest_2 = distances_to_others[:2]
        
        for z2_id, _ in nearest_2:
            # Connect one station from each zone (first by sorted station_id)
            s1_list = sorted(stations_by_zone[z1_id], key=lambda s: s["station_id"])
            s2_list = sorted(stations_by_zone[z2_id], key=lambda s: s["station_id"])
            
            s1 = s1_list[0]
            s2 = s2_list[0]
            
            distance_km = haversine_km(
                s1["latitude"], s1["longitude"],
                s2["latitude"], s2["longitude"]
            )
            
            # Average traffic factor between zones
            tf1 = CAPACITY_RULES[zones[z1_id]["zone_type"]]["traffic_factor"]
            tf2 = CAPACITY_RULES[zones[z2_id]["zone_type"]]["traffic_factor"]
            traffic_factor = round((tf1 + tf2) / 2, 2)
            
            base_travel_time_min = distance_km / 0.5
            
            # Bidirectional edges
            edges.append({
                "from_station_id": s1["station_id"],
                "to_station_id": s2["station_id"],
                "distance_km": round(distance_km, 3),
                "base_travel_time_min": round(base_travel_time_min, 2),
                "traffic_factor": traffic_factor,
                "edge_type": "inter_zone"
            })
            edges.append({
                "from_station_id": s2["station_id"],
                "to_station_id": s1["station_id"],
                "distance_km": round(distance_km, 3),
                "base_travel_time_min": round(base_travel_time_min, 2),
                "traffic_factor": traffic_factor,
                "edge_type": "inter_zone"
            })
    
    return edges


def step7_validate(stations: List[Dict], zones: Dict[str, Dict], edges: List[Dict]) -> None:
    """
    STEP 7: Validate the output before writing.
    """
    station_ids = {s["station_id"] for s in stations}
    
    # Check every station has required fields
    required_fields = [
        "station_id", "zone_id", "latitude", "longitude",
        "swap_bays", "inventory_capacity", "status"
    ]
    for station in stations:
        for field in required_fields:
            if field not in station:
                raise ValueError(f"Station {station.get('station_id', 'UNKNOWN')} missing field: {field}")
    
    # Check every station has at least 1 outgoing edge
    outgoing_edges: Dict[str, int] = {sid: 0 for sid in station_ids}
    for edge in edges:
        if edge["from_station_id"] in outgoing_edges:
            outgoing_edges[edge["from_station_id"]] += 1
    
    for sid, count in outgoing_edges.items():
        if count == 0:
            raise ValueError(f"Station {sid} has no outgoing edges")
    
    # Check all zones are reachable (at least one inter-zone edge per zone)
    zones_with_inter = set()
    for edge in edges:
        if edge["edge_type"] == "inter_zone":
            # Find zone of from_station
            for station in stations:
                if station["station_id"] == edge["from_station_id"]:
                    zones_with_inter.add(station["zone_id"])
                    break
    
    # Zones with single station might not have inter-zone if isolated
    # Just warn, don't fail for now
    for zone_id in zones:
        if zone_id not in zones_with_inter:
            print(f"Warning: Zone {zone_id} has no inter-zone connections")
    
    print(f"Validation passed: {len(stations)} stations, {len(zones)} zones, {len(edges)} edges")


def create_output_graph(
    stations: List[Dict],
    zones: Dict[str, Dict],
    edges: List[Dict]
) -> Dict[str, Any]:
    """
    STEP 6 & 8: Create the final output structure with metadata.
    """
    # Convert zones dict to list for JSON
    zones_list = []
    for zone_id in sorted(zones.keys()):
        zone = zones[zone_id]
        zones_list.append({
            "zone_id": zone["zone_id"],
            "zone_type": zone["zone_type"],
            "description": zone["description"],
            "station_count": zone["station_count"],
            "centroid": {
                "latitude": round(zone["centroid_lat"], 6),
                "longitude": round(zone["centroid_lon"], 6)
            },
            "cost_model": zone["cost_model"]
        })
    
    # Sort edges deterministically
    sorted_edges = sorted(edges, key=lambda e: (e["from_station_id"], e["to_station_id"]))
    
    # Sort stations deterministically
    sorted_stations = sorted(stations, key=lambda s: s["station_id"])
    
    # Clean up station output (remove zone_type helper field)
    output_stations = []
    for s in sorted_stations:
        output_stations.append({
            "station_id": s["station_id"],
            "original_id": s["original_id"],
            "zone_id": s["zone_id"],
            "latitude": round(s["latitude"], 6),
            "longitude": round(s["longitude"], 6),
            "swap_bays": s["swap_bays"],
            "chargers_total": s["chargers_total"],
            "inventory_capacity": s["inventory_capacity"],
            "inventory_initial": s["inventory_initial"],
            "swap_time_sec": s["swap_time_sec"],
            "queue_limit": s["queue_limit"],
            "status": s["status"]
        })
    
    intra_edges = sum(1 for e in sorted_edges if e["edge_type"] == "intra_zone")
    inter_edges = sum(1 for e in sorted_edges if e["edge_type"] == "inter_zone")
    
    output = {
        "metadata": {
            "city": "Lucknow",
            "source": "Battery Smart (geometry only)",
            "enrichment": "deterministic rule-based",
            "graph_version": "1.0.0",
            "total_stations": len(output_stations),
            "total_zones": len(zones_list),
            "total_edges": len(sorted_edges),
            "intra_zone_edges": intra_edges,
            "inter_zone_edges": inter_edges,
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        "zones": zones_list,
        "stations": output_stations,
        "edges": sorted_edges,
        "graph_properties": {
            "is_directed": True,
            "grid_size_km": GRID_SIZE_KM,
            "energy_cost_per_charge": ENERGY_COST_PER_CHARGE,
            "lost_swap_penalty": LOST_SWAP_PENALTY
        }
    }
    
    return output


def main():
    """Main entry point for the enrichment pipeline."""
    # Paths
    script_dir = Path(__file__).parent
    input_path = script_dir.parent / "data" / "lucknow_stations.json"
    output_path = script_dir / "city_graph_lucknow.json"
    
    print(f"Loading input: {input_path}")
    stations = load_input_stations(input_path)
    print(f"Loaded {len(stations)} stations")
    
    print("Step 1: Assigning station IDs...")
    stations = step1_assign_station_ids(stations)
    
    print("Step 2: Constructing zones...")
    zones, stations = step2_construct_zones(stations)
    print(f"Created {len(zones)} zones")
    
    print("Step 3: Deriving station capacities...")
    stations = step3_derive_station_capacities(stations)
    
    print("Step 4: Adding cost model...")
    zones = step4_add_cost_model(zones)
    
    print("Step 5: Building graph edges...")
    edges = step5_build_graph_edges(stations, zones)
    print(f"Created {len(edges)} edges")
    
    print("Step 7: Validating...")
    step7_validate(stations, zones, edges)
    
    print("Step 8: Creating output graph...")
    output = create_output_graph(stations, zones, edges)
    
    print(f"Writing output: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("Done!")


if __name__ == "__main__":
    main()

"""
Test NetworkGraph load_topology, connectivity validation, and clone functionality.

Run: python test_network_graph_loader.py
"""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.network_graph import NetworkGraph



def test_load_baseline_graph_success():
    """Test loading city_graph_baseline.json successfully."""
    # Load baseline graph
    graph_path = os.path.join(
        os.path.dirname(__file__),
        'simulation',
        'city_graph_baseline.json'
    )
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_config = json.load(f)
    
    # Create graph and load topology
    network_graph = NetworkGraph()
    network_graph.load_topology(graph_config)
    
    # Assert correct number of stations added
    assert network_graph.graph.number_of_nodes() == 25, \
        f"Expected 25 stations, got {network_graph.graph.number_of_nodes()}"
    
    # Assert correct number of edges added
    assert network_graph.graph.number_of_edges() == 31, \
        f"Expected 31 edges, got {network_graph.graph.number_of_edges()}"
    
    # Assert all 5 zones present in metadata
    zones = network_graph.graph.graph.get("zones", {})
    assert len(zones) == 5, f"Expected 5 zones, got {len(zones)}"
    
    expected_zones = {
        "Z_DOWNTOWN", "Z_INDUSTRIAL", "Z_RESIDENTIAL_NORTH", 
        "Z_RESIDENTIAL_SOUTH", "Z_AIRPORT"
    }
    assert set(zones.keys()) == expected_zones, \
        f"Zone IDs mismatch: {set(zones.keys())} vs {expected_zones}"
    
    # Assert each zone has station_ids populated
    for zone_id, zone_data in zones.items():
        assert "station_ids" in zone_data, f"Zone {zone_id} missing station_ids"
        assert len(zone_data["station_ids"]) > 0, f"Zone {zone_id} has no stations"
    
    print("✅ test_load_baseline_graph_success passed")


def test_zone_level_connectivity():
    """Test zone-level connectivity validation."""
    graph_path = os.path.join(
        os.path.dirname(__file__),
        'simulation',
        'city_graph_baseline.json'
    )
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_config = json.load(f)
    
    network_graph = NetworkGraph()
    network_graph.load_topology(graph_config)
    
    # Verify that each zone connects to at least one other zone
    zones = network_graph.graph.graph.get("zones", {})
    zone_connections = {zone_id: set() for zone_id in zones.keys()}
    
    for from_station, to_station in network_graph.graph.edges():
        from_zone = network_graph.graph.nodes[from_station].get("zone_id")
        to_zone = network_graph.graph.nodes[to_station].get("zone_id")
        
        if from_zone and to_zone and from_zone != to_zone:
            zone_connections[from_zone].add(to_zone)
    
    # Assert all zones have at least one inter-zone connection
    for zone_id, connections in zone_connections.items():
        assert len(connections) > 0, \
            f"Zone {zone_id} is isolated (no inter-zone connections)"
    
    print("✅ test_zone_level_connectivity passed")


def test_clone_creates_independent_copy():
    """Test that clone() creates an independent copy."""
    graph_path = os.path.join(
        os.path.dirname(__file__),
        'simulation',
        'city_graph_baseline.json'
    )
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_config = json.load(f)
    
    # Load baseline graph
    network_graph = NetworkGraph()
    network_graph.load_topology(graph_config)
    
    baseline_node_count = network_graph.graph.number_of_nodes()
    
    # Clone the graph
    cloned_graph = network_graph.clone()
    
    # Add a new station node to the clone
    cloned_graph.graph.add_node(
        "ST_TEST_001",
        zone_id="Z_DOWNTOWN",
        swap_bays=5,
        inventory_capacity=50,
        status="up",
        station=None
    )
    
    # Assert baseline graph unchanged
    assert network_graph.graph.number_of_nodes() == baseline_node_count, \
        "Baseline graph was modified when clone was changed"
    
    # Assert clone has new station
    assert cloned_graph.graph.number_of_nodes() == baseline_node_count + 1, \
        "Clone does not have the new station"
    
    assert "ST_TEST_001" in cloned_graph.graph.nodes(), \
        "New station not found in clone"
    
    assert "ST_TEST_001" not in network_graph.graph.nodes(), \
        "New station incorrectly appears in baseline graph"
    
    # Verify zone metadata is also deep copied
    cloned_graph.graph.graph["zones"]["Z_DOWNTOWN"]["station_ids"].append("ST_TEST_001")
    
    assert "ST_TEST_001" not in network_graph.graph.graph["zones"]["Z_DOWNTOWN"]["station_ids"], \
        "Zone metadata not deep copied"
    
    print("✅ test_clone_creates_independent_copy passed")


def test_invalid_topology_raises_error():
    """Test that invalid topology config raises appropriate errors."""
    network_graph = NetworkGraph()
    
    # Test missing zones key
    with pytest.raises(ValueError, match="must contain 'zones' key"):
        network_graph.load_topology({"stations": [], "edges": []})
    
    # Test missing stations key
    with pytest.raises(ValueError, match="must contain 'stations' key"):
        network_graph.load_topology({"zones": [], "edges": []})
    
    # Test missing edges key
    with pytest.raises(ValueError, match="must contain 'edges' key"):
        network_graph.load_topology({"zones": [], "stations": []})
    
    # Test station referencing unknown zone
    with pytest.raises(ValueError, match="references unknown zone"):
        network_graph.load_topology({
            "zones": [{"zone_id": "Z_TEST"}],
            "stations": [{"station_id": "ST_001", "zone_id": "Z_UNKNOWN"}],
            "edges": []
        })
    
    print("✅ test_invalid_topology_raises_error passed")


def test_snapshot_includes_zone_data():
    """Test that snapshot() includes zone data and connectivity."""
    graph_path = os.path.join(
        os.path.dirname(__file__),
        'simulation',
        'city_graph_baseline.json'
    )
    
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_config = json.load(f)
    
    network_graph = NetworkGraph()
    network_graph.load_topology(graph_config)
    
    snapshot = network_graph.snapshot()
    
    # Assert zones included
    assert "zones" in snapshot, "Snapshot missing zones"
    assert len(snapshot["zones"]) == 5, f"Expected 5 zones in snapshot, got {len(snapshot['zones'])}"
    
    # Assert edge counts included
    assert "intra_zone_edges" in snapshot, "Snapshot missing intra_zone_edges"
    assert "inter_zone_edges" in snapshot, "Snapshot missing inter_zone_edges"
    assert snapshot["intra_zone_edges"] + snapshot["inter_zone_edges"] == 31, \
        "Edge counts don't sum to total edges"
    
    # Assert zone connectivity matrix included
    assert "zone_connectivity" in snapshot, "Snapshot missing zone_connectivity"
    
    print("✅ test_snapshot_includes_zone_data passed")


if __name__ == "__main__":
    # Run tests
    test_load_baseline_graph_success()
    test_zone_level_connectivity()
    test_clone_creates_independent_copy()
    test_invalid_topology_raises_error()
    test_snapshot_includes_zone_data()
    print("\n🎉 All tests passed!")

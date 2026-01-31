"""
Test ScenarioInterventionEngine: Verify deterministic interventions.

Tests intervention application, graph immutability, and intervention types.

Run: python test_scenario_intervention.py
"""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.scenario_intervention_engine import (
    ScenarioInterventionEngine,
    Intervention,
    InterventionType,
    create_intervention
)
from simulation.network_graph import NetworkGraph


def create_test_graph():
    """Create simple test graph."""
    graph = NetworkGraph()
    
    topology = {
        "zones": [
            {"zone_id": "zone_01", "zone_name": "Commercial District", "description": "commercial area"},
            {"zone_id": "zone_02", "zone_name": "Residential Area", "description": "residential area"}
        ],
        "stations": [
            {"station_id": "ST_01_01", "zone_id": "zone_01", "swap_bays": 5, "chargers_total": 5, "inventory_current": 40, "swap_time_sec": 300, "queue_limit": 10},
            {"station_id": "ST_01_02", "zone_id": "zone_01", "swap_bays": 5, "chargers_total": 5, "inventory_current": 40, "swap_time_sec": 300, "queue_limit": 10},
            {"station_id": "ST_02_01", "zone_id": "zone_02", "swap_bays": 5, "chargers_total": 5, "inventory_current": 40, "swap_time_sec": 300, "queue_limit": 10}
        ],
        "edges": [
            {"from_station_id": "ST_01_01", "to_station_id": "ST_01_02", "weight": 1.0},
            {"from_station_id": "ST_01_02", "to_station_id": "ST_01_01", "weight": 1.0},
            {"from_station_id": "ST_01_01", "to_station_id": "ST_02_01", "weight": 2.0},
            {"from_station_id": "ST_02_01", "to_station_id": "ST_01_01", "weight": 2.0},
            {"from_station_id": "ST_01_02", "to_station_id": "ST_02_01", "weight": 2.0},
            {"from_station_id": "ST_02_01", "to_station_id": "ST_01_02", "weight": 2.0}
        ]
    }
    
    graph.load_topology(topology)
    return graph


def test_intervention_engine_init():
    """Test intervention engine initializes."""
    engine = ScenarioInterventionEngine()
    assert engine is not None
    print("✅ test_intervention_engine_init passed")


def test_baseline_immutability():
    """Test baseline graph is never modified."""
    baseline = create_test_graph()
    engine = ScenarioInterventionEngine()
    
    # Get initial node count
    initial_node_count = baseline.graph.number_of_nodes()
    
    # Apply intervention
    intervention = create_intervention(
        "add_station",
        "ST_NEW_01",
        zone_id="zone_01",
        swap_bays=10
    )
    
    intervention_graph = engine.apply(baseline, intervention)
    
    # Verify baseline unchanged
    assert baseline.graph.number_of_nodes() == initial_node_count
    assert "ST_NEW_01" not in baseline.graph.nodes()
    
    # Verify intervention graph changed
    assert intervention_graph.graph.number_of_nodes() == initial_node_count + 1
    assert "ST_NEW_01" in intervention_graph.graph.nodes()
    
    print("✅ test_baseline_immutability passed")


def test_add_station_intervention():
    """Test adding new station."""
    baseline = create_test_graph()
    engine = ScenarioInterventionEngine()
    
    intervention = create_intervention(
        "add_station",
        "ST_NEW_01",
        zone_id="zone_01",
        swap_bays=10,
        chargers_total=15,
        inventory_current=50
    )
    
    result = engine.apply(baseline, intervention)
    
    # Verify station added
    assert "ST_NEW_01" in result.graph.nodes()
    node_data = result.graph.nodes["ST_NEW_01"]
    assert node_data["zone_id"] == "zone_01"
    assert node_data["swap_bays"] == 10
    assert node_data["chargers_total"] == 15
    assert node_data["inventory_current"] == 50
    
    # Verify station added to zone
    zones = result.graph.graph["zones"]
    assert "ST_NEW_01" in zones["zone_01"]["station_ids"]
    
    print("✅ test_add_station_intervention passed")


def test_remove_station_intervention():
    """Test removing existing station."""
    baseline = create_test_graph()
    engine = ScenarioInterventionEngine()
    
    intervention = Intervention(
        InterventionType.REMOVE_STATION,
        "ST_01_02"
    )
    
    result = engine.apply(baseline, intervention)
    
    # Verify station removed
    assert "ST_01_02" not in result.graph.nodes()
    
    # Verify station removed from zone
    zones = result.graph.graph["zones"]
    assert "ST_01_02" not in zones["zone_01"]["station_ids"]
    
    print("✅ test_remove_station_intervention passed")


def test_modify_capacity_intervention():
    """Test modifying station capacity."""
    baseline = create_test_graph()
    engine = ScenarioInterventionEngine()
    
    intervention = create_intervention(
        "modify_capacity",
        "ST_01_01",
        swap_bays=20,
        inventory_current=100
    )
    
    result = engine.apply(baseline, intervention)
    
    # Verify capacity modified
    node_data = result.graph.nodes["ST_01_01"]
    assert node_data["swap_bays"] == 20
    assert node_data["inventory_current"] == 100
    
    print("✅ test_modify_capacity_intervention passed")


def test_modify_swap_time_intervention():
    """Test modifying swap time."""
    baseline = create_test_graph()
    engine = ScenarioInterventionEngine()
    
    intervention = create_intervention(
        "modify_swap_time",
        "ST_01_01",
        swap_time_sec=180
    )
    
    result = engine.apply(baseline, intervention)
    
    # Verify swap time modified
    node_data = result.graph.nodes["ST_01_01"]
    assert node_data["swap_time_sec"] == 180
    
    print("✅ test_modify_swap_time_intervention passed")


def test_multiple_interventions():
    """Test applying multiple interventions in sequence."""
    baseline = create_test_graph()
    engine = ScenarioInterventionEngine()
    
    interventions = [
        create_intervention("add_station", "ST_NEW_01", zone_id="zone_02", swap_bays=8),
        create_intervention("modify_capacity", "ST_01_01", swap_bays=15),
        create_intervention("remove_station", "ST_02_01")
    ]
    
    result = engine.apply(baseline, interventions)
    
    # Verify all interventions applied
    assert "ST_NEW_01" in result.graph.nodes()
    assert result.graph.nodes["ST_01_01"]["swap_bays"] == 15
    assert "ST_02_01" not in result.graph.nodes()
    
    # Verify baseline unchanged
    assert "ST_NEW_01" not in baseline.graph.nodes()
    assert baseline.graph.nodes["ST_01_01"]["swap_bays"] == 5  # Original value
    assert "ST_02_01" in baseline.graph.nodes()
    
    print("✅ test_multiple_interventions passed")


def test_deterministic_interventions():
    """Test same intervention produces same result."""
    baseline = create_test_graph()
    engine = ScenarioInterventionEngine()
    
    intervention = create_intervention(
        "add_station",
        "ST_NEW_01",
        zone_id="zone_01",
        swap_bays=10
    )
    
    # Apply twice
    result1 = engine.apply(baseline, intervention)
    result2 = engine.apply(baseline, intervention)
    
    # Verify identical results
    assert result1.graph.number_of_nodes() == result2.graph.number_of_nodes()
    assert "ST_NEW_01" in result1.graph.nodes()
    assert "ST_NEW_01" in result2.graph.nodes()
    assert result1.graph.nodes["ST_NEW_01"]["swap_bays"] == result2.graph.nodes["ST_NEW_01"]["swap_bays"]
    
    print("✅ test_deterministic_interventions passed")


if __name__ == "__main__":
    # Run tests
    test_intervention_engine_init()
    test_baseline_immutability()
    test_add_station_intervention()
    test_remove_station_intervention()
    test_modify_capacity_intervention()
    test_modify_swap_time_intervention()
    test_multiple_interventions()
    test_deterministic_interventions()
    print("\n🎉 All scenario intervention tests passed!")

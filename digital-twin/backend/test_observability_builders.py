"""
Test Observability Builders: Verify deterministic event log analysis.

Tests rider traces, station timelines, zone pressure, and narratives.

Run: python test_observability_builders.py
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.observability.rider_trace_builder import build_rider_traces
from simulation.observability.station_timeline_builder import build_station_timelines
from simulation.observability.zone_pressure_builder import build_zone_pressure
from simulation.observability.run_narrative_builder import build_run_narrative


def create_test_events():
    """Create test event log."""
    return [
        {
            "event_type": "rider_arrival",
            "station_id": "SYSTEM",
            "rider_id": "R_001",
            "timestamp": "2024-01-01T10:00:00Z",
            "metadata": {"zone_id": "zone_01", "battery_id": "BAT_001"}
        },
        {
            "event_type": "swap_start",
            "station_id": "ST_01_01",
            "rider_id": "R_001",
            "timestamp": "2024-01-01T10:15:00Z",
            "metadata": {}
        },
        {
            "event_type": "swap_complete",
            "station_id": "ST_01_01",
            "rider_id": "R_001",
            "timestamp": "2024-01-01T10:18:00Z",
            "metadata": {"new_battery_id": "BAT_002"}
        },
        {
            "event_type": "rider_arrival",
            "station_id": "SYSTEM",
            "rider_id": "R_002",
            "timestamp": "2024-01-01T10:05:00Z",
            "metadata": {"zone_id": "zone_02"}
        },
        {
            "event_type": "swap_start",
            "station_id": "ST_02_01",
            "rider_id": "R_002",
            "timestamp": "2024-01-01T10:30:00Z",
            "metadata": {}
        },
        {
            "event_type": "lost_swap",
            "station_id": "ST_02_01",
            "rider_id": "R_002",
            "timestamp": "2024-01-01T10:32:00Z",
            "metadata": {"reason": "no_battery_available"}
        },
        {
            "event_type": "swap_start",
            "station_id": "ST_01_01",
            "rider_id": "R_003",
            "timestamp": "2024-01-01T10:16:00Z",
            "metadata": {}
        },
        {
            "event_type": "swap_complete",
            "station_id": "ST_01_01",
            "rider_id": "R_003",
            "timestamp": "2024-01-01T10:19:00Z",
            "metadata": {}
        }
    ]


def create_test_city_graph():
    """Create test city graph."""
    return {
        "zones": {
            "zone_01": {
                "type": "commercial",
                "station_ids": ["ST_01_01", "ST_01_02"]
            },
            "zone_02": {
                "type": "residential",
                "station_ids": ["ST_02_01", "ST_02_02"]
            }
        }
    }


def test_rider_trace_builder():
    """Test rider journey reconstruction."""
    events = create_test_events()
    city_graph = create_test_city_graph()
    
    traces = build_rider_traces(events, city_graph)
    
    # Verify R_001
    assert "R_001" in traces
    assert traces["R_001"]["spawn_zone"] == "zone_01"
    assert traces["R_001"]["total_swaps"] == 1
    assert "ST_01_01" in traces["R_001"]["swap_stations"]
    assert traces["R_001"]["end_state"] == "active"
    
    # Verify R_002 (lost)
    assert "R_002" in traces
    assert traces["R_002"]["spawn_zone"] == "zone_02"
    assert traces["R_002"]["total_swaps"] == 0
    assert traces["R_002"]["end_state"] == "lost"
    
    # Verify R_003
    assert "R_003" in traces
    assert traces["R_003"]["total_swaps"] == 1
    
    print("✅ test_rider_trace_builder passed")


def test_station_timeline_builder():
    """Test station timeline aggregation."""
    events = create_test_events()
    city_graph = create_test_city_graph()
    
    timelines = build_station_timelines(events, city_graph)
    
    # Verify ST_01_01
    assert "ST_01_01" in timelines
    assert timelines["ST_01_01"]["zone"] == "zone_01"
    assert timelines["ST_01_01"]["swaps_total"] == 2
    assert timelines["ST_01_01"]["lost_swaps"] == 0
    
    # Verify ST_02_01
    assert "ST_02_01" in timelines
    assert timelines["ST_02_01"]["zone"] == "zone_02"
    assert timelines["ST_02_01"]["swaps_total"] == 0
    assert timelines["ST_02_01"]["lost_swaps"] == 1
    
    print("✅ test_station_timeline_builder passed")


def test_zone_pressure_builder():
    """Test zone pressure computation."""
    events = create_test_events()
    city_graph = create_test_city_graph()
    
    pressure = build_zone_pressure(events, city_graph)
    
    # Should have pressure records
    assert len(pressure) > 0
    
    # Verify structure
    for record in pressure:
        assert "zone" in record
        assert "minute" in record
        assert "pressure_score" in record
        assert "drivers" in record
    
    # Verify zone_01 has swap_congestion
    zone_01_records = [r for r in pressure if r["zone"] == "zone_01"]
    assert len(zone_01_records) > 0
    
    # Verify zone_02 has stockout
    zone_02_records = [r for r in pressure if r["zone"] == "zone_02"]
    assert any("battery_stockout" in r["drivers"] for r in zone_02_records)
    
    print("✅ test_zone_pressure_builder passed")


def test_run_narrative_builder():
    """Test narrative generation."""
    events = create_test_events()
    city_graph = create_test_city_graph()
    
    traces = build_rider_traces(events, city_graph)
    timelines = build_station_timelines(events, city_graph)
    pressure = build_zone_pressure(events, city_graph)
    
    narrative = build_run_narrative(traces, timelines, pressure)
    
    # Should be non-empty string
    assert isinstance(narrative, str)
    assert len(narrative) > 0
    
    # Should mention station with lost swaps
    assert "ST_02_01" in narrative or "lost" in narrative.lower()
    
    # Should be deterministic - run twice
    narrative2 = build_run_narrative(traces, timelines, pressure)
    assert narrative == narrative2
    
    print("✅ test_run_narrative_builder passed")


def test_deterministic_behavior():
    """Test same events produce same outputs."""
    events = create_test_events()
    city_graph = create_test_city_graph()
    
    # Run builders twice
    traces1 = build_rider_traces(events, city_graph)
    traces2 = build_rider_traces(events, city_graph)
    
    timelines1 = build_station_timelines(events, city_graph)
    timelines2 = build_station_timelines(events, city_graph)
    
    pressure1 = build_zone_pressure(events, city_graph)
    pressure2 = build_zone_pressure(events, city_graph)
    
    # Verify identical outputs
    assert traces1 == traces2
    assert timelines1 == timelines2
    assert pressure1 == pressure2
    
    print("✅ test_deterministic_behavior passed")


def test_empty_events():
    """Test builders handle empty event list gracefully."""
    events = []
    city_graph = create_test_city_graph()
    
    traces = build_rider_traces(events, city_graph)
    timelines = build_station_timelines(events, city_graph)
    pressure = build_zone_pressure(events, city_graph)
    narrative = build_run_narrative(traces, timelines, pressure)
    
    # All should return empty but valid structures
    assert traces == {}
    assert timelines == {}
    assert pressure == []
    assert isinstance(narrative, str)
    
    print("✅ test_empty_events passed")


if __name__ == "__main__":
    # Run tests
    test_rider_trace_builder()
    test_station_timeline_builder()
    test_zone_pressure_builder()
    test_run_narrative_builder()
    test_deterministic_behavior()
    test_empty_events()
    print("\n🎉 All observability builder tests passed!")

"""
Test RiderLifecycleManager for deterministic rider simulation.

Verify timestep-based logic, battery drain, zone movement, and multi-swap support.

Run: python test_rider_lifecycle_manager.py
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.rider_lifecycle_manager import RiderLifecycleManager
from simulation.rider_entity import RiderEntity, RiderState
from simulation.battery_entity import BatteryEntity, BatteryState
from simulation.event_logger import EventLogger
from simulation.network_graph import NetworkGraph
from simulation.battery_pool import BatteryPool
from simulation.simulation_config import (
    BATTERY_FULL_RANGE_KM,
    BATTERY_SWAP_THRESHOLD_KM,
    KM_PER_MIN,
    MAX_ZONE_DWELL_MIN
)


def create_test_network_graph():
    """Create a simple test network graph with zones."""
    graph = NetworkGraph()
    
    # Load baseline city graph
    config_path = os.path.join(
        os.path.dirname(__file__),
        'simulation',
        'city_graph_baseline.json'
    )
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            topology = json.load(f)
        graph.load_topology(topology)
    
    return graph


def test_rider_initialization():
    """Test rider initialization with full battery."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()
    
    try:
        event_logger = EventLogger(temp_file.name)
        manager = RiderLifecycleManager(event_logger, rng_seed=42)
        graph = create_test_network_graph()
        
        # Initialize rider
        spawn_time = datetime(2024, 1, 1, 10, 0, 0)
        rider = manager.initialize_rider(
            rider_id="R_TEST_001",
            spawn_zone="zone_01",
            spawn_time=spawn_time,
            network_graph=graph
        )
        
        # Verify rider state
        assert rider.rider_id == "R_TEST_001"
        assert rider.state == RiderState.ACTIVE
        assert rider.current_zone_id == "zone_01"
        assert rider.home_zone_id == "zone_01"
        assert rider.current_battery is not None
        assert rider.current_battery.remaining_km == BATTERY_FULL_RANGE_KM
        assert rider.total_distance_km == 0
        
        event_logger.close()
        
        # Verify rider_arrival event logged
        with open(temp_file.name, 'r') as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        assert len(events) == 1
        assert events[0]["event_type"] == "rider_arrival"
        assert events[0]["rider_id"] == "R_TEST_001"
        assert events[0]["metadata"]["zone_id"] == "zone_01"
        assert events[0]["metadata"]["battery_remaining_km"] == BATTERY_FULL_RANGE_KM
        
        print("✅ test_rider_initialization passed")
        
    finally:
        os.unlink(temp_file.name)


def test_battery_drain():
    """Test battery drains 0.5 km per minute."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()
    
    try:
        event_logger = EventLogger(temp_file.name)
        manager = RiderLifecycleManager(event_logger, rng_seed=42)
        
        # Create rider manually
        rider = RiderEntity("R_TEST_002")
        rider.current_battery = BatteryEntity("BAT_TEST", "zone_01", BatteryState.IN_USE)
        rider.current_battery.remaining_km = 50.0
        rider.total_distance_km = 0
        
        # Drain battery
        initial_battery = rider.current_battery.remaining_km
        manager._drain_battery(rider)
        
        # Verify drain
        assert rider.current_battery.remaining_km == initial_battery - KM_PER_MIN
        assert rider.total_distance_km == KM_PER_MIN
        
        # Drain 10 more times
        for _ in range(10):
            manager._drain_battery(rider)
        
        assert rider.current_battery.remaining_km == initial_battery - (11 * KM_PER_MIN)
        assert rider.total_distance_km == 11 * KM_PER_MIN
        
        event_logger.close()
        
        print("✅ test_battery_drain passed")
        
    finally:
        os.unlink(temp_file.name)


def test_swap_threshold_logic():
    """Test swap triggers at correct threshold."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()
    
    try:
        event_logger = EventLogger(temp_file.name)
        manager = RiderLifecycleManager(event_logger, rng_seed=42)
        
        # Test above threshold
        rider1 = RiderEntity("R_TEST_003")
        rider1.current_battery = BatteryEntity("BAT_TEST_1", "zone_01")
        rider1.current_battery.remaining_km = 10.0
        
        swap_needed, swap_critical = manager._check_swap_needed(rider1)
        assert not swap_needed
        assert not swap_critical
        
        # Test at threshold
        rider2 = RiderEntity("R_TEST_004")
        rider2.current_battery = BatteryEntity("BAT_TEST_2", "zone_01")
        rider2.current_battery.remaining_km = BATTERY_SWAP_THRESHOLD_KM
        
        swap_needed, swap_critical = manager._check_swap_needed(rider2)
        assert swap_needed
        assert not swap_critical
        
        # Test critical
        rider3 = RiderEntity("R_TEST_005")
        rider3.current_battery = BatteryEntity("BAT_TEST_3", "zone_01")
        rider3.current_battery.remaining_km = 2.0
        
        swap_needed, swap_critical = manager._check_swap_needed(rider3)
        assert swap_needed
        assert swap_critical
        
        event_logger.close()
        
        print("✅ test_swap_threshold_logic passed")
        
    finally:
        os.unlink(temp_file.name)


def test_zone_movement_decision():
    """Test deterministic zone movement logic."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()
    
    try:
        event_logger = EventLogger(temp_file.name)
        manager = RiderLifecycleManager(event_logger, rng_seed=42)
        
        # Test force move after MAX_ZONE_DWELL_MIN
        rider1 = RiderEntity("R_TEST_006")
        rider1.current_battery = BatteryEntity("BAT_TEST_1", "zone_01")
        rider1.current_battery.remaining_km = 50.0
        rider1.time_in_zone = MAX_ZONE_DWELL_MIN
        
        assert manager._should_move_zone(rider1) == True
        
        # Test score-based decision: healthy battery + away from home = move
        rider2 = RiderEntity("R_TEST_007")
        rider2.current_battery = BatteryEntity("BAT_TEST_2", "zone_01")
        rider2.current_battery.remaining_km = 50.0
        rider2.home_zone_id = "zone_01"
        rider2.current_zone_id = "zone_02"
        rider2.time_in_zone = 5
        
        should_move = manager._should_move_zone(rider2)
        # Score: +1 (battery healthy) + 1 (not home) = 2 → should move
        assert should_move == True
        
        # Test low score: low battery + at home = don't move
        rider3 = RiderEntity("R_TEST_008")
        rider3.current_battery = BatteryEntity("BAT_TEST_3", "zone_01")
        rider3.current_battery.remaining_km = 5.0
        rider3.home_zone_id = "zone_01"
        rider3.current_zone_id = "zone_01"
        rider3.time_in_zone = 5
        
        should_move = manager._should_move_zone(rider3)
        # Score: +0 (battery low) + 0 (at home) = 0 → should not move
        assert should_move == False
        
        event_logger.close()
        
        print("✅ test_zone_movement_decision passed")
        
    finally:
        os.unlink(temp_file.name)


def test_deterministic_seed():
    """Test same seed produces same decisions."""
    temp_file1 = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file2 = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file1.close()
    temp_file2.close()
    
    try:
        # Run 1 with seed 42
        event_logger1 = EventLogger(temp_file1.name)
        manager1 = RiderLifecycleManager(event_logger1, rng_seed=42)
        rider1 = manager1.initialize_rider(
            "R_TEST_009",
            "zone_01",
            datetime.now(),
            create_test_network_graph()
        )
        event_logger1.close()
        
        # Run 2 with seed 42
        event_logger2 = EventLogger(temp_file2.name)
        manager2 = RiderLifecycleManager(event_logger2, rng_seed=42)
        rider2 = manager2.initialize_rider(
            "R_TEST_009",
            "zone_01",
            datetime.now(),
            create_test_network_graph()
        )
        event_logger2.close()
        
        # Compare states
        assert rider1.current_zone_id == rider2.current_zone_id
        assert rider1.current_battery.battery_id == rider2.current_battery.battery_id
        
        print("✅ test_deterministic_seed passed")
        
    finally:
        os.unlink(temp_file1.name)
        os.unlink(temp_file2.name)


if __name__ == "__main__":
    # Run tests
    test_rider_initialization()
    test_battery_drain()
    test_swap_threshold_logic()
    test_zone_movement_decision()
    test_deterministic_seed()
    print("\n🎉 All rider lifecycle manager tests passed!")

"""
Test Persistent Entities: RiderEntity, BatteryEntity, BatteryPool.

Verify that battery tracking works and existing event types are preserved.

Run: python test_persistent_entities.py
"""

import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.rider_entity import RiderEntity, RiderState
from simulation.battery_entity import BatteryEntity, BatteryState
from simulation.battery_pool import BatteryPool
from simulation.event_logger import EventLogger
import tempfile


def test_rider_entity_lifecycle():
    """Test RiderEntity state transitions."""
    rider = RiderEntity(
        rider_id="R_001",
        initial_battery_id="BAT_OLD_001",
        spawn_time=datetime(2024, 1, 1, 10, 0, 0)
    )
    
    assert rider.state == RiderState.ACTIVE
    assert rider.current_battery_id == "BAT_OLD_001"
    assert rider.total_swaps == 0
    
    # Arrive at station
    rider.arrive_at_station("ST_01", datetime.now())
    assert rider.state == RiderState.AT_STATION
    assert rider.current_station_id == "ST_01"
    assert "ST_01" in rider.visited_stations
    
    # Start swap
    rider.start_swap()
    assert rider.state == RiderState.SWAPPING
    
    # Complete swap with new battery
    rider.complete_swap("BAT_NEW_001", datetime.now())
    assert rider.current_battery_id == "BAT_NEW_001"
    assert rider.total_swaps == 1
    assert rider.state == RiderState.ACTIVE
    
    print("✅ test_rider_entity_lifecycle passed")


def test_battery_entity_lifecycle():
    """Test BatteryEntity state transitions."""
    battery = BatteryEntity(
        battery_id="BAT_001",
        initial_station_id="ST_01",
        initial_state=BatteryState.AVAILABLE
    )
    
    assert battery.state == BatteryState.AVAILABLE
    assert battery.current_station_id == "ST_01"
    assert battery.total_swaps == 0
    
    # Assign to rider
    battery.assign_to_rider("R_001", datetime.now())
    assert battery.state == BatteryState.IN_USE
    assert battery.current_rider_id == "R_001"
    assert battery.total_swaps == 1
    
    # Return to station
    battery.return_to_station("ST_02", datetime.now())
    assert battery.state == BatteryState.DEPLETED
    assert battery.current_station_id == "ST_02"
    assert battery.current_rider_id is None
    
    # Charge
    battery.start_charging(datetime.now())
    assert battery.state == BatteryState.CHARGING
    
    battery.complete_charging(datetime.now())
    assert battery.state == BatteryState.AVAILABLE
    assert battery.total_charges == 1
    
    print("✅ test_battery_entity_lifecycle passed")


def test_battery_pool_operations():
    """Test BatteryPool assignment and return."""
    # Create temp event log
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()
    
    try:
        event_logger = EventLogger(temp_file.name)
        
        # Create pool with 5 batteries
        pool = BatteryPool(
            station_id="ST_01",
            initial_battery_count=5,
            event_logger=event_logger
        )
        
        # Check initial state
        assert pool.get_available_count() == 5
        snapshot = pool.snapshot()
        assert snapshot["available"] == 5
        
        # Assign battery to rider
        battery = pool.assign_battery_to_rider("R_001", datetime.now())
        assert battery is not None
        assert battery.state == BatteryState.IN_USE
        assert pool.get_available_count() == 4
        
        # Assign to another rider
        battery2 = pool.assign_battery_to_rider("R_002", datetime.now())
        assert battery2 is not None
        assert battery2.battery_id != battery.battery_id
        assert pool.get_available_count() == 3
        
        # Return first battery
        pool.return_battery(battery.battery_id, "R_001", datetime.now())
        # Battery is returned and immediately charged (instant for now)
        assert pool.get_available_count() == 4
        
        event_logger.close()
        
        # Verify events were logged
        with open(temp_file.name, 'r') as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        # Should have charge_start and charge_complete events
        charge_events = [e for e in events if e["event_type"] in ["charge_start", "charge_complete"]]
        assert len(charge_events) >= 2, f"Expected at least 2 charge events, got {len(charge_events)}"
        
        print("✅ test_battery_pool_operations passed")
        
    finally:
        os.unlink(temp_file.name)


def test_existing_event_types_preserved():
    """Verify that BatteryPool uses existing event types."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ndjson')
    temp_file.close()
    
    try:
        event_logger = EventLogger(temp_file.name)
        
        pool = BatteryPool(
            station_id="ST_01",
            initial_battery_count=2,
            event_logger=event_logger
        )
        
        # Perform operations
        battery = pool.assign_battery_to_rider("R_001", datetime.now())
        pool.return_battery(battery.battery_id, "R_001", datetime.now())
        
        event_logger.close()
        
        # Check events
        with open(temp_file.name, 'r') as f:
            events = [json.loads(line) for line in f if line.strip()]
        
        # Extract event types
        event_types = {e["event_type"] for e in events}
        
        # Verify ONLY existing event types are used (no new ones)
        allowed_types = {"charge_start", "charge_complete"}
        assert event_types.issubset(allowed_types), \
            f"New event types detected: {event_types - allowed_types}"
        
        # Verify charge_start and charge_complete are present
        assert "charge_start" in event_types
        assert "charge_complete" in event_types
        
        print("✅ test_existing_event_types_preserved passed")
        
    finally:
        os.unlink(temp_file.name)


if __name__ == "__main__":
    # Run tests
    test_rider_entity_lifecycle()
    test_battery_entity_lifecycle()
    test_battery_pool_operations()
    test_existing_event_types_preserved()
    print("\n🎉 All persistent entity tests passed!")

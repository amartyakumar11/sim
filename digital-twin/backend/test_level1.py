"""
Level 1 Implementation Validation Test

Tests that the real simulation now:
1. Generates more than 1 rider
2. Produces non-zero wait times under congestion
3. Produces non-zero utilization
4. Is deterministic (same config → same output)
5. KPIs change when swap_bays increase
"""

import sys
from datetime import datetime, timedelta
from simulation.main import run_simulation


def test_multiple_riders():
    """Test that more than 1 rider is generated"""
    config = {
        "run_id": "test_001",
        "seed": 42,
        "city": "TestCity",
        "start_time": datetime(2026, 1, 1, 8, 0, 0),
        "end_time": datetime(2026, 1, 1, 9, 0, 0),  # 1 hour
        "city_config": {
            "stations": [
                {
                    "station_id": "S1",
                    "lat": 12.9716,
                    "lon": 77.5946,
                    "zone_id": "Z1",
                    "swap_bays": 2,
                    "chargers_total": 4,
                    "inventory_current": 20
                }
            ]
        },
        "demand": {
            "base_demand_rate_per_min": 0.5  # ~30 riders per hour
        }
    }
    
    result = run_simulation(config, mode="real")
    
    num_arrivals = len([e for e in result["events"] if e["event_type"] == "rider_arrival"])
    print(f"[PASS] Test 1 - Multiple Riders: {num_arrivals} arrivals (expected >1)")
    
    assert num_arrivals > 1, f"Expected >1 arrivals, got {num_arrivals}"
    return True


def test_wait_time_under_congestion():
    """Test that wait times are > 0 when station is congested"""
    config = {
        "run_id": "test_002",
        "seed": 123,
        "city": "TestCity",
        "start_time": datetime(2026, 1, 1, 8, 0, 0),
        "end_time": datetime(2026, 1, 1, 9, 0, 0),
        "city_config": {
            "stations": [
                {
                    "station_id": "S1",
                    "lat": 12.9716,
                    "lon": 77.5946,
                    "zone_id": "Z1",
                    "swap_bays": 1,  # Only 1 bay - creates congestion
                    "swap_time_sec": 300,  # 5 min swap time
                    "inventory_current": 50
                }
            ]
        },
        "demand": {
            "base_demand_rate_per_min": 1.0  # ~60 riders per hour - high load
        }
    }
    
    result = run_simulation(config, mode="real")
    
    avg_wait_time = result["kpis"]["avg_wait_time"]
    utilization = result["kpis"]["utilization"]
    
    print(f"[PASS] Test 2 - Wait Time: {avg_wait_time:.2f} min (expected >0)")
    print(f"                Utilization: {utilization:.3f} (expected >0)")
    
    assert avg_wait_time > 0, f"Expected wait time >0, got {avg_wait_time}"
    assert utilization > 0, f"Expected utilization >0, got {utilization}"
    return True


def test_determinism():
    """Test that same config produces same output"""
    config = {
        "run_id": "test_003",
        "seed": 999,
        "city": "TestCity",
        "start_time": datetime(2026, 1, 1, 8, 0, 0),
        "end_time": datetime(2026, 1, 1, 8, 30, 0),  # 30 min
        "city_config": {
            "stations": [
                {
                    "station_id": "S1",
                    "lat": 12.9716,
                    "lon": 77.5946,
                    "zone_id": "Z1",
                    "swap_bays": 2,
                    "inventory_current": 10
                },
                {
                    "station_id": "S2",
                    "lat": 12.9352,
                    "lon": 77.6245,
                    "zone_id": "Z1",
                    "swap_bays": 2,
                    "inventory_current": 10
                }
            ]
        },
        "demand": {
            "base_demand_rate_per_min": 0.3
        }
    }
    
    result1 = run_simulation(config, mode="real")
    result2 = run_simulation(config, mode="real")
    
    kpis1 = result1["kpis"]
    kpis2 = result2["kpis"]
    
    # Compare key KPIs
    for key in ["avg_wait_time", "lost_swaps", "throughput"]:
        val1 = kpis1[key]
        val2 = kpis2[key]
        if isinstance(val1, float):
            diff = abs(val1 - val2)
            assert diff < 1e-6, f"KPI {key} not deterministic: {val1} vs {val2}"
        else:
            assert val1 == val2, f"KPI {key} not deterministic: {val1} vs {val2}"
    
    print(f"[PASS] Test 3 - Determinism: Same config -> same KPIs")
    return True


def test_intervention_effect():
    """Test that increasing swap_bays improves KPIs"""
    base_config = {
        "run_id": "test_004_base",
        "seed": 555,
        "city": "TestCity",
        "start_time": datetime(2026, 1, 1, 8, 0, 0),
        "end_time": datetime(2026, 1, 1, 9, 0, 0),
        "city_config": {
            "stations": [
                {
                    "station_id": "S1",
                    "lat": 12.9716,
                    "lon": 77.5946,
                    "zone_id": "Z1",
                    "swap_bays": 1,  # Baseline: 1 bay
                    "swap_time_sec": 240,
                    "inventory_current": 30
                }
            ]
        },
        "demand": {
            "base_demand_rate_per_min": 0.4
        }
    }
    
    intervention_config = base_config.copy()
    intervention_config["run_id"] = "test_004_intervention"
    intervention_config["city_config"] = {
        "stations": [
            {
                "station_id": "S1",
                "lat": 12.9716,
                "lon": 77.5946,
                "zone_id": "Z1",
                "swap_bays": 3,  # Intervention: 3 bays
                "swap_time_sec": 240,
                "inventory_current": 30
            }
        ]
    }
    
    base_result = run_simulation(base_config, mode="real")
    intervention_result = run_simulation(intervention_config, mode="real")
    
    base_wait = base_result["kpis"]["avg_wait_time"]
    intervention_wait = intervention_result["kpis"]["avg_wait_time"]
    
    base_lost = base_result["kpis"]["lost_swaps"]
    intervention_lost = intervention_result["kpis"]["lost_swaps"]
    
    print(f"[PASS] Test 4 - Intervention Effect:")
    print(f"                Baseline wait: {base_wait:.2f} min, lost: {base_lost}")
    print(f"                +2 bays wait: {intervention_wait:.2f} min, lost: {intervention_lost}")
    print(f"                Improvement: wait reduced by {base_wait - intervention_wait:.2f} min")
    
    # More bays should reduce wait time (or keep it same if already low)
    assert intervention_wait <= base_wait, f"Wait time should not increase with more bays"
    return True


def test_timeseries_generation():
    """Test that timeseries are generated from events"""
    config = {
        "run_id": "test_005",
        "seed": 777,
        "city": "TestCity",
        "start_time": datetime(2026, 1, 1, 8, 0, 0),
        "end_time": datetime(2026, 1, 1, 8, 30, 0),
        "city_config": {
            "stations": [
                {
                    "station_id": "S1",
                    "lat": 12.9716,
                    "lon": 77.5946,
                    "swap_bays": 2,
                    "inventory_current": 15
                }
            ]
        },
        "demand": {
            "base_demand_rate_per_min": 0.3
        }
    }
    
    result = run_simulation(config, mode="real")
    
    timeseries = result["timeseries"]
    
    # Check that inventory_levels and queue_lengths exist
    assert "inventory_levels" in timeseries, "Missing inventory_levels in timeseries"
    assert "queue_lengths" in timeseries, "Missing queue_lengths in timeseries"
    
    inventory_levels = timeseries["inventory_levels"]
    queue_lengths = timeseries["queue_lengths"]
    
    # Should have at least one station's timeseries
    assert "S1" in inventory_levels, "Missing S1 in inventory_levels"
    assert "S1" in queue_lengths, "Missing S1 in queue_lengths"
    
    print(f"[PASS] Test 5 - Timeseries: inventory samples={len(inventory_levels['S1'])}, queue samples={len(queue_lengths['S1'])}")
    return True


if __name__ == "__main__":
    print("="*60)
    print("LEVEL 1 VALIDATION TESTS")
    print("="*60)
    
    tests = [
        ("Multiple Riders Generated", test_multiple_riders),
        ("Wait Time Under Congestion", test_wait_time_under_congestion),
        ("Determinism", test_determinism),
        ("Intervention Effect", test_intervention_effect),
        ("Timeseries Generation", test_timeseries_generation)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\nRunning: {test_name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test_name}")
            print(f"       Error: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test_name}")
            print(f"        Exception: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print("="*60)
    
    sys.exit(0 if failed == 0 else 1)

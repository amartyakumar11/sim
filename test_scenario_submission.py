"""
Test scenario submission via API to verify simulation runs correctly.
"""
import requests
import time
import json

API_BASE = "http://localhost:8000/api"

# Test scenario with minimal config
scenario = {
    "description": "Test - Fixed pricing deterministic run",
    "city_config": {
        "zones": ["zone_1"],
        "stations": [
            {
                "station_id": "TEST_S1",
                "lat": 26.8467,
                "lon": 80.9462,
                "zone_id": "zone_1",
                "chargers_total": 3,
                "chargers_active": 3
            },
            {
                "station_id": "TEST_S2",
                "lat": 26.8500,
                "lon": 80.9500,
                "zone_id": "zone_1",
                "chargers_total": 2,
                "chargers_active": 2
            }
        ]
    },
    "interventions": {},
    "simulation_duration": 600,  # 10 minutes
    "duration_minutes": 10,
    "seed": 42,
    "mode": "real"
}

print("=" * 70)
print("TESTING SCENARIO SUBMISSION & SIMULATION")
print("=" * 70)

# Step 1: Submit scenario
print("\n[STEP 1] Submitting scenario...")
try:
    response = requests.post(f"{API_BASE}/scenarios/submit", json=scenario, timeout=10)
    response.raise_for_status()
    result = response.json()
    run_id = result["run_id"]
    print(f"✅ Scenario submitted successfully")
    print(f"   Run ID: {run_id}")
    print(f"   Status: {result['status']}")
except Exception as e:
    print(f"❌ Failed to submit scenario: {e}")
    exit(1)

# Step 2: Poll for completion
print("\n[STEP 2] Polling for completion...")
max_polls = 60  # 3 minutes max
poll_interval = 3

for i in range(max_polls):
    try:
        response = requests.get(f"{API_BASE}/jobs/{run_id}/status", timeout=10)
        response.raise_for_status()
        status_data = response.json()
        
        status = status_data["status"]
        message = status_data.get("message", "")
        
        print(f"   Poll {i+1}: {status} - {message}")
        
        if status == "completed":
            print("✅ Simulation completed!")
            break
        elif status == "failed":
            print(f"❌ Simulation failed: {message}")
            exit(1)
        
        time.sleep(poll_interval)
    except Exception as e:
        print(f"❌ Error polling status: {e}")
        exit(1)
else:
    print("❌ Timeout waiting for completion")
    exit(1)

# Step 3: Fetch results
print("\n[STEP 3] Fetching results...")
try:
    response = requests.get(f"{API_BASE}/jobs/{run_id}/result", timeout=10)
    response.raise_for_status()
    result = response.json()
    
    summary = result.get("summary", {})
    
    print("✅ Results retrieved!")
    print("\n[KPIs]")
    print(f"   Avg Wait Time: {summary.get('avg_wait_time', 0):.3f} minutes")
    print(f"   Lost Swaps: {summary.get('lost_swaps', 0)}")
    print(f"   Utilization: {summary.get('charger_utilization', 0):.1%}")
    print(f"   Throughput: {summary.get('city_throughput', 0)} swaps")
    print(f"   Revenue: ₹{summary.get('revenue', 0):.2f}")
    print(f"   ROI: {summary.get('roi', 0):.2f}%")
    print(f"   Events Count: {result.get('events_count', 0)}")
    
    # Check financials
    financials = summary.get('financials', {})
    if financials:
        print("\n[Financials]")
        print(f"   Total Revenue: ₹{financials.get('total_revenue', 0):.2f}")
        print(f"   Primary Swaps: {financials.get('primary_swaps', 0)}")
        print(f"   Secondary Swaps: {financials.get('secondary_swaps', 0)}")
        print(f"   Total Penalties: ₹{financials.get('total_penalties', 0):.2f}")
        print(f"   Service Charges: ₹{financials.get('total_service_charges', 0):.2f}")
    
except Exception as e:
    print(f"❌ Error fetching results: {e}")
    exit(1)

# Step 4: Test determinism - submit same scenario again
print("\n[STEP 4] Testing determinism (same seed)...")
try:
    response = requests.post(f"{API_BASE}/scenarios/submit", json=scenario, timeout=10)
    response.raise_for_status()
    result2 = response.json()
    run_id_2 = result2["run_id"]
    print(f"✅ Second scenario submitted: {run_id_2}")
    
    # Wait for completion
    for i in range(max_polls):
        response = requests.get(f"{API_BASE}/jobs/{run_id_2}/status", timeout=10)
        status_data = response.json()
        if status_data["status"] == "completed":
            break
        time.sleep(poll_interval)
    
    # Get results
    response = requests.get(f"{API_BASE}/jobs/{run_id_2}/result", timeout=10)
    result2_data = response.json()
    summary2 = result2_data.get("summary", {})
    
    print("\n[Comparing Results]")
    print(f"   Run 1 Revenue: ₹{summary.get('revenue', 0):.2f}")
    print(f"   Run 2 Revenue: ₹{summary2.get('revenue', 0):.2f}")
    print(f"   Run 1 Throughput: {summary.get('city_throughput', 0)}")
    print(f"   Run 2 Throughput: {summary2.get('city_throughput', 0)}")
    print(f"   Run 1 Wait Time: {summary.get('avg_wait_time', 0):.3f} min")
    print(f"   Run 2 Wait Time: {summary2.get('avg_wait_time', 0):.3f} min")
    
    # Check if deterministic
    if (abs(summary.get('revenue', 0) - summary2.get('revenue', 0)) < 0.01 and
        summary.get('city_throughput', 0) == summary2.get('city_throughput', 0)):
        print("\n✅ ✅ ✅ DETERMINISM VERIFIED! Same seed produces identical results.")
    else:
        print("\n⚠️  Results differ - may not be fully deterministic")
        
except Exception as e:
    print(f"⚠️  Could not test determinism: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

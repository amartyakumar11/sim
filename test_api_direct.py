"""Test API directly to see what's being returned"""
import requests
import json

run_id = "57045740-6bfb-4a01-b0c0-2dd752e41dad"

print("=" * 70)
print(f"Testing API for run_id: {run_id}")
print("=" * 70)

# Test status endpoint
print("\n1. GET /api/jobs/{run_id}/status")
status_response = requests.get(f"http://localhost:8000/api/jobs/{run_id}/status")
print(f"Status Code: {status_response.status_code}")
if status_response.status_code == 200:
    status_data = status_response.json()
    print(f"Status: {status_data.get('status')}")
    print(f"Progress: {status_data.get('progress')}")
    print(f"Message: {status_data.get('message')}")

# Test result endpoint
print("\n2. GET /api/jobs/{run_id}/result")
result_response = requests.get(f"http://localhost:8000/api/jobs/{run_id}/result")
print(f"Status Code: {result_response.status_code}")

if result_response.status_code == 200:
    result_data = result_response.json()
    print("\nResult structure:")
    print(f"  Keys: {list(result_data.keys())}")
    
    if 'summary' in result_data:
        print(f"\n  Summary keys: {list(result_data['summary'].keys())}")
        print(f"\n  Summary values:")
        for key, value in result_data['summary'].items():
            if isinstance(value, float):
                print(f"    {key}: {value:.3f}")
            else:
                print(f"    {key}: {value}")
    
    print(f"\n  events_count: {result_data.get('events_count')}")
    print(f"  frames_count: {result_data.get('frames_count')}")
    print(f"  status: {result_data.get('status')}")
    
    print("\n3. Full JSON response (first 500 chars):")
    json_str = json.dumps(result_data, indent=2)
    print(json_str[:500] + "...")
    
elif result_response.status_code == 202:
    print("Simulation still running...")
else:
    print(f"Error: {result_response.text}")

print("\n" + "=" * 70)

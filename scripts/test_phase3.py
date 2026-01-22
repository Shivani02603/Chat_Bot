"""
Quick test script for Phase 3 integration
Tests both FastAPI endpoints
"""

import requests

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{API_BASE}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_chat():
    """Test chat endpoint"""
    print("\n=== Testing Chat Endpoint ===")
    payload = {
        "user_id": "test_user_phase3",
        "message": "Show me 3 bedroom properties"
    }
    response = requests.post(f"{API_BASE}/api/chat", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response preview: {result['response'][:150]}...")
    return response.status_code == 200

def test_root():
    """Test root endpoint"""
    print("\n=== Testing Root Endpoint ===")
    response = requests.get(f"{API_BASE}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

if __name__ == "__main__":
    print("=" * 60)
    print("Phase 3 Integration Test")
    print("=" * 60)

    tests = [
        ("Root Endpoint", test_root),
        ("Health Check", test_health),
        ("Chat API", test_chat)
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "PASSED" if success else "FAILED"))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((name, "ERROR"))

    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    for name, status in results:
        symbol = "[PASS]" if status == "PASSED" else "[FAIL]"
        print(f"{symbol} {name}: {status}")

    print("=" * 60)

    all_passed = all(status == "PASSED" for _, status in results)
    if all_passed:
        print("\n==> All tests PASSED! Phase 3 is ready.")
    else:
        print("\n==> Some tests failed. Check the output above.")

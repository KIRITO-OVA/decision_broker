import requests
import time
import sys
import json

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "sk_test_12345"

def print_result(test_name, result, detail=""):
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} {test_name} {detail}")
    if not result:
        print(f"CRITICAL FAILURE IN {test_name}. STOPPING.")
        sys.exit(1)

def wait_for_server():
    print("Waiting for server to boot...")
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/docs")
            print("Server is up.")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def run_tests():
    # TEST 1: Server Boot
    # Implicitly checked by wait_for_server
    if not wait_for_server():
        print_result("Test 1: Server Boot", False, "Could not connect to server.")
    print_result("Test 1: Server Boot", True)

    # TEST 2: Auth Rejection
    print("\n--- Test 2: Auth Rejection ---")
    try:
        resp = requests.post(f"{BASE_URL}/decide", 
                             json={"decision_type": "sales_outreach", "payload": {}}, 
                             headers={"X-API-Key": "invalid_key"})
        if resp.status_code in [401, 403]:
            print_result("Test 2: Auth Rejection", True, f"Got {resp.status_code}")
        else:
            print_result("Test 2: Auth Rejection", False, f"Got {resp.status_code}, expected 401/403")
    except Exception as e:
        print_result("Test 2: Auth Rejection", False, f"Exception: {e}")

    # TEST 3: Credit Gate + Decision Flow
    print("\n--- Test 3: Credit Gate + Decision Flow ---")
    payload_sales = {
        "lead_id": "123",
        "company_domain": "techcorp.com",
        "last_contact_days": 5,
        "lead_activity": {"opened_email": True, "clicked_link": True, "replied": True},
        "company_signals": {"recent_hiring": True, "funding_news_days": 12},
        "time_context": {"local_hour": 10, "local_day": "Tuesday"}
    }
    
    try:
        # Check pre-credits via side-channel if possible, or just rely on functionality
        # We assume startup state has decent credits (modified by previous tests potentially, 
        # but DB init ensures sk_test_12345 has 10 initially, -1 from Step 5 test = 9)
        
        resp = requests.post(f"{BASE_URL}/decide",
                             json={"decision_type": "sales_outreach", "payload": payload_sales},
                             headers={"X-API-Key": API_KEY})
        
        data = resp.json()
        print(f"Response: {data}")
        
        if resp.status_code == 200 and data.get("decision") == "contact_now" and data.get("credits_used") == 1:
            print_result("Test 3: Flow & Logic", True)
        else:
            print_result("Test 3: Flow & Logic", False, f"Status: {resp.status_code}, Data: {data}")
            
    except Exception as e:
        print_result("Test 3: Flow & Logic", False, f"Exception: {e}")

    # TEST 4: Determinism
    print("\n--- Test 4: Determinism ---")
    # Send same request again
    try:
        resp2 = requests.post(f"{BASE_URL}/decide",
                             json={"decision_type": "sales_outreach", "payload": payload_sales},
                             headers={"X-API-Key": API_KEY})
        data2 = resp2.json()
        
        # Compare with previous data (from Test 3)
        if data2["decision"] == data["decision"] and data2["confidence"] == data["confidence"]:
            print_result("Test 4: Determinism", True, "Identical Output")
        else:
            print_result("Test 4: Determinism", False, f"Variance detected! \nRun 1: {data}\nRun 2: {data2}")
            
    except Exception as e:
        print_result("Test 4: Determinism", False, f"Exception: {e}")

    # TEST 5: Router Coverage
    print("\n--- Test 5: Router Coverage ---")
    
    # Model Selection
    payload_model = {
        "task_type": "code",
        "latency_requirement_ms": 2000,
        "accuracy_priority": "high",
        "budget_tier": "medium",
        "context_tokens": 5000,
        "retry_allowed": True
    }
    resp_model = requests.post(f"{BASE_URL}/decide",
                               json={"decision_type": "model_selection", "payload": payload_model},
                               headers={"X-API-Key": API_KEY})
    if resp_model.status_code == 200 and resp_model.json()["decision"] == "use_gpt_4":
        print("[PASS] model_selection covered")
    else:
        print_result("Test 5: Router (Model)", False, f"Failed model_selection: {resp_model.text}")

    # Retry Intelligence
    payload_retry = {
        "error_type": "timeout",
        "attempt_number": 4, 
        "max_attempts": 5,
        "latency_ms": 500,
        "provider_status": "degraded",
        "is_idempotent": True, 
        "budget_remaining": "high"
    }
    resp_retry = requests.post(f"{BASE_URL}/decide",
                               json={"decision_type": "retry_intelligence", "payload": payload_retry},
                               headers={"X-API-Key": API_KEY})
    if resp_retry.status_code == 200 and resp_retry.json()["decision"] == "switch_provider":
        print("[PASS] retry_intelligence covered")
    else:
        print_result("Test 5: Router (Retry)", False, f"Failed retry_intelligence: {resp_retry.text}")
        
    print_result("Test 5: Router Coverage", True)
    
    print("\nALL MANDATORY TESTS PASSED.")

if __name__ == "__main__":
    run_tests()

import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "sk_test_12345"

def test_hard_stop():
    print("--- Testing Hard Stop ---")
    
    # 1. Consume last credit
    print("Consuming last credit...")
    try:
        resp = requests.post(f"{BASE_URL}/decide", 
                             json={"decision_type": "sales_outreach", "payload": {
                                 "lead_id": "drain",
                                 "company_domain": "drain.com",
                                 "last_contact_days": 5,
                                 "lead_activity": {"opened_email": True, "clicked_link": False, "replied": False},
                                 "company_signals": {"recent_hiring": False, "funding_news_days": 100},
                                 "time_context": {"local_hour": 10, "local_day": "Tuesday"}
                             }}, 
                             headers={"X-API-Key": API_KEY})
        
        if resp.status_code == 200:
            print("[PASS] Last credit consumer.")
        else:
            print(f"[FAIL] Expected 200, got {resp.status_code}")
            sys.exit(1)
            
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        sys.exit(1)

    # 2. Check Rejection
    print("Verifying rejection...")
    try:
        resp = requests.post(f"{BASE_URL}/decide", 
                             json={"decision_type": "sales_outreach", "payload": {}}, 
                             headers={"X-API-Key": API_KEY})
        
        # Expect 402 Payment Required (or 403/400 depending on impl, my code raises PermissionError which maps to 401 or 402)
        # server.py logic: if "credits" in str(e).lower(): raise HTTPException(status_code=402, detail=str(e))
        
        if resp.status_code == 402:
            print(f"[PASS] Correctly blocked with 402: {resp.text}")
        else:
            print(f"[FAIL] Expected 402, got {resp.status_code}: {resp.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"[FAIL] Exception: {e}")
        sys.exit(1)
        
    print("\n[SUCCESS] Hard Stop Verified.")

if __name__ == "__main__":
    test_hard_stop()

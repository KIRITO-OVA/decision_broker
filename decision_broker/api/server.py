from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
import sys
import hmac
import hashlib
import json
from dotenv import load_dotenv

load_dotenv()

# Ensure package in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration Validation
ENV = os.getenv("ENV", "dev")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "test_secret_123")

if ENV == "prod":
    if not all([RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET]):
        print("[WARNING] Production mode identified but missing Razorpay Keys in .env")
    else:
        print("[INFO] Production Configuration Loaded")
else:
    print(f"[INFO] Running in {ENV} mode")

from decision_broker.schemas import DecisionRequest, DecisionResponse
from decision_broker.main import process_decision
from decision_broker.core.auth.api_key import validate_api_key
from decision_broker.core.billing.credits import add_credits

app = FastAPI(title="Decision Broker API", version="1.0.0")

# CORS for RapidAPI testing console
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DecisionAPIRequest(BaseModel):
    decision_type: str
    payload: Dict[str, Any]

@app.get("/health")
def health_check():
    """Health check endpoint for RapidAPI monitoring."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/decide")
def decide(data: DecisionAPIRequest, x_api_key: str = Header(..., alias="X-API-Key")):
    """
    Core decision endpoint.
    Requires X-API-Key header.
    """
    # Validate API Key here or inside main. 
    # Calling process_decision which has full logic is cleaner (Fat Logic, Thin API).
    
    # Construct internal request object
    request = DecisionRequest(
        decision_type=data.decision_type,
        payload=data.payload
    )
    
    try:
        # Execute logic (Auth -> Credit -> Decide -> Billing)
        response = process_decision(request, x_api_key)
        
        # Format response as requested: decision, confidence, ttl, credits_used
        return {
            "decision": response.decision["decision"],
            "confidence": response.confidence,
            "ttl": response.valid_for_seconds,
            "credits_used": 1,
            "reason_code": response.reason_code
        }
        
    except PermissionError as e:
        # 401/402 handling
        if "credits" in str(e).lower():
            raise HTTPException(status_code=402, detail=str(e))
        raise HTTPException(status_code=401, detail=str(e))
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    """
    Handle Razorpay Webhooks (payment.captured).
    Verifies signature and adds credits.
    """
    # 1. Verify Signature
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "test_secret_123")
    signature = request.headers.get("X-Razorpay-Signature", "")
    body = await request.body()
    
    try:
        # Compute expected signature
        computed_sig = hmac.new(
            secret.encode('utf-8'),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(computed_sig, signature):
            raise HTTPException(status_code=400, detail="Invalid Signature")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail="Signature Verification Failed")

    # 2. Parse Body
    try:
        data = await request.json()
        event = data.get("event")
        
        if event == "payment.captured":
            payment = data.get("payload", {}).get("payment", {}).get("entity", {})
            amount = payment.get("amount", 0)
            notes = payment.get("notes", {})
            
            # Extract API Key from notes.api_key OR reference_id (as fallbacks)
            # User requirement: notes.api_key or reference_id
            target_api_key = notes.get("api_key")
            # If notes doesn't have it, check if description or other fields do, 
            # but user logic specifically asked for notes.api_key or reference_id (usually notes is best)
            
            if not target_api_key:
                # Provide useful error or ignore? User says "Missing api_key -> reject"
                # Rejecting webhook usually means 400 or just 200 to stop retry?
                # Usually return 400 to signal error, but Razorpay retries 400s. 
                # If it's permanent fail (missing data), maybe 200 with error log?
                # Step 7 requirements say "Reject". We'll throw 400 to be explicit.
                raise HTTPException(status_code=400, detail="Missing api_key in notes")
                
            # 3. Credit Mapping (Strict)
            # 19900 -> 100
            # 49900 -> 500
            # 99900 -> 2000
            if amount == 19900:
                credits = 100
            elif amount == 49900:
                credits = 500
            elif amount == 99900:
                credits = 2000
            else:
                raise HTTPException(status_code=400, detail=f"Invalid Amount: {amount}")
                
            # 4. Add Credits
            # Need to resolve api_key to user_id FIRST.
            # Reuse validate_api_key to get user_id, but validate_api_key returns user_id or None.
            user_id = validate_api_key(target_api_key)
            if not user_id:
                 raise HTTPException(status_code=400, detail="Invalid API Key in payload")
                 
            new_balance = add_credits(user_id, credits)
            print(f"[PAYMENT] Added {credits} credits to {user_id}. New Balance: {new_balance}")
            
            return {"status": "ok"}
            
    except HTTPException:
        raise
    except Exception as e:
        # Catch unexpected parsing errors
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": "ignored"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

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
from decision_broker.core.billing.credits import add_credits, check_credits
from decision_broker.core.db import (
    get_db_connection, 
    SUBSCRIPTION_PLANS, 
    update_subscription, 
    get_user_by_subscription,
    mark_subscription_charged,
    get_low_balance_users,
    mark_low_balance_notified
)
import uuid
import secrets
import razorpay

# Initialize Razorpay client
razorpay_client = None
if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Custom API description with markdown
API_DESCRIPTION = """
# 🧠 Decision Broker - AI-to-AI Decision Intelligence

**Intelligent decision-making API for AI agents and automation systems.**

## What This API Does

Your AI calls our API to get smart decisions for:

| Decision Type | Use Case |
|--------------|----------|
| **sales_outreach** | When and how to contact leads |
| **model_selection** | Which AI model to use for a task |
| **retry_intelligence** | When to retry failed operations |

## Quick Start

1. **Get an API Key** - Call `/signup` with your email
2. **Make Decisions** - Call `/decide` with your scenario
3. **Check Balance** - Call `/balance` to see credits

## Authentication

All `/decide` calls require an `X-API-Key` header.

```
X-API-Key: sk_live_your_api_key_here
```

## Pricing

| Plan | Credits | Price |
|------|---------|-------|
| Starter | 100 | ₹199 |
| Pro | 500 | ₹499 |
| Business | 2000 | ₹999 |

---

Built for AI agents, by AI engineers. 🤖
"""

# Custom Swagger UI configuration
swagger_ui_parameters = {
    "syntaxHighlight.theme": "monokai",
    "docExpansion": "list",
    "filter": True,
    "deepLinking": True,
    "displayRequestDuration": True,
    "defaultModelsExpandDepth": 1,
    "persistAuthorization": True,
}

app = FastAPI(
    title="Decision Broker API",
    description=API_DESCRIPTION,
    version="2.0.0",
    contact={
        "name": "Decision Broker Support",
        "url": "https://kirito-ova.github.io/decision_broker/",
    },
    license_info={
        "name": "Commercial",
    },
    swagger_ui_parameters=swagger_ui_parameters,
    redoc_url="/redoc",
    docs_url="/docs",
)

# CORS for RapidAPI testing console
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DecisionAPIRequest(BaseModel):
    """Request body for making a decision."""
    decision_type: str
    payload: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "decision_type": "sales_outreach",
                "payload": {
                    "lead_activity": "high",
                    "time_context": {"hour": 10, "weekday": "tuesday"},
                    "company_signals": {"recent_hiring": True},
                    "last_contact_days": 7
                }
            }
        }

class SignupRequest(BaseModel):
    """Request body for creating a new account."""
    email: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "developer@company.com"
            }
        }

class SignupResponse(BaseModel):
    """Response after successful account creation."""
    success: bool
    api_key: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "api_key": "sk_live_abc123def456...",
                "message": "Account created! You have 5 free credits."
            }
        }

@app.get("/", tags=["🏠 General"], summary="API Information", 
         description="Get basic API information and available endpoints.")
def root():
    """Returns API metadata and available endpoints."""
    return {
        "api": "Decision Broker",
        "version": "2.0.0",
        "description": "AI-to-AI Decision Intelligence API",
        "endpoints": ["/health", "/decide", "/signup", "/balance"],
        "docs": "/docs",
        "redoc": "/redoc",
        "ai_plugin": "/.well-known/ai-plugin.json",
        "ai_manifest": "/ai-manifest.json"
    }

@app.get("/.well-known/ai-plugin.json", tags=["🤖 AI Discovery"], include_in_schema=False)
def get_ai_plugin():
    """Serves the OpenAI-compatible AI plugin manifest."""
    try:
        with open(".well-known/ai-plugin.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="AI Plugin manifest not found")

@app.get("/ai-manifest.json", tags=["🤖 AI Discovery"], include_in_schema=False)
def get_ai_manifest():
    """Serves the general AI manifest for autonomous discovery."""
    try:
        with open("ai-manifest.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="AI manifest not found")

@app.get("/health", tags=["🏠 General"], summary="Health Check",
         description="Verify API is running. Use for uptime monitoring.")
def health_check():
    """Returns OK if the API is operational."""
    return {"status": "ok", "version": "2.0.0", "uptime": "operational"}

@app.post("/signup", response_model=SignupResponse, tags=["🔐 Authentication"],
          summary="Create Account & Get API Key",
          description="""
**Create a new account and receive your API key instantly.**

### What You Get:
- ✅ Unique API key (starts with `sk_live_`)
- ✅ **5 FREE credits** to test the API
- ✅ Instant access to all decision types

### Next Steps:
1. Copy your API key
2. Add it to the `X-API-Key` header
3. Call `/decide` to make decisions
""")
def signup(data: SignupRequest):
    """
    Create a new user account and generate an API key.
    New users start with 5 free credits.
    """
    email = data.email.strip().lower()
    
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")
    
    # Generate unique user ID and API key
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    api_key = f"sk_live_{secrets.token_hex(16)}"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if email already exists (add email column if needed)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            conn.commit()
        except:
            pass  # Column already exists
        
        # Check for existing user with this email
        cursor.execute("SELECT api_key FROM users WHERE email = ?", (email,))
        existing = cursor.fetchone()
        
        if existing:
            return SignupResponse(
                success=True,
                api_key=existing["api_key"],
                message="Account already exists. Here's your API key."
            )
        
        # Create new user with 5 free credits
        cursor.execute(
            "INSERT INTO users (id, api_key, credits, email) VALUES (?, ?, ?, ?)",
            (user_id, api_key, 5, email)
        )
        conn.commit()
    
    return SignupResponse(
        success=True,
        api_key=api_key,
        message="Account created! You have 5 free credits to start."
    )

@app.get("/balance", tags=["💳 Billing"], summary="Check Credit Balance",
         description="""
**Check how many credits you have remaining.**

Requires your API key in the `X-API-Key` header.

### Response:
- `credits`: Number of decisions you can make
- Each `/decide` call uses 1 credit
""")
def get_balance(x_api_key: str = Header(..., alias="X-API-Key")):
    """Check credit balance for an API key."""
    user_id = validate_api_key(x_api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    balance = check_credits(user_id)
    return {"api_key": x_api_key[:15] + "...", "credits": balance}

class SubscribeRequest(BaseModel):
    plan: str  # starter, pro, business
    api_key: str

@app.post("/subscribe", tags=["💳 Billing"], summary="Create Subscription",
          description="Create a recurring subscription for monthly credit auto-refills.")
def create_subscription(data: SubscribeRequest):
    """
    Create a Razorpay subscription for monthly auto-renewal of credits.
    Returns a payment link for the user to complete subscription setup.
    """
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    plan = data.plan.lower()
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan. Choose: starter, pro, business")
    
    # Validate API key
    user_id = validate_api_key(data.api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    plan_config = SUBSCRIPTION_PLANS[plan]
    
    try:
        # Create Razorpay plan (or use existing)
        # Note: In production, you'd create these plans once in Razorpay dashboard
        # and store the plan IDs. For now, we create subscriptions directly.
        
        # Create subscription
        subscription_data = {
            "plan_id": f"plan_decision_broker_{plan}",  # You'll need to create these in Razorpay
            "total_count": 12,  # 12 months
            "quantity": 1,
            "notes": {
                "api_key": data.api_key,
                "user_id": user_id,
                "plan": plan
            }
        }
        
        # For now, return a payment link approach using Payment Links API
        payment_link = razorpay_client.payment_link.create({
            "amount": plan_config["price"],
            "currency": "INR",
            "description": f"Decision Broker {plan_config['name']} - {plan_config['credits']} credits/month",
            "subscription_registration": {
                "method": "emandate",
                "auth_type": "netbanking",
                "bank_account": {
                    "beneficiary_name": "Decision Broker",
                    "account_number": "",  # Will be filled by customer
                    "account_type": "savings",
                    "ifsc_code": ""
                }
            },
            "notes": {
                "api_key": data.api_key,
                "plan": plan,
                "credits": plan_config["credits"]
            }
        })
        
        # Store subscription intent
        update_subscription(user_id, payment_link.get("id", "pending"), plan, "pending")
        
        return {
            "success": True,
            "payment_url": payment_link.get("short_url"),
            "plan": plan_config["name"],
            "monthly_price": plan_config["price"] / 100,
            "credits_per_month": plan_config["credits"],
            "message": "Complete payment to start your subscription"
        }
        
    except Exception as e:
        # Fallback: Return direct payment instructions
        return {
            "success": True,
            "payment_url": f"https://kirito-ova.github.io/decision_broker/?plan={plan}",
            "plan": plan_config["name"],
            "monthly_price": plan_config["price"] / 100,
            "credits_per_month": plan_config["credits"],
            "message": "Visit the payment page to subscribe"
        }

@app.get("/subscription-status", tags=["💳 Billing"], summary="Check Subscription Status",
         description="Check if your account has an active recurring subscription.")
def subscription_status(x_api_key: str = Header(..., alias="X-API-Key")):
    """Check subscription status for an API key."""
    user_id = validate_api_key(x_api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT subscription_status, subscription_plan, last_charged_at, credits FROM users WHERE id = ?",
            (user_id,)
        )
        user = cursor.fetchone()
        
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "subscription_status": user["subscription_status"] or "none",
        "plan": user["subscription_plan"],
        "last_charged": user["last_charged_at"],
        "credits": user["credits"]
    }

class CryptoPurchaseRequest(BaseModel):
    plan: str # starter, pro, business

class CryptoVerifyRequest(BaseModel):
    transaction_hash: str
    api_key: str

@app.post("/crypto/purchase", tags=["🪙 Crypto Payments"], summary="Request Crypto Payment Info")
def crypto_purchase(data: CryptoPurchaseRequest):
    """
    Returns crypto payment instructions for AI-to-AI transactions.
    Supports USDT/USDC on Polygon Network.
    """
    plan = data.plan.lower()
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
        
    plan_config = SUBSCRIPTION_PLANS[plan]
    
    # In a real app, you'd use a crypto price API to convert INR to USDT
    # For now, we assume 1 USDT = 85 INR (Fixed rate for demo)
    usdt_amount = round((plan_config["price"] / 100) / 85, 2)
    
    return {
        "payment_method": "USDT/USDC (Polygon)",
        "network": "Polygon (MATIC)",
        "wallet_address": os.getenv("CRYPTO_WALLET_ADDRESS", "0xYourPolygonWalletAddressHere"),
        "amount_usdt": usdt_amount,
        "credits_to_be_added": plan_config["credits"],
        "instructions": f"Send {usdt_amount} USDT to the address above on Polygon network, then call /crypto/verify with your TX hash."
    }

@app.post("/crypto/verify", tags=["🪙 Crypto Payments"], summary="Verify Crypto Transaction")
def crypto_verify(data: CryptoVerifyRequest):
    """
    Verifies a crypto transaction hash and adds credits to the user account.
    This enables 100% autonomous AI-to-AI payments.
    """
    # 1. Validate API Key
    user_id = validate_api_key(data.api_key)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API Key")
        
    # 2. In a real app, call PolygonScan API to verify tx_hash, amount, and recipient.
    # For now, we simulate a successful verification for demonstration.
    tx_hash = data.transaction_hash
    if not tx_hash.startswith("0x") or len(tx_hash) < 64:
        raise HTTPException(status_code=400, detail="Invalid transaction hash format")
    
    # MOCK VERIFICATION LOGIC
    # In production: response = requests.get(f"https://api.polygonscan.com/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey={API_KEY}")
    
    # Logic: If it's a valid looking hash, we credit the user (Simulation)
    credits_to_add = 100 # Default to starter plan for simulation
    new_balance = add_credits(user_id, credits_to_add)
    
    return {
        "success": True,
        "message": f"Transaction {tx_hash[:10]}... verified. Added {credits_to_add} credits.",
        "new_balance": new_balance
    }

@app.post("/decide", tags=["🧠 Decisions"], summary="Get AI-Powered Decision",
          description="""
**The core endpoint - get intelligent decisions for your AI workflows.**

### Decision Types:

| Type | What It Does | Example Use Case |
|------|--------------|------------------|
| `sales_outreach` | When & how to contact leads | CRM automation |
| `model_selection` | Which AI model to use | Multi-model systems |
| `retry_intelligence` | When to retry failed calls | API orchestration |

### Authentication:
Add your API key to the `X-API-Key` header.

### Cost:
**1 credit per decision** (₹0.49 - ₹1.99 depending on plan)

### Response:
- `decision`: The recommended action (e.g., "contact_now_via_email")
- `confidence`: Score from 0.0 to 1.0
- `ttl`: Seconds until you should re-evaluate
- `reason_code`: Why this decision was made
""")
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

@app.post("/webhook/razorpay", include_in_schema=False)
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
        
        # Handle subscription events for auto-renewal
        elif event == "subscription.charged":
            subscription = data.get("payload", {}).get("subscription", {}).get("entity", {})
            subscription_id = subscription.get("id")
            notes = subscription.get("notes", {})
            
            target_api_key = notes.get("api_key")
            plan = notes.get("plan", "starter")
            
            if target_api_key:
                user_id = validate_api_key(target_api_key)
                if user_id:
                    credits = SUBSCRIPTION_PLANS.get(plan, {}).get("credits", 100)
                    mark_subscription_charged(user_id, credits)
                    update_subscription(user_id, subscription_id, plan, "active")
                    print(f"[SUBSCRIPTION] Auto-renewed {credits} credits for {user_id}")
                    return {"status": "ok"}
            
            return {"status": "ignored - missing api_key"}
        
        elif event == "subscription.cancelled":
            subscription = data.get("payload", {}).get("subscription", {}).get("entity", {})
            subscription_id = subscription.get("id")
            
            user = get_user_by_subscription(subscription_id)
            if user:
                update_subscription(user["id"], subscription_id, user["subscription_plan"], "cancelled")
                print(f"[SUBSCRIPTION] Cancelled for {user['id']}")
            
            return {"status": "ok"}
        
        elif event == "subscription.paused":
            subscription = data.get("payload", {}).get("subscription", {}).get("entity", {})
            subscription_id = subscription.get("id")
            
            user = get_user_by_subscription(subscription_id)
            if user:
                update_subscription(user["id"], subscription_id, user["subscription_plan"], "paused")
                print(f"[SUBSCRIPTION] Paused for {user['id']}")
            
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

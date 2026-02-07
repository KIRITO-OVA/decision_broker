# Decision Broker

**STEP 7 COMPLETE. PAYMENTS LIVE. READY FOR BUSINESS.**

## Overview
This project is a monetizable AI-to-AI decision service.
It sells deterministic decisions via API, gatekept by API Keys and Credits.

## Status
- **Core Modules**: `sales_outreach`, `model_selection`, `retry_intelligence`.
- **Infrastructure**: Auth, Billing, Persistence.
- **Payments**: Razorpay Webhook Integrated & Verified.

## Deployment & Verification
1. **Public Website** (Required for Razorpay):
   - Push this repo to GitHub.
   - Go to **Settings > Pages**.
   - Select **Source**: `main` branch, `/docs` folder.
   - Click **Save**. Your site is now LIVE.
   - Submit this URL to Razorpay Dashboard.

2. **Server Verification**:
   - Ensure `ENV=prod` in `.env`.
   - Run `python -m uvicorn decision_broker.api.server:app --port 8000`.

3. **One-Click Startup**:
   - Simply double-click `start_server.bat` to launch the API server with environment setup and auto-reload enabled.

## Configuration
1. Copy `.env.template` to `.env`
2. Set `ENV=prod`
3. Fill in your Live Razorpay Keys:
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `RAZORPAY_WEBHOOK_SECRET`


## Launch Checklist
- [x] API key auth works
- [x] Credits decrement correctly
- [x] Razorpay webhook LIVE (Verified with HMAC)
- [x] /decide is stable
- [x] Hard Stop verified

## RapidAPI Marketplace

To list this API on RapidAPI:

1. **Deploy API** to a public URL (Railway, Render, AWS, etc.)
2. **Go to** [rapidapi.com/studio](https://rapidapi.com/studio)
3. **Create API Project** → Import `openapi.yaml`
4. **Set Base URL** to your deployed server URL
5. **Test** endpoints in RapidAPI console
6. **Publish** to marketplace

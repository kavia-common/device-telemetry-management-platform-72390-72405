# Device Telemetry Backend (FastAPI)

Features:
- JWT auth (signup/login)
- Device registration and listing
- Telemetry ingestion via MQTT or HTTP
- Hourly/Daily rollups
- Threshold and anomaly alerts
- Email notifications for premium users
- Payments integrations: Stripe and Razorpay (webhook handling)
- Firebase Firestore storage

Run locally:
1. Create and populate .env from .env.example.
2. Install deps:
   pip install -r requirements.txt
3. Start server:
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

OpenAPI docs: /docs

Notes:
- MQTT uses asyncio-mqtt; if MQTT is not available, set MQTT_ENABLED=false.
- For Stripe/Razorpay production deployments, use official SDKs to create sessions/orders and verify webhooks.
- Firestore: set FIREBASE_PROJECT_ID and FIREBASE_CREDENTIALS_JSON (file path or JSON).

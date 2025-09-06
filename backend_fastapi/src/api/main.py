import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from .routes import auth, devices, telemetry, alerts, payments, health
from .core.config import settings
from .core.scheduler import Scheduler
from .services.mqtt_service import mqtt_client_singleton
from .services.firestore_service import init_firestore

# Initialize logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("app")

# Create FastAPI app with metadata and tags for OpenAPI
app = FastAPI(
    title="Device Telemetry Backend",
    description=(
        "Backend API for device telemetry management, featuring JWT auth, device registration, MQTT ingestion, "
        "hourly/daily rollups, threshold/anomaly alerts, email notifications for premium users, payments via Stripe/Razorpay, "
        "and Firebase Firestore integration."
    ),
    version="1.0.0",
    contact={"name": "Platform Support", "email": "support@example.com"},
    license_info={"name": "Proprietary"},
    terms_of_service="https://example.com/terms",
    openapi_tags=[
        {"name": "health", "description": "Service health and diagnostics"},
        {"name": "auth", "description": "JWT authentication and user profile"},
        {"name": "devices", "description": "Device registration and management"},
        {"name": "telemetry", "description": "Telemetry ingestion and retrieval"},
        {"name": "alerts", "description": "Threshold and anomaly alerts"},
        {"name": "payments", "description": "Subscriptions, billing and webhooks"},
        {"name": "websocket", "description": "Real-time MQTT and WebSocket usage notes"},
    ],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
@app.get(
    "/docs/websocket",
    tags=["websocket"],
    summary="WebSocket usage help",
    description="Provides usage note for establishing WebSocket connections for real-time updates."
)
def websocket_usage_note():
    """
    This route provides instructions for connecting to WebSocket feeds for real-time telemetry/alerts.
    - Telemetry stream: ws://<host>/ws/telemetry/{device_id}
    - Alerts stream: ws://<host>/ws/alerts

    Messages are in JSON lines, carrying event and payload fields.
    """
    return {
        "telemetry_ws": "/ws/telemetry/{device_id}",
        "alerts_ws": "/ws/alerts",
        "notes": "Authenticate via standard JWT in query string token parameter or via header if your client supports custom headers for WS."
    }


# Include Routers
app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(payments.router, prefix="/payments", tags=["payments"])


@app.on_event("startup")
async def on_startup():
    """
    Initialize Firestore, MQTT client and start the scheduler for rollups and alert checks.
    """
    logger.info("Starting application...")
    init_firestore()

    # Start MQTT client if configured
    if settings.MQTT_ENABLED:
        await mqtt_client_singleton.connect()

    # Start scheduler for background rollups and alert checks
    Scheduler.start()


@app.on_event("shutdown")
async def on_shutdown():
    """
    Gracefully shutdown MQTT client and scheduler.
    """
    logger.info("Shutting down application...")
    if settings.MQTT_ENABLED:
        await mqtt_client_singleton.disconnect()
    Scheduler.stop()


def custom_openapi():
    """
    Customize OpenAPI schema with OAuth2/JWT security schemes.
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Provide the JWT token obtained from /auth/login"
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

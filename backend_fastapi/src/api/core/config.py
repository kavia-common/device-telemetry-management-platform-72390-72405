import os
from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env automatically if present
load_dotenv()


class Settings(BaseModel):
    """App settings loaded from environment variables."""
    ENV: str = Field(default=os.getenv("ENV", "development"), description="Environment name")
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "INFO"), description="Logging level")
    CORS_ORIGINS: str = Field(default=os.getenv("CORS_ORIGINS", "*"), description="CORS allowed origins")

    # Security
    JWT_SECRET_KEY: str = Field(default=os.getenv("JWT_SECRET_KEY", ""), description="Secret key for JWT")
    JWT_ALGORITHM: str = Field(default=os.getenv("JWT_ALGORITHM", "HS256"), description="Algorithm for JWT")
    JWT_EXPIRES_MINUTES: int = Field(default=int(os.getenv("JWT_EXPIRES_MINUTES", "60")), description="JWT expiration in minutes")

    # Firebase
    FIREBASE_PROJECT_ID: str = Field(default=os.getenv("FIREBASE_PROJECT_ID", ""), description="Firebase project ID")
    FIREBASE_CREDENTIALS_JSON: str = Field(default=os.getenv("FIREBASE_CREDENTIALS_JSON", ""), description="Path to Firebase credentials JSON or raw JSON string")
    FIREBASE_EMULATOR: bool = Field(default=os.getenv("FIREBASE_EMULATOR", "false").lower() == "true", description="Use Firestore emulator")

    # MQTT
    MQTT_ENABLED: bool = Field(default=os.getenv("MQTT_ENABLED", "true").lower() == "true", description="Enable MQTT client")
    MQTT_BROKER_URL: str = Field(default=os.getenv("MQTT_BROKER_URL", "localhost"), description="MQTT broker host")
    MQTT_BROKER_PORT: int = Field(default=int(os.getenv("MQTT_BROKER_PORT", "1883")), description="MQTT broker port")
    MQTT_USERNAME: str = Field(default=os.getenv("MQTT_USERNAME", ""), description="MQTT username")
    MQTT_PASSWORD: str = Field(default=os.getenv("MQTT_PASSWORD", ""), description="MQTT password")
    MQTT_TELEMETRY_TOPIC_TEMPLATE: str = Field(default=os.getenv("MQTT_TELEMETRY_TOPIC_TEMPLATE", "devices/{device_id}/telemetry"), description="Telemetry topic template")

    # Email (for premium alerts)
    EMAIL_FROM: str = Field(default=os.getenv("EMAIL_FROM", "no-reply@example.com"), description="From email")
    SMTP_HOST: str = Field(default=os.getenv("SMTP_HOST", ""), description="SMTP server host")
    SMTP_PORT: int = Field(default=int(os.getenv("SMTP_PORT", "587")), description="SMTP port")
    SMTP_USER: str = Field(default=os.getenv("SMTP_USER", ""), description="SMTP username")
    SMTP_PASSWORD: str = Field(default=os.getenv("SMTP_PASSWORD", ""), description="SMTP password")
    EMAIL_ENABLED: bool = Field(default=os.getenv("EMAIL_ENABLED", "false").lower() == "true", description="Enable email notifications")

    # Stripe/Razorpay
    STRIPE_SECRET_KEY: str = Field(default=os.getenv("STRIPE_SECRET_KEY", ""), description="Stripe secret")
    STRIPE_WEBHOOK_SECRET: str = Field(default=os.getenv("STRIPE_WEBHOOK_SECRET", ""), description="Stripe webhook secret")
    RAZORPAY_KEY_ID: str = Field(default=os.getenv("RAZORPAY_KEY_ID", ""), description="Razorpay key id")
    RAZORPAY_KEY_SECRET: str = Field(default=os.getenv("RAZORPAY_KEY_SECRET", ""), description="Razorpay secret")
    RAZORPAY_WEBHOOK_SECRET: str = Field(default=os.getenv("RAZORPAY_WEBHOOK_SECRET", ""), description="Razorpay webhook secret")

    # Feature flags
    PREMIUM_FEATURES_ENABLED: bool = Field(default=os.getenv("PREMIUM_FEATURES_ENABLED", "true").lower() == "true", description="Enable premium features")
    ANOMALY_DETECTION_ENABLED: bool = Field(default=os.getenv("ANOMALY_DETECTION_ENABLED", "true").lower() == "true", description="Enable anomaly detection")

    # Scheduler
    ROLLUP_SCHEDULE_CRON: str = Field(default=os.getenv("ROLLUP_SCHEDULE_CRON", "0 * * * *"), description="Cron for hourly rollups")
    DAILY_ROLLUP_SCHEDULE_CRON: str = Field(default=os.getenv("DAILY_ROLLUP_SCHEDULE_CRON", "0 0 * * *"), description="Cron for daily rollups")


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


settings = get_settings()

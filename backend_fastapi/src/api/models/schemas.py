from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# PUBLIC_INTERFACE
class TokenResponse(BaseModel):
    """JWT token response model."""
    access_token: str = Field(..., description="JWT Bearer token")
    token_type: str = Field(default="bearer", description="Token type")


# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """User signup request."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")


# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


# PUBLIC_INTERFACE
class UserProfile(BaseModel):
    """User profile model."""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    is_premium: bool = Field(default=False, description="Premium subscription status")


# PUBLIC_INTERFACE
class DeviceCreate(BaseModel):
    """Device registration payload."""
    name: str = Field(..., description="Device name")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional device metadata")


# PUBLIC_INTERFACE
class Device(BaseModel):
    """Device model."""
    id: str = Field(..., description="Device ID")
    name: str = Field(..., description="Device name")
    owner_id: str = Field(..., description="Owner user ID")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata map")
    registered_at: int = Field(..., description="Unix timestamp of registration")


# PUBLIC_INTERFACE
class TelemetryIngest(BaseModel):
    """Telemetry ingestion payload."""
    device_id: str = Field(..., description="Device ID")
    ts: int = Field(..., description="Event timestamp (unix seconds)")
    metrics: Dict[str, float] = Field(..., description="Key/value metrics e.g., {'temp': 21.3}")


# PUBLIC_INTERFACE
class TelemetryQuery(BaseModel):
    """Telemetry query filters."""
    device_id: str = Field(..., description="Device ID")
    start_ts: int = Field(..., description="Start timestamp (inclusive)")
    end_ts: int = Field(..., description="End timestamp (exclusive)")
    limit: int = Field(default=500, description="Max records to return")


# PUBLIC_INTERFACE
class ThresholdRule(BaseModel):
    """Threshold rule definition."""
    id: Optional[str] = Field(default=None, description="Rule ID")
    device_id: str = Field(..., description="Device ID")
    metric: str = Field(..., description="Metric name")
    op: str = Field(..., description="Comparison operator: gt, gte, lt, lte, eq, ne")
    value: float = Field(..., description="Threshold value")
    notify_email: bool = Field(default=False, description="Send email notification when triggered")


# PUBLIC_INTERFACE
class Alert(BaseModel):
    """Alert record model."""
    id: Optional[str] = Field(default=None, description="Alert ID")
    device_id: str = Field(..., description="Device ID")
    rule_id: Optional[str] = Field(default=None, description="Rule ID if threshold-based")
    ts: int = Field(..., description="Timestamp")
    message: str = Field(..., description="Alert message")
    severity: str = Field(default="warning", description="Severity level")


# PUBLIC_INTERFACE
class RollupRecord(BaseModel):
    """Rollup data record."""
    device_id: str = Field(..., description="Device ID")
    metric: str = Field(..., description="Metric")
    period: str = Field(..., description="hourly or daily")
    ts: int = Field(..., description="Period timestamp")
    avg: float = Field(..., description="Average value")
    min: float = Field(..., description="Min value")
    max: float = Field(..., description="Max value")
    count: int = Field(..., description="Number of samples")


# PUBLIC_INTERFACE
class StripeCheckoutRequest(BaseModel):
    """Create a Stripe checkout session."""
    price_id: str = Field(..., description="Stripe price ID")
    success_url: str = Field(..., description="Success redirect URL")
    cancel_url: str = Field(..., description="Cancel redirect URL")


# PUBLIC_INTERFACE
class RazorpayOrderRequest(BaseModel):
    """Create a Razorpay order."""
    amount: int = Field(..., description="Amount in smallest currency unit")
    currency: str = Field(default="INR", description="Currency code")
    receipt: str = Field(..., description="Client-generated receipt id")

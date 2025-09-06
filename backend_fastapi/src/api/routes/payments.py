import json
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request, Depends
from ..models.schemas import StripeCheckoutRequest, RazorpayOrderRequest, UserProfile
from ..core.config import settings
from ..dependencies.auth import get_current_user
from ..services.firestore_service import set_user_premium

router = APIRouter()


# PUBLIC_INTERFACE
@router.post("/stripe/checkout", summary="Create Stripe checkout session")
def stripe_checkout(body: StripeCheckoutRequest, user: UserProfile = Depends(get_current_user)):
    """
    Returns a placeholder checkout URL for Stripe. In real deployment, use stripe SDK to create a session.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=400, detail="Stripe not configured")
    # Here, we would use stripe SDK. For portability, return a mock URL containing price_id.
    return {
        "checkout_url": f"https://checkout.stripe.com/pay/{body.price_id}?client_reference_id={user.id}"
    }


# PUBLIC_INTERFACE
@router.post("/stripe/webhook", summary="Stripe webhook handler")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    """
    Handle Stripe checkout completion and mark user as premium.
    Expects json payload that includes client_reference_id (user id).
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Stripe webhook secret not configured")
    payload = await request.body()
    # In production, verify via stripe SDK and check that the signature in header matches.
    # For this template we just parse and proceed.
    try:
        event = json.loads(payload.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")
    data = event.get("data", {})
    user_id = data.get("client_reference_id")
    if user_id:
        set_user_premium(user_id, True)
    return {"status": "ok"}


# PUBLIC_INTERFACE
@router.post("/razorpay/order", summary="Create Razorpay order")
def razorpay_order(body: RazorpayOrderRequest, user: UserProfile = Depends(get_current_user)):
    """
    Returns a placeholder order creation response. Use official Razorpay SDK in production.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=400, detail="Razorpay not configured")
    order_id = f"order_{body.receipt}"
    return {"id": order_id, "amount": body.amount, "currency": body.currency, "receipt": body.receipt}


# PUBLIC_INTERFACE
@router.post("/razorpay/webhook", summary="Razorpay webhook handler")
async def razorpay_webhook(request: Request, x_razorpay_signature: Optional[str] = Header(None)):
    """
    Handle Razorpay webhook and mark user as premium when payment is captured.
    Expects payload containing notes.user_id or similar mapping.
    """
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Razorpay webhook secret not configured")
    payload = await request.body()
    # In production, verify signature using official Razorpay SDK with x_razorpay_signature header.
    try:
        event = json.loads(payload.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")
    notes = (event.get("payload", {}).get("payment", {}).get("entity", {}).get("notes", {})) or {}
    user_id = notes.get("user_id")
    if user_id:
        set_user_premium(user_id, True)
    return {"status": "ok"}

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.oauth2 import service_account
from ..core.config import settings

logger = logging.getLogger("firestore")

_db: Optional[firestore.Client] = None


def init_firestore():
    """
    Initialize Firestore client. Uses emulator if FIREBASE_EMULATOR is true.
    """
    global _db
    if _db:
        return

    if settings.FIREBASE_EMULATOR:
        os.environ["FIRESTORE_EMULATOR_HOST"] = os.getenv("FIRESTORE_EMULATOR_HOST", "localhost:8080")
        logger.warning("Using Firestore emulator at %s", os.environ["FIRESTORE_EMULATOR_HOST"])

    creds = None
    if settings.FIREBASE_CREDENTIALS_JSON:
        try:
            if os.path.isfile(settings.FIREBASE_CREDENTIALS_JSON):
                creds = service_account.Credentials.from_service_account_file(settings.FIREBASE_CREDENTIALS_JSON)
            else:
                creds = service_account.Credentials.from_service_account_info(json.loads(settings.FIREBASE_CREDENTIALS_JSON))
        except Exception as e:
            logger.error("Failed to load Firebase credentials: %s", e)
            creds = None

    _db = firestore.Client(project=settings.FIREBASE_PROJECT_ID or None, credentials=creds)


def get_db() -> firestore.Client:
    """
    Returns initialized Firestore client.
    """
    if not _db:
        init_firestore()
    assert _db is not None
    return _db


# PUBLIC_INTERFACE
def create_user(email: str, password_hash: str) -> str:
    """Create a user document and return user ID."""
    db = get_db()
    doc = db.collection("users").document()
    doc.set({"email": email, "password_hash": password_hash, "is_premium": False, "created_at": int(time.time())})
    return doc.id


# PUBLIC_INTERFACE
def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email."""
    db = get_db()
    q = db.collection("users").where("email", "==", email).limit(1).stream()
    for d in q:
        doc = d.to_dict()
        doc["id"] = d.id
        return doc
    return None


# PUBLIC_INTERFACE
def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID."""
    db = get_db()
    d = db.collection("users").document(user_id).get()
    if d.exists:
        doc = d.to_dict()
        doc["id"] = d.id
        return doc
    return None


# PUBLIC_INTERFACE
def set_user_premium(user_id: str, is_premium: bool):
    """Update user's premium status."""
    db = get_db()
    db.collection("users").document(user_id).update({"is_premium": is_premium})


# PUBLIC_INTERFACE
def register_device(owner_id: str, name: str, metadata: Optional[Dict[str, Any]]) -> str:
    """Register a device for a user and return device id."""
    db = get_db()
    doc = db.collection("devices").document()
    doc.set({
        "owner_id": owner_id,
        "name": name,
        "metadata": metadata or {},
        "registered_at": int(time.time()),
        "active": True
    })
    return doc.id


# PUBLIC_INTERFACE
def list_user_devices(owner_id: str) -> List[Dict[str, Any]]:
    """List devices for a user."""
    db = get_db()
    res = []
    for d in db.collection("devices").where("owner_id", "==", owner_id).stream():
        doc = d.to_dict()
        doc["id"] = d.id
        res.append(doc)
    return res


# PUBLIC_INTERFACE
def get_device(device_id: str) -> Optional[Dict[str, Any]]:
    """Get device by id."""
    db = get_db()
    d = db.collection("devices").document(device_id).get()
    if d.exists:
        doc = d.to_dict()
        doc["id"] = d.id
        return doc
    return None


# PUBLIC_INTERFACE
def upsert_telemetry(device_id: str, ts: int, metrics: Dict[str, float]):
    """Insert telemetry point."""
    db = get_db()
    doc = db.collection("telemetry").document()
    doc.set({
        "device_id": device_id,
        "ts": ts,
        "metrics": metrics
    })


# PUBLIC_INTERFACE
def query_telemetry(device_id: str, start_ts: int, end_ts: int, limit: int = 500) -> List[Dict[str, Any]]:
    """Query telemetry points by time range."""
    db = get_db()
    res = []
    q = (
        db.collection("telemetry")
        .where("device_id", "==", device_id)
        .where("ts", ">=", start_ts)
        .where("ts", "<", end_ts)
        .order_by("ts")
        .limit(limit)
        .stream()
    )
    for d in q:
        doc = d.to_dict()
        doc["id"] = d.id
        res.append(doc)
    return res


# PUBLIC_INTERFACE
def save_alert(alert: Dict[str, Any]) -> str:
    """Save an alert entry and return alert id."""
    db = get_db()
    doc = db.collection("alerts").document()
    doc.set(alert)
    return doc.id


# PUBLIC_INTERFACE
def list_alerts(device_id: Optional[str], limit: int = 100) -> List[Dict[str, Any]]:
    """List alerts optionally filtered by device."""
    db = get_db()
    col = db.collection("alerts")
    q = col if not device_id else col.where("device_id", "==", device_id)
    res = []
    for d in q.order_by("ts", direction=firestore.Query.DESCENDING).limit(limit).stream():
        doc = d.to_dict()
        doc["id"] = d.id
        res.append(doc)
    return res


# PUBLIC_INTERFACE
def save_threshold_rule(rule: Dict[str, Any]) -> str:
    """Create a threshold rule."""
    db = get_db()
    doc = db.collection("threshold_rules").document()
    doc.set(rule)
    return doc.id


# PUBLIC_INTERFACE
def list_threshold_rules(device_id: str) -> List[Dict[str, Any]]:
    """List threshold rules for a device."""
    db = get_db()
    res = []
    for d in db.collection("threshold_rules").where("device_id", "==", device_id).stream():
        rule = d.to_dict()
        rule["id"] = d.id
        res.append(rule)
    return res


# PUBLIC_INTERFACE
def delete_threshold_rule(rule_id: str):
    """Delete threshold rule."""
    db = get_db()
    db.collection("threshold_rules").document(rule_id).delete()


# PUBLIC_INTERFACE
def save_rollup(record: Dict[str, Any]):
    """Save a rollup record."""
    db = get_db()
    doc = db.collection("rollups").document()
    doc.set(record)


# PUBLIC_INTERFACE
def query_rollups(device_id: str, metric: str, period: str, start_ts: int, end_ts: int, limit: int = 500) -> List[Dict[str, Any]]:
    """Query rollups for a period."""
    db = get_db()
    res = []
    q = (
        db.collection("rollups")
        .where("device_id", "==", device_id)
        .where("metric", "==", metric)
        .where("period", "==", period)
        .where("ts", ">=", start_ts)
        .where("ts", "<", end_ts)
        .order_by("ts")
        .limit(limit)
        .stream()
    )
    for d in q:
        doc = d.to_dict()
        doc["id"] = d.id
        res.append(doc)
    return res

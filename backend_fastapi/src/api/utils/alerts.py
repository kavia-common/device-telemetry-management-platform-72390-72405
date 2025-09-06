import logging
import time
from typing import Dict, List

from ..services.firestore_service import list_threshold_rules, save_alert, query_telemetry, get_db
from ..services.email_service import send_email
from ..core.config import settings

logger = logging.getLogger("alerts")


def _compare(op: str, val: float, threshold: float) -> bool:
    if op == "gt":
        return val > threshold
    if op == "gte":
        return val >= threshold
    if op == "lt":
        return val < threshold
    if op == "lte":
        return val <= threshold
    if op == "eq":
        return val == threshold
    if op == "ne":
        return val != threshold
    return False


async def _maybe_notify_email(user_email: str, message: str):
    send_email([user_email], subject="Device Alert", body=message)


# PUBLIC_INTERFACE
async def evaluate_thresholds_for_device(device_id: str, ts: int, metrics: Dict[str, float]):
    """Evaluate threshold rules for a device given a telemetry record."""
    rules = list_threshold_rules(device_id)
    if not rules:
        return
    # Get user email for notification
    db = get_db()
    device_doc = db.collection("devices").document(device_id).get()
    user_email = None
    if device_doc.exists:
        owner_id = device_doc.to_dict().get("owner_id")
        user_doc = db.collection("users").document(owner_id).get()
        if user_doc.exists:
            user_email = user_doc.to_dict().get("email")
            is_premium = user_doc.to_dict().get("is_premium", False)
        else:
            is_premium = False
    else:
        is_premium = False

    for r in rules:
        metric = r.get("metric")
        if metric not in metrics:
            continue
        val = float(metrics[metric])
        if _compare(r.get("op"), val, float(r.get("value"))):
            message = f"Threshold alert on {device_id} {metric} {r.get('op')} {r.get('value')} (value={val})"
            alert = {
                "device_id": device_id,
                "rule_id": r.get("id"),
                "ts": ts,
                "message": message,
                "severity": "warning",
            }
            save_alert(alert)
            if is_premium and r.get("notify_email") and user_email:
                await _maybe_notify_email(user_email, message)


# PUBLIC_INTERFACE
async def periodic_anomaly_check():
    """Run simple anomaly detection across devices (premium feature)."""
    if not settings.ANOMALY_DETECTION_ENABLED:
        return
    db = get_db()
    devices = db.collection("devices").stream()
    now = int(time.time())
    start = now - 3600
    for d in devices:
        device_id = d.id
        points = query_telemetry(device_id, start, now, limit=5000)
        if not points:
            continue
        # Simple anomaly: if any metric has > 3x stddev from mean
        # Build series per metric
        series: Dict[str, List[float]] = {}
        for p in points:
            for k, v in p.get("metrics", {}).items():
                series.setdefault(k, []).append(float(v))
        for metric, vals in series.items():
            if len(vals) < 10:
                continue
            mean = sum(vals) / len(vals)
            var = sum((x - mean) ** 2 for x in vals) / len(vals)
            std = var ** 0.5
            if std == 0:
                continue
            # last value deviates
            last = vals[-1]
            if abs(last - mean) > 3 * std:
                message = f"Anomaly detected on {device_id} metric={metric} mean={mean:.2f} std={std:.2f} last={last:.2f}"
                alert = {
                    "device_id": device_id,
                    "rule_id": None,
                    "ts": now,
                    "message": message,
                    "severity": "critical",
                }
                save_alert(alert)

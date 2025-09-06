import logging
import time
from typing import Dict, List

from ..services.firestore_service import query_telemetry, save_rollup, get_db

logger = logging.getLogger("rollups")


def _aggregate(points: List[Dict], metric: str):
    vals = [float(p["metrics"].get(metric)) for p in points if metric in p.get("metrics", {})]
    if not vals:
        return None
    return {
        "avg": sum(vals) / len(vals),
        "min": min(vals),
        "max": max(vals),
        "count": len(vals),
    }


async def _rollup_for_window(device_id: str, start_ts: int, end_ts: int, period: str):
    # Pick all metrics observed in window
    points = query_telemetry(device_id, start_ts, end_ts, limit=10000)
    metric_keys = set()
    for p in points:
        metric_keys.update(p.get("metrics", {}).keys())
    for metric in metric_keys:
        agg = _aggregate(points, metric)
        if agg:
            save_rollup({
                "device_id": device_id,
                "metric": metric,
                "period": period,
                "ts": start_ts,
                **agg,
            })


# PUBLIC_INTERFACE
async def run_hourly_rollups():
    """Compute hourly rollups for all devices."""
    logger.info("Running hourly rollups...")
    now = int(time.time())
    hour_start = now - (now % 3600)
    hour_end = hour_start + 3600

    # Iterate devices
    db = get_db()
    devices = db.collection("devices").stream()
    for d in devices:
        device_id = d.id
        await _rollup_for_window(device_id, hour_start, hour_end, "hourly")


# PUBLIC_INTERFACE
async def run_daily_rollups():
    """Compute daily rollups for all devices."""
    logger.info("Running daily rollups...")
    now = int(time.time())
    day_start = now - (now % 86400)
    day_end = day_start + 86400

    db = get_db()
    devices = db.collection("devices").stream()
    for d in devices:
        device_id = d.id
        await _rollup_for_window(device_id, day_start, day_end, "daily")

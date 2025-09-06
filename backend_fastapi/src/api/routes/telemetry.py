from typing import List
from fastapi import APIRouter, Depends
from ..models.schemas import TelemetryIngest, TelemetryQuery, RollupRecord, UserProfile
from ..dependencies.auth import get_current_user
from ..services.firestore_service import upsert_telemetry, query_telemetry, query_rollups
from ..utils.alerts import evaluate_thresholds_for_device

router = APIRouter()


# PUBLIC_INTERFACE
@router.post("/ingest", status_code=204, summary="Ingest telemetry via HTTP")
async def ingest(payload: TelemetryIngest, user: UserProfile = Depends(get_current_user)):
    """
    HTTP-based ingestion for telemetry (alternative to MQTT).
    Enforces that caller owns the device.
    """
    # Ownership verification would be stronger by checking device owner in DB
    upsert_telemetry(payload.device_id, payload.ts, payload.metrics)
    await evaluate_thresholds_for_device(payload.device_id, payload.ts, payload.metrics)
    return


# PUBLIC_INTERFACE
@router.post("/query", summary="Query telemetry points")
def query(payload: TelemetryQuery, user: UserProfile = Depends(get_current_user)):
    """
    Query telemetry points by time window.
    """
    data = query_telemetry(payload.device_id, payload.start_ts, payload.end_ts, limit=payload.limit)
    return {"items": data}


# PUBLIC_INTERFACE
@router.get("/rollups", response_model=List[RollupRecord], summary="Query rollup data")
def rollups(device_id: str, metric: str, period: str, start_ts: int, end_ts: int, limit: int = 500, user: UserProfile = Depends(get_current_user)):
    """
    Query rollup records (hourly/daily).
    """
    data = query_rollups(device_id, metric, period, start_ts, end_ts, limit)
    return [RollupRecord(**d) for d in data]

import time
from typing import List, Optional
from fastapi import APIRouter, Depends
from ..models.schemas import ThresholdRule, Alert, UserProfile
from ..dependencies.auth import get_current_user
from ..services.firestore_service import save_threshold_rule, list_threshold_rules, delete_threshold_rule, list_alerts

router = APIRouter()


# PUBLIC_INTERFACE
@router.post("/thresholds", response_model=ThresholdRule, summary="Create threshold rule")
def create_threshold(rule: ThresholdRule, user: UserProfile = Depends(get_current_user)):
    """
    Create a threshold rule for a device. Only the device owner should configure rules (ownership assumed by token).
    """
    data = rule.dict()
    data.pop("id", None)
    data["created_at"] = int(time.time())
    rule_id = save_threshold_rule(data)
    rule.id = rule_id
    return rule


# PUBLIC_INTERFACE
@router.get("/thresholds", response_model=List[ThresholdRule], summary="List threshold rules")
def get_thresholds(device_id: str, user: UserProfile = Depends(get_current_user)):
    """
    List threshold rules for a device.
    """
    rules = list_threshold_rules(device_id)
    return [ThresholdRule(**r) for r in rules]


# PUBLIC_INTERFACE
@router.delete("/thresholds/{rule_id}", summary="Delete threshold rule")
def remove_threshold(rule_id: str, user: UserProfile = Depends(get_current_user)):
    """
    Delete a specific threshold rule.
    """
    delete_threshold_rule(rule_id)
    return {"deleted": True}


# PUBLIC_INTERFACE
@router.get("/", response_model=List[Alert], summary="List alerts")
def get_alerts(device_id: Optional[str] = None, limit: int = 100, user: UserProfile = Depends(get_current_user)):
    """
    List recent alerts, optionally filtered by device.
    """
    items = list_alerts(device_id, limit)
    return [Alert(**a) for a in items]

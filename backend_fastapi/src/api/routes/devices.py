from typing import List
from fastapi import APIRouter, Depends
from ..models.schemas import DeviceCreate, Device, UserProfile
from ..dependencies.auth import get_current_user
from ..services.firestore_service import register_device, list_user_devices, get_device

router = APIRouter()


# PUBLIC_INTERFACE
@router.post("/", response_model=Device, summary="Register a new device")
def create_device(payload: DeviceCreate, user: UserProfile = Depends(get_current_user)):
    """
    Register a new device belonging to the current user.
    """
    device_id = register_device(user.id, payload.name, payload.metadata)
    d = get_device(device_id)
    assert d is not None
    return Device(
        id=device_id,
        name=d["name"],
        owner_id=d["owner_id"],
        metadata=d.get("metadata"),
        registered_at=d["registered_at"],
    )


# PUBLIC_INTERFACE
@router.get("/", response_model=List[Device], summary="List my devices")
def my_devices(user: UserProfile = Depends(get_current_user)):
    """
    List all devices registered to the current user.
    """
    devices = list_user_devices(user.id)
    return [
        Device(
            id=d["id"],
            name=d["name"],
            owner_id=d["owner_id"],
            metadata=d.get("metadata"),
            registered_at=d["registered_at"],
        )
        for d in devices
    ]

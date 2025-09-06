from typing import Dict, Any, Optional
from fastapi import Header, HTTPException, status
from ..core.security import verify_token
from ..services.firestore_service import get_user
from ..models.schemas import UserProfile


# PUBLIC_INTERFACE
def get_current_user(authorization: Optional[str] = Header(None)) -> UserProfile:
    """Dependency to decode JWT from Authorization header and return the authenticated user's profile."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload: Dict[str, Any] = verify_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    user_doc = get_user(user_id)
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return UserProfile(id=user_doc["id"], email=user_doc["email"], is_premium=user_doc.get("is_premium", False))

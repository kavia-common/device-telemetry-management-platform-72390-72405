from fastapi import APIRouter, HTTPException, status, Depends
from ..models.schemas import UserCreate, UserLogin, TokenResponse, UserProfile
from ..services.firestore_service import create_user, get_user_by_email
from ..core.security import hash_password, verify_password, create_access_token
from ..core.config import settings
from ..dependencies.auth import get_current_user

router = APIRouter()


# PUBLIC_INTERFACE
@router.post("/signup", response_model=UserProfile, summary="User signup")
def signup(payload: UserCreate):
    """
    Create a new user with email/password.
    """
    existing = get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    pwd_hash = hash_password(payload.password)
    user_id = create_user(payload.email, pwd_hash)
    return UserProfile(id=user_id, email=payload.email, is_premium=False)


# PUBLIC_INTERFACE
@router.post("/login", response_model=TokenResponse, summary="User login to obtain JWT")
def login(payload: UserLogin):
    """
    Authenticate the user and return a JWT token.
    """
    user = get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user["id"], user["email"], user.get("is_premium", False), settings.JWT_EXPIRES_MINUTES)
    return TokenResponse(access_token=token, token_type="bearer")


# PUBLIC_INTERFACE
@router.get("/me", response_model=UserProfile, summary="Get current user profile")
def me(user: UserProfile = Depends(get_current_user)):
    """
    Return the authenticated user's profile.
    """
    return user

import time
import bcrypt
import hmac
import base64
import json
from typing import Dict, Any
from .config import settings

# Minimal JWT encode/decode using HS256 to avoid extra deps
import hashlib


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("utf-8")


def _b64url_decode(s: str) -> bytes:
    pad = 4 - (len(s) % 4)
    if pad and pad < 4:
        s = s + ("=" * pad)
    return base64.urlsafe_b64decode(s.encode("utf-8"))


def _sign(header_b64: str, payload_b64: str, secret: str) -> str:
    to_sign = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), to_sign, hashlib.sha256).digest()
    return _b64url_encode(sig)


def jwt_encode(payload: Dict[str, Any], secret: str, alg: str = "HS256") -> str:
    header = {"typ": "JWT", "alg": alg}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(header_b64, payload_b64, secret)
    return f"{header_b64}.{payload_b64}.{signature}"


def jwt_decode(token: str, secret: str, alg: str = "HS256") -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token")
    header_b64, payload_b64, signature = parts
    expected_sig = _sign(header_b64, payload_b64, secret)
    if not hmac.compare_digest(signature, expected_sig):
        raise ValueError("Invalid signature")
    payload = json.loads(_b64url_decode(payload_b64))
    if "exp" in payload and int(payload["exp"]) < int(time.time()):
        raise ValueError("Token expired")
    return payload


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(sub: str, email: str, is_premium: bool, expires_minutes: int) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "email": email,
        "premium": is_premium,
        "iat": now,
        "exp": now + (expires_minutes * 60),
    }
    return jwt_encode(payload, settings.JWT_SECRET_KEY, alg=settings.JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    return jwt_decode(token, settings.JWT_SECRET_KEY, alg=settings.JWT_ALGORITHM)

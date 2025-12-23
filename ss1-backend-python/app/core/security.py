from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional, Literal, Dict, Any
import re

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TwoFaPurpose = Literal["login", "enable", "disable"]

def hash_value(value: str) -> str:
    return pwd_context.hash(value)

def verify_hash(value: str, hashed: str) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(value, hashed)

def _parse_expires(expires_in: str) -> timedelta:
    """
    Soporta: "10m", "7d", "12h"
    """
    m = re.fullmatch(r"(\d+)([smhd])", expires_in.strip())
    if not m:
        # fallback: 7 días
        return timedelta(days=7)
    n = int(m.group(1))
    unit = m.group(2)
    if unit == "s":
        return timedelta(seconds=n)
    if unit == "m":
        return timedelta(minutes=n)
    if unit == "h":
        return timedelta(hours=n)
    if unit == "d":
        return timedelta(days=n)
    return timedelta(days=7)

def create_access_token(*, subject: str, secret: str, expires_in: str, extra: Dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + _parse_expires(expires_in)
    payload: Dict[str, Any] = {"sub": subject, "iat": int(now.timestamp()), "exp": exp}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
        return None

def create_2fa_challenge(*, user_id: int, purpose: TwoFaPurpose, secret: str, expires_in: str) -> str:
    return create_access_token(
        subject=str(user_id),
        secret=secret,
        expires_in=expires_in,
        extra={"type": "2fa", "purpose": purpose},
    )

def decode_2fa_challenge(challenge_id: str, secret: str) -> Optional[Dict[str, Any]]:
    payload = decode_token(challenge_id, secret)
    if not payload:
        return None
    if payload.get("type") != "2fa":
        return None
    if payload.get("purpose") not in ("login", "enable", "disable"):
        return None
    return payload

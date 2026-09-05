"""Enterprise JWT Session and Token Management Service.

Implements:
- HMAC-SHA256 (HS256) signature verification using PyJWT
- Configurable expiration (default 60 minutes)
- Unique token ID (jti) for cryptographic revocation and logout enforcement
- Strict token revocation blacklist store
"""

from datetime import datetime, timedelta, timezone
import logging
import os
import secrets
from typing import Any, Dict, Optional, Set
import jwt

logger = logging.getLogger("maritime-oil-attribution.security.tokens")

# Retrieve secret key from environment, or generate an ephemeral random key
DEFAULT_SECRET = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
if not DEFAULT_SECRET:
    DEFAULT_SECRET = secrets.token_hex(32)
    logger.warning("No JWT_SECRET_KEY found in environment. Generated ephemeral random secret for session lifecycle.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


class TokenRevocationStore:
    """Thread-safe in-memory store for tracking revoked token JTIs (logout)."""

    def __init__(self):
        self._revoked_jtis: Set[str] = set()

    def revoke_token(self, jti: str) -> None:
        if jti:
            self._revoked_jtis.add(jti)

    def is_revoked(self, jti: str) -> bool:
        return jti in self._revoked_jtis


revocation_store = TokenRevocationStore()


def create_access_token(
    subject: str,
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Encodes a signed JWT access token with unique JTI and expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    jti = secrets.token_hex(16)
    payload = {
        "sub": subject,
        "user_id": user_id,
        "role": role,
        "exp": expire,
        "iat": now,
        "nbf": now,
        "jti": jti,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, DEFAULT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Validates signature, expiration, and revocation status of an access token."""
    try:
        payload = jwt.decode(token, DEFAULT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")

    jti = payload.get("jti")
    if jti and revocation_store.is_revoked(jti):
        raise ValueError("Token has been revoked (session logged out).")

    return payload


def revoke_token(token: str) -> bool:
    """Revokes a token during logout."""
    try:
        payload = decode_access_token(token)
        jti = payload.get("jti")
        if jti:
            revocation_store.revoke_token(jti)
            return True
        return False
    except Exception:
        return False

"""Password hashing + JWT issue/verify. Username/password auth, no external
identity provider (per the approved plan) — JWT is self-issued and
self-verified by this API only.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(hours=12)


def _jwt_secret() -> str:
    secret = os.environ.get("NUDGE_JWT_SECRET")
    if not secret:
        # Dev-only fallback so a fresh checkout doesn't hard-fail before
        # anyone's set up .env — NOT safe for a real deployment. Any token
        # issued with this default becomes invalid the moment a real secret
        # is set, which is the right failure mode (not a silent weak secret).
        return "dev-only-insecure-secret-set-NUDGE_JWT_SECRET-in-.env"
    return secret


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (expired/invalid/etc.) — caller maps to 401."""
    return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])

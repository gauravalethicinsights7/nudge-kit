from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.auth.security import decode_access_token
from api.db_deps import get_db
from schemas.enums import UserRole
from schemas.user import User
from store.user_repo import UserRepo

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}") from e

    user = UserRepo(db).get(UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


def require_role(*roles: UserRole):
    """Dependency factory: 403s unless the current user's role is one of
    `roles`. platform_admin always passes, since admins administer
    everything (consistent with the blueprint's 'Platform admin ... Pack
    changes, user access')."""

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.role != UserRole.platform_admin and user.role not in roles:
            raise HTTPException(status_code=403, detail=f"role '{user.role.value}' cannot perform this action")
        return user

    return _check

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api.auth.deps import get_current_user, require_role
from api.auth.security import create_access_token, hash_password, verify_password
from api.db_deps import get_db
from api.deps import get_brand
from schemas.brand import Brand
from schemas.enums import UserRole
from schemas.user import Tenant, User, UserBrandAccess
from store.user_repo import TenantRepo, UserBrandAccessRepo, UserRepo

router = APIRouter(tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    user: User


class SignupRequest(BaseModel):
    tenant_name: str
    name: str
    email: EmailStr
    password: str


@router.post("/auth/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Creates a brand-new Tenant plus its first user, as platform_admin —
    how a new organization onboards (there's no invite-only gate before the
    first user exists)."""
    if UserRepo(db).get_by_email(body.email) is not None:
        raise HTTPException(status_code=409, detail="a user with this email already exists")

    tenant = TenantRepo(db).add(Tenant(name=body.tenant_name))
    user = User(tenant_id=tenant.id, email=body.email, name=body.name, role=UserRole.platform_admin)
    saved_user = UserRepo(db).add(user, hash_password(body.password))
    token = create_access_token(saved_user.id, saved_user.tenant_id, saved_user.role.value)
    return TokenResponse(access_token=token, user=saved_user)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    found = UserRepo(db).get_by_email(body.email)
    if found is None or not verify_password(body.password, found[1]):
        raise HTTPException(status_code=401, detail="invalid email or password")
    user, _ = found
    token = create_access_token(user.id, user.tenant_id, user.role.value)
    return TokenResponse(access_token=token, user=user)


@router.get("/auth/me", response_model=User)
def me(user: User = Depends(get_current_user)) -> User:
    return user


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


@router.post("/tenants/{tenant_id}/users", response_model=User)
def create_teammate(
    tenant_id: UUID,
    body: CreateUserRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.platform_admin)),
) -> User:
    if admin.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")
    if UserRepo(db).get_by_email(body.email) is not None:
        raise HTTPException(status_code=409, detail="a user with this email already exists")
    new_user = User(tenant_id=tenant_id, email=body.email, name=body.name, role=body.role)
    return UserRepo(db).add(new_user, hash_password(body.password))


@router.get("/tenants/{tenant_id}/users", response_model=list[User])
def list_teammates(
    tenant_id: UUID, db: Session = Depends(get_db), admin: User = Depends(require_role(UserRole.platform_admin))
) -> list[User]:
    if admin.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="tenant not found")
    return UserRepo(db).list_by_tenant(tenant_id)


class GrantAccessRequest(BaseModel):
    user_id: UUID


@router.post("/brands/{brand_id}/access", response_model=UserBrandAccess)
def grant_brand_access(
    brand_id: UUID,
    body: GrantAccessRequest,
    db: Session = Depends(get_db),
    brand: Brand = Depends(get_brand),  # also 404s if brand_id is outside the caller's tenant
    granter: User = Depends(require_role(UserRole.platform_admin, UserRole.brand_manager)),
) -> UserBrandAccess:
    target = UserRepo(db).get(body.user_id)
    if target is None or target.tenant_id != granter.tenant_id:
        raise HTTPException(status_code=404, detail="user not found in this tenant")
    return UserBrandAccessRepo(db).grant(body.user_id, brand.id)

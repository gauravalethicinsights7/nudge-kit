from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from schemas.enums import UserRole
from schemas.user import Tenant, User, UserBrandAccess
from store.orm import TenantORM, UserBrandAccessORM, UserORM


def _tenant_to_pydantic(row: TenantORM) -> Tenant:
    return Tenant(id=row.id, name=row.name, created_at=row.created_at)


def _user_to_pydantic(row: UserORM) -> User:
    return User(id=row.id, tenant_id=row.tenant_id, email=row.email, name=row.name, role=UserRole(row.role), created_at=row.created_at)


class TenantRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, tenant: Tenant) -> Tenant:
        row = TenantORM(id=tenant.id, name=tenant.name, created_at=tenant.created_at)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _tenant_to_pydantic(row)

    def get(self, tenant_id: UUID) -> Tenant | None:
        row = self.session.get(TenantORM, tenant_id)
        return _tenant_to_pydantic(row) if row else None


class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User, password_hash: str) -> User:
        row = UserORM(
            id=user.id, tenant_id=user.tenant_id, email=user.email, name=user.name,
            role=user.role.value, password_hash=password_hash, created_at=user.created_at,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return _user_to_pydantic(row)

    def get(self, user_id: UUID) -> User | None:
        row = self.session.get(UserORM, user_id)
        return _user_to_pydantic(row) if row else None

    def get_by_email(self, email: str) -> tuple[User, str] | None:
        """Returns (user, password_hash) — the hash never leaves this repo otherwise."""
        row = self.session.scalars(select(UserORM).where(UserORM.email == email)).first()
        return (_user_to_pydantic(row), row.password_hash) if row else None

    def list_by_tenant(self, tenant_id: UUID) -> list[User]:
        rows = self.session.scalars(select(UserORM).where(UserORM.tenant_id == tenant_id)).all()
        return [_user_to_pydantic(r) for r in rows]


class UserBrandAccessRepo:
    def __init__(self, session: Session):
        self.session = session

    def grant(self, user_id: UUID, brand_id: UUID) -> UserBrandAccess:
        existing = self.session.scalars(
            select(UserBrandAccessORM).where(UserBrandAccessORM.user_id == user_id, UserBrandAccessORM.brand_id == brand_id)
        ).first()
        if existing:
            return UserBrandAccess(id=existing.id, user_id=existing.user_id, brand_id=existing.brand_id, granted_at=existing.granted_at)
        grant = UserBrandAccess(user_id=user_id, brand_id=brand_id)
        row = UserBrandAccessORM(id=grant.id, user_id=user_id, brand_id=brand_id, granted_at=grant.granted_at)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return UserBrandAccess(id=row.id, user_id=row.user_id, brand_id=row.brand_id, granted_at=row.granted_at)

    def has_access(self, user_id: UUID, brand_id: UUID) -> bool:
        return (
            self.session.scalars(
                select(UserBrandAccessORM).where(UserBrandAccessORM.user_id == user_id, UserBrandAccessORM.brand_id == brand_id)
            ).first()
            is not None
        )

    def list_brand_ids_for_user(self, user_id: UUID) -> list[UUID]:
        rows = self.session.scalars(select(UserBrandAccessORM).where(UserBrandAccessORM.user_id == user_id)).all()
        return [r.brand_id for r in rows]

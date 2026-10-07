"""Platform-level auth entities. Deliberately NOT built on schemas.base.Base —
Tenant/User don't go through the draft->approved human-checkpoint workflow
(CLAUDE.md rule 8 is about brand-plan content, not account records), so they
get their own minimal id/timestamp fields instead of Base's status/version.

User never carries a password field — the hash lives only in UserORM
(store/orm.py), never serialized into an API response.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import EmailStr, Field

from schemas.base import StrictModel, utcnow
from schemas.enums import UserRole


class Tenant(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    created_at: datetime = Field(default_factory=utcnow)


class User(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    email: EmailStr
    name: str
    role: UserRole
    created_at: datetime = Field(default_factory=utcnow)


class UserBrandAccess(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    brand_id: UUID
    granted_at: datetime = Field(default_factory=utcnow)

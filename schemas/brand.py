from __future__ import annotations

from schemas.base import Base
from schemas.enums import LifecycleStage, Market


class Brand(Base):
    name: str
    molecule: str
    indication: str
    market: Market
    lifecycle_stage: LifecycleStage
    company: str
    price_band: str | None = None
    notes: str | None = None

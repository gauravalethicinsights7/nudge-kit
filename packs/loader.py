from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from schemas.enums import Market
from schemas.pack import Pack

PACKS_ROOT = Path(__file__).parent


class PackLoadError(Exception):
    pass


def load_pack(market: Market | str) -> Pack:
    market = Market(market)
    path = PACKS_ROOT / market.value / "pack.yaml"
    if not path.exists():
        raise PackLoadError(f"no pack.yaml for market '{market.value}' at {path}")

    raw = yaml.safe_load(path.read_text())
    try:
        return Pack.model_validate(raw)
    except ValidationError as e:
        raise PackLoadError(f"pack.yaml for '{market.value}' failed validation:\n{e}") from e

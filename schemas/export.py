"""Export every entity's JSON Schema to schemas/_export/<Entity>.schema.json."""

import json
from pathlib import Path

from schemas.registry import ENTITIES

EXPORT_DIR = Path(__file__).parent / "_export"


def export_all() -> list[Path]:
    EXPORT_DIR.mkdir(exist_ok=True)
    written = []
    for entity in ENTITIES:
        path = EXPORT_DIR / f"{entity.__name__}.schema.json"
        path.write_text(json.dumps(entity.model_json_schema(), indent=2, default=str))
        written.append(path)
    return written


if __name__ == "__main__":
    for path in export_all():
        print(f"wrote {path}")

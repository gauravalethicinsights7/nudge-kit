import json

from schemas.export import export_all
from schemas.registry import ENTITIES


def test_export_writes_valid_json_schema_per_entity():
    paths = export_all()
    assert len(paths) == len(ENTITIES)
    for path in paths:
        assert path.exists()
        schema = json.loads(path.read_text())
        assert "properties" in schema or "$defs" in schema

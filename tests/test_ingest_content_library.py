from uuid import uuid4

from ingest.content_library import load_content_library
from schemas.content import ContentModule
from schemas.enums import MlrStatus

FIXTURE_PATH = "fixtures/content_library_sample.yaml"


def test_load_content_library_round_trips():
    brand_id = uuid4()
    modules = load_content_library(FIXTURE_PATH, brand_id)
    assert len(modules) >= 10
    assert all(isinstance(m, ContentModule) for m in modules)
    assert all(m.brand_id == brand_id for m in modules)


def test_load_content_library_has_at_least_one_approved_module_per_most_channels():
    modules = load_content_library(FIXTURE_PATH, uuid4())
    approved_channels = {
        ref for m in modules if m.mlr_status == MlrStatus.approved and content_is_usable_stub(m) for ref in m.channel_refs
    }
    assert "rep_visit" in approved_channels
    assert "chemist_trade" not in approved_channels  # deliberate gap — see fixture comment


def content_is_usable_stub(m):
    from models.guardrails import content_is_usable

    return content_is_usable(m)


def test_load_content_library_includes_a_deliberately_blocked_patient_directed_module():
    modules = load_content_library(FIXTURE_PATH, uuid4())
    patient_support_modules = [m for m in modules if "patient_support" in m.channel_refs]
    assert patient_support_modules
    assert all(m.patient_directed for m in patient_support_modules)

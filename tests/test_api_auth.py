"""Regression coverage for the auth/multi-tenancy layer (api/auth/*,
api/routers/auth.py, api/deps.py::get_brand's tenant/access checks) — the
previous API session was verified live via curl/browser rather than
pytest; this is new, correctness-critical infrastructure, so it gets a
real pytest suite against the actual FastAPI app + test DB.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def _signup(tenant_name="Test Tenant") -> dict:
    resp = client.post(
        "/auth/signup",
        json={"tenant_name": tenant_name, "name": "Admin", "email": _unique_email("admin"), "password": "a-decent-password"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_signup_issues_a_token_and_platform_admin_user():
    body = _signup()
    assert body["user"]["role"] == "platform_admin"
    assert body["access_token"]


def test_signup_rejects_duplicate_email():
    email = _unique_email("dup")
    first = client.post("/auth/signup", json={"tenant_name": "T1", "name": "A", "email": email, "password": "pw123456"})
    assert first.status_code == 200
    second = client.post("/auth/signup", json={"tenant_name": "T2", "name": "B", "email": email, "password": "pw123456"})
    assert second.status_code == 409


def test_login_round_trips_and_rejects_wrong_password():
    email = _unique_email("login")
    client.post("/auth/signup", json={"tenant_name": "T", "name": "A", "email": email, "password": "right-password"})

    good = client.post("/auth/login", json={"email": email, "password": "right-password"})
    assert good.status_code == 200

    bad = client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert bad.status_code == 401


def test_unauthenticated_request_is_rejected():
    resp = client.get("/brands")
    assert resp.status_code == 401


def test_me_returns_the_authenticated_user():
    signed_up = _signup()
    token = signed_up["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == signed_up["user"]["id"]


def test_brand_is_scoped_to_the_creating_tenant():
    tenant_a = _signup("Tenant A")
    tenant_b = _signup("Tenant B")
    headers_a = {"Authorization": f"Bearer {tenant_a['access_token']}"}
    headers_b = {"Authorization": f"Bearer {tenant_b['access_token']}"}

    created = client.post(
        "/brands", headers=headers_a,
        json={"name": "A's Brand", "molecule": "x", "indication": "y", "market": "india", "lifecycle_stage": "launch", "company": "C"},
    )
    assert created.status_code == 200
    brand_id = created.json()["id"]

    # tenant A sees it
    list_a = client.get("/brands", headers=headers_a)
    assert any(b["id"] == brand_id for b in list_a.json())

    # tenant B does not, and a direct GET 404s rather than leaking existence
    list_b = client.get("/brands", headers=headers_b)
    assert not any(b["id"] == brand_id for b in list_b.json())
    direct_b = client.get(f"/brands/{brand_id}", headers=headers_b)
    assert direct_b.status_code == 404


def test_non_admin_role_needs_explicit_brand_access_grant():
    admin = _signup("Grant Tenant")
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}
    tenant_id = admin["user"]["tenant_id"]

    brand = client.post(
        "/brands", headers=admin_headers,
        json={"name": "Brand", "molecule": "x", "indication": "y", "market": "india", "lifecycle_stage": "launch", "company": "C"},
    ).json()

    teammate_email = _unique_email("teammate")
    teammate = client.post(
        f"/tenants/{tenant_id}/users", headers=admin_headers,
        json={"name": "Teammate", "email": teammate_email, "password": "teammate-pw", "role": "insights_analytics_lead"},
    ).json()
    teammate_token = client.post("/auth/login", json={"email": teammate_email, "password": "teammate-pw"}).json()["access_token"]
    teammate_headers = {"Authorization": f"Bearer {teammate_token}"}

    # no access yet -> 404, not visible in the list either
    assert client.get(f"/brands/{brand['id']}", headers=teammate_headers).status_code == 404
    assert brand["id"] not in [b["id"] for b in client.get("/brands", headers=teammate_headers).json()]

    grant = client.post(f"/brands/{brand['id']}/access", headers=admin_headers, json={"user_id": teammate["id"]})
    assert grant.status_code == 200

    assert client.get(f"/brands/{brand['id']}", headers=teammate_headers).status_code == 200
    assert brand["id"] in [b["id"] for b in client.get("/brands", headers=teammate_headers).json()]


def test_approval_role_gating_rejects_wrong_role_and_allows_right_role():
    admin = _signup("Approval Tenant")
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}
    tenant_id = admin["user"]["tenant_id"]

    brand = client.post(
        "/brands", headers=admin_headers,
        json={"name": "Brand", "molecule": "x", "indication": "y", "market": "india", "lifecycle_stage": "launch", "company": "C"},
    ).json()

    teammate_email = _unique_email("sales")
    teammate = client.post(
        f"/tenants/{tenant_id}/users", headers=admin_headers,
        json={"name": "Sales", "email": teammate_email, "password": "sales-pw-123", "role": "sales_ops_field_excellence"},
    ).json()
    client.post(f"/brands/{brand['id']}/access", headers=admin_headers, json={"user_id": teammate["id"]})
    teammate_token = client.post("/auth/login", json={"email": teammate_email, "password": "sales-pw-123"}).json()["access_token"]
    teammate_headers = {"Authorization": f"Bearer {teammate_token}"}

    # sales_ops_field_excellence is not in brand_plan's approver set
    rejected = client.post(f"/brands/{brand['id']}/approvals/brand_plan/approve-all", headers=teammate_headers)
    assert rejected.status_code == 403

    # platform_admin always passes (bypasses the per-entity-type map)
    allowed = client.post(f"/brands/{brand['id']}/approvals/brand_plan/approve-all", headers=admin_headers)
    assert allowed.status_code == 200

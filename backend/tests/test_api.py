"""Smoke + behavior tests for the HTTP surface the frontend depends on."""

import pytest
from fastapi.testclient import TestClient

from houseaccount.api.app import app
from houseaccount.marketplace.store import store


@pytest.fixture(autouse=True)
def _reset_store():
    store.seed()
    yield
    store.seed()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_insights_and_stats(client: TestClient):
    r = client.get("/api/insights")
    assert r.status_code == 200
    views = r.json()
    assert len(views) == 120
    assert {"conversation", "insight"} <= views[0].keys()

    stats = client.get("/api/insights/stats").json()
    assert stats["total"] == 120
    assert sum(stats["by_route"].values()) == 120
    assert 0.0 <= stats["complaint_rate"] <= 1.0


def test_eval_endpoint_passes(client: TestClient):
    r = client.get("/api/eval", params={"mode": "mock"})
    assert r.status_code == 200
    assert r.json()["passed"] is True


def test_apply_insight_for_auto_request(client: TestClient):
    # Find an auto-routed new_request conversation and apply it.
    views = client.get("/api/insights").json()
    target = next(
        v for v in views
        if v["insight"]["action"] == "create_job" and v["insight"]["route"] == "auto"
        and v["insight"]["classification"]["entities"]["service_type"]
    )
    cid = target["conversation"]["id"]
    r = client.post(f"/api/insights/{cid}/apply")
    assert r.status_code == 200
    body = r.json()
    assert body["created_request_id"] is not None
    assert body["request"]["source"] == "chat"


def test_marketplace_flow_over_http(client: TestClient):
    req = client.post(
        "/api/requests",
        json={"homeowner_id": "ho-1", "service_type": "plumbing", "zip_code": "94110"},
    ).json()
    quotes = client.post(f"/api/requests/{req['id']}/quotes").json()
    assert quotes
    booking = client.post(
        f"/api/quotes/{quotes[0]['id']}/accept", json={"scheduled_time": "Sat 10am"}
    ).json()
    assert booking["status"] == "scheduled"
    assert any(b["id"] == booking["id"] for b in client.get("/api/bookings").json())

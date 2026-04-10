import json
import pytest


@pytest.mark.anyio
async def test_webhook_accepts_valid_event(client):
    payload = {
        "eventType": "iModels.iModelCreated.v1",
        "content": {
            "iTwinId": "test-itwin-001",
            "iModelId": "test-imodel-001",
            "iTwinName": "Test Project",
            "iModelName": "Test Model",
        }
    }
    resp = await client.post("/webhook", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "processed"
    assert data["event_type"] == "iModels.iModelCreated.v1"
    assert "event_id" in data


@pytest.mark.anyio
async def test_webhook_rejects_bad_json(client):
    resp = await client.post(
        "/webhook",
        content=b"not json{{",
        headers={"Content-Type": "application/json"}
    )
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_webhook_empty_body(client):
    resp = await client.post("/webhook", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_type"] == "UnknownEvent"


@pytest.mark.anyio
async def test_events_endpoint_after_webhook(client):
    payload = {"eventType": "iTwins.iTwinCreated.v1", "content": {"iTwinId": "tw-999"}}
    await client.post("/webhook", json=payload)
    resp = await client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert data["events"][0]["event_type"] == "iTwins.iTwinCreated.v1"

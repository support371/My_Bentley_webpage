import pytest


@pytest.mark.anyio
async def test_events_empty(client):
    resp = await client.get("/events")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert "total" in data
    assert "page" in data


@pytest.mark.anyio
async def test_events_pagination(client):
    for i in range(5):
        await client.post("/webhook", json={"eventType": f"test.event{i}.v1"})
    resp = await client.get("/events?page=1&page_size=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["events"]) <= 3


@pytest.mark.anyio
async def test_event_detail(client):
    r1 = await client.post("/webhook", json={"eventType": "iModels.iModelDeleted.v1"})
    event_id = r1.json()["event_id"]
    r2 = await client.get(f"/events/{event_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["id"] == event_id
    assert data["event_type"] == "iModels.iModelDeleted.v1"


@pytest.mark.anyio
async def test_event_not_found(client):
    resp = await client.get("/events/nonexistent-id-12345")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data

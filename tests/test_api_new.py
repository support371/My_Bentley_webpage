import pytest

@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]

@pytest.mark.asyncio
async def test_dashboard_feed(client):
    response = await client.get("/dashboard/feed")
    assert response.status_code == 200
    assert "kpis" in response.json()

@pytest.mark.asyncio
async def test_api_events(client):
    response = await client.get("/events")
    assert response.status_code == 200
    assert "events" in response.json()

@pytest.mark.asyncio
async def test_api_itwins(client):
    response = await client.get("/api/itwins")
    assert response.status_code == 200
    assert "itwins" in response.json()

@pytest.mark.asyncio
async def test_api_imodels(client):
    response = await client.get("/api/imodels")
    assert response.status_code == 200
    assert "imodels" in response.json()

@pytest.mark.asyncio
async def test_api_integrations(client):
    response = await client.get("/api/integrations")
    assert response.status_code == 200
    assert "integrations" in response.json()

@pytest.mark.asyncio
async def test_api_mobile_summary(client):
    response = await client.get("/api/mobile/summary")
    assert response.status_code == 200
    assert "kpis" in response.json()

@pytest.mark.asyncio
async def test_api_control_plane(client):
    response = await client.get("/api/control-plane")
    assert response.status_code == 200
    assert "modules" in response.json()

@pytest.mark.asyncio
async def test_control_plane_website_studio(client):
    response = await client.get("/control-plane/website-studio")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_control_plane_infrastructure(client):
    response = await client.get("/control-plane/infrastructure")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_control_plane_env(client):
    response = await client.get("/control-plane/env/development")
    assert response.status_code == 200

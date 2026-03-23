from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "Bentley iTwin Automation Platform"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_webhook():
    payload = {"eventType": "test.event.v1", "content": {}}
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "processed"

def test_dashboard():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

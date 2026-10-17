from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200

def test_model_status_mock():
    r = client.get("/api/v1/model/status")
    assert r.status_code == 200
    d = r.json()
    assert d["mock"] is False
    assert d["ready"] is True

def test_chat():
    r = client.post("/api/v1/chat", json={"message": "hi"})
    assert r.status_code == 200
    assert "response" in r.json()

def test_chat_validation():
    r = client.post("/api/v1/chat", json={})
    assert r.status_code == 422

def test_code_generate():
    r = client.post("/api/v1/code/generate", json={"description": "hello"})
    assert r.status_code == 200

"""Loading the model from a file (USB stick) instead of downloading it."""
import hashlib
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.inference import models

client = TestClient(app)
GOOD = b"GGUF" + os.urandom(5000)


@pytest.fixture
def local(tmp_path, monkeypatch):
    fake = models.ModelOption(id="small", name="Test", file="test-model.gguf", size=len(GOOD),
                              sha256=hashlib.sha256(GOOD).hexdigest(), ram_needed=0, min_total_ram=0, repo="x/y")
    monkeypatch.setattr(models, "BY_FILE", {fake.file: fake})
    monkeypatch.setenv("AI_PROVIDER", "local")
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODEL_PATH", raising=False)
    return tmp_path


def send(data):
    return client.post("/api/v1/model/import", content=data, headers={"Content-Type": "application/octet-stream"})


def test_good_file_is_loaded_and_selected(local):
    r = send(GOOD)
    assert r.status_code == 200, r.text
    assert (local / "test-model.gguf").read_bytes() == GOOD
    assert models.active_path() == str(local / "test-model.gguf")
    assert not (local / "import.part").exists()


def test_wrong_file_is_refused_before_copying(local):
    r = send(b"not a model")
    assert r.status_code == 422 and "not a BilaNet model" in r.json()["detail"]
    assert os.listdir(local) == []


def test_damaged_file_is_refused_and_removed(local):
    r = send(b"X" + GOOD[1:])  # same size, different content
    assert r.status_code == 422 and "damaged" in r.json()["detail"]
    assert os.listdir(local) == []


def test_only_in_desktop_app(local, monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "api")
    assert send(GOOD).status_code == 400

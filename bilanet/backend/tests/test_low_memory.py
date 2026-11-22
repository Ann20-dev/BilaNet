"""Tests for the low-memory laptop support: model choice by RAM, disk check, hash check, idle unload."""
import hashlib
import os
import sys
import time
import types
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.inference import download, models
from app.inference.llama import LlamaProvider
from app.inference.provider import get_provider

client = TestClient(app)
GB = 1024 ** 3


@pytest.fixture
def desktop(monkeypatch, tmp_path):
    """Backend set up the way the desktop app starts it."""
    monkeypatch.setenv("AI_PROVIDER", "local")
    monkeypatch.setenv("MODELS_DIR", str(tmp_path))
    monkeypatch.delenv("MODEL_PATH", raising=False)
    monkeypatch.delenv("MODEL_URL", raising=False)
    download._state.update(state="idle", downloaded=0, total=0, error=None)
    get_provider.cache_clear()
    yield tmp_path
    get_provider.cache_clear()


def test_recommended_model_follows_ram():
    assert models.recommended(4 * GB).id == "small"
    assert models.recommended(6 * GB).id == "small"
    assert models.recommended(8 * GB).id == "standard"
    assert models.recommended(0).id == "small"  # unknown RAM: the one that runs everywhere


def test_status_reports_laptop_and_options(desktop):
    d = client.get("/api/v1/model/status").json()
    assert d["model_present"] is False
    assert {o["id"] for o in d["options"]} == {"small", "standard"}
    assert d["recommended"] in ("small", "standard")
    assert d["disk_free"] > 0


def test_active_path_prefers_selected_then_any_known_file(desktop):
    assert models.active_path() == ""
    legacy = desktop / models.LEGACY.file
    legacy.write_bytes(b"x")
    assert models.active_path() == str(legacy)  # earlier installs keep working
    small = desktop / models.SMALL.file
    small.write_bytes(b"x")
    models.write_selected(str(small))
    assert models.active_path() == str(small)


def test_download_refused_when_disk_is_full(desktop, monkeypatch):
    monkeypatch.setattr(models, "free_disk", lambda p: 100 * 1024 ** 2)
    r = client.post("/api/v1/model/download", json={"model": "small"}).json()
    assert r["started"] is False
    assert "disk space" in r["reason"]
    assert download.status()["state"] == "idle"


def test_download_rejects_unknown_model(desktop):
    r = client.post("/api/v1/model/download", json={"model": "huge"}).json()
    assert r["started"] is False and "Unknown model" in r["reason"]


class FakeStream:
    def __init__(self, data):
        self.data, self.status_code, self.headers = data, 200, {"Content-Length": str(len(data))}
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def raise_for_status(self): pass
    def close(self): pass
    def iter_bytes(self, n): yield self.data


@pytest.mark.parametrize("good", [True, False])
def test_download_verifies_hash(desktop, monkeypatch, good):
    data = b"model-bytes"
    monkeypatch.setattr(download.httpx, "stream", lambda *a, **k: FakeStream(data))
    target = str(desktop / "m.gguf")
    sha = hashlib.sha256(data if good else b"other").hexdigest()
    download._run(target, "http://example.invalid/m.gguf", sha)
    st = download.status()
    if good:
        assert st["state"] == "done" and os.path.exists(target)
        assert models.read_selected(str(desktop)) == "m.gguf"
    else:
        assert st["state"] == "error" and "damaged" in st["error"]
        assert not os.path.exists(target) and not os.path.exists(target + ".part")


def test_model_unloads_when_idle(tmp_path, monkeypatch):
    class FakeLlama:
        def __init__(self, **kw): pass
        def __call__(self, prompt, **kw): return {"choices": [{"text": "hi"}]}
    monkeypatch.setitem(sys.modules, "llama_cpp", types.SimpleNamespace(Llama=FakeLlama))
    path = tmp_path / "m.gguf"
    path.write_bytes(b"x")
    p = LlamaProvider(lambda: str(path), idle_unload=1)
    assert p.generate("hello") == "hi"
    assert p.llm is not None
    for _ in range(40):
        if p.llm is None:
            break
        time.sleep(0.1)
    assert p.llm is None  # RAM given back
    assert p.generate("again") == "hi"  # and it reloads on the next question

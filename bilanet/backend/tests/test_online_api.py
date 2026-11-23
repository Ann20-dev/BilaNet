"""The online demo's hosted AI: busy (HTTP 429) handling and backup models."""
import httpx
import pytest
from fastapi import HTTPException
from app.inference import openai_compat
from app.inference.openai_compat import OpenAICompatProvider


def reply(status, text="", retry_after=None, body=None):
    headers = {"retry-after": str(retry_after)} if retry_after is not None else {}
    req = httpx.Request("POST", "https://api.example/chat/completions")
    if status == 200:
        return httpx.Response(200, json={"choices": [{"message": {"content": text}}]}, request=req)
    return httpx.Response(status, text=body or "rate limit", headers=headers, request=req)


@pytest.fixture
def calls(monkeypatch):
    sent, queue = [], []
    def fake_post(url, headers, json, timeout):
        sent.append(json)
        return queue.pop(0)
    monkeypatch.setattr(openai_compat.httpx, "post", fake_post)
    monkeypatch.setattr(openai_compat.time, "sleep", lambda s: sent.append({"slept": s}))
    return sent, queue


def provider():
    return OpenAICompatProvider("https://api.example", "key", "main", fallback_models=["backup-a", "openai/gpt-oss-20b"])


def test_short_wait_retries_same_model(calls):
    sent, queue = calls
    queue += [reply(429, retry_after=2), reply(200, "hi")]
    assert provider().generate("q") == "hi"
    assert [c.get("model", c.get("slept")) for c in sent] == ["main", 2.0, "main"]


def test_long_wait_switches_to_backup_model(calls):
    sent, queue = calls
    queue += [reply(429, retry_after=40), reply(200, "from backup")]
    assert provider().generate("q") == "from backup"
    assert [c["model"] for c in sent] == ["main", "backup-a"]


def test_retired_backup_model_is_skipped(calls):
    sent, queue = calls
    queue += [reply(429), reply(404, body="The model backup-a does not exist"), reply(200, "ok")]
    assert provider().generate("q") == "ok"
    assert sent[-1]["model"] == "openai/gpt-oss-20b" and sent[-1]["reasoning_effort"] == "low"
    assert "reasoning_effort" not in sent[0]


def test_all_models_busy_gives_friendly_message(calls):
    sent, queue = calls
    queue += [reply(429), reply(429), reply(429)]
    with pytest.raises(HTTPException) as e:
        provider().generate("q")
    assert e.value.status_code == 429 and "try again" in e.value.detail


def test_main_model_errors_are_not_hidden(calls):
    sent, queue = calls
    queue += [reply(400, body="bad request: model field")]
    with pytest.raises(HTTPException) as e:
        provider().generate("q")
    assert e.value.status_code == 502 and len(sent) == 1


def test_online_server_cannot_index_its_own_folders(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app
    (tmp_path / "secret.txt").write_text("server secret")
    monkeypatch.setenv("AI_PROVIDER", "api")
    r = TestClient(app).post("/api/v1/documents/index", json={"directory": str(tmp_path)})
    assert r.status_code == 403

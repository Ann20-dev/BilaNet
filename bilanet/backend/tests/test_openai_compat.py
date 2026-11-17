import httpx
import pytest
from fastapi import HTTPException
from app.inference.openai_compat import OpenAICompatProvider


class FakeResp:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


def make(monkeypatch, status, body, capture=None):
    def fake_post(url, **kw):
        if capture is not None:
            capture.update(url=url, **kw)
        return FakeResp(status, body)
    monkeypatch.setattr(httpx, "post", fake_post)
    return OpenAICompatProvider("https://api.example.com/v1/", "key123", "qwen/qwen3.8-27b")


def test_generate_strips_think_and_sends_request(monkeypatch):
    seen = {}
    p = make(monkeypatch, 200, {"choices": [{"message": {"content": "<think>hmm</think>\nprint('hi')"}}]}, seen)
    assert p.generate("say hi") == "print('hi')"
    assert seen["url"] == "https://api.example.com/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer key123"
    assert seen["json"]["model"] == "qwen/qwen3.8-27b"
    assert seen["json"]["messages"][-1] == {"role": "user", "content": "say hi"}


def test_rate_limit_gives_friendly_error(monkeypatch):
    p = make(monkeypatch, 429, {"error": "rate"})
    with pytest.raises(HTTPException) as e:
        p.generate("x")
    assert e.value.status_code == 429


def test_missing_key(monkeypatch):
    p = OpenAICompatProvider("https://api.example.com/v1", "", "m")
    with pytest.raises(HTTPException) as e:
        p.generate("x")
    assert e.value.status_code == 503

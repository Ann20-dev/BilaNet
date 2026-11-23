"""Hosted inference through any OpenAI-compatible chat API (Groq, Hugging Face router, OpenRouter, ...).

Used only for the online demo (AI_PROVIDER=api). The desktop app keeps using the local GGUF model.

Free plans allow only a few thousand tokens per minute per model, shared by every tester.
When the service says "too many requests" (HTTP 429) we first wait briefly and retry if it
asks for only a short wait, then try the backup models in turn (each has its own limit),
and only then tell the student to try again.
"""
import re
import time
import httpx
from fastapi import HTTPException

SYSTEM_PROMPT = (
    "You are BilaNet, a concise, friendly coding assistant for developers and students. "
    "Give clear explanations and correct, runnable code."
)
# Qwen3 models may emit their reasoning in <think> tags; testers only need the answer.
_THINK = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
# Wait and retry the same model when the service asks for at most this many seconds.
SHORT_WAIT = 8
BUSY_MESSAGE = "Many students are using BilaNet right now. Please wait about a minute and try again."


def _retry_after(r):
    try:
        return float((getattr(r, "headers", None) or {}).get("retry-after", ""))
    except ValueError:
        return None


class OpenAICompatProvider:
    def __init__(self, base_url, api_key, model, max_tokens=1024, timeout=60.0, fallback_models=()):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.fallback_models = [m for m in fallback_models if m and m != model]
        self.max_tokens = max_tokens
        self.timeout = timeout

    def _body(self, model, prompt, max_tokens, system):
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": (system or SYSTEM_PROMPT) + " /no_think"},
                {"role": "user", "content": str(prompt)},
            ],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": 0.3,
        }
        if model.startswith("openai/gpt-oss"):
            # Reasoning models: think briefly, so the answer fits in max_tokens and arrives fast.
            body["reasoning_effort"] = "low"
        return body

    def _post(self, model, prompt, max_tokens, system):
        try:
            return httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=self._body(model, prompt, max_tokens, system),
                timeout=self.timeout,
            )
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Could not reach the AI service: {e}") from e

    def generate(self, prompt, max_tokens=None, system=None):
        if not self.api_key:
            raise HTTPException(503, "Hosted AI is not configured: set AI_API_KEY on the server.")
        last_error = None
        for model in [self.model, *self.fallback_models]:
            r = self._post(model, prompt, max_tokens, system)
            if r.status_code == 429:
                wait = _retry_after(r)
                if wait is not None and wait <= SHORT_WAIT:
                    time.sleep(wait)
                    r = self._post(model, prompt, max_tokens, system)
            if r.status_code == 429:
                last_error = HTTPException(429, BUSY_MESSAGE)
                continue
            if r.status_code in (400, 404) and model != self.model and "model" in r.text.lower():
                # A backup model was renamed or retired: skip it rather than fail the student.
                continue
            if r.status_code >= 400:
                raise HTTPException(502, f"AI service error {r.status_code}: {r.text[:300]}")
            text = r.json()["choices"][0]["message"].get("content") or ""
            return _THINK.sub("", text).strip()
        raise last_error or HTTPException(429, BUSY_MESSAGE)

    def stream(self, prompt, max_tokens=None, system=None):
        yield self.generate(prompt, max_tokens, system)

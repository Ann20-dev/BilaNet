"""Hosted inference through any OpenAI-compatible chat API (Groq, Hugging Face router, OpenRouter, ...).

Used only for the online demo (AI_PROVIDER=api). The desktop app keeps using the local GGUF model.
"""
import re
import httpx
from fastapi import HTTPException

SYSTEM_PROMPT = (
    "You are BilaNet, a concise, friendly coding assistant for developers and students. "
    "Give clear explanations and correct, runnable code. /no_think"
)
# Qwen3 models may emit their reasoning in <think> tags; testers only need the answer.
_THINK = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


class OpenAICompatProvider:
    def __init__(self, base_url, api_key, model, max_tokens=1024, timeout=60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout

    def generate(self, prompt, max_tokens=None):
        if not self.api_key:
            raise HTTPException(503, "Hosted AI is not configured: set AI_API_KEY on the server.")
        try:
            r = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": str(prompt)},
                    ],
                    "max_tokens": max_tokens or self.max_tokens,
                    "temperature": 0.3,
                },
                timeout=self.timeout,
            )
        except httpx.HTTPError as e:
            raise HTTPException(502, f"Could not reach the AI service: {e}") from e
        if r.status_code == 429:
            raise HTTPException(429, "The free AI service is busy (rate limit reached). Please try again in a minute.")
        if r.status_code >= 400:
            raise HTTPException(502, f"AI service error {r.status_code}: {r.text[:300]}")
        text = r.json()["choices"][0]["message"]["content"] or ""
        return _THINK.sub("", text).strip()

    def stream(self, prompt, max_tokens=None):
        yield self.generate(prompt, max_tokens)

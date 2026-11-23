import os
from functools import lru_cache
from app.core.config import settings
from app.inference.mock import MockProvider
from app.inference.llama import LlamaProvider
from app.inference import models
from app.inference.openai_compat import OpenAICompatProvider

@lru_cache(maxsize=1)
def get_provider():
    """One shared provider for the whole app, so the local model is loaded into RAM only once."""
    mode = os.getenv("AI_PROVIDER", "mock").lower()
    if mode == "local":
        return LlamaProvider(models.active_path, settings.context_size, settings.threads, settings.max_tokens, settings.idle_unload,
                             settings.temperature, settings.repeat_penalty)
    if mode == "api":
        # Online demo only: hosted OpenAI-compatible API (default: Groq).
        return OpenAICompatProvider(settings.api_base_url, settings.api_key, settings.api_model, settings.max_tokens)
    return MockProvider()

def is_mock():
    return os.getenv("AI_PROVIDER", "mock").lower() not in ("local", "api")

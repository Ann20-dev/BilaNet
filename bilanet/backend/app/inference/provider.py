import os
from app.core.config import settings
from app.inference.mock import MockProvider
from app.inference.llama import LlamaProvider
from app.inference.openai_compat import OpenAICompatProvider

def get_provider():
    mode = os.getenv("AI_PROVIDER", "mock").lower()
    if mode == "local":
        return LlamaProvider(settings.model_path, settings.context_size, settings.threads, settings.max_tokens)
    if mode == "api":
        # Online demo only: hosted OpenAI-compatible API (default: Groq).
        return OpenAICompatProvider(settings.api_base_url, settings.api_key, settings.api_model, settings.max_tokens)
    return MockProvider()

def is_mock():
    return os.getenv("AI_PROVIDER", "mock").lower() not in ("local", "api")

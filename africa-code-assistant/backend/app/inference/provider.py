import os
from app.core.config import settings
from app.inference.mock import MockProvider
from app.inference.llama import LlamaProvider

def get_provider():
    mode = os.getenv("AI_PROVIDER", "mock").lower()
    if mode == "local":
        return LlamaProvider(settings.model_path, settings.context_size, settings.threads, settings.max_tokens)
    return MockProvider()

def is_mock():
    return os.getenv("AI_PROVIDER", "mock").lower() != "local"

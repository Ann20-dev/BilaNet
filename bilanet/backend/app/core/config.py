import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")
def _auto_threads():
    return max(2, min(6, (os.cpu_count() or 4) // 2))


class Settings:
    # Fixed model file (dev setup). The desktop app sets MODELS_DIR instead; see app/inference/models.py.
    model_path: str = os.getenv("MODEL_PATH", "")
    context_size: int = int(os.getenv("CONTEXT_SIZE", "4096"))
    # "auto" = number of physical cores (capped), which is fastest for llama.cpp.
    threads: int = _auto_threads() if os.getenv("THREADS", "auto") == "auto" else int(os.getenv("THREADS"))
    # Free the model's RAM after this many idle seconds (0 = keep it loaded).
    idle_unload: int = int(os.getenv("IDLE_UNLOAD_SECONDS", "300"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1024"))
    docs_dir: str = os.getenv("DOCS_DIR", "./docs")
    # The user's own indexed notes/code for offline docs search (built-in docs ship with the app).
    docs_user_db: str = os.getenv("DOCS_USER_DB", "bilanet_docs.db")
    db_url: str = os.getenv("DB_URL", "sqlite:///./bilanet.db")
    # Hosted API for the online demo (AI_PROVIDER=api). Any OpenAI-compatible endpoint works.
    api_base_url: str = os.getenv("AI_API_BASE_URL", "https://api.groq.com/openai/v1")
    api_key: str = os.getenv("AI_API_KEY", "")
    api_model: str = os.getenv("AI_MODEL", "qwen/qwen3.8-27b")
settings = Settings()
AI_PROVIDER = __import__('os').getenv('AI_PROVIDER','mock')

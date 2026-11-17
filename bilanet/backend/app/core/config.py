import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")
class Settings:
    model_path: str = os.getenv("MODEL_PATH", "")
    context_size: int = int(os.getenv("CONTEXT_SIZE", "4096"))
    threads: int = int(os.getenv("THREADS", "4"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "1024"))
    docs_dir: str = os.getenv("DOCS_DIR", "./docs")
    db_url: str = os.getenv("DB_URL", "sqlite:///./bilanet.db")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    # Hosted API for the online demo (AI_PROVIDER=api). Any OpenAI-compatible endpoint works.
    api_base_url: str = os.getenv("AI_API_BASE_URL", "https://api.groq.com/openai/v1")
    api_key: str = os.getenv("AI_API_KEY", "")
    api_model: str = os.getenv("AI_MODEL", "qwen/qwen3-32b")
settings = Settings()
AI_PROVIDER = __import__('os').getenv('AI_PROVIDER','mock')

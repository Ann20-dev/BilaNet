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
    db_url: str = os.getenv("DB_URL", "sqlite:///./aca.db")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
settings = Settings()
AI_PROVIDER = __import__('os').getenv('AI_PROVIDER','mock')

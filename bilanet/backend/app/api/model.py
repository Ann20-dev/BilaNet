from fastapi import APIRouter
from app.core.config import settings
from app.inference.provider import is_mock, get_provider
import os
router = APIRouter()
@router.get("/model/status")
def status():
    provider = os.getenv("AI_PROVIDER", "mock").lower()
    real_configured = bool(settings.model_path) and provider == "local"
    loaded = False
    if real_configured:
        try:
            p = get_provider()
            loaded = p.llm is not None if hasattr(p, "llm") else False
        except Exception:
            loaded = False
    return {
        "provider": provider,
        "mock": provider != "local",
        "model_path": settings.model_path,
        "configured": real_configured,
        "loaded": loaded,
        "ready": real_configured,
    }

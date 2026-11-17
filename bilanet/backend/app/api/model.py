from fastapi import APIRouter
from app.core.config import settings
from app.inference import download
from app.inference.provider import get_provider
import os
router = APIRouter()


@router.get("/model/status")
def status():
    provider = os.getenv("AI_PROVIDER", "mock").lower()
    real_configured = bool(settings.model_path) and provider == "local"
    model_present = real_configured and os.path.exists(settings.model_path)
    loaded = False
    if real_configured:
        try:
            p = get_provider()
            loaded = p.llm is not None if hasattr(p, "llm") else False
        except Exception:
            loaded = False
    api_ready = provider == "api" and bool(settings.api_key)
    return {
        "provider": provider,
        "mock": provider not in ("local", "api"),
        "model_path": settings.model_path if provider == "local" else None,
        "model": settings.api_model if provider == "api" else None,
        "configured": real_configured or api_ready,
        "model_present": model_present,
        "loaded": loaded,
        "ready": real_configured or api_ready,
        "download": download.status(),
    }


@router.post("/model/download")
def start_download():
    """Desktop first-run setup: fetch the local model once (resumable)."""
    if os.getenv("AI_PROVIDER", "mock").lower() != "local" or not settings.model_path:
        return {"started": False, "reason": "Local model is not used on this server."}
    if os.path.exists(settings.model_path):
        return {"started": False, "reason": "Model already downloaded."}
    return {"started": download.start(settings.model_path)}


@router.get("/model/download")
def download_status():
    return download.status()

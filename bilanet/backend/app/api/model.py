from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings
from app.inference import download, models
from app.inference.provider import get_provider
import os
router = APIRouter()


def _local():
    return os.getenv("AI_PROVIDER", "mock").lower() == "local"


@router.get("/model/status")
def status():
    provider = os.getenv("AI_PROVIDER", "mock").lower()
    local = provider == "local"
    path = models.active_path() if local else ""
    real_configured = local and bool(models.models_dir() or path)
    model_present = bool(path) and os.path.exists(path)
    loaded = False
    if real_configured:
        try:
            p = get_provider()
            loaded = p.llm is not None if hasattr(p, "llm") else False
        except Exception:
            loaded = False
    api_ready = provider == "api" and bool(settings.api_key)
    out = {
        "provider": provider,
        "mock": provider not in ("local", "api"),
        "model_path": path if local else None,
        "model": settings.api_model if provider == "api" else None,
        "configured": real_configured or api_ready,
        "model_present": model_present,
        "loaded": loaded,
        "ready": real_configured or api_ready,
        "download": download.status(),
    }
    if local:
        # First-run setup info: what this laptop can run and whether there is room for it.
        ram = models.total_ram()
        out.update(
            ram_total=ram,
            disk_free=models.free_disk(models.models_dir() or path),
            recommended=models.recommended(ram).id,
            options=[models.describe(m, ram) for m in models.CATALOG.values()],
        )
    return out


class DownloadRequest(BaseModel):
    model: Optional[str] = None  # "small" or "standard"; default = recommended for this laptop


@router.post("/model/download")
def start_download(req: Optional[DownloadRequest] = None):
    """Desktop first-run setup: fetch the local model once (resumable, verified)."""
    if not _local() or not (models.models_dir() or settings.model_path):
        return {"started": False, "reason": "Local model is not used on this server."}
    if models.active_path() and os.path.exists(models.active_path()):
        return {"started": False, "reason": "Model already downloaded."}
    choice = (req.model if req else None) or models.recommended().id
    option = models.CATALOG.get(choice)
    if option is None:
        return {"started": False, "reason": f"Unknown model {choice!r}. Choose one of: {', '.join(models.CATALOG)}."}
    target, fetch = models.download_plan(option)
    custom_url = os.getenv("MODEL_URL")  # e.g. a local mirror; size and hash are then unknown
    if custom_url:
        reason = download.start(target, custom_url)
    elif fetch is None:
        return {"started": False, "reason": "MODEL_PATH names an unknown file; set MODEL_URL to download it."}
    else:
        reason = download.start(target, fetch.url, sha256=fetch.sha256, size=fetch.size)
    return {"started": reason is None, "reason": reason, "model": fetch.id if fetch and not custom_url else choice}


@router.get("/model/download")
def download_status():
    return download.status()

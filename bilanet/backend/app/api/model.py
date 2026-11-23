from typing import Optional
import hashlib
from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect
from pydantic import BaseModel
from app.core.config import settings
from app import coderun
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
        "can_run_code": coderun.allowed(),
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


_importing = False


@router.post("/model/import")
async def import_model(request: Request):
    """Load a model file the student already has (e.g. copied from a friend's laptop on a USB stick).

    For schools with little or no internet: one person downloads the model, everyone else loads
    it from a USB stick. The file must be one of BilaNet's known models: its size is checked before
    anything is copied, and its SHA256 while it is copied, so a damaged copy is never used.
    The body is the raw file (the page sends it straight from the file picker).
    """
    global _importing
    folder = models.models_dir()
    if not _local() or not folder:
        raise HTTPException(400, "Loading a model file only works in the desktop app.")
    size = int(request.headers.get("content-length") or 0)
    option = next((m for m in models.BY_FILE.values() if m.size == size), None)
    if option is None:
        raise HTTPException(422, "This is not a BilaNet model file. Choose the file named "
                                 f"{models.SMALL.file} (or {models.STANDARD.file}).")
    if download.status()["state"] in ("downloading", "verifying") or _importing:
        raise HTTPException(409, "A model is already being downloaded or loaded. Wait for it to finish.")
    free = models.free_disk(folder)
    if free and free < size + download.DISK_MARGIN:
        raise HTTPException(507, f"Not enough free disk space: {(size + download.DISK_MARGIN) / 1e9:.1f} GB needed, "
                                 f"{free / 1e9:.1f} GB free. Delete some files and try again.")
    _importing = True
    os.makedirs(folder, exist_ok=True)
    part = os.path.join(folder, "import.part")
    h, got, buf = hashlib.sha256(), 0, bytearray()

    def flush(f, data):
        f.write(data)
        h.update(data)

    try:
        with open(part, "wb") as f:
            async for chunk in request.stream():
                buf += chunk
                got += len(chunk)
                if len(buf) >= 4 * 1024 * 1024:  # write and hash off the event loop, in big blocks
                    data, buf = bytes(buf), bytearray()
                    await run_in_threadpool(flush, f, data)
            await run_in_threadpool(flush, f, bytes(buf))
        if got != size:
            raise HTTPException(422, "The file was not copied completely. Try again.")
        if h.hexdigest() != option.sha256:
            raise HTTPException(422, "This model file is damaged (it does not match the original). "
                                     "Copy it again from the other laptop, or download it.")
        target = os.path.join(folder, option.file)
        os.replace(part, target)
        models.write_selected(target)
        return {"loaded": True, "model": option.id, "file": option.file}
    except ClientDisconnect:
        raise HTTPException(499, "Loading was cancelled.")
    finally:
        _importing = False
        if os.path.exists(part):
            os.remove(part)

import os
from fastapi import APIRouter, HTTPException
from app.schemas.models import DocIndexRequest, DocSearchRequest
from app.rag.store import get_store

router = APIRouter()


@router.get("/documents/info")
def info():
    return get_store().info()


@router.post("/documents/search")
def search(req: DocSearchRequest):
    return {"results": get_store().search(req.query, req.top_k, req.library)}


@router.post("/documents/index")
def index(req: DocIndexRequest):
    """Add a folder of your own notes or code (.md, .txt, .py, .rst) to the offline search."""
    if os.getenv("AI_PROVIDER", "mock").lower() == "api":
        # The online demo is a shared server: indexing would let anyone read the server's own files.
        raise HTTPException(403, "Adding your own notes only works in the desktop app.")
    try:
        n = get_store().index_folder(req.directory)
    except FileNotFoundError:
        raise HTTPException(404, f"Folder not found: {req.directory}")
    return {"ok": True, "docs": n}

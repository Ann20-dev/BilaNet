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
    try:
        n = get_store().index_folder(req.directory)
    except FileNotFoundError:
        raise HTTPException(404, f"Folder not found: {req.directory}")
    return {"ok": True, "docs": n}

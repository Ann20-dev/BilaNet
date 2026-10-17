from fastapi import APIRouter
from app.schemas.models import DocIndexRequest, DocSearchRequest
from app.rag.indexer import DocIndex
router = APIRouter()
idx = DocIndex()
@router.post("/documents/index")
def index(req: DocIndexRequest):
    idx.build(req.directory)
    return {"ok": True, "docs": len(idx.docs)}
@router.post("/documents/search")
def search(req: DocSearchRequest):
    return {"results": idx.search(req.query, req.top_k)}

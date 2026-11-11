from fastapi import APIRouter
from app.schemas.models import CodeRequest
from app.inference.provider import get_provider
router = APIRouter()
p = get_provider()
@router.post("/code/generate")
def gen(req: CodeRequest):
    return {"code": p.generate(req.description or "")}
@router.post("/code/explain")
def exp(req: CodeRequest):
    return {"explanation": p.generate("explain: " + req.code)}
@router.post("/code/debug")
def dbg(req: CodeRequest):
    return {"debug": p.generate("debug: " + req.code)}
@router.post("/code/optimize")
def opt(req: CodeRequest):
    return {"optimized": p.generate("optimize: " + req.code)}
@router.post("/code/translate")
def tr(req: CodeRequest):
    return {"translated": p.generate(f"translate {req.language} to {req.target_language}: {req.code}")}

from fastapi import APIRouter
from app.schemas.models import ChatRequest
from app.inference.provider import get_provider
router = APIRouter()
provider = get_provider()
@router.post("/chat")
def chat(req: ChatRequest):
    return {"response": provider.generate(req.message)}

from fastapi import APIRouter
from app.schemas.models import ChatRequest
from app.inference.provider import get_provider
from app.rag.store import get_store
from app import prompts

router = APIRouter()

# How much documentation goes into the prompt. Kept small for the 4096-token offline model.
DOC_SNIPPETS = 3
DOC_CHARS = 900


@router.post("/chat")
def chat(req: ChatRequest):
    question = req.message
    if req.context:
        question = f"{question}\n\n```\n{req.context}\n```"
    sources = []
    if req.use_docs:
        hits = get_store().search(req.message, top_k=DOC_SNIPPETS)
        snippets = [{"title": h["title"], "text": (h["signature"] and h["title"] + h["signature"] + "\n") + h["text"][:DOC_CHARS]} for h in hits]
        question = prompts.with_docs(question, snippets)
        sources = [{"title": h["title"], "library": h["library"]} for h in hits]
    response = get_provider().generate(question, system=prompts.system_prompt(req.reply_language))
    return {"response": response, "sources": sources}

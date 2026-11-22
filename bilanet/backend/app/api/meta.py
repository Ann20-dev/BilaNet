from fastapi import APIRouter
from app import prompts

router = APIRouter()


@router.get("/languages")
def languages():
    """Languages the assistant can explain in, and programming languages it supports."""
    return {"reply_languages": prompts.REPLY_LANGUAGES, "code_languages": prompts.CODE_LANGUAGES}

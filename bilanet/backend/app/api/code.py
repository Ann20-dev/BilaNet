from fastapi import APIRouter, HTTPException
from app.schemas.models import CodeRequest
from app.inference.provider import get_provider
from app import coderun, prompts

router = APIRouter()


def run(prompt: str, req: CodeRequest) -> str:
    return get_provider().generate(prompts.with_reply_language(prompt, req.reply_language), system=prompts.system_prompt(req.reply_language))


def need_code(req: CodeRequest):
    if not req.code.strip():
        raise HTTPException(422, "Paste some code first.")


@router.post("/code/generate")
def gen(req: CodeRequest):
    if not (req.description or "").strip():
        raise HTTPException(422, "Describe what the code should do.")
    return {"code": run(prompts.generate(req.description, req.language), req)}


@router.post("/code/explain")
def exp(req: CodeRequest):
    need_code(req)
    return {"explanation": run(prompts.explain(req.code, req.language), req)}


@router.post("/code/debug")
def dbg(req: CodeRequest):
    need_code(req)
    ran = None
    if req.language == "python" and req.run_code and coderun.allowed() and not (req.error or "").strip():
        ran = coderun.run(req.code)
    return {"debug": run(prompts.debug(req.code, req.language, req.error, ran), req), "run": ran}


@router.post("/code/optimize")
def opt(req: CodeRequest):
    need_code(req)
    return {"optimized": run(prompts.optimize(req.code, req.language), req)}


@router.post("/code/translate")
def tr(req: CodeRequest):
    need_code(req)
    if not req.target_language:
        raise HTTPException(422, "Choose the language to translate to.")
    return {"translated": run(prompts.translate(req.code, req.language, req.target_language), req)}

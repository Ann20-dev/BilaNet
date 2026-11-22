from fastapi import APIRouter, HTTPException
from app.schemas.models import ScaffoldRequest
from app.inference.provider import get_provider
from app.project.templates import TEMPLATES, tree
from app import prompts

router = APIRouter()


@router.get("/project/templates")
def list_templates():
    return [{"id": k, "name": t["name"]} for k, t in TEMPLATES.items()]


@router.get("/project/templates/{template_id}")
def get_template(template_id: str):
    t = TEMPLATES.get(template_id)
    if not t:
        raise HTTPException(404, "Unknown template")
    return {"id": template_id, "name": t["name"], "tree": tree(t["files"]), "files": t["files"]}


@router.post("/project/scaffold")
def scaffold(req: ScaffoldRequest):
    """Custom project structure and boilerplate written by the AI."""
    text = get_provider().generate(prompts.scaffold(req.description, req.stack), system=prompts.system_prompt(req.reply_language))
    return {"plan": text}

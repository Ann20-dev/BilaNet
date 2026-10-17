from fastapi import APIRouter
from app.schemas.models import ConversationCreate
from app.database.db import SessionLocal, Conversation, Message
router = APIRouter()
@router.get("/conversations")
def list_conv():
    db = SessionLocal(); rows = db.query(Conversation).all(); db.close()
    return [{"id": c.id, "title": c.title} for c in rows]
@router.post("/conversations")
def create_conv(req: ConversationCreate):
    db = SessionLocal(); c = Conversation(title=req.title); db.add(c); db.commit(); db.refresh(c); db.close()
    return {"id": c.id, "title": c.title}
@router.get("/conversations/{cid}")
def get_conv(cid: int):
    db = SessionLocal(); msgs = db.query(Message).filter(Message.conversation_id==cid).all(); db.close()
    return [{"role": m.role, "content": m.content} for m in msgs]
@router.delete("/conversations/{cid}")
def del_conv(cid: int):
    db = SessionLocal()
    db.query(Conversation).filter(Conversation.id==cid).delete()
    db.query(Message).filter(Message.conversation_id==cid).delete()
    db.commit(); db.close()
    return {"ok": True}

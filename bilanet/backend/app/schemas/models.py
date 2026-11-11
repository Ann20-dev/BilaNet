from pydantic import BaseModel
from typing import Optional
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    context: Optional[str] = None
class CodeRequest(BaseModel):
    code: str = ""
    language: str = "python"
    description: Optional[str] = None
    target_language: Optional[str] = None
class ConversationCreate(BaseModel):
    title: str = "New conversation"
class DocIndexRequest(BaseModel):
    directory: str
class DocSearchRequest(BaseModel):
    query: str
    top_k: int = 5

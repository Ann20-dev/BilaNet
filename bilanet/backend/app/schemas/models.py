from pydantic import BaseModel, Field
from typing import Optional

# Inputs are capped so a pasted file cannot overflow the offline model's 4096-token window
# (or the hosted demo's limits). About 12,000 characters is roughly 3,000 tokens of code.
MAX_CODE = 12_000
MAX_TEXT = 4_000


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=MAX_TEXT)
    conversation_id: Optional[int] = None
    context: Optional[str] = Field(None, max_length=MAX_CODE)
    reply_language: str = "en"
    # Look up the offline Python / NumPy / pandas docs and answer from them (RAG).
    use_docs: bool = False


class CodeRequest(BaseModel):
    code: str = Field("", max_length=MAX_CODE)
    language: str = "python"
    description: Optional[str] = Field(None, max_length=MAX_TEXT)
    target_language: Optional[str] = None
    error: Optional[str] = Field(None, max_length=MAX_TEXT)  # debugging: the error message, if any
    reply_language: str = "en"


class ConversationCreate(BaseModel):
    title: str = "New conversation"


class DocIndexRequest(BaseModel):
    directory: str


class DocSearchRequest(BaseModel):
    query: str = Field(..., max_length=500)
    top_k: int = 5
    library: Optional[str] = None  # python | numpy | pandas | mine


class QuizChallengeRequest(BaseModel):
    topic: str = "python"
    level: str = "beginner"
    reply_language: str = "en"


class QuizCheckRequest(BaseModel):
    challenge: str = Field(..., max_length=MAX_TEXT)
    solution: str = Field(..., max_length=MAX_CODE)
    language: str = "python"
    reply_language: str = "en"


class ScaffoldRequest(BaseModel):
    description: str = Field(..., max_length=MAX_TEXT)
    stack: str = "Python"
    reply_language: str = "en"

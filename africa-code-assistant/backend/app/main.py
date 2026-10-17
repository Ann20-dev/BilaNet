from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, chat, code, conversations, documents, model
from app.core.config import settings

app = FastAPI(title="Africa Code Assistant", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:1420","http://localhost:5173","tauri://localhost"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(health.router, prefix="/api/v1")
app.include_router(model.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(code.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Africa Code Assistant API", "health": "/api/v1/health"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

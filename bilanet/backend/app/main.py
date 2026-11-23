import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, chat, code, conversations, documents, model, quiz, project, meta

app = FastAPI(title="BilaNet", version="0.1.4")
# tauri://localhost is the desktop app on macOS/Linux; http(s)://tauri.localhost on Windows.
_default_origins = ["http://localhost:1420", "http://localhost:5173", "tauri://localhost", "http://tauri.localhost", "https://tauri.localhost"]
_extra_origins = [o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    # Optional regex, e.g. to allow Vercel preview deployments: https://bilanet.*\.vercel\.app
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX") or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(model.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(code.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(quiz.router, prefix="/api/v1")
app.include_router(project.router, prefix="/api/v1")
app.include_router(meta.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "BilaNet API", "health": "/api/v1/health"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

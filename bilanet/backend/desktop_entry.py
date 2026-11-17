"""Entry point for the backend bundled inside the BilaNet desktop app (built with PyInstaller).

The desktop app starts this process with AI_PROVIDER, MODEL_PATH, DB_URL and PORT set,
and keeps its stdin open. When the app quits or crashes, stdin closes and this server
exits too, so no orphaned background process is left running.
"""
import os
import sys
import threading


def _exit_when_parent_exits():
    try:
        while sys.stdin and sys.stdin.read(1024):
            pass
    except Exception:
        pass
    os._exit(0)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    if os.getenv("BILANET_WATCH_STDIN") == "1":
        threading.Thread(target=_exit_when_parent_exits, daemon=True).start()
    import uvicorn
    from app.main import app
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8765")), log_level="info")

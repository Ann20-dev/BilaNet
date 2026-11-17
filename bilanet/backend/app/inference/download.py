"""One-time download of the local GGUF model, used by the desktop app's first-run setup.

Downloads to "<model>.part" and resumes from there if the connection drops, which
matters on slow or unreliable connections. The file is only renamed into place
once it is complete, so a half-downloaded model is never loaded.
"""
import os
import threading
import httpx

DEFAULT_MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/"
    "qwen2.5-coder-3b-instruct-q4_0.gguf"
)

_lock = threading.Lock()
_state = {"state": "idle", "downloaded": 0, "total": 0, "error": None}


def status():
    with _lock:
        return dict(_state)


def _set(**kw):
    with _lock:
        _state.update(kw)


def start(model_path, url=None):
    """Start downloading in the background. Returns False if a download is already running."""
    with _lock:
        if _state["state"] == "downloading":
            return False
        _state.update(state="downloading", downloaded=0, total=0, error=None)
    threading.Thread(target=_run, args=(model_path, url or os.getenv("MODEL_URL", DEFAULT_MODEL_URL)), daemon=True).start()
    return True


def _run(model_path, url):
    part = model_path + ".part"
    try:
        os.makedirs(os.path.dirname(os.path.abspath(model_path)), exist_ok=True)
        have = os.path.getsize(part) if os.path.exists(part) else 0
        headers = {"Range": f"bytes={have}-"} if have else {}
        with httpx.stream("GET", url, headers=headers, follow_redirects=True, timeout=httpx.Timeout(30.0, read=120.0)) as r:
            if r.status_code == 416:  # .part already holds the whole file
                r.close()
                total = have
            else:
                r.raise_for_status()
                if r.status_code != 206:  # server ignored Range: start over
                    have = 0
                length = int(r.headers.get("Content-Length", 0))
                total = have + length if length else 0
                _set(downloaded=have, total=total)
                with open(part, "ab" if have else "wb") as f:
                    for chunk in r.iter_bytes(1024 * 1024):
                        f.write(chunk)
                        have += len(chunk)
                        _set(downloaded=have)
        if total and os.path.getsize(part) != total:
            raise IOError("Download incomplete. Click Download again to resume.")
        os.replace(part, model_path)
        _set(state="done", downloaded=os.path.getsize(model_path), total=os.path.getsize(model_path))
    except Exception as e:  # report any failure to the UI; the .part file is kept for resuming
        _set(state="error", error=f"{type(e).__name__}: {e}")

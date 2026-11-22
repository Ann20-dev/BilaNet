"""One-time download of the local GGUF model, used by the desktop app's first-run setup.

Downloads to "<model>.part" and resumes from there if the connection drops, which
matters on slow or unreliable connections. Before starting it checks there is enough
free disk space; when finished it checks the file's SHA256 against the published
hash. The file is only renamed into place once it is complete and verified, so a
half-downloaded or damaged model is never loaded.
"""
import hashlib
import os
import threading
import httpx
from app.inference import models

# Keep some space free so the laptop does not run out of disk while the model downloads.
DISK_MARGIN = 300 * 1024 ** 2

_lock = threading.Lock()
_state = {"state": "idle", "downloaded": 0, "total": 0, "error": None}


def status():
    with _lock:
        return dict(_state)


def _set(**kw):
    with _lock:
        _state.update(kw)


def space_needed(model_path, size):
    """Bytes of free disk space still needed to finish downloading `size` bytes to `model_path`."""
    part = model_path + ".part"
    have = os.path.getsize(part) if os.path.exists(part) else 0
    return max(0, size - have) + DISK_MARGIN


def start(model_path, url, sha256=None, size=0):
    """Start downloading in the background.

    Returns None when started, otherwise a short reason it did not start.
    """
    if size:
        need, free = space_needed(model_path, size), models.free_disk(model_path)
        if free and free < need:
            return f"Not enough free disk space: {need / 1e9:.1f} GB needed, {free / 1e9:.1f} GB free. Delete some files and try again."
    with _lock:
        if _state["state"] in ("downloading", "verifying"):
            return "A download is already running."
        _state.update(state="downloading", downloaded=0, total=size, error=None)
    threading.Thread(target=_run, args=(model_path, url, sha256), daemon=True).start()
    return None


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _run(model_path, url, sha256=None):
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
        if sha256:
            _set(state="verifying")
            if _sha256(part) != sha256:
                os.remove(part)  # a damaged file cannot be resumed; start clean next time
                raise IOError("The downloaded file was damaged. Click Download to get it again.")
        os.replace(part, model_path)
        if not os.getenv("MODEL_PATH"):
            models.write_selected(model_path)
        _set(state="done", downloaded=os.path.getsize(model_path), total=os.path.getsize(model_path))
    except Exception as e:  # report any failure to the UI; the .part file is kept for resuming
        _set(state="error", error=f"{type(e).__name__}: {e}")

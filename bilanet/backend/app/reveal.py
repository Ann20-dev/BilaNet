"""Show a file in the computer's file manager (Explorer, Finder, Files), with the file selected.

Used by "Copy model to USB": the student sees the model file and copies it the normal way.
Only the desktop app uses this; the file is always the app's own model, never a path from the page.
"""
import os
import subprocess
import sys
from pathlib import Path


def _clean_env():
    """Environment for the file manager, without what PyInstaller / AppImage set for our own libraries
    (otherwise the file manager can load the wrong libraries and fail to open)."""
    env = dict(os.environ)
    for key in ("LD_LIBRARY_PATH", "LD_PRELOAD", "PYTHONHOME", "PYTHONPATH"):
        orig = env.pop(key + "_ORIG", None)  # PyInstaller keeps the user's original value here
        env.pop(key, None)
        if orig:
            env[key] = orig
    return env


def show(path):
    """Open the file manager at `path`. Returns True if a file manager was started."""
    path = os.path.abspath(path)
    kw = {"env": _clean_env(), "stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    try:
        if sys.platform == "win32":
            subprocess.Popen(["explorer", f"/select,{path}"], **kw)
            return True
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path], **kw)
            return True
        # Linux: ask the file manager (Files, Dolphin, Nemo...) to select the file; else open the folder.
        uri = Path(path).as_uri()
        r = subprocess.run(["gdbus", "call", "--session", "--dest", "org.freedesktop.FileManager1",
                            "--object-path", "/org/freedesktop/FileManager1",
                            "--method", "org.freedesktop.FileManager1.ShowItems", f"['{uri}']", ""],
                           timeout=10, **kw)
        if r.returncode == 0:
            return True
        subprocess.Popen(["xdg-open", os.path.dirname(path)], **kw)
        return True
    except (OSError, subprocess.SubprocessError):
        return False

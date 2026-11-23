"""Entry point for the backend bundled inside the BilaNet desktop app (built with PyInstaller).

The desktop app starts this process with AI_PROVIDER, MODELS_DIR, DB_URL and PORT set,
plus BILANET_PARENT_PID (its own process id). When that process goes away (the app quits
or crashes), this server exits too, so no orphaned background process is left running.

Started as `bilanet-backend --bilanet-run-python <file>` it instead runs a student's
Python file for the Debug tab and exits (see app/coderun.py).
"""
import os
import threading
import time


def _parent_alive(pid):
    try:
        os.kill(pid, 0)  # signal 0: only checks that the process exists
        return True
    except PermissionError:
        return True
    except OSError:
        return False


def _exit_when_parent_exits(pid):
    if os.name == "nt":
        import ctypes
        SYNCHRONIZE, INFINITE = 0x00100000, 0xFFFFFFFF
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            kernel32.WaitForSingleObject(handle, INFINITE)
    else:
        while _parent_alive(pid):
            time.sleep(2)
    os._exit(0)


if __name__ == "__main__":
    import sys
    # The Debug tab runs a student's Python code with this same program (there is no
    # separate Python in the desktop app). See app/coderun.py.
    if len(sys.argv) == 3 and sys.argv[1] == "--bilanet-run-python":
        from app.coderun import child_main
        child_main(sys.argv[2])
        sys.exit(0)
    import multiprocessing
    multiprocessing.freeze_support()
    parent = os.getenv("BILANET_PARENT_PID")
    if parent and parent.isdigit():
        threading.Thread(target=_exit_when_parent_exits, args=(int(parent),), daemon=True).start()
    import uvicorn
    from app.main import app
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8765")), log_level="info")

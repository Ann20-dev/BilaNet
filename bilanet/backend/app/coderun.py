"""Run a student's Python code to get the REAL error for the Debug tab.

Small offline models invent bugs when they have to guess. Given the actual Python error
("ZeroDivisionError: division by zero" on line 2) they explain the right problem.

Safety on the student's own laptop:
- a syntax check happens first with compile(), which never runs anything;
- the code only runs when the student leaves "Run my code" ticked;
- it runs in a separate process, in an empty temporary folder, with no input, a
  5-second time limit and (on Linux/macOS) a memory limit.

In the desktop app there is no separate Python: the bundled backend program runs the
code itself when started with --bilanet-run-python (see desktop_entry.py).
"""
import os
import subprocess
import sys
import tempfile
import traceback

FILE = "main.py"
TIMEOUT = 5
MAX_OUTPUT = 2000
MEMORY_LIMIT = 512 * 1024 * 1024


def allowed():
    """Only run code on the student's own computer. The online demo (AI_PROVIDER=api) runs
    on a shared server, where a stranger's code could read the server's secrets."""
    return os.getenv("AI_PROVIDER", "mock").lower() != "api" and os.getenv("ALLOW_CODE_RUN", "1") != "0"


def syntax_error(code):
    """The SyntaxError message (with line number) or None. Runs nothing."""
    try:
        compile(code, FILE, "exec")
        return None
    except SyntaxError as e:
        line = f"line {e.lineno}" if e.lineno else "unknown line"
        text = (e.text or "").rstrip()
        return f'File "{FILE}", {line}\n    {text}\n{type(e).__name__}: {e.msg}'


def _limit_memory():
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))
    except (ImportError, ValueError, OSError):
        pass


def run(code):
    """Check and run `code`. Returns {"error": str|None, "output": str, "timed_out": bool}."""
    err = syntax_error(code)
    if err:
        return {"error": err, "output": "", "timed_out": False}
    with tempfile.TemporaryDirectory(prefix="bilanet-run-") as tmp:
        path = os.path.join(tmp, FILE)
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--bilanet-run-python", path]
        else:
            cmd = [sys.executable, "-I", os.path.abspath(__file__), path]
        kw = {}
        if os.name == "nt":
            kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW: no console window pops up
        else:
            kw["preexec_fn"] = _limit_memory
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "LANG", "TEMP", "TMP", "HOME", "USERPROFILE")}
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            p = subprocess.run(cmd, cwd=tmp, stdin=subprocess.DEVNULL, capture_output=True,
                               timeout=TIMEOUT, env=env, **kw)
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode("utf-8", "replace")[-MAX_OUTPUT:]
            return {"error": f"The code was stopped after {TIMEOUT} seconds (maybe an endless loop).",
                    "output": out, "timed_out": True}
    out = p.stdout.decode("utf-8", "replace")[-MAX_OUTPUT:]
    err = p.stderr.decode("utf-8", "replace").strip()[-MAX_OUTPUT:]
    return {"error": err or None, "output": out, "timed_out": False}


def child_main(path):
    """Runs in the separate process: execute the file, print a traceback of only its frames."""
    with open(path, encoding="utf-8") as f:
        src = f.read()
    sys.argv = [FILE]
    try:
        exec(compile(src, FILE, "exec"), {"__name__": "__main__", "__file__": FILE})
    except SystemExit:
        pass
    except BaseException as e:  # noqa: BLE001 - we report whatever the student's code raised
        frames = [fr for fr in traceback.extract_tb(e.__traceback__) if fr.filename == FILE]
        lines = ["Traceback (most recent call last):\n"] + traceback.format_list(frames)
        lines += traceback.format_exception_only(type(e), e)
        sys.stderr.write("".join(lines))
        sys.stderr.flush()
        os._exit(1)


if __name__ == "__main__":
    child_main(sys.argv[1])

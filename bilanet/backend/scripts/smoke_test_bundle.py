"""Smoke-test the PyInstaller backend bundle the way the desktop app runs it.

usage: python smoke_test_bundle.py <dist/bilanet-backend dir> [tiny-model.gguf]

Checks that the bundled server starts, answers /health, can run the llama.cpp model
(if a model file is given, e.g. a tiny test GGUF) and exits when its stdin closes.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

bundle = sys.argv[1]
model = sys.argv[2] if len(sys.argv) > 2 and os.path.getsize(sys.argv[2]) > 0 else None
exe = os.path.join(bundle, "bilanet-backend.exe" if os.name == "nt" else "bilanet-backend")
port = "8799"
base = f"http://127.0.0.1:{port}/api/v1"
data = tempfile.mkdtemp()
env = dict(
    os.environ,
    AI_PROVIDER="local",
    MODEL_PATH=os.path.abspath(model) if model else os.path.join(data, "missing.gguf"),
    DB_URL="sqlite:///" + os.path.join(data, "bilanet.db").replace("\\", "/"),
    PORT=port,
    THREADS="2",
    MAX_TOKENS="16",
    BILANET_WATCH_STDIN="1",
)
proc = subprocess.Popen([exe], stdin=subprocess.PIPE, env=env, cwd=data)


def call(path, body=None, timeout=120):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


try:
    for _ in range(120):
        try:
            assert call("/health")["status"] == "ok"
            break
        except (urllib.error.URLError, ConnectionError, OSError):
            if proc.poll() is not None:
                sys.exit(f"backend exited early with code {proc.returncode}")
            time.sleep(1)
    else:
        sys.exit("backend did not answer /health within 120 s")
    print("health ok")
    if model:
        out = call("/chat", {"message": "Once upon a time"})
        assert isinstance(out.get("response"), str), out
        print("llama.cpp inference ok:", repr(out["response"][:80]))
    else:
        print("WARNING: no test model given, skipped the inference check")
finally:
    proc.stdin.close()  # like the desktop app quitting
    try:
        proc.wait(timeout=15)
        print("backend exited when stdin closed")
    except subprocess.TimeoutExpired:
        proc.kill()
        sys.exit("backend did not exit after stdin closed")

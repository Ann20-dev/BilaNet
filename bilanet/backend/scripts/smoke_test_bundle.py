"""Smoke-test the PyInstaller backend bundle the way the desktop app runs it.

usage: python smoke_test_bundle.py <dist/bilanet-backend dir> [tiny-model.gguf]

Checks that the bundled server starts, answers /health, can run the llama.cpp model
(if a model file is given, e.g. a tiny test GGUF) and exits when its parent app exits.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

bundle = os.path.abspath(sys.argv[1])
model = sys.argv[2] if len(sys.argv) > 2 and os.path.getsize(sys.argv[2]) > 0 else None
exe = os.path.join(bundle, "bilanet-backend.exe" if os.name == "nt" else "bilanet-backend")
port = "8799"
base = f"http://127.0.0.1:{port}/api/v1"
data = tempfile.mkdtemp()

# Stand-in for the desktop app: the backend should exit when this process exits.
fake_app = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(3600)"])
env = dict(
    os.environ,
    AI_PROVIDER="local",
    MODEL_PATH=os.path.abspath(model) if model else os.path.join(data, "missing.gguf"),
    DB_URL="sqlite:///" + os.path.join(data, "bilanet.db").replace("\\", "/"),
    PORT=port,
    THREADS="2",
    CONTEXT_SIZE="512",
    MAX_TOKENS="16",
    LLAMA_VERBOSE="1",
    BILANET_PARENT_PID=str(fake_app.pid),
)
proc = subprocess.Popen([exe], env=env, cwd=data)


def call(path, body=None, timeout=300):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


try:
    for _ in range(120):
        try:
            assert call("/health", timeout=5)["status"] == "ok"
            break
        except (urllib.error.URLError, ConnectionError, OSError):
            if proc.poll() is not None:
                sys.exit(f"backend exited early with code {proc.returncode}")
            time.sleep(1)
    else:
        sys.exit("backend did not answer /health within 120 s")
    print("health ok", flush=True)
    # Data files must be inside the bundle (PyInstaller --add-data).
    docs = call("/documents/search", {"query": "read csv with pandas"})["results"]
    assert any(d["title"] == "pandas.read_csv" for d in docs), docs
    print(f"offline docs ok: {call('/documents/info')['counts']}", flush=True)
    with urllib.request.urlopen(base + "/quiz/questions?count=3", timeout=10) as r:
        assert len(json.loads(r.read())) == 3
    print("quiz ok", flush=True)
    # The Debug tab runs Python code with the bundled program itself (--bilanet-run-python),
    # exactly as app/coderun.py starts it. Tested directly: the /code/debug prompt is too long
    # for the tiny test model's 512-token context.
    def run_with_bundle(src):
        path = os.path.join(data, "student.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        return subprocess.run([exe, "--bilanet-run-python", path], cwd=data, capture_output=True,
                              stdin=subprocess.DEVNULL, timeout=120, text=True)
    bad = run_with_bundle("def average(xs):\n    return sum(xs) / len(xs)\n\nprint(average([]))\n")
    assert bad.returncode != 0 and "ZeroDivisionError" in bad.stderr and 'line 2' in bad.stderr, (bad.returncode, bad.stderr)
    good = run_with_bundle("print('hello from bundle')\n")
    assert good.returncode == 0 and good.stdout.strip() == "hello from bundle", (good.returncode, good.stdout, good.stderr)
    print("bundled code runner ok:", bad.stderr.strip().splitlines()[-1], flush=True)
    if model:
        t = time.time()
        out = call("/chat", {"message": "Once upon a time"})
        assert isinstance(out.get("response"), str), out
        print(f"llama.cpp inference ok in {time.time() - t:.1f}s:", repr(out["response"][:80]), flush=True)
    else:
        print("WARNING: no test model given, skipped the inference check")
finally:
    fake_app.kill()  # like the desktop app quitting or crashing
    fake_app.wait()
    try:
        proc.wait(timeout=15)
        print("backend exited after its parent app exited")
    except subprocess.TimeoutExpired:
        proc.kill()
        sys.exit("backend did not exit after its parent app exited")

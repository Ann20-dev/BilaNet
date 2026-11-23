"""Tests for the learning features. They use the mock AI so they run fast without the model."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.inference.provider import get_provider
from app.rag.store import BUILTIN_DB
from app import prompts

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_provider.cache_clear()
    yield
    get_provider.cache_clear()


def post(path, body):
    r = client.post("/api/v1" + path, json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_code_features():
    assert "[mock]" in post("/code/generate", {"description": "fizzbuzz", "language": "java"})["code"]
    assert "line by line" in post("/code/explain", {"code": "print(1)"})["explanation"]
    assert post("/code/debug", {"code": "prnt(1)", "error": "NameError"})["debug"]
    assert post("/code/optimize", {"code": "x=[i for i in range(9)]"})["optimized"]
    assert "C++" in post("/code/translate", {"code": "print(1)", "language": "python", "target_language": "cpp"})["translated"]


def test_code_needs_input():
    assert client.post("/api/v1/code/explain", json={"code": "  "}).status_code == 422
    assert client.post("/api/v1/code/translate", json={"code": "x"}).status_code == 422


def test_reply_language_goes_into_system_prompt():
    assert "Hausa" in prompts.system_prompt("ha")
    assert "Write all explanations" not in prompts.system_prompt("en")
    assert len(prompts.REPLY_LANGUAGES) >= 20


def test_languages_endpoint():
    d = client.get("/api/v1/languages").json()
    assert d["reply_languages"]["sw"].startswith("Swahili")
    assert len(d["code_languages"]) >= 10


def test_quiz():
    qs = client.get("/api/v1/quiz/questions?topic=python&count=5").json()
    assert len(qs) == 5 and all(q["topic"] == "python" for q in qs)
    for q in client.get("/api/v1/quiz/questions?count=50").json():
        assert 0 <= q["answer"] < len(q["options"])
    assert post("/quiz/challenge", {"topic": "loops"})["challenge"]
    assert post("/quiz/check", {"challenge": "sum a list", "solution": "sum(x)"})["feedback"]


def test_project_templates():
    ids = [t["id"] for t in client.get("/api/v1/project/templates").json()]
    assert "python-cli" in ids
    t = client.get("/api/v1/project/templates/python-cli").json()
    assert "main.py" in t["files"] and "app/" in t["tree"]
    assert client.get("/api/v1/project/templates/nope").status_code == 404
    assert post("/project/scaffold", {"description": "school fees tracker", "stack": "Flask"})["plan"]


@pytest.mark.skipif(not BUILTIN_DB.exists(), reason="run scripts/build_docs_db.py first")
def test_docs_search_and_rag():
    hits = post("/documents/search", {"query": "merge two dataframes", "library": "pandas"})["results"]
    assert any("merge" in h["title"] for h in hits)
    hits = post("/documents/search", {"query": "reshape array"})["results"]
    assert any(h["title"] == "numpy.reshape" for h in hits)
    # FTS syntax characters in the question must not break the search.
    post("/documents/search", {"query": 'what does "df[(a OR b)]* do?'})
    d = post("/chat", {"message": "how do I read a csv file with pandas", "use_docs": True})
    assert any(s["title"] == "pandas.read_csv" for s in d["sources"])
    assert "documentation" in d["response"]


def test_input_too_long_rejected():
    assert client.post("/api/v1/code/explain", json={"code": "x" * 20000}).status_code == 422


def test_quiz_questions_in_french_and_portuguese():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.api.quiz import QUESTIONS
    c = TestClient(app)
    # Every built-in question has a full French and Portuguese version; code stays unchanged.
    for q in QUESTIONS:
        for lang in ("fr", "pt"):
            t = q["translations"][lang]
            assert t["question"] and t["explanation"], (q["id"], lang)
            assert len(t.get("options", q["options"])) == len(q["options"]), (q["id"], lang)
    fr = c.get("/api/v1/quiz/questions?topic=python&count=50&lang=fr").json()
    assert all("translations" not in q for q in fr)
    py3 = next(q for q in fr if q["id"] == "py3")
    assert py3["question"].startswith("Quelle ligne") and py3["options"][1] == "def greet():"
    pt = c.get("/api/v1/quiz/questions?topic=general&count=50&lang=pt").json()
    assert next(q for q in pt if q["id"] == "gen1")["options"][0] == "Um vírus"
    # Other languages fall back to English.
    sw = c.get("/api/v1/quiz/questions?topic=python&count=50&lang=sw").json()
    assert next(q for q in sw if q["id"] == "py3")["question"].startswith("Which line")

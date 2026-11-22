"""Offline documentation search with SQLite full-text search (FTS5 + BM25 ranking).

Two indexes:
- the built-in one (docs.db next to this file): Python, NumPy and pandas, made by
  scripts/build_docs_db.py at build time and read-only at runtime;
- the user's own one (DOCS_USER_DB), filled by indexing a folder of notes or code.

Uses a few MB of RAM, compared with roughly 1 GB for an embedding model, so it suits
low-memory laptops.
"""
import glob
import os
import re
import sqlite3
import threading
from pathlib import Path

BUILTIN_DB = Path(__file__).resolve().parent / "docs.db"
LIBRARIES = ("python", "numpy", "pandas", "mine")
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_STOP = {"how", "do", "i", "the", "a", "an", "in", "to", "of", "is", "what", "and", "or", "with",
         "for", "use", "using", "can", "my", "it", "on", "does", "from", "python", "numpy", "pandas"}


_HINTS = {"pandas": "pandas", "pd": "pandas", "df": "pandas", "dataframe": "pandas", "series": "pandas",
          "numpy": "numpy", "np": "numpy", "ndarray": "numpy", "array": "numpy", "matrix": "numpy"}


def library_hint(query: str) -> str | None:
    """Which library the question is about, if it says (e.g. "with pandas", "df.merge", "np.array")."""
    for w in _WORD.findall(query.lower()):
        if w in _HINTS:
            return _HINTS[w]
    return None


def to_match(query: str) -> str:
    """Turn free text into a safe FTS5 query: words joined with OR (FTS syntax characters dropped)."""
    words = [w.lower() for w in _WORD.findall(query)]
    words = [w for w in words if w not in _STOP] or words
    return " OR ".join(f'"{w}"' for w in dict.fromkeys(words))


def _rerank(rows, query, hint):
    """Small fixes on top of BM25 (lower score = better):
    - a name the user typed ("read csv" -> read_csv, "np.linspace" -> linspace) wins;
    - top-level names (numpy.reshape) beat deep ones (numpy.ma.reshape);
    - questions that name a library ("... with pandas") prefer that library."""
    words = [w.lower() for w in _WORD.findall(query)]
    words = [w for w in words if w not in _STOP] or words  # "read a csv" -> read, csv -> read_csv
    wanted = set(words) | {f"{a}_{b}" for a, b in zip(words, words[1:])}
    out = []
    for row in rows:
        title, lib, score = row[0], row[1], row[5]
        last = title.rsplit(".", 1)[-1].replace("Python: ", "").lower()
        score += 1.0 * title.count(".")
        if last in wanted:
            score -= 15.0
        if hint and lib == hint:
            score -= 8.0
        out.append((*row[:5], score))
    out.sort(key=lambda r: r[5])
    return out


class DocStore:
    def __init__(self, user_db: str):
        self.user_db = user_db
        self.lock = threading.Lock()
        self.db = sqlite3.connect(user_db, check_same_thread=False, uri=True)  # uri=True lets ATTACH open docs.db read-only
        self.db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(title, library UNINDEXED, signature UNINDEXED, body, tokenize='porter unicode61')")
        self.has_builtin = BUILTIN_DB.exists()
        if self.has_builtin:
            # Read-only: the app folder may not be writable (e.g. Program Files on Windows).
            self.db.execute("ATTACH DATABASE ? AS builtin", (f"file:{BUILTIN_DB.as_posix()}?mode=ro",))

    def info(self):
        with self.lock:
            counts = {}
            if self.has_builtin:
                for lib, n in self.db.execute("SELECT library, count(*) FROM builtin.docs GROUP BY library"):
                    counts[lib] = n
                versions = dict(self.db.execute("SELECT key, value FROM builtin.meta"))
            else:
                versions = {}
            counts["mine"] = self.db.execute("SELECT count(*) FROM main.docs").fetchone()[0]
        return {"builtin_available": self.has_builtin, "counts": counts, "versions": versions}

    def search(self, query: str, top_k: int = 5, library: str | None = None):
        match = to_match(query)
        if not match:
            return []
        top_k = max(1, min(top_k, 20))
        # BM25 with the title weighted 10x the body, then re-ranked in Python (see _rerank).
        sources = ["main"] + (["builtin"] if self.has_builtin else [])
        if library == "mine":
            sources = ["main"]
        elif library in ("python", "numpy", "pandas"):
            sources = ["builtin"] if self.has_builtin else []
        results = []
        with self.lock:
            for src in sources:
                where = "docs MATCH ?"
                args = [match]
                if library and library != "mine":
                    where += " AND library = ?"
                    args.append(library)
                sql = (f"SELECT title, library, signature, snippet(docs, 3, '', '', ' … ', 40), body, bm25(docs, 10.0, 0, 0, 1.0) AS r "
                       f"FROM {src}.docs WHERE {where} ORDER BY r LIMIT ?")
                try:
                    results += self.db.execute(sql, (*args, max(60, top_k * 10))).fetchall()
                except sqlite3.OperationalError:
                    continue
        results = _rerank(results, query, None if library else library_hint(query))
        return [
            {"title": t, "library": lib, "signature": sig, "snippet": snip, "text": body}
            for t, lib, sig, snip, body, _ in results[:top_k]
        ]

    def index_folder(self, directory: str) -> int:
        """Add the user's own notes and code (.md, .txt, .py) to their personal index."""
        if not os.path.isdir(directory):
            raise FileNotFoundError(directory)
        files = []
        for ext in ("*.md", "*.txt", "*.py", "*.rst"):
            files += glob.glob(os.path.join(directory, "**", ext), recursive=True)
        rows = []
        for f in files[:5000]:
            try:
                with open(f, encoding="utf-8", errors="ignore") as fh:
                    text = fh.read(200_000)
            except OSError:
                continue
            # Split long files into ~2000-character chunks so answers can quote the relevant part.
            for i in range(0, max(len(text), 1), 2000):
                chunk = text[i:i + 2000]
                if chunk.strip():
                    rows.append((f"{os.path.relpath(f, directory)}#{i // 2000 + 1}", "mine", "", chunk))
        with self.lock:
            self.db.execute("DELETE FROM main.docs")
            self.db.executemany("INSERT INTO main.docs(title, library, signature, body) VALUES (?,?,?,?)", rows)
            self.db.commit()
        return len(rows)


_store = None
_store_lock = threading.Lock()


def get_store() -> DocStore:
    global _store
    with _store_lock:
        if _store is None:
            from app.core.config import settings
            _store = DocStore(settings.docs_user_db)
        return _store

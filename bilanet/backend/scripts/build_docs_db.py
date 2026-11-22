"""Build the offline documentation database used by BilaNet's "Docs" search and RAG answers.

usage: python scripts/build_docs_db.py [output.db]    (default: app/rag/docs.db)

Needs numpy and pandas installed in the Python that runs it (only at build time; the app
itself never imports them). It collects the built-in documentation that ships inside
Python, NumPy and pandas (docstrings plus Python's language reference topics) into a
SQLite full-text index. No internet, no embedding model, no extra RAM at runtime.
"""
import importlib
import inspect
import os
import re
import sqlite3
import sys
import warnings
from pathlib import Path

MAX_BODY = 6000  # characters kept per entry; long numpydoc pages are cut

STDLIB = [
    "builtins", "os", "os.path", "sys", "math", "random", "re", "json", "datetime", "time",
    "collections", "itertools", "functools", "pathlib", "csv", "string", "statistics",
    "typing", "sqlite3", "urllib.request", "subprocess", "shutil", "glob", "argparse",
    "logging", "unittest", "dataclasses", "enum", "heapq", "bisect", "decimal", "fractions",
    "copy", "pprint", "textwrap", "threading", "asyncio", "http.server", "zipfile", "hashlib",
    "uuid", "secrets", "tkinter",
]
BUILTIN_TYPES = [str, list, dict, set, tuple, int, float, bytes, range, frozenset]

NUMPY_NAMESPACES = ["numpy", "numpy.linalg", "numpy.random", "numpy.fft", "numpy.char", "numpy.ma"]


def clean(doc: str | None) -> str:
    if not doc:
        return ""
    doc = inspect.cleandoc(doc)
    doc = re.sub(r"\n{3,}", "\n\n", doc)
    return doc[:MAX_BODY]


def signature(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return ""


class Collector:
    def __init__(self):
        self.rows: dict[str, tuple] = {}
        self.bodies: set[str] = set()  # numpy.ma / numpy.char repeat many numpy docstrings

    def add(self, library: str, title: str, obj=None, body: str | None = None, sig: str | None = None):
        body = clean(body if body is not None else getattr(obj, "__doc__", None))
        if len(body) < 20 or title in self.rows or body in self.bodies:
            return
        self.bodies.add(body)
        if sig is None:
            sig = signature(obj) if obj is not None and callable(obj) else ""
        self.rows[title] = (title, library, sig, body)

    def module(self, library: str, modname: str, public_only=True):
        try:
            mod = importlib.import_module(modname)
        except Exception as e:  # e.g. tkinter missing on a build machine
            print(f"  skip {modname}: {e}")
            return
        self.add(library, modname, mod)
        names = getattr(mod, "__all__", None) or [n for n in dir(mod) if not n.startswith("_")]
        for name in names:
            if public_only and name.startswith("_"):
                continue
            try:
                obj = getattr(mod, name)
            except Exception:
                continue
            if inspect.ismodule(obj):
                continue
            prefix = "" if modname == "builtins" else modname + "."
            self.add(library, prefix + name, obj)
            if inspect.isclass(obj):
                self.klass(library, prefix + name, obj)

    def klass(self, library: str, title: str, cls):
        for name, member in inspect.getmembers(cls):
            if name.startswith("_") and name not in ("__init__", "__getitem__", "__len__", "__iter__"):
                continue
            self.add(library, f"{title}.{name}", member)


def collect() -> list[tuple]:
    c = Collector()

    print("Python language reference topics")
    try:
        from pydoc_data.topics import topics
        for key, text in topics.items():
            c.add("python", f"Python: {key}", body=text, sig="")
    except Exception as e:
        print(f"  skip topics: {e}")

    print("Python built-in types")
    for t in BUILTIN_TYPES:
        c.add("python", t.__name__, t)
        c.klass("python", t.__name__, t)

    print("Python standard library")
    for m in STDLIB:
        c.module("python", m)

    print("NumPy")
    import numpy as np
    for m in NUMPY_NAMESPACES:
        c.module("numpy", m)
    c.klass("numpy", "numpy.ndarray", np.ndarray)
    c.klass("numpy", "numpy.random.Generator", np.random.Generator)

    print("pandas")
    import pandas as pd
    c.module("pandas", "pandas")
    for name in ("DataFrame", "Series", "Index", "Timestamp", "Timedelta", "Categorical"):
        c.klass("pandas", f"pandas.{name}", getattr(pd, name))
    from pandas.core.groupby import DataFrameGroupBy, SeriesGroupBy
    c.klass("pandas", "pandas.DataFrameGroupBy", DataFrameGroupBy)
    c.klass("pandas", "pandas.SeriesGroupBy", SeriesGroupBy)
    c.klass("pandas", "pandas.Series.str", pd.Series.str)
    c.klass("pandas", "pandas.Series.dt", type(pd.Series(pd.to_datetime(["2020-01-01"])).dt))
    c.klass("pandas", "pandas.DataFrame.plot", pd.DataFrame.plot)
    c.klass("pandas", "pandas.DataFrame.rolling", type(pd.DataFrame({"a": [1]}).rolling(1)))

    meta = {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
    }
    return list(c.rows.values()), meta


def write(rows, meta, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    db = sqlite3.connect(out)
    # Porter stemming so "sorting" finds "sort"; dots split names so "merge" finds pandas.DataFrame.merge.
    db.execute("CREATE VIRTUAL TABLE docs USING fts5(title, library UNINDEXED, signature UNINDEXED, body, tokenize='porter unicode61')")
    db.executemany("INSERT INTO docs(title, library, signature, body) VALUES (?,?,?,?)", rows)
    db.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
    db.executemany("INSERT INTO meta VALUES (?,?)", meta.items())
    db.commit()
    db.execute("INSERT INTO docs(docs) VALUES('optimize')")
    db.commit()
    db.execute("VACUUM")
    db.close()


if __name__ == "__main__":
    warnings.simplefilter("ignore")
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "app" / "rag" / "docs.db"
    rows, meta = collect()
    write(rows, meta, out)
    by_lib = {}
    for r in rows:
        by_lib[r[1]] = by_lib.get(r[1], 0) + 1
    print(f"Wrote {len(rows)} entries {by_lib} to {out} ({os.path.getsize(out) / 1e6:.1f} MB)")

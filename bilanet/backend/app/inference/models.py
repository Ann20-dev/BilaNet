"""Which offline model to use, chosen to fit the user's laptop.

BilaNet targets low-memory laptops, so there are two sizes of the same model family
(Qwen2.5-Coder, same prompt format):

- "small"    1.5B, ~1.1 GB download, ~1.5 GB RAM while running. For 4-6 GB laptops.
- "standard" 3B,   ~2.1 GB download, ~2.7 GB RAM while running. For 8 GB and up.

The desktop app passes MODELS_DIR; the model the user downloaded is remembered in
"<MODELS_DIR>/selected.txt". MODEL_PATH still works as a fixed override (dev setup,
smoke tests).
"""
import ctypes
import os
import shutil
from dataclasses import dataclass, asdict

GB = 1024 ** 3
HF = "https://huggingface.co/Qwen/{repo}/resolve/main/{file}"


@dataclass(frozen=True)
class ModelOption:
    id: str
    name: str
    file: str
    size: int          # download size in bytes
    sha256: str
    ram_needed: int    # approximate RAM used while answering, in bytes
    min_total_ram: int  # recommend this option only on laptops with at least this much RAM
    repo: str

    @property
    def url(self):
        return HF.format(repo=self.repo, file=self.file)


SMALL = ModelOption(
    id="small", name="Qwen2.5-Coder 1.5B",
    file="qwen2.5-coder-1.5b-instruct-q4_k_m.gguf", size=1117320768,
    sha256="cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046",
    ram_needed=int(1.5 * GB), min_total_ram=0, repo="Qwen2.5-Coder-1.5B-Instruct-GGUF",
)
STANDARD = ModelOption(
    id="standard", name="Qwen2.5-Coder 3B",
    file="qwen2.5-coder-3b-instruct-q4_k_m.gguf", size=2104932800,
    sha256="724fb256bec1ff062b2f65e4569e871ad2e95ab2a3989723d1769c54294730b7",
    ram_needed=int(2.7 * GB), min_total_ram=int(7.5 * GB), repo="Qwen2.5-Coder-3B-Instruct-GGUF",
)
CATALOG = {m.id: m for m in (SMALL, STANDARD)}
# Files earlier versions downloaded; still used if they are already on disk.
LEGACY = ModelOption(
    id="standard-q4_0", name="Qwen2.5-Coder 3B (Q4_0)",
    file="qwen2.5-coder-3b-instruct-q4_0.gguf", size=1997879744,
    sha256="282085f05511706c7b59b32ccabfc452f214771076298c29183e595c576417e0",
    ram_needed=int(2.6 * GB), min_total_ram=int(7.5 * GB), repo="Qwen2.5-Coder-3B-Instruct-GGUF",
)
LEGACY_FILES = {LEGACY.file: LEGACY}
BY_FILE = {m.file: m for m in (*CATALOG.values(), LEGACY)}
SELECTED_FILE = "selected.txt"


def total_ram():
    """Total physical RAM in bytes, or 0 if it cannot be read."""
    try:
        if os.name == "nt":
            class MemStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            st = MemStatus()
            st.dwLength = ctypes.sizeof(MemStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
            return int(st.ullTotalPhys)
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (OSError, ValueError, AttributeError):
        return 0


def free_disk(path):
    """Free bytes on the drive that holds `path` (or its nearest existing parent)."""
    p = os.path.abspath(path or ".")
    while not os.path.exists(p) and os.path.dirname(p) != p:
        p = os.path.dirname(p)
    try:
        return shutil.disk_usage(p).free
    except OSError:
        return 0


def recommended(ram=None):
    ram = total_ram() if ram is None else ram
    # Unknown RAM: pick the option that runs everywhere.
    return STANDARD if ram >= STANDARD.min_total_ram and ram else SMALL


def models_dir():
    if os.getenv("MODELS_DIR"):
        return os.getenv("MODELS_DIR")
    fixed = os.getenv("MODEL_PATH", "")
    return os.path.dirname(os.path.abspath(fixed)) if fixed else ""


def active_path():
    """Path of the model to load, or "" if none is downloaded yet."""
    fixed = os.getenv("MODEL_PATH", "")
    if fixed:
        return fixed
    d = models_dir()
    if not d:
        return ""
    names = [read_selected(d)] + [m.file for m in CATALOG.values()] + list(LEGACY_FILES)
    for name in names:
        if name and os.path.exists(os.path.join(d, name)):
            return os.path.join(d, name)
    return ""


def download_plan(option):
    """(target path, option actually fetched). A fixed MODEL_PATH decides the file itself."""
    fixed = os.getenv("MODEL_PATH", "")
    if fixed:
        return fixed, BY_FILE.get(os.path.basename(fixed))
    return os.path.join(models_dir(), option.file), option


def read_selected(d):
    try:
        with open(os.path.join(d, SELECTED_FILE), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def write_selected(path):
    with open(os.path.join(os.path.dirname(path), SELECTED_FILE), "w", encoding="utf-8") as f:
        f.write(os.path.basename(path))


def describe(option, ram):
    d = asdict(option)
    d["url"] = option.url
    d["fits"] = not ram or ram >= option.ram_needed + int(1.5 * GB)  # leave room for the OS and the app window
    return d

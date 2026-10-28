"""Shared paths, configuration loading, JSONL I/O and hashing helpers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "configs"
DATA_DIR = REPO_ROOT / "data"
BENCH_DIR = DATA_DIR / "benchmark_v1"
CACHE_DIR = DATA_DIR / "cache"
RUNS_DIR = REPO_ROOT / "runs"
RESULTS_DIR = REPO_ROOT / "results"

PROMPT_STRINGS_PATH = CONFIG_DIR / "prompt_strings.yaml"
EXPERIMENT_PATH = CONFIG_DIR / "experiment.yaml"
MODELS_PATH = CONFIG_DIR / "models.yaml"

WORD_RE = re.compile(r"\S+")

# Instruction slots in the fixed order of the letters A-E (brief §5.4).
SLOTS = ("T1", "T2", "T3", "T4", "T5")
# Constraint flag names used in evaluation records, one per slot.
SLOT_TO_FLAG = {"T1": "format", "T2": "length", "T3": "cardinality", "T4": "t4", "T5": "verbatim"}
FAMILIES = ("F1_QA", "F2_CLASSIFICATION", "F3_SUMMARIZATION", "F4_EXTRACTION", "F5_TRANSFORMATION")


def word_count(text: str) -> int:
    """Number of whitespace-delimited tokens (``\\S+``), the word definition used everywhere."""
    return len(WORD_RE.findall(text))


def load_yaml(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_prompt_strings(path: str | Path = PROMPT_STRINGS_PATH) -> dict:
    return load_yaml(path)


def load_experiment(path: str | Path = EXPERIMENT_PATH) -> dict:
    return load_yaml(path)


def load_models(path: str | Path = MODELS_PATH) -> dict:
    return load_yaml(path)


def all_instruction_strings(prompt_strings: dict) -> dict[str, str]:
    """Every instruction key -> string, including the calibration fallbacks."""
    out = dict(prompt_strings["instructions"])
    out.update(prompt_strings.get("calibration_fallbacks") or {})
    return out


def active_instruction_keys(experiment: dict) -> dict[str, str]:
    """Slot (T1..T5) -> active instruction key for the current calibration round."""
    active = experiment["active_instructions"]
    return {slot: active[slot] for slot in SLOTS}


def load_phase_prompts(experiment: dict, phase: str, root: Path = REPO_ROOT) -> list[dict]:
    """Prompt records of a phase: its prompts file, restricted to ``prompt_arms`` when the phase sets them."""
    cfg = experiment["phases"][phase]
    prompts = read_jsonl(root / cfg["prompts_file"])
    arms = cfg.get("prompt_arms")
    if arms:
        prompts = [p for p in prompts if p["arm"] in arms]
    return prompts


def dumps_record(record: dict) -> str:
    """Canonical one-line JSON used for every JSONL file (stable key order = insertion order)."""
    return json.dumps(record, ensure_ascii=False)


def read_jsonl(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: str | Path, records: Iterable[dict]) -> None:
    text = "".join(dumps_record(r) + "\n" for r in records)
    atomic_write_text(path, text)


def write_json(path: str | Path, obj: Any) -> None:
    atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def read_json(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def atomic_write_text(path: str | Path, text: str) -> None:
    """Write a file through a temporary file in the same directory and an atomic rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(tmp, 0o666 & ~umask)  # mkstemp creates 0600; use the normal file mode
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def prompt_text_sha256(system_prompt: str, user_prompt: str) -> str:
    """SHA-256 identifying a prompt text (system + user). Identical texts are generated once."""
    payload = json.dumps([system_prompt, user_prompt], ensure_ascii=False, separators=(",", ":"))
    return sha256_text(payload)


def repo_relpath(path: str | Path) -> str:
    return str(Path(path).resolve().relative_to(REPO_ROOT))

"""Personal-data guard (decisions D01, D02 §3, D03 §2.3, D04 §4).

Looks for home-directory paths (/Users/<name>, /home/<name>), e-mail addresses and ORCID iDs
* in every file under runs/, results/ and release/ (``scan``), and
* in every file tracked by git (``scan_repository``: code, configs, docs, metadata).
Logs show repository paths as <repo> and the home directory as ~, so they never match.

Text that comes from the source datasets (task inputs, prompts, questions, gold answers) or from the models
(``output_text``) is not the authors' data and is never edited; it is excluded from these scans and listed
separately by ``dataset_text_findings`` so that the release step can decide how to handle it.

Usage: python -m src.privacy            (scan runs/, results/, release/ and all tracked files)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from src.common import BENCH_DIR, REPO_ROOT, read_jsonl

PATTERNS: dict[str, re.Pattern] = {
    "home_directory_path": re.compile(r"(?:/Users|/home)/[A-Za-z0-9._-]+"),
    "email_address": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
    "orcid_id": re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b"),
}
# JSON fields holding dataset or model text (excluded from the scans; see dataset_text_findings)
EXTERNAL_TEXT_FIELDS = frozenset({"output_text", "input_text", "user_prompt", "task_directive", "gold", "question"})
TEXT_SUFFIXES = (".json", ".jsonl", ".txt", ".log", ".md", ".csv", ".yaml", ".yml", ".py", ".toml", ".in",
                 ".ipynb", "")
DEFAULT_DIRS = ("runs", "results", "release")


def find_personal_data(text: str) -> list[tuple[str, str]]:
    return [(kind, m.group()) for kind, rx in PATTERNS.items() for m in rx.finditer(text)]


def _strip_external(obj):
    if isinstance(obj, dict):
        return {k: _strip_external(v) for k, v in obj.items() if k not in EXTERNAL_TEXT_FIELDS}
    if isinstance(obj, list):
        return [_strip_external(v) for v in obj]
    return obj


def scannable_text(path: Path) -> str:
    """File text with dataset and model text removed from JSON/JSONL records."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".jsonl":
        lines = []
        for line in text.splitlines():
            try:
                lines.append(json.dumps(_strip_external(json.loads(line)), ensure_ascii=False))
            except json.JSONDecodeError:
                lines.append(line)
        return "\n".join(lines)
    return text


def _scan_files(files: list[Path], base: Path) -> list[tuple[str, str, str]]:
    findings = []
    for path in files:
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        for kind, match in find_personal_data(scannable_text(path)):
            findings.append((str(path.relative_to(base)) if path.is_relative_to(base) else str(path), kind, match))
    return findings


def scan(dirs: list[Path]) -> list[tuple[str, str, str]]:
    """(file, kind, match) for every finding under the given directories."""
    files = [p for d in dirs if d.exists() for p in sorted(d.rglob("*"))]
    return _scan_files(files, REPO_ROOT)


def scan_repository(root: Path = REPO_ROOT) -> list[tuple[str, str, str]]:
    """(file, kind, match) for every finding in the files tracked by git."""
    names = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout.split("\n")
    return _scan_files([root / n for n in names if n], root)


def dataset_text_findings(bench_dir: Path = BENCH_DIR) -> list[tuple[str, str, str]]:
    """(task_id, kind, match) for patterns inside the task texts taken from the source datasets."""
    out = []
    for split in ("main", "pilot"):
        for t in read_jsonl(bench_dir / f"tasks_{split}.jsonl"):
            text = "\n".join([t["input_text"], t["task_directive"], json.dumps(t["gold"], ensure_ascii=False)])
            out += [(t["task_id"], kind, match) for kind, match in find_personal_data(text)]
    return out


def main(argv: list[str] | None = None) -> int:
    findings = scan([REPO_ROOT / d for d in DEFAULT_DIRS]) + scan_repository()
    for f, kind, match in findings:
        print(f"{kind}: {match!r} in {f}")
    print(f"{len(findings)} finding(s) in runs/, results/, release/ and the tracked files")
    known = dataset_text_findings()
    if known:
        print("In source-dataset text (not the authors' data; handled at release):")
        for task_id, kind, match in known:
            print(f"  {task_id}: {kind} {match!r}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

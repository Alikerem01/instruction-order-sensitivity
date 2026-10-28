"""Build the public-release tree in release/ (decisions D03 §2, D04 §4, G2 §2.5; brief §7).

The public repository is a history-free snapshot of the release tag, published separately. This script builds its
content from the tracked files of the current commit (the working tree must be clean; normally the
release tag is checked out):

* every tracked file except those listed in release_exclude.txt (internal working files and the developer README)
  and the Mac dry-run outputs;
* AG News (F2) and XSum (F3) texts are not redistributed: in the task files `input_text` is removed (and, for XSum,
  the reference summary `gold.summary`); in the prompt files `user_prompt`, which contains the INPUT, is removed
  for F2 and F3. Each changed record lists the removed fields in `removed_for_release`. `make tasks` and
  `make prompts` rebuild the full files byte for byte from the pinned dataset revisions, and `make freeze-check`
  then confirms them against data/benchmark_v1/manifest.json;
* every e-mail address in released text becomes `[email removed]` (G2 §2.5); evaluation flags stay as computed on
  the original outputs; RELEASE_REDACTIONS.json lists every changed file with its original SHA-256;
* wording-only changes to the comments and messages of a few frozen files, read from release_wording.json (not
  released): each changed file must match its data/benchmark_v1/manifest.json hash before the change; Python files
  must parse to the same syntax tree apart from docstrings and the listed string literals, YAML files to the same
  content; RELEASE_REDACTIONS.json records the original and the release SHA-256 of each file;
* README.md is the release README (README_RELEASE.md);
* a final scan of the full text of every file (model and dataset text included): no e-mail address, no
  home-directory path, no ORCID iD. The build fails otherwise.

Usage: python scripts/make_release.py [--out release] [--allow-dirty]   (``make release``)
"""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common import sha256_bytes  # noqa: E402
from src.privacy import PATTERNS  # noqa: E402

EXCLUDED_PREFIXES = ("runs/dryrun/",)
EXCLUDE_LIST = ROOT / "release_exclude.txt"  # tracked, never released


WORDING_FILE = ROOT / "release_wording.json"  # tracked, never released
MANIFEST = ROOT / "data" / "benchmark_v1" / "manifest.json"


def _excluded_files() -> set[str]:
    if not EXCLUDE_LIST.exists():  # e.g. in the public tree, which holds no internal file
        return set()
    lines = EXCLUDE_LIST.read_text(encoding="utf-8").splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")} | {EXCLUDE_LIST.name}


EXCLUDED_FILES = _excluded_files()
WORDING = json.loads(WORDING_FILE.read_text(encoding="utf-8")) if WORDING_FILE.exists() else {"files": {}}
NOT_REDISTRIBUTED = {"F2_CLASSIFICATION": ("input_text",), "F3_SUMMARIZATION": ("input_text", "gold.summary")}
PROMPT_FAMILIES = ("F2_CLASSIFICATION", "F3_SUMMARIZATION")
REDACTED = "[email removed]"
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".csv", ".txt", ".log", ".py", ".yaml", ".yml", ".toml", ".in", ".ipynb",
                 ".cfg", ""}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def strip_task(rec: dict) -> dict:
    fields = NOT_REDISTRIBUTED.get(rec.get("family"))
    if not fields:
        return rec
    rec = json.loads(json.dumps(rec))
    for f in fields:
        if "." in f:
            outer, inner = f.split(".", 1)
            rec.get(outer, {}).pop(inner, None)
        else:
            rec.pop(f, None)
    rec["removed_for_release"] = list(fields)
    return rec


def strip_prompt(rec: dict) -> dict:
    if rec.get("family") not in PROMPT_FAMILIES:
        return rec
    rec = dict(rec)
    rec.pop("user_prompt", None)
    rec["removed_for_release"] = ["user_prompt"]
    return rec


def transform_jsonl(text: str, fn) -> str:
    return "".join(json.dumps(fn(json.loads(line)), ensure_ascii=False) + "\n" for line in text.splitlines() if line.strip())


def redact(text: str) -> tuple[str, int]:
    return PATTERNS["email_address"].subn(REDACTED, text)


def _without_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                node.body = node.body[1:] or [ast.Pass()]
    return tree


def _string_constants(tree: ast.AST) -> list[ast.Constant]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def check_wording_change(rel: str, before: str, after: str, literals_allowed: int = 0) -> None:
    """A wording change must not change behaviour or values: Python files parse to the same tree apart from
    docstrings and at most ``literals_allowed`` string literals; YAML files load to the same content."""
    if rel.endswith(".py"):
        a, b = _without_docstrings(ast.parse(before)), _without_docstrings(ast.parse(after))
        changed = sum(x.value != y.value for x, y in zip(_string_constants(a), _string_constants(b)))
        for tree in (a, b):
            for node in _string_constants(tree):
                node.value = ""
        if ast.dump(a) != ast.dump(b) or changed != literals_allowed:
            raise SystemExit(f"{rel}: the wording change touches code ({changed} string literals changed)")
    elif rel.endswith((".yaml", ".yml")):
        import yaml

        if yaml.safe_load(before) != yaml.safe_load(after):
            raise SystemExit(f"{rel}: the wording change alters the YAML content")


def apply_wording(rel: str, data: bytes, manifest: dict) -> str:
    if sha256_bytes(data) != manifest.get(rel):
        raise SystemExit(f"{rel}: differs from data/benchmark_v1/manifest.json; the wording map applies to the frozen version")
    text = after = data.decode("utf-8")
    for item in WORDING["files"][rel]:
        if after.count(item["old"]) != 1:
            raise SystemExit(f"{rel}: a wording item does not occur exactly once")
        after = after.replace(item["old"], item["new"])
    check_wording_change(rel, text, after, WORDING.get("string_literals_changed", {}).get(rel, 0))
    return after


def term_hits(out: Path) -> list[tuple[str, int]]:
    """Lines of released text files that contain a term of the wording map's scan list."""
    terms = [t.lower() for t in WORDING.get("scan_terms", [])]
    hits = []
    for p in sorted(out.rglob("*")):
        if terms and p.is_file() and p.suffix in TEXT_SUFFIXES:
            for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").lower().splitlines(), 1):
                if any(t in line for t in terms):
                    hits.append((p.relative_to(out).as_posix(), i))
    return hits


def build(out: Path, allow_dirty: bool = False) -> dict:
    if git("status", "--porcelain").strip() and not allow_dirty:
        raise SystemExit("The working tree is not clean; commit first (the release is built from a commit).")
    files = [f for f in git("ls-files").splitlines()
             if f not in EXCLUDED_FILES and not f.startswith(EXCLUDED_PREFIXES)]
    if out.exists():
        shutil.rmtree(out)
    redactions, stripped, wording = [], [], []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["files_sha256"]
    for rel in files:
        src = ROOT / rel
        if not src.is_file():
            continue
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = src.read_bytes()
        if Path(rel).suffix not in TEXT_SUFFIXES:
            dest.write_bytes(data)
            continue
        text = data.decode("utf-8")
        if rel in WORDING["files"]:
            text = apply_wording(rel, data, manifest)
        name = Path(rel).name
        if rel.startswith("data/benchmark_v1/") and name.startswith("tasks_") and name.endswith(".jsonl"):
            text = transform_jsonl(text, strip_task)
            stripped.append(rel)
        elif rel.startswith("data/benchmark_v1/") and name.startswith("prompts_") and name.endswith(".jsonl"):
            text = transform_jsonl(text, strip_prompt)
            stripped.append(rel)
        text, n = redact(text)
        if n:
            redactions.append({"file": rel, "replacements": n, "original_sha256": sha256_bytes(data)})
        dest.write_text(text, encoding="utf-8")
        if rel in WORDING["files"]:
            wording.append({"file": rel, "original_sha256": manifest[rel], "release_sha256": sha256_bytes(dest.read_bytes()),
                            "reason": WORDING["reason"]})
    if sorted(r["file"] for r in wording) != sorted(WORDING["files"]):
        raise SystemExit("a file of the wording map is missing from the release")
    (out / "README.md").write_text((ROOT / "README_RELEASE.md").read_text(encoding="utf-8"), encoding="utf-8")
    report = {"source_commit": git("rev-parse", "HEAD").strip(), "files": len(files) + 1,
              "texts_not_redistributed": {"families": NOT_REDISTRIBUTED, "prompt_families": PROMPT_FAMILIES,
                                          "files": stripped},
              "email_rule": f"every e-mail address in released text replaced with '{REDACTED}' (decision G2 §2.5)",
              "redactions": redactions,
              "wording_redactions": wording}
    (out / "RELEASE_REDACTIONS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    findings = scan(out)
    if findings:
        raise SystemExit(f"Release scan found personal data: {findings[:10]}")
    hits = term_hits(out)
    if hits:
        raise SystemExit(f"Release scan found internal references: {hits[:10]}")
    return report


def scan(out: Path) -> list[tuple[str, str, str]]:
    """Full-text scan of every released file: e-mail addresses (after redaction), home paths, ORCID iDs."""
    found = []
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.suffix in TEXT_SUFFIXES:
            text = p.read_text(encoding="utf-8", errors="replace").replace(REDACTED, "")
            for kind, rx in PATTERNS.items():
                found += [(p.relative_to(out).as_posix(), kind, m.group()) for m in rx.finditer(text)]
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "release")
    ap.add_argument("--allow-dirty", action="store_true", help="tests only")
    args = ap.parse_args(argv)
    report = build(args.out, args.allow_dirty)
    print(f"Release tree in {args.out}: {report['files']} files from commit {report['source_commit'][:7]}; "
          f"{len(report['texts_not_redistributed']['files'])} data files stripped of AG News/XSum text; "
          f"{sum(r['replacements'] for r in report['redactions'])} e-mail address(es) redacted; "
          f"{len(report['wording_redactions'])} frozen files with wording-only changes; scan clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

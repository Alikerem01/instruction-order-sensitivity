"""Build dist/colab_bundle_<phase>_<gitsha7>.zip for the Colab generation notebook.

Contents: src/, configs/, the phase's prompts file, requirements-colab.txt, colab/run_generation.ipynb and
manifest_bundle.json (SHA-256 of every other file). Tasks and gold labels are not bundled. A phase with a
``determinism_check`` (main, decision G2 §3.2) also bundles the check prompts and the A6 reference file, and is
refused unless that reference covers every model of the phase (built by scripts/make_a6_reference.py after
Gemma's pilot import).

Preconditions: every integrity test passes, and the bundled paths have no uncommitted changes (the git sha
in the name must describe the content). The zip is deterministic: sorted entries, fixed timestamps.

Usage: python scripts/make_bundle.py --phase PHASE [--allow-dirty]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common import load_experiment, load_phase_prompts, read_json, read_jsonl, sha256_bytes, sha256_file  # noqa: E402
from src.generate import dedup_prompts  # noqa: E402
from src.runs import utc_now  # noqa: E402

FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def experimental_phases() -> tuple[str, ...]:
    """Phases that run on Colab (smoke, pilot, pilot_bs1, main); the dry-run uses the smoke bundle."""
    return tuple(p for p, cfg in load_experiment()["phases"].items() if cfg["experimental"])


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def bundle_paths(phase: str) -> list[str]:
    exp = load_experiment()
    paths = []
    for p in sorted((ROOT / "src").rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".md"):
            paths.append(p.relative_to(ROOT).as_posix())
    paths += ["configs/prompt_strings.yaml", "configs/models.yaml", "configs/experiment.yaml",
              exp["phases"][phase]["prompts_file"], "requirements-colab.txt", "colab/run_generation.ipynb"]
    a6 = exp["phases"][phase].get("determinism_check")
    if a6:
        paths += [p for p in (a6["prompts_file"], a6["reference_file"]) if p not in paths]
    return paths


def a6_reference_problems(exp: dict, phase: str, root: Path = ROOT) -> list[str]:
    """Problems that block a bundle of a phase with a determinism check (decision G2 §3.2): the reference file
    must exist and give, for every model of the phase, one batch-1 output per check prompt."""
    cfg = exp["phases"][phase].get("determinism_check")
    if not cfg:
        return []
    path = root / cfg["reference_file"]
    if not path.exists():
        return [f"{cfg['reference_file']} is missing (run scripts/make_a6_reference.py after Gemma's pilot import)"]
    ref = read_json(path)
    expected = sorted(g["prompt_sha256"] for g in dedup_prompts(read_jsonl(root / cfg["prompts_file"])))
    problems = []
    for m in exp["phases"][phase]["models"]:
        r = (ref.get("models") or {}).get(m)
        if not r:
            problems.append(f"no A6 reference for {m}")
        elif sorted(r["outputs"]) != expected:
            problems.append(f"the A6 reference for {m} does not cover the {len(expected)} check prompts")
        elif r.get("batch_size") != 1:
            problems.append(f"the A6 reference for {m} is not from a batch-size-1 run")
    return problems


def verify_bundle_dir(work_dir: Path) -> dict:
    """Check every SHA-256 listed in manifest_bundle.json (the notebook performs the same check)."""
    manifest = json.loads((work_dir / "manifest_bundle.json").read_text(encoding="utf-8"))
    bad = [rel for rel, digest in manifest["files"].items() if sha256_file(work_dir / rel) != digest]
    if bad:
        raise SystemExit(f"SHA-256 mismatch: {bad}")
    return manifest


def build(phase: str, allow_dirty: bool = False, skip_integrity: bool = False, out_dir: Path | None = None) -> Path:
    """Build the bundle into ``out_dir`` (default dist/). Paths are handled with pathlib only, so directories
    whose names contain spaces (Drive's "Colab Notebooks", decision D02) work unchanged."""
    if phase not in experimental_phases():
        raise SystemExit(f"phase must be one of {experimental_phases()}")
    paths = bundle_paths(phase)
    if not skip_integrity:
        from src import validate_integrity

        res = validate_integrity.run()
        if not res.ok:
            res.print()
            raise SystemExit("Integrity tests failed; no bundle built.")
    exp = load_experiment()
    problems = a6_reference_problems(exp, phase)
    if problems:
        raise SystemExit("A6 reference incomplete; no bundle built:\n  " + "\n  ".join(problems))
    dirty = git("status", "--porcelain", "--", *paths)
    gitsha = git("rev-parse", "HEAD")
    gitsha7 = gitsha[:7]
    if dirty and not allow_dirty:
        raise SystemExit(f"Uncommitted changes in bundled files; commit first:\n{dirty}")
    suffix = "-dirty" if dirty else ""
    name = f"colab_bundle_{phase}_{gitsha7}{suffix}.zip"
    ph = exp["phases"][phase]
    prompts = load_phase_prompts(exp, phase)
    manifest = {
        "bundle_name": name,
        "phase": phase,
        "gitsha": gitsha,
        "gitsha7": gitsha7 + suffix,
        "dirty": bool(dirty),
        "created_utc": utc_now(),
        "prompts_file": ph["prompts_file"],
        "prompt_arms": ph.get("prompt_arms"),
        "n_prompt_ids": len(prompts),
        "n_unique_texts": len({p["prompt_sha256"] for p in prompts}),
        "models": ph["models"],
        "passes": ph.get("passes", 1),
        "batch_size": ph.get("batch_size", exp["generation"]["batch_size"]),
        "determinism_check": ({**ph["determinism_check"], "reference_runs": {
            m: f"{r['phase']}/{r['run_id']}" for m, r in read_json(ROOT / ph["determinism_check"]["reference_file"])
            ["models"].items()}} if ph.get("determinism_check") else None),
        "files": {rel: sha256_file(ROOT / rel) for rel in paths},
    }
    out = (Path(out_dir) if out_dir is not None else ROOT / "dist") / name
    out.parent.mkdir(parents=True, exist_ok=True)
    entries = [(rel, (ROOT / rel).read_bytes()) for rel in paths]
    entries.append(("manifest_bundle.json", (json.dumps(manifest, indent=2) + "\n").encode("utf-8")))
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel, data in sorted(entries):
            info = zipfile.ZipInfo(rel, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"{shown}  ({len(paths)} files + manifest; {manifest['n_prompt_ids']} prompt ids, "
          f"{manifest['n_unique_texts']} unique texts; sha256 {sha256_bytes(out.read_bytes())[:16]}...)")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", required=True, choices=experimental_phases())
    ap.add_argument("--allow-dirty", action="store_true", help="testing only; the bundle name gets a -dirty suffix")
    args = ap.parse_args(argv)
    build(args.phase, args.allow_dirty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

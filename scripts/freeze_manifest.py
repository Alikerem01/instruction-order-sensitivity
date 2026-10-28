"""Write data/benchmark_v1/manifest.json, the G3 freeze manifest (implementation specification C3 step 3).

It records the SHA-256 of every frozen file: tasks, prompts and the selection report; the configs; the source
code under src/ (prompt construction, generation, evaluators, evaluation); the analysis plan; the pinned
requirements. It also records the counts and the generation settings that the main run uses. The manifest is
committed with the freeze and tagged ``benchmark-v1.0.0``; tests/test_freeze_manifest.py fails if a frozen file
changes afterwards (a change then needs a DESIGN_DEVIATIONS.md entry, a recorded design decision and a new manifest).

Usage: python scripts/freeze_manifest.py [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common import load_experiment, read_json, read_jsonl, sha256_file, write_json  # noqa: E402

TAG = "benchmark-v1.0.0"
MANIFEST = ROOT / "data" / "benchmark_v1" / "manifest.json"


def frozen_files() -> list[str]:
    data = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "data" / "benchmark_v1").iterdir()
                  if p.is_file() and p.name != "manifest.json")
    src = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts and p.suffix in (".py", ".md"))
    return data + ["configs/experiment.yaml", "configs/models.yaml", "configs/prompt_strings.yaml"] + src + [
        "ANALYSIS_PLAN.md", "requirements.txt", "requirements-colab.txt"]


def build() -> dict:
    exp = load_experiment()
    main = exp["phases"]["main"]
    prompts = read_jsonl(ROOT / main["prompts_file"])
    return {
        "tag": TAG,
        "decisions": "brief §5 with the approved changes in DESIGN_DEVIATIONS.md (G1, D02-D06, G2)",
        "counts": {
            "tasks_main": len(read_jsonl(ROOT / "data/benchmark_v1/tasks_main.jsonl")),
            "tasks_pilot": len(read_jsonl(ROOT / "data/benchmark_v1/tasks_pilot.jsonl")),
            "prompts_main_ids": len(prompts), "prompts_main_unique_texts": len({p["prompt_sha256"] for p in prompts}),
            "models_main": main["models"],
        },
        "generation": {k: exp["generation"][k] for k in ("do_sample", "num_beams", "max_new_tokens",
                                                          "repetition_penalty", "dtype", "padding_side",
                                                          "attn_implementation")} | {"main_batch_size": main["batch_size"]},
        "calibration": {"round": exp["calibration_round"], "active_instructions": exp["active_instructions"],
                        "length_limit_words": exp["length_limit_words"]},
        "files_sha256": {rel: sha256_file(ROOT / rel) for rel in frozen_files()},
    }


RELEASE_REDACTIONS = ROOT / "RELEASE_REDACTIONS.json"  # present only in the public release tree


def wording_redactions() -> dict:
    """{file: (original SHA-256, release SHA-256)} of the release's wording-only changes (empty outside the release)."""
    if not RELEASE_REDACTIONS.exists():
        return {}
    rows = read_json(RELEASE_REDACTIONS).get("wording_redactions", [])
    return {r["file"]: (r["original_sha256"], r["release_sha256"]) for r in rows}


def differences(manifest: dict) -> list[str]:
    """Frozen files that changed, appeared or disappeared since the manifest was written. In the public release, a
    file with a documented wording-only change counts as unchanged if it has its recorded release hash and the
    recorded original hash is the manifest hash."""
    now = build()["files_sha256"]
    old = manifest["files_sha256"]
    redacted = wording_redactions()
    return sorted(k for k in set(now) | set(old) if now.get(k) != old.get(k)
                  and redacted.get(k) != (old.get(k), now.get(k)))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="compare the files with the committed manifest")
    args = ap.parse_args(argv)
    if args.check:
        diff = differences(read_json(MANIFEST))
        print("frozen files unchanged" if not diff else f"changed since the freeze: {diff}")
        for rel, (original, release) in sorted(wording_redactions().items()):
            print(f"  wording-only change for the public release: {rel} (original SHA-256 {original}, "
                  f"release SHA-256 {release})")
        return 1 if diff else 0
    manifest = build()
    write_json(MANIFEST, manifest)
    print(f"Wrote {MANIFEST.relative_to(ROOT)}: {len(manifest['files_sha256'])} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

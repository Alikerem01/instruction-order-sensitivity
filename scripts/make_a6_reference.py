"""Build the A6 reference file (decision G2 §3.2) from imported batch-1 pilot runs.

For every model of a phase with a ``determinism_check`` (main), the reference phase (``reference_phases``:
pilot_bs1 for the three original models, pilot_gemma for Gemma) must have exactly one imported run. From its
generations, the records of the check prompts (the 5 smoke prompts, order arm) are taken; every record must
come from batch size 1. The reference stores, per model and check prompt, the SHA-256 of the output text, the
token count, the finish reason and the rendered-prompt hash, plus the run id and its environment fingerprint.

Usage: python scripts/make_a6_reference.py [--phase main] [--allow-missing]
Output: the reference_file of the phase (results/qc/a6_reference.json)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common import RUNS_DIR, load_experiment, read_json, read_jsonl, sha256_file, sha256_text, write_json  # noqa: E402
from src.generate import dedup_prompts  # noqa: E402
from src.runs import utc_now  # noqa: E402


def imported_run(runs_root: Path, phase: str) -> str:
    records = [read_json(p) for p in sorted((runs_root / phase).glob("*.import.json"))]
    passed = [r["run_id"] for r in records if r.get("passed") and not r.get("fixture")]
    if len(passed) != 1:
        raise SystemExit(f"expected exactly one imported run in runs/{phase}/, found {passed}")
    return passed[0]


def model_reference(runs_root: Path, phase: str, run_id: str, model: str, check_hashes: list[str]) -> dict:
    run_dir = runs_root / phase / run_id
    by_hash = {r["prompt_sha256"]: r for r in read_jsonl(run_dir / model / "generations.jsonl")}
    missing = [h for h in check_hashes if h not in by_hash]
    if missing:
        raise SystemExit(f"{phase}/{run_id}/{model}: {len(missing)} check prompts have no output")
    picked = [by_hash[h] for h in check_hashes]
    if any(r["batch_size"] != 1 for r in picked):
        raise SystemExit(f"{phase}/{run_id}/{model}: the check prompts were not generated at batch size 1")
    meta = read_json(run_dir / model / "run_meta.json")
    return {
        "phase": phase, "run_id": run_id, "batch_size": 1, "environment_fingerprint": meta["environment_fingerprint"],
        "generations_sha256": sha256_file(run_dir / model / "generations.jsonl"),
        "outputs": {r["prompt_sha256"]: {"prompt_id": r["prompt_ids"][0], "output_sha256": sha256_text(r["output_text"]),
                                         "n_output_tokens": r["n_output_tokens"], "finish_reason": r["finish_reason"],
                                         "rendered_prompt_sha256": r["rendered_prompt_sha256"]} for r in picked},
    }


def build(phase: str = "main", runs_root: Path = RUNS_DIR, root: Path = ROOT, allow_missing: bool = False) -> dict:
    exp = load_experiment()
    cfg = exp["phases"][phase]["determinism_check"]
    check_hashes = [g["prompt_sha256"] for g in dedup_prompts(read_jsonl(root / cfg["prompts_file"]))]
    models, missing = {}, []
    for model in exp["phases"][phase]["models"]:
        ref_phase = cfg["reference_phases"][model]
        try:
            run_id = imported_run(runs_root, ref_phase)
        except SystemExit as e:
            if not allow_missing:
                raise
            missing.append(f"{model}: {e}")
            continue
        models[model] = model_reference(runs_root, ref_phase, run_id, model, check_hashes)
    out = {"decision": "G2 §3.2 (A6)", "created_utc": utc_now(), "check_prompts_file": cfg["prompts_file"],
           "check_prompts_file_sha256": sha256_file(root / cfg["prompts_file"]), "models": models}
    write_json(root / cfg["reference_file"], out)
    for m in missing:
        print(f"not yet available: {m}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", default="main")
    ap.add_argument("--allow-missing", action="store_true", help="write the models that are available")
    args = ap.parse_args(argv)
    out = build(args.phase, allow_missing=args.allow_missing)
    for m, r in out["models"].items():
        print(f"{m}: {len(r['outputs'])} check outputs from {r['phase']}/{r['run_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

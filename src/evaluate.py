"""Evaluate an imported run: one record per prompt id per model (implementation specification §6.2).

Evaluation is a pure function of the raw outputs, the prompts and the tasks, so it is reproducible from the
raw files with one command. Only phases marked ``analysis_eligible`` (main) ever enter an analysis; dry-run,
smoke, pilot, pilot_bs1 and fixture evaluations are checks only.

Usage: python -m src.evaluate --phase PHASE --run RUN_ID
Output: results/eval/<phase>/<run_id>/<model_key>.jsonl and summary.json
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from src.common import RESULTS_DIR, load_experiment, read_json, read_jsonl, sha256_file, write_json, write_jsonl
from src.evaluators import evaluate_output
from src.evaluators.tags import TAG_ORDER
from src.phases import PhaseContext, context_for_phase


def evaluate_run(ctx: PhaseContext, run_id: str, results_root: Path = RESULTS_DIR) -> Path:
    """``ctx``: the phase context of a real phase or of the golden-output fixture."""
    import_record_path = ctx.runs_root / ctx.phase / f"{run_id}.import.json"
    if not import_record_path.exists() or not read_json(import_record_path).get("passed"):
        raise SystemExit(f"Run {run_id} is not imported; run `make import PHASE={ctx.phase} RUN={run_id}` first.")
    import_record = read_json(import_record_path)
    prompts = {p["prompt_id"]: p for p in ctx.prompts}
    tasks = {t["task_id"]: t for t in ctx.tasks}
    out_dir = results_root / "eval" / ctx.phase / run_id
    summary = {"run_id": run_id, "phase": ctx.phase, "analysis_eligible": ctx.analysis_eligible,
               "fixture": ctx.fixture, "replicate_of": import_record.get("replicate_of"), "models": {}}
    if not ctx.analysis_eligible:
        summary["note"] = "CHECK ONLY: this phase never enters any main analysis."
    for model_key in sorted(import_record["models"]):
        gen_path = ctx.runs_root / ctx.phase / run_id / model_key / "generations.jsonl"
        if sha256_file(gen_path) != import_record["raw_files_sha256"][f"{model_key}/generations.jsonl"]:
            raise SystemExit(f"{gen_path} changed since import")
        records = []
        for g in read_jsonl(gen_path):
            for pid in g["prompt_ids"]:
                p = prompts[pid]
                if p["prompt_sha256"] != g["prompt_sha256"]:
                    raise SystemExit(f"{pid}: prompt hash mismatch")
                records.append(evaluate_output(g["output_text"], g["finish_reason"], tasks[p["task_id"]], p, model_key))
        records.sort(key=lambda r: r["prompt_id"])
        if len(records) != len(prompts):
            raise SystemExit(f"{model_key}: {len(records)} evaluation records for {len(prompts)} prompt ids")
        write_jsonl(out_dir / f"{model_key}.jsonl", records)
        n = len(records)
        tags = Counter(t for r in records for t in r["error_tags"])
        f1 = [r for r in records if r["family"] == "F1_QA" and r["q_answer_available"]]
        f2 = [r for r in records if r["family"] == "F2_CLASSIFICATION" and r["q_answer_available"]]
        summary["models"][model_key] = {
            "n_prompt_ids": n,
            "parse_rule": dict(Counter(r["parse_rule"] for r in records)),
            "evaluable_rate": sum(r["evaluable"] for r in records) / n,
            "format_strict_rate": sum(r["format_strict"] for r in records) / n,
            "truncated_rate": sum(r["finish_reason"] == "length" for r in records) / n,
            "verbatim_vs_min3_disagreements": sum(r["verbatim"] != r["verbatim_min3"] for r in records),
            "f1_token_vs_char_containment_disagreements": sum(
                int(r["q_primary"]) != r["quality_detail"]["containment_char"] for r in f1),
            "f2_label_status": dict(Counter(r["quality_detail"]["label_status"] for r in f2)),
            "error_tags": {t: tags[t] for t in TAG_ORDER if tags[t]},
            "eval_file_sha256": sha256_file(out_dir / f"{model_key}.jsonl"),
        }
    write_json(out_dir / "summary.json", summary)
    print(f"Wrote {out_dir} ({', '.join(summary['models'])})")
    return out_dir


def main(argv: list[str] | None = None) -> int:
    exp = load_experiment()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", required=True, choices=sorted(exp["phases"]))
    ap.add_argument("--run", required=True)
    args = ap.parse_args(argv)
    evaluate_run(context_for_phase(args.phase), args.run)
    return 0


if __name__ == "__main__":
    sys.exit(main())

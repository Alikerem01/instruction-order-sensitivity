"""Smoke-test report for G2 (implementation specification C2 step 1; design decision G1, A1, A2 and A5).

For the imported and evaluated smoke runs (normally the two passes of one Colab session): the environment
(GPU, driver, CUDA, torch >= 2.5, the pinned transformers), per model the model class (native transformers
class), the R4 fail-fast record, timing and finish reasons, a degeneracy screen, the A1 comparison, and every raw
output with its evaluator decisions.

Usage: python scripts/smoke_report.py --runs RUN_A [RUN_B]
Output: results/report/smoke_report.md
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.compare_runs import determinism  # noqa: E402
from src.common import RESULTS_DIR, RUNS_DIR, atomic_write_text, load_models, read_json, read_jsonl  # noqa: E402
from src.genconfig import torch_version_ok  # noqa: E402

PINNED_TRANSFORMERS = "5.17.0"
FENCE = "~~~~"


def degeneracy_flags(text: str, finish_reason: str) -> list[str]:
    """A screen for degenerate text (e.g. a LongRoPE problem in Phi-4-mini); every output is also read."""
    flags = []
    if finish_reason == "length":
        flags.append("hit the length limit")
    if not text.strip():
        flags.append("empty")
    words = re.findall(r"\S+", text)
    grams = Counter(tuple(words[i : i + 4]) for i in range(max(0, len(words) - 3)))
    if grams and grams.most_common(1)[0][1] >= 5:
        flags.append(f"4-gram repeated {grams.most_common(1)[0][1]} times")
    if text and sum(ch.isascii() for ch in text) / len(text) < 0.8:
        flags.append("mostly non-ASCII")
    return flags


def run_section(phase: str, run_id: str, runs_root: Path, results_root: Path) -> tuple[list[str], dict]:
    run_dir = runs_root / phase / run_id
    env = read_json(run_dir / "env.json")["environment"]
    info = read_json(run_dir / "run_info.json")
    imp = read_json(runs_root / phase / f"{run_id}.import.json")
    checks = {
        "torch >= 2.5": torch_version_ok(env.get("torch_version") or ""),
        f"transformers == {PINNED_TRANSFORMERS}": env.get("transformers_version") == PINNED_TRANSFORMERS,
        "GPU is an A100": "A100" in (env.get("gpu_name") or ""),
        "import passed": bool(imp.get("passed")),
    }
    lines = [f"## Run `{run_id}` (pass {info.get('pass', 1)}" + (f", replicate of `{info['replicate_of']}`"
                                                                    if info.get("replicate_of") else "") + ")", "",
             f"Bundle commit `{(imp.get('bundle_gitsha') or '')[:7]}`; GPU `{env.get('gpu_name')}` "
             f"({env.get('gpu_memory_total_mib')}), driver {env.get('driver_version')}, CUDA {env.get('cuda_version')}, "
             f"cuDNN {env.get('cudnn_version')}, Python {env.get('python_version')}, torch {env.get('torch_version')}, "
             f"transformers {env.get('transformers_version')}, accelerate {env.get('accelerate_version')}, "
             f"tokenizers {env.get('tokenizers_version')}.", "",
             "| Check | Result |", "|---|---|"]
    lines += [f"| {k} | {'yes' if v else 'NO'} |" for k, v in checks.items()]
    lines += ["", "| Model | Class | Native | R4 | Logits processors | Stopping criteria | Batches | Sessions | "
              "Generation s | Finish reasons |", "|---|---|---|---|---|---|---:|---:|---:|---|"]
    gpu_seconds = 0.0
    model_ok = {}
    specs = {**load_models()["models"], **load_models()["dryrun_models"]}
    for model in sorted(imp["models"]):
        markers = specs.get(model, {}).get("thinking_markers", [])
        if markers:
            found = [g["prompt_ids"][0] for g in read_jsonl(run_dir / model / "generations.jsonl")
                     if any(m in g["output_text"] for m in markers)]
            checks[f"{model}: no thinking markers in outputs"] = not found
    for model in sorted(imp["models"]):
        meta = read_json(run_dir / model / "run_meta.json")
        r4 = meta.get("r4_check", {})
        cls = meta.get("model_class", "")
        native = cls.startswith("transformers.models.")
        model_ok[model] = native and r4.get("passed") is True
        gpu_seconds += meta.get("generation_seconds_total") or 0.0
        lines.append(f"| {model} | `{cls.rsplit('.', 1)[-1]}` | {'yes' if native else 'NO'} | "
                     f"{'passed' if r4.get('passed') else 'NOT PASSED'} | {r4.get('logits_processors')} | "
                     f"{r4.get('stopping_criteria')} | {r4.get('batches_checked')}/{meta['counts']['n_batches']} | "
                     f"{len(meta['sessions'])} | {meta.get('generation_seconds_total')} | "
                     f"{imp['models'][model]['finish_reason']} |")
    lines.append("")
    for model in sorted(imp["models"]):
        evals = {r["prompt_id"]: r for r in read_jsonl(results_root / "eval" / phase / run_id / f"{model}.jsonl")}
        lines += [f"### {model}", ""]
        for g in read_jsonl(run_dir / model / "generations.jsonl"):
            for pid in g["prompt_ids"]:
                e = evals[pid]
                flags = degeneracy_flags(g["output_text"], g["finish_reason"])
                lines += [f"**{pid}** — {g['n_output_tokens']} tokens, finish `{g['finish_reason']}`, parse "
                          f"`{e['parse_rule']}`; FORMAT {e['format_strict']} LENGTH {e['length']} CARDINALITY "
                          f"{e['cardinality']} T4 {e['t4']} VERBATIM {e['verbatim']} (CSR {e['csr']:.1f}); "
                          f"Q {e['q_primary']:.3f}; tags {e['error_tags'] or '[]'}"
                          + (f"; screen: {', '.join(flags)}" if flags else ""), "", FENCE, g["output_text"], FENCE, ""]
    summary = {"checks": checks, "models_native_and_r4": model_ok, "generation_seconds": gpu_seconds}
    return lines, summary


def build(run_ids: list[str], phase: str = "smoke", runs_root: Path = RUNS_DIR, results_root: Path = RESULTS_DIR) -> str:
    lines = ["# Smoke-test report", "",
             "Check only: smoke outputs never enter any analysis, and no smoke number enters the abstract (D04).", ""]
    bodies, summaries = [], {}
    for rid in run_ids:
        body, summ = run_section(phase, rid, runs_root, results_root)
        bodies.append(body)
        summaries[rid] = summ
    lines += ["## Summary", "", "| Run | Checks passed | Models native + R4 | Generation time (min) |", "|---|---|---|---:|"]
    for rid, s in summaries.items():
        lines.append(f"| `{rid}` | {all(s['checks'].values())} | {all(s['models_native_and_r4'].values())} | "
                     f"{s['generation_seconds'] / 60:.2f} |")
    if len(run_ids) == 2:
        a1 = determinism(phase, run_ids[0], run_ids[1], runs_root)
        lines += ["", "A1 run-to-run determinism (byte-identical outputs per model): " + ", ".join(
            f"{m} {'yes' if r['byte_identical'] else 'NO'} ({r['n_fully_identical']}/{r['n_compared']})"
            for m, r in a1["models"].items())]
    lines.append("")
    for body in bodies:
        lines += body
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--phase", default="smoke")
    args = ap.parse_args(argv)
    out = RESULTS_DIR / "report" / f"{args.phase}_report.md"
    atomic_write_text(out, build(args.runs, args.phase))
    print(f"Wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

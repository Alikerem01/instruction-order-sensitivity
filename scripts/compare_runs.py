"""Technical quality-control checks between imported runs (design decision G1, A1 and A3).

A1 run-to-run determinism: two runs of the same phase (the two smoke passes) are compared record by record
(same prompt text): byte-identical output text, identical token count and finish reason, per model.

A3 batch invariance: the batch-16 pilot run and the batch-size-1 run (phase pilot_bs1) are compared on the 100
order-arm pilot texts per model: exact output agreement (generations) and agreement of the 5-bit constraint
vectors (evaluation records). Rule (pre-specified): if vector agreement is at least 98% for every model, the main
run keeps batch size 16; otherwise the study team decides at G2. Descriptive details for that decision: where
differing outputs first diverge, the direction of every constraint flip, the change in CSR and the generation time
per text at each batch size.

Usage:
  python scripts/compare_runs.py determinism --phase smoke --runs RUN_A RUN_B
  python scripts/compare_runs.py batch-invariance --pilot-run RUN --bs1-run RUN
Outputs: results/report/a1_run_to_run_determinism.{json,md} or results/report/a3_batch_invariance.{json,md}
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common import RESULTS_DIR, RUNS_DIR, atomic_write_text, read_json, read_jsonl, write_json  # noqa: E402

VECTOR = ("format_strict", "length", "cardinality", "t4", "verbatim")
A3_THRESHOLD = 0.98


def _imported(runs_root: Path, phase: str, run_id: str) -> dict:
    path = runs_root / phase / f"{run_id}.import.json"
    if not path.exists() or not read_json(path).get("passed"):
        raise SystemExit(f"{phase}/{run_id} is not imported (make import PHASE={phase} RUN={run_id})")
    return read_json(path)


def _generations(runs_root: Path, phase: str, run_id: str, model: str) -> dict[str, dict]:
    return {r["prompt_sha256"]: r for r in read_jsonl(runs_root / phase / run_id / model / "generations.jsonl")}


def determinism(phase: str, run_a: str, run_b: str, runs_root: Path = RUNS_DIR) -> dict:
    rec_a, rec_b = _imported(runs_root, phase, run_a), _imported(runs_root, phase, run_b)
    out = {"check": "A1 run-to-run determinism", "phase": phase, "runs": [run_a, run_b], "models": {}}
    for model in sorted(set(rec_a["models"]) & set(rec_b["models"])):
        ga, gb = _generations(runs_root, phase, run_a, model), _generations(runs_root, phase, run_b, model)
        shared = sorted(set(ga) & set(gb))
        text_same = [h for h in shared if ga[h]["output_text"] == gb[h]["output_text"]]
        full_same = [h for h in text_same if (ga[h]["n_output_tokens"], ga[h]["finish_reason"])
                     == (gb[h]["n_output_tokens"], gb[h]["finish_reason"])]
        env_a = read_json(runs_root / phase / run_a / model / "run_meta.json")["environment_fingerprint"]
        env_b = read_json(runs_root / phase / run_b / model / "run_meta.json")["environment_fingerprint"]
        out["models"][model] = {
            "n_compared": len(shared),
            "n_only_in_one_run": len(set(ga) ^ set(gb)),
            "n_output_text_identical": len(text_same),
            "n_fully_identical": len(full_same),
            "byte_identical": len(shared) > 0 and len(full_same) == len(shared) and not set(ga) ^ set(gb),
            "same_environment": env_a == env_b,
            "differing_prompt_ids": sorted(ga[h]["prompt_ids"][0] for h in shared if h not in full_same),
        }
    return out


def first_difference(a: str, b: str) -> int:
    """Index of the first differing character (the shorter length if one text is a prefix of the other)."""
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))


def _seconds_per_text(meta: dict) -> float | None:
    n = (meta.get("counts") or {}).get("n_records")
    secs = meta.get("generation_seconds_total")
    return round(secs / n, 3) if n and secs is not None else None


def batch_invariance(pilot_run: str, bs1_run: str, runs_root: Path = RUNS_DIR, results_root: Path = RESULTS_DIR,
                     threshold: float = A3_THRESHOLD, pilot_phase: str = "pilot", bs1_phase: str = "pilot_bs1") -> dict:
    rec_p, rec_1 = _imported(runs_root, pilot_phase, pilot_run), _imported(runs_root, bs1_phase, bs1_run)
    out = {"check": "A3 batch invariance", "phases": [pilot_phase, bs1_phase],
           "runs": {"pilot": pilot_run, "pilot_bs1": bs1_run},
           "threshold_vector_agreement": threshold, "models": {}}
    for model in sorted(set(rec_p["models"]) & set(rec_1["models"])):
        gp, g1 = _generations(runs_root, pilot_phase, pilot_run, model), _generations(runs_root, bs1_phase, bs1_run, model)
        missing = sorted(set(g1) - set(gp))
        if missing:
            raise SystemExit(f"{model}: {len(missing)} pilot_bs1 texts are not in the pilot run")
        same_text = [h for h in g1 if gp[h]["output_text"] == g1[h]["output_text"]]
        ep = {r["prompt_id"]: r for r in read_jsonl(results_root / "eval" / pilot_phase / pilot_run / f"{model}.jsonl")}
        e1 = {r["prompt_id"]: r for r in read_jsonl(results_root / "eval" / bs1_phase / bs1_run / f"{model}.jsonl")}
        same_vector = [pid for pid in e1 if tuple(ep[pid][k] for k in VECTOR) == tuple(e1[pid][k] for k in VECTOR)]
        n = len(e1)
        differing = [h for h in g1 if gp[h]["output_text"] != g1[h]["output_text"]]
        firsts = [first_difference(gp[h]["output_text"], g1[h]["output_text"]) for h in differing]
        flips = {k: {"batch16_pass_batch1_fail": 0, "batch1_pass_batch16_fail": 0} for k in VECTOR}
        for pid in e1:
            for k in VECTOR:
                if ep[pid][k] != e1[pid][k]:
                    flips[k]["batch16_pass_batch1_fail" if ep[pid][k] > e1[pid][k] else "batch1_pass_batch16_fail"] += 1
        csr_delta = [e1[pid]["csr"] - ep[pid]["csr"] for pid in e1]
        meta_p = read_json(runs_root / pilot_phase / pilot_run / model / "run_meta.json")
        meta_1 = read_json(runs_root / bs1_phase / bs1_run / model / "run_meta.json")
        out["models"][model] = {
            "n_texts": len(g1),
            "exact_output_agreement": len(same_text) / len(g1) if g1 else None,
            "n_exact_output_agreement": len(same_text),
            "n_prompt_ids": n,
            "vector_agreement": len(same_vector) / n if n else None,
            "n_vector_agreement": len(same_vector),
            "mean_csr_batch16": sum(ep[pid]["csr"] for pid in e1) / n if n else None,
            "mean_csr_batch1": sum(e1[pid]["csr"] for pid in e1) / n if n else None,
            "vector_disagreements": sorted(set(e1) - set(same_vector)),
            "differing_texts_by_family": dict(sorted(Counter(
                e1.get(g1[h]["prompt_ids"][0], {}).get("family", "?") for h in differing).items())),
            "first_difference_char": {
                "median": statistics.median(firsts) if firsts else None, "min": min(firsts, default=None),
                "max": max(firsts, default=None), "n_at_first_char": sum(i == 0 for i in firsts)},
            "constraint_flips": flips,
            "csr_change_batch1_minus_batch16": {
                "mean": sum(csr_delta) / n if n else None, "n_higher_batch1": sum(d > 0 for d in csr_delta),
                "n_lower_batch1": sum(d < 0 for d in csr_delta)},
            "generation_seconds_per_text": {"batch16": _seconds_per_text(meta_p), "batch1": _seconds_per_text(meta_1)},
        }
    agreements = [m["vector_agreement"] for m in out["models"].values()]
    out["rule"] = (f"keep batch size 16 for the main run if vector agreement >= {threshold:.0%} for every model; "
                   "otherwise the study team decides at G2")
    out["keep_batch_size_16"] = bool(agreements) and all(a is not None and a >= threshold for a in agreements)
    return out


def _markdown(result: dict) -> str:
    lines = [f"# {result['check']}", ""]
    if result["check"].startswith("A1"):
        lines += [f"Phase `{result['phase']}`; runs `{result['runs'][0]}` and `{result['runs'][1]}`.", "",
                  "| Model | Compared | Output text identical | Fully identical | Byte-identical | Same environment |",
                  "|---|---:|---:|---:|---|---|"]
        for m, r in result["models"].items():
            lines.append(f"| {m} | {r['n_compared']} | {r['n_output_text_identical']} | {r['n_fully_identical']} | "
                         f"{'yes' if r['byte_identical'] else 'NO'} | {'yes' if r['same_environment'] else 'NO'} |")
        for m, r in result["models"].items():
            if r["differing_prompt_ids"]:
                lines.append(f"\n{m}: differing prompt ids: {', '.join(r['differing_prompt_ids'])}")
    else:
        lines += [f"Pilot run `{result['runs']['pilot']}` (batch 16) versus `{result['runs']['pilot_bs1']}` (batch 1), "
                  "order-arm pilot texts.", "",
                  "| Model | Texts | Exact output agreement | Vector agreement | Mean CSR batch 16 | Mean CSR batch 1 |",
                  "|---|---:|---:|---:|---:|---:|"]
        for m, r in result["models"].items():
            lines.append(f"| {m} | {r['n_texts']} | {r['exact_output_agreement']:.1%} ({r['n_exact_output_agreement']}) | "
                         f"{r['vector_agreement']:.1%} ({r['n_vector_agreement']}) | {r['mean_csr_batch16']:.3f} | "
                         f"{r['mean_csr_batch1']:.3f} |")
        lines += ["", f"Rule: {result['rule']}.", f"Mechanical outcome: keep batch size 16 = "
                  f"**{'yes' if result['keep_batch_size_16'] else 'no (the study team decides)'}**.", "",
                  "Details (descriptive): where differing outputs first diverge, the direction of the constraint flips, "
                  "the CSR change and the generation time per text (sum of batch times / texts; loading excluded).", "",
                  "| Model | Differing texts | First difference (character): median [min, max] | Differ at the first "
                  "character | Flips: batch 16 pass, batch 1 fail | Flips: batch 1 pass, batch 16 fail | Mean CSR "
                  "change (batch 1 - batch 16) | s/text batch 16 | s/text batch 1 |",
                  "|---|---:|---|---:|---:|---:|---:|---:|---:|"]
        for m, r in result["models"].items():
            fd, fl, cc, sp = (r["first_difference_char"], r["constraint_flips"], r["csr_change_batch1_minus_batch16"],
                              r["generation_seconds_per_text"])
            n_diff = r["n_texts"] - r["n_exact_output_agreement"]
            lines.append(f"| {m} | {n_diff} | {fd['median']} [{fd['min']}, {fd['max']}] | {fd['n_at_first_char']} | "
                         f"{sum(v['batch16_pass_batch1_fail'] for v in fl.values())} | "
                         f"{sum(v['batch1_pass_batch16_fail'] for v in fl.values())} | "
                         f"{cc['mean']:+.3f} ({cc['n_higher_batch1']} up, {cc['n_lower_batch1']} down) | "
                         f"{sp['batch16']} | {sp['batch1']} |")
        for m, r in result["models"].items():
            per = ", ".join(f"{k} {v['batch16_pass_batch1_fail']}/{v['batch1_pass_batch16_fail']}"
                            for k, v in r["constraint_flips"].items() if any(v.values()))
            lines.append(f"\n{m}: differing texts by family {r['differing_texts_by_family']}; flips per constraint "
                         f"(batch 16 pass, batch 1 fail / the reverse): {per or 'none'}")
        for m, r in result["models"].items():
            if r["vector_disagreements"]:
                lines.append(f"\n{m}: vector disagreements: {', '.join(r['vector_disagreements'])}")
    return "\n".join(lines) + "\n"


def write(result: dict, stem: str, results_root: Path = RESULTS_DIR) -> Path:
    out_dir = results_root / "report"
    write_json(out_dir / f"{stem}.json", result)
    atomic_write_text(out_dir / f"{stem}.md", _markdown(result))
    return out_dir / f"{stem}.md"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("determinism")
    d.add_argument("--phase", default="smoke")
    d.add_argument("--runs", nargs=2, required=True)
    b = sub.add_parser("batch-invariance")
    b.add_argument("--pilot-run", required=True)
    b.add_argument("--bs1-run", required=True)
    b.add_argument("--pilot-phase", default="pilot")
    b.add_argument("--bs1-phase", default="pilot_bs1")
    args = ap.parse_args(argv)
    if args.cmd == "determinism":
        suffix = "" if args.phase == "smoke" else f"_{args.phase}"
        path = write(determinism(args.phase, *args.runs), f"a1_run_to_run_determinism{suffix}")
    else:
        suffix = "" if args.pilot_phase == "pilot" else f"_{args.pilot_phase}"
        path = write(batch_invariance(args.pilot_run, args.bs1_run, pilot_phase=args.pilot_phase,
                                      bs1_phase=args.bs1_phase), f"a3_batch_invariance{suffix}")
    print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Pilot report, calibration decision and audit sample for G2 (implementation specification C2 steps 3-4; brief §5.6;
design decision G1, A4 and A5).

Everything is pooled: the report never compares orders or variants, because the pilot is never used to choose
prompts or orders. Pilot outputs never enter any analysis, and no pilot number enters the abstract (D04).

* Pooled compliance per model × constraint over the 190 unique pilot texts per model (P01-P10 and V02-V10; V01 is
  the same text as P01 and is counted once).
* Parse rules, code-fence, truncation and evaluable rates, error tags.
* The pre-specified calibration rule with its numbers (pooled over all unique pilot texts and all models):
  T2 LENGTH above 95% -> T2_LENGTH_20; T4 NO_COMMA below 5% or above 95% -> T4_LOWERCASE; more than 2% of outputs
  at the length limit -> max_new_tokens 768.
* Task-quality sanity checks, the F2 label_status distribution with every non-"single" case, and every F1 case
  where character-level and token-level containment disagree (A4).
* Compute so far (A5) from the imported smoke, pilot and pilot_bs1 runs.
* audit_sample.md: 30 outputs sampled with seed 20261003, 2 per model × family stratum, each with the raw output,
  the parsed object and every evaluator decision.

Usage: python scripts/pilot_report.py --run PILOT_RUN_ID
Outputs: results/report/pilot_report.md, pilot_summary.json, audit_sample.md
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common import RESULTS_DIR, RUNS_DIR, atomic_write_text, load_experiment, read_json, read_jsonl, write_json  # noqa: E402
from src.evaluators.format import lenient_parse  # noqa: E402
from src.evaluators.tags import TAG_ORDER  # noqa: E402
from src.phases import PhaseContext, context_for_phase  # noqa: E402

FLAGS = ("format_strict", "length", "cardinality", "t4", "verbatim")
FENCE = "~~~~"
SEED = 20261003


def unique_text_ids(prompts: list[dict]) -> set[str]:
    """One prompt id per prompt text: the first in sorted order (P01 before V01)."""
    first: dict[str, str] = {}
    for p in sorted(prompts, key=lambda p: p["prompt_id"]):
        first.setdefault(p["prompt_sha256"], p["prompt_id"])
    return set(first.values())


def load(ctx: PhaseContext, run_id: str, results_root: Path):
    imp = read_json(ctx.runs_root / ctx.phase / f"{run_id}.import.json")
    keep = unique_text_ids(ctx.prompts)
    evals, gens = {}, {}
    for model in sorted(imp["models"]):
        evals[model] = [r for r in read_jsonl(results_root / "eval" / ctx.phase / run_id / f"{model}.jsonl")
                        if r["prompt_id"] in keep]
        gens[model] = {r["prompt_sha256"]: r for r in
                       read_jsonl(ctx.runs_root / ctx.phase / run_id / model / "generations.jsonl")}
    return imp, evals, gens


def rate(records: list[dict], key: str) -> float:
    return sum(r[key] for r in records) / len(records) if records else float("nan")


def calibration(evals: dict[str, list[dict]], max_new_tokens: int, models: list[str] | None = None) -> dict:
    """The rule of brief §5.6 on the pooled outputs of the calibration models only (decision D06 §4)."""
    used = [m for m in evals if models is None or m in models]
    if not used:
        return {"applicable": False, "models_used": [], "note": "no calibration model in this run (D06 §4): "
                "this pilot never changes the prompt strings", "decisions": {}, "any_string_change": False}
    pooled = [r for m in used for r in evals[m]]
    t4_rules = {r["t4_rule"] for r in pooled}
    length_rate = rate(pooled, "length")
    t4_rate = rate(pooled, "t4")
    trunc_rate = sum(r["finish_reason"] == "length" for r in pooled) / len(pooled)
    decisions = {
        "T2": ("replace T2_LENGTH with T2_LENGTH_20" if length_rate > 0.95 else "keep T2_LENGTH"),
        "T4": ("replace T4_NO_COMMA with T4_LOWERCASE" if t4_rules == {"T4_NO_COMMA"} and
               (t4_rate < 0.05 or t4_rate > 0.95) else "keep the current T4"),
        "max_new_tokens": (f"raise max_new_tokens from {max_new_tokens} to 768" if trunc_rate > 0.02 and
                           max_new_tokens == 512 else f"keep max_new_tokens {max_new_tokens}"),
    }
    return {"applicable": True, "models_used": used, "n_outputs_pooled": len(pooled), "t4_rule": sorted(t4_rules),
            "length_pass_rate": length_rate, "t4_pass_rate": t4_rate, "truncation_rate": trunc_rate,
            "thresholds": {"T2_above": 0.95, "T4_below": 0.05, "T4_above": 0.95, "truncation_above": 0.02},
            "decisions": decisions,
            "any_string_change": decisions["T2"].startswith("replace") or decisions["T4"].startswith("replace")}


def compute_time(runs_root: Path, phases=("smoke", "pilot", "pilot_bs1", "smoke_gemma", "pilot_gemma")) -> dict:
    out = {}
    for phase in phases:
        for rec_path in sorted((runs_root / phase).glob("*.import.json")) if (runs_root / phase).exists() else []:
            rec = read_json(rec_path)
            secs = sum((m.get("generation_seconds_total") or 0.0) for m in rec["models"].values())
            out[rec["run_id"]] = {"phase": phase, "generation_seconds": round(secs, 1)}
    out["total_generation_hours"] = round(sum(v["generation_seconds"] for v in out.values()
                                              if isinstance(v, dict)) / 3600, 3)
    return out


def build(ctx: PhaseContext, run_id: str, results_root: Path = RESULTS_DIR, max_new_tokens: int | None = None,
          calibration_models: list[str] | None = None):
    """``calibration_models`` defaults to experiment.yaml (the three original models, decision D06 §4)."""
    exp = load_experiment()
    max_new_tokens = max_new_tokens or exp["generation"]["max_new_tokens"]
    imp, evals, gens = load(ctx, run_id, results_root)
    tasks = {t["task_id"]: t for t in ctx.tasks}
    summary = {"run_id": run_id, "phase": ctx.phase, "calibration_round": exp["calibration_round"],
               "active_instructions": exp["active_instructions"], "models": {}}
    L = [f"# Pilot report — run `{run_id}`", "",
         "Pooled descriptive checks only. Orders and format variants are never compared here (brief §5.6), "
         "pilot outputs never enter any analysis, and no pilot number enters the abstract (D04).", "",
         f"Calibration round {exp['calibration_round']}; active instructions: "
         + ", ".join(f"{k}={v}" for k, v in exp["active_instructions"].items()) + ".", "",
         "## 1. Compliance per model × constraint (unique texts, pooled over orders and variants)", "",
         "| Model | n | FORMAT | LENGTH | CARDINALITY | T4 | VERBATIM | PCR | evaluable | truncated |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for model, recs in evals.items():
        m = {k: rate(recs, k) for k in FLAGS}
        m.update({"pcr": rate(recs, "pcr"), "evaluable": rate(recs, "evaluable"),
                  "truncated": sum(r["finish_reason"] == "length" for r in recs) / len(recs), "n": len(recs),
                  "parse_rule": dict(Counter(r["parse_rule"] for r in recs)),
                  "code_fence_rate": sum("code_fence" in r["error_tags"] for r in recs) / len(recs),
                  "error_tags": {t: c for t, c in Counter(t for r in recs for t in r["error_tags"]).items()},
                  "verbatim_min3": rate(recs, "verbatim_min3")})
        summary["models"][model] = m
        L.append(f"| {model} | {m['n']} | " + " | ".join(f"{m[k]:.1%}" for k in FLAGS) +
                 f" | {m['pcr']:.1%} | {m['evaluable']:.1%} | {m['truncated']:.1%} |")
    L += ["", "## 2. Parsing and error tags", "", "| Model | strict | fence | first_object | none | code-fence rate |",
          "|---|---:|---:|---:|---:|---:|"]
    for model, m in summary["models"].items():
        pr = m["parse_rule"]
        L.append(f"| {model} | {pr.get('strict', 0)} | {pr.get('fence', 0)} | {pr.get('first_object', 0)} | "
                 f"{pr.get('none', 0)} | {m['code_fence_rate']:.1%} |")
    L += ["", "| Tag | " + " | ".join(summary["models"]) + " |", "|---|" + "---:|" * len(summary["models"])]
    for tag in TAG_ORDER:
        counts = [summary["models"][m]["error_tags"].get(tag, 0) for m in summary["models"]]
        if any(counts):
            L.append(f"| {tag} | " + " | ".join(str(c) for c in counts) + " |")
    cal = calibration(evals, max_new_tokens,
                      calibration_models if calibration_models is not None else exp.get("calibration_models"))
    summary["calibration"] = cal
    L += ["", "## 3. Calibration rule (brief §5.6), applied mechanically", ""]
    if not cal["applicable"]:
        L += [f"Not applicable: {cal['note']}."]
    else:
        L += _calibration_lines(cal)
    L += ["", "## 4. Task-quality sanity checks", "", "| Family | " + " | ".join(evals) + " |",
          "|---|" + "---:|" * len(evals)]
    return _quality_and_compute_lines(L, ctx, evals, gens, tasks, summary)


def _calibration_lines(cal: dict) -> list[str]:
    return [f"Pooled over {cal['n_outputs_pooled']} outputs (all unique pilot texts of the calibration models "
            f"{', '.join(cal['models_used'])}; decision D06 §4).", "",
          "| Quantity | Value | Threshold | Decision |", "|---|---:|---|---|",
          f"| LENGTH pass rate | {cal['length_pass_rate']:.1%} | > 95% | {cal['decisions']['T2']} |",
          f"| T4 ({', '.join(cal['t4_rule'])}) pass rate | {cal['t4_pass_rate']:.1%} | < 5% or > 95% | "
          f"{cal['decisions']['T4']} |",
          f"| Outputs at the length limit | {cal['truncation_rate']:.1%} | > 2% | {cal['decisions']['max_new_tokens']} |",
          "", ("A string replacement is triggered: rebuild the prompts and re-run the pilot once (brief §5.6)."
               if cal["any_string_change"] else "No string replacement is triggered.")]


def _quality_and_compute_lines(L: list[str], ctx: PhaseContext, evals, gens, tasks, summary):
    fams = sorted({r["family"] for recs in evals.values() for r in recs})
    for fam in fams:
        cells = []
        for model, recs in evals.items():
            fr = [r for r in recs if r["family"] == fam]
            avail = [r for r in fr if r["q_answer_available"]]
            cells.append(f"{rate(fr, 'q_primary'):.3f} (answered {len(avail)}/{len(fr)})")
        L.append(f"| {fam} | " + " | ".join(cells) + " |")
    L += ["", "### F2 label status (A4)", ""]
    f2 = [(m, r) for m, recs in evals.items() for r in recs if r["family"] == "F2_CLASSIFICATION" and r["q_answer_available"]]
    status = Counter(r["quality_detail"]["label_status"] for _, r in f2)
    summary["f2_label_status"] = dict(status)
    L.append("Distribution: " + (", ".join(f"{k} {v}" for k, v in sorted(status.items())) or "no answers") + ".")
    for model, r in f2:
        if r["quality_detail"]["label_status"] != "single":
            ans = _answer(gens[model], ctx, r["prompt_id"])
            L.append(f"- {model} `{r['prompt_id']}` ({r['quality_detail']['label_status']}, gold "
                     f"{tasks[r['task_id']]['gold']['label']}): {ans!r}")
    L += ["", "### F1 character-level versus token-level containment (A4)", ""]
    f1 = [(m, r) for m, recs in evals.items() for r in recs if r["family"] == "F1_QA" and r["q_answer_available"]]
    dis = [(m, r) for m, r in f1 if int(r["q_primary"]) != r["quality_detail"]["containment_char"]]
    summary["f1_char_token_disagreements"] = len(dis)
    L.append(f"{len(dis)} disagreement(s) among {len(f1)} answered F1 outputs.")
    for model, r in dis:
        L.append(f"- {model} `{r['prompt_id']}` token {int(r['q_primary'])} / char "
                 f"{r['quality_detail']['containment_char']}, gold {tasks[r['task_id']]['gold']['answers']}: "
                 f"{_answer(gens[model], ctx, r['prompt_id'])!r}")
    comp = compute_time(ctx.runs_root)
    summary["compute"] = comp
    L += ["", "## 5. Compute so far (A5)", "",
          f"Generation time of the imported smoke and pilot runs (all models): {comp['total_generation_hours']:.2f} "
          "A100 hours (sum of batch times; model loading excluded)."]
    return "\n".join(L) + "\n", summary


def _answer(gens: dict, ctx: PhaseContext, prompt_id: str):
    sha = next(p["prompt_sha256"] for p in ctx.prompts if p["prompt_id"] == prompt_id)
    obj = lenient_parse(gens[sha]["output_text"]).obj
    return obj.get("answer") if obj else None


def audit_sample(ctx: PhaseContext, run_id: str, results_root: Path = RESULTS_DIR, per_stratum: int = 2) -> str:
    imp, evals, gens = load(ctx, run_id, results_root)
    rng = random.Random(SEED)
    sha_of = {p["prompt_id"]: p["prompt_sha256"] for p in ctx.prompts}
    L = [f"# Audit sample — pilot run `{run_id}`", "",
         f"{per_stratum} outputs per model × family stratum, drawn with random.Random({SEED}) from the unique pilot "
         "texts (strata in sorted order). For each: the raw output, the parsed object and every evaluator decision.", ""]
    strata = defaultdict(list)
    for model, recs in evals.items():
        for r in recs:
            strata[(model, r["family"])].append(r)
    n = 0
    for key in sorted(strata):
        recs = sorted(strata[key], key=lambda r: r["prompt_id"])
        for r in rng.sample(recs, min(per_stratum, len(recs))):
            n += 1
            g = gens[key[0]][sha_of[r["prompt_id"]]]
            parsed = lenient_parse(g["output_text"])
            decisions = {k: v for k, v in r.items() if k not in ("prompt_id", "task_id", "family", "model_key")}
            L += [f"## {n}. {key[0]} · `{r['prompt_id']}` ({key[1]})", "", "Raw output:", "", FENCE, g["output_text"],
                  FENCE, "", f"Parsed object (rule `{parsed.rule}`):", "", FENCE,
                  json.dumps(parsed.obj, ensure_ascii=False, indent=1) if parsed.obj is not None else "(none)", FENCE,
                  "", "Evaluator decisions:", "", FENCE, json.dumps(decisions, ensure_ascii=False, indent=1), FENCE, ""]
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--phase", default="pilot", help="pilot (three models) or pilot_gemma (decision D06)")
    args = ap.parse_args(argv)
    ctx = context_for_phase(args.phase)
    text, summary = build(ctx, args.run)
    out = RESULTS_DIR / "report"
    stem = "" if args.phase == "pilot" else f"_{args.phase}"
    atomic_write_text(out / f"pilot_report{stem}.md", text)
    write_json(out / f"pilot_summary{stem}.json", summary)
    atomic_write_text(out / f"audit_sample{stem}.md", audit_sample(ctx, args.run))
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

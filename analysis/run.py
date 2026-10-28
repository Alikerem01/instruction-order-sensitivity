"""Run every analysis of the frozen ANALYSIS_PLAN.md on the imported main run (phase C4; ``make analyze``).

Outputs: results/metrics/summary.json (flat dotted keys plus "_meta"), results/tables/table2-5 (CSV and Markdown),
results/report/RESULTS_SUMMARY.md. The analysis reads only evaluation records, import records and the A1/A3
check reports; it never changes a frozen file.

Usage: python -m analysis.run [--n-boot 5000] [--seed 20261003]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.compute import Analysis, robustness  # noqa: E402
from analysis.data import check_main_table, imported_run, load_eval, main_models, pilot_difficulties  # noqa: E402
from analysis.report import results_summary, tables  # noqa: E402
from analysis.spillover import comma_spillover  # noqa: E402
from analysis.posthoc_r1 import run_all as posthoc_r1  # noqa: E402
from src.common import RESULTS_DIR, RUNS_DIR, atomic_write_text, read_json, sha256_file, write_json  # noqa: E402
from src.runs import utc_now  # noqa: E402

PLAN_TAG = "benchmark-v1.0.0"


def checks(models: list[str], run_id: str, runs_root: Path = RUNS_DIR, results_root: Path = RESULTS_DIR) -> dict:
    """Technical checks (method validation, never results): A1, A3, A6, environment, generation time."""
    s = {}
    for name in ("a1_run_to_run_determinism.json", "a1_run_to_run_determinism_smoke_gemma.json"):
        for m, r in read_json(results_root / "report" / name)["models"].items():
            s[f"checks.a1.{m}.byte_identical"] = bool(r["byte_identical"])
    a3 = read_json(results_root / "report" / "a3_batch_invariance.json")
    for m, r in a3["models"].items():
        s[f"checks.a3.{m}.vector_agreement"] = r["vector_agreement"]
        s[f"checks.a3.{m}.exact_output_agreement"] = r["exact_output_agreement"]
    s["checks.a3.keep_batch_16"] = bool(a3["keep_batch_size_16"])
    s["checks.main_batch_size"] = 1
    imp = read_json(runs_root / "main" / f"{run_id}.import.json")
    s["checks.main_import.passed"] = bool(imp["passed"])
    s["checks.main_import.n_checks"] = len(imp["checks"])
    for m in models:
        r = imp["models"][m]
        s[f"checks.a6.{m}.byte_identical"] = bool(r["a6_check"]["passed"])
        s[f"checks.environment.{m}.gpu_name"] = r["environment"]["gpu_name"]
        s[f"checks.environment.{m}.torch_version"] = r["environment"]["torch_version"]
        s[f"checks.environment.{m}.transformers_version"] = r["environment"]["transformers_version"]
        s[f"checks.compute.main.{m}.generation_hours"] = round(r["generation_seconds_total"] / 3600, 3)
        s[f"checks.main_import.{m}.sessions"] = r["n_sessions"]
        s[f"checks.main_import.{m}.superseded_runs"] = len(r.get("superseded", []))
    import platform
    from importlib.metadata import version
    s["checks.software.analysis.python"] = platform.python_version()
    for pkg in ("numpy", "scipy", "statsmodels", "pandas", "pyarrow", "matplotlib"):
        s[f"checks.software.analysis.{pkg}"] = version(pkg)
    return s


def caveats(s: dict, models: list[str]) -> list[str]:
    out = []
    for m in models:
        r = s.get(f"main.counts.{m}.truncated_rate")
        if r:
            out.append(f"{m}: {r:.1%} of outputs ended at the length limit (512 new tokens); they are scored as generated.")
    out.append("Gemma 4 E4B fenced its JSON in every output, so its strict FORMAT compliance and PCR are 0: Gemma is "
               "left out of the FORMAT position GEE (constant compliance, decision G2 §2.4), its Cochran's Q test is "
               "not applicable, and E3 for its PCR is not applicable.")
    not_est = [c for c in ("format", "length", "cardinality", "t4", "verbatim") if s.get(f"main.p1.{c}.status") != "estimated"]
    if not_est:
        out.append("P1 GEE not estimable for " + ", ".join(not_est) + " (separation or non-convergence of the "
                   "pre-specified exchangeable GEE; ANALYSIS_PLAN §8): the observed compliance by position with bootstrap "
                   "CIs (Table 4) is relied on for these instructions. No other estimator was substituted (no model "
                   "specification changes after seeing results without a recorded design decision).")
    ni = [c for c in ("format", "length", "cardinality", "t4", "verbatim") if s.get(f"main.s2.interaction.{c}.status") != "estimated"]
    if ni:
        out.append("S2 position × model interaction GEE not estimable for " + ", ".join(ni) + ".")
    out += ["E2: for NO_COMMA and VERBATIM only position 3 informs the contrast.",
            "E3: the Williams design was not built to vary HE, and 10 orders give it a limited range.",
            "Task quality is computed from the parsed answer; Q = 0 when no answer can be parsed, so a model's Q in a "
            "family partly reflects its FORMAT failures there. Q is never averaged across families.",
            "Model differences are descriptive of these four models; they are not attributed to size or family."]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261003)
    args = ap.parse_args(argv)
    models = main_models()
    run_id = imported_run("main", analysis_eligible=True)
    df = load_eval("main", run_id, models)
    check_main_table(df, models)

    a = Analysis(df, models, n_boot=args.n_boot, seed=args.seed)
    a.counts()
    a.s1()
    a.positions()
    a.gee_family("main.p1", interaction=False)
    a.p2()
    a.p3()
    a.s2()
    a.s3()
    a.e1()
    a.e2()
    a.e3(pilot_difficulties(models))
    a.e4()
    a.e5()
    a.presentation()
    a.p1_independence()
    a.constraint_instability()
    comma_spillover(a, run_id)
    posthoc_r1(a, run_id)  # decision R1 §3.2-§3.8
    from analysis.edit_distance import edit_distances

    a.s.update(edit_distances(models))  # decision R1 §3.10 (tokenizers from the local cache only)
    s = {**a.s, **robustness(df, models, args.n_boot, args.seed), **checks(models, run_id)}
    meta = {
        "run_id": run_id, "analysis_plan_tag": PLAN_TAG, "analysis_plan_sha256": sha256_file(ROOT / "ANALYSIS_PLAN.md"),
        "n_boot": args.n_boot, "seed": args.seed, "generated_utc": utc_now(), "models": models,
        "eval_files_sha256": {m: sha256_file(RESULTS_DIR / "eval" / "main" / run_id / f"{m}.jsonl") for m in models},
        "code_sha256": {p.relative_to(ROOT).as_posix(): sha256_file(p) for p in sorted((ROOT / "analysis").glob("*.py"))},
        "caveats": caveats(s, models),
    }
    nan = [k for k, v in s.items() if isinstance(v, float) and v != v]
    assert not nan, f"NaN values would make summary.json invalid JSON: {nan[:5]}"
    write_json(RESULTS_DIR / "metrics" / "summary.json", {"_meta": meta, **dict(sorted(s.items()))})
    md = tables(s, models, RESULTS_DIR / "tables")
    atomic_write_text(RESULTS_DIR / "report" / "RESULTS_SUMMARY.md", results_summary(s, models, meta, md))
    print(f"summary.json: {len(s)} keys; tables 2-5 and RESULTS_SUMMARY.md written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

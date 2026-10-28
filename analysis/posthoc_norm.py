"""Post-hoc re-analysis of the main run with normalized FORMAT scoring.

Normalized FORMAT removes one code fence that encloses the whole response and then applies the unchanged strict
FORMAT check (rule text: ``FENCE_RULE``). Nothing else in a response is changed. LENGTH, CARDINALITY, NO_COMMA,
VERBATIM and task quality keep their existing evaluation, and the five constraints stay scored independently (no
cascade). The rule is the same for all four models and both arms.

The rule was defined after the outputs had been seen, so every result here is a post-hoc re-analysis. The
pre-specified strict results stay in results/metrics/summary.json; this module never writes that file.

Steps:
1. inventory of the main run, and reproduction of the strict evaluation records and strict results from the raw
   outputs;
2. normalized FORMAT flags at record level, and a check that the other four flags and task quality do not change;
3. every reported analysis under the normalized policy;
4. tables, figures and an audit that no table or figure mixes the two policies (except the labelled comparison).

Outputs in results/posthoc_norm/: summary_norm.json (keys main.posthoc_norm.*), records_format.csv,
tables/*.{csv,md}, figures/*.{png,pdf}, policy_audit.json and SUMMARY_NORM.md.

Usage: python -m analysis.posthoc_norm [--n-boot 5000] [--seed 20261003]   (make posthoc-norm)
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis.bootstrap import bootstrap_p  # noqa: E402
from analysis.compute import Analysis, _put  # noqa: E402
from analysis.data import (ARM_IDS, CONSTRAINTS, FAMILIES, ORDER_IDS, _row, check_main_table,  # noqa: E402
                           imported_run, load_eval, main_models, pilot_difficulties)
from analysis.posthoc_r1 import failure_type, kendall_companion, order_level  # noqa: E402
from analysis.report import CNAMES, FNAMES, NAMES, _md_table, _write_csv, dec, olabel, pct, pval  # noqa: E402
from analysis.stats import bh  # noqa: E402
from analysis.numerics import canonical  # noqa: E402
from src.common import RESULTS_DIR, RUNS_DIR, atomic_write_text, read_jsonl, sha256_file, write_json  # noqa: E402
from src.evaluators import evaluate_output  # noqa: E402
from src.evaluators.format import _FENCE_RE, format_strict  # noqa: E402
from src.phases import context_for_phase  # noqa: E402
from src.runs import utc_now  # noqa: E402

P = "main.posthoc_norm"
OUT = RESULTS_DIR / "posthoc_norm"
STATUS = "post-hoc re-analysis with normalized FORMAT scoring"
FLAGS_NORM = {**{c: c for c in CONSTRAINTS}, "format": "format_norm"}
OTHER = tuple(c for c in CONSTRAINTS if c != "format")
CONTENT_FIELDS = ("length", "cardinality", "t4", "verbatim", "verbatim_min3", "verbatim_case_insensitive",
                  "q_primary", "q_secondary", "q_answer_available", "evaluable")
FENCE_RULE = (
    "Normalized FORMAT: whitespace around the response is ignored. If the response is exactly one code fence, opened "
    "by ``` or ```json (any letter case; optional spaces or tabs and an optional line break after the opening) and "
    "closed by ``` at the very end, with no further ``` inside, the strict FORMAT check is applied to the content of "
    "the fence. Otherwise the strict FORMAT check is applied to the response itself. Strict FORMAT: the text parses as "
    "JSON without duplicate keys into an object whose keys are exactly answer and evidence. Nothing is repaired.")
REJECTED_CASES = (
    "text before or after the fence",
    "more than one fenced block, or a fence inside the fenced content",
    "a fence that is not closed",
    "a language tag other than json (for example ```python or ```jsonc)",
    "other fence styles (~~~ or a four-backtick opening)",
    "fence content that fails the strict check (broken JSON, duplicate keys, missing or extra keys)",
)
FIGURES = {  # file stem -> (paper figure in v2.9 numbering, content)
    "fig_overall_strict_vs_norm": ("Fig. 2", "FORMAT, CSR and PCR per model, pre-specified strict versus normalized"),
    "fig_order_level_norm": ("Fig. 3", "mean CSR and FORMAT compliance in O01-O10, normalized"),
    "fig_noise_floor_norm": ("Fig. 4", "PS by arm and PS_order - PS_format, normalized"),
    "fig_position_norm": ("Fig. 5", "compliance by instruction position, normalized"),
    "fig_constraints_norm": ("Fig. 7", "constraint profiles and PCR, normalized"),
}


# ---- the rule ---------------------------------------------------------------------------------------------
def normalize_output(text: str) -> str:
    """The response with one enclosing code fence removed, or the response unchanged."""
    m = _FENCE_RE.match(text.strip())
    return m.group(1) if m and "```" not in m.group(1) else text


def format_normalized(text: str) -> int:
    return int(format_strict(normalize_output(text)))


def fence_form(text: str) -> str:
    if "```" not in text:
        return "no fence"
    s = text.strip()
    m = _FENCE_RE.match(s)
    if m and "```" not in m.group(1):
        tag = re.match(r"```([^\n]*)", s).group(1).strip().lower()
        return f"one enclosing fence, tag '{tag}'" if tag else "one enclosing fence, no tag"
    return "fence present but not one enclosing fence"


# ---- step 1: inventory and strict reproduction -------------------------------------------------------------
def _canon(rec: dict) -> str:
    return json.dumps(rec, sort_keys=True, ensure_ascii=False)


def reevaluate(run_id: str, models: list[str]) -> tuple[dict, dict, pd.DataFrame]:
    """Every raw output evaluated with the frozen evaluator, as generated and after normalization."""
    ctx = context_for_phase("main")
    prompts = {p["prompt_id"]: p for p in ctx.prompts}
    tasks = {t["task_id"]: t for t in ctx.tasks}
    raw, norm, gens = {}, {}, []
    for m in models:
        for g in read_jsonl(RUNS_DIR / "main" / run_id / m / "generations.jsonl"):
            text = g["output_text"]
            text_n = normalize_output(text)
            arms = sorted({prompts[pid]["arm"] for pid in g["prompt_ids"]})
            gens.append({"model_key": m, "form": fence_form(text), "n_prompt_ids": len(g["prompt_ids"]),
                         "arms": "+".join(arms)})
            for pid in g["prompt_ids"]:
                p = prompts[pid]
                r = evaluate_output(text, g["finish_reason"], tasks[p["task_id"]], p, m)
                raw[(m, pid)] = r
                norm[(m, pid)] = r if text_n == text else evaluate_output(text_n, g["finish_reason"],
                                                                          tasks[p["task_id"]], p, m)
    return raw, norm, pd.DataFrame(gens)


def frame(records: dict, models: list[str]) -> pd.DataFrame:
    """Records as the analysis table, in the row order of analysis.data.load_eval."""
    rows = [_row(records[(m, pid)]) for m in models for pid in sorted(pid for mm, pid in records if mm == m)]
    return pd.DataFrame(rows)


def _same(a, b) -> bool:
    return json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def inventory_and_reproduction(run_id: str, models: list[str], raw: dict, gens: pd.DataFrame, strict: dict,
                               n_boot: int, seed: int, s: dict) -> None:
    for m in models:
        g = gens[gens.model_key == m]
        s[f"{P}.inventory.{m}.unique_generations"] = int(len(g))
        s[f"{P}.inventory.{m}.evaluation_records"] = int(g.n_prompt_ids.sum())
        s[f"{P}.inventory.{m}.shared_generations"] = int((g.n_prompt_ids > 1).sum())
        for form, n in g.form.value_counts().sort_index().items():
            s[f"{P}.inventory.{m}.fence_form.{form}"] = int(n)
    s[f"{P}.inventory.unique_generations"] = int(len(gens))
    s[f"{P}.inventory.evaluation_records"] = int(gens.n_prompt_ids.sum())
    # stored evaluation records against a fresh evaluation of the raw outputs
    n = mismatch = 0
    for m in models:
        for rec in read_jsonl(RESULTS_DIR / "eval" / "main" / run_id / f"{m}.jsonl"):
            n += 1
            mismatch += _canon(raw[(m, rec["prompt_id"])]) != _canon(rec)
    s[f"{P}.checks.strict_records.n"] = n
    s[f"{P}.checks.strict_records.n_mismatch"] = int(mismatch)
    # strict results from the fresh records against summary.json
    df = frame(raw, models)
    check_main_table(df, models)
    a = Analysis(df, models, n_boot, seed)
    a.s1()
    a.positions()
    a.gee_family("main.p1", interaction=False)
    a.p2()
    a.p3()
    a.s2(interaction=False)
    a.s3()
    keys = sorted(a.s)
    bad = [k for k in keys if k not in strict or not _same(a.s[k], strict[k])]
    s[f"{P}.checks.strict_keys.n"] = len(keys)
    s[f"{P}.checks.strict_keys.n_mismatch"] = len(bad)
    s[f"{P}.checks.strict_keys.mismatches"] = bad[:20]
    s[f"{P}.checks.strict_keys.scope"] = ("S1 (both arms), position rates, P1 GEE, P2, P3, S2 pairs and task quality "
                                          "recomputed from the fresh records and compared with summary.json")


# ---- step 2: normalized flags at record level --------------------------------------------------------------
def normalized_frame(raw: dict, norm: dict, models: list[str], s: dict) -> pd.DataFrame:
    df = frame(raw, models)
    df["format_norm"] = [int(norm[(m, pid)]["format_strict"]) for m, pid in zip(df.model_key, df.prompt_id)]
    for c in CONSTRAINTS:
        df[f"cascade_norm_{c}"] = df[FLAGS_NORM[c]] * df.format_norm
    # direction and content invariance
    s[f"{P}.checks.format_direction.n_strict_pass_norm_fail"] = int(((df["format"] == 1) & (df.format_norm == 0)).sum())
    content_bad = sum(any(not _same(raw[k].get(f), norm[k].get(f)) for f in CONTENT_FIELDS) for k in raw)
    detail_bad = sum(not _same(raw[k].get("quality_detail"), norm[k].get("quality_detail")) for k in raw)
    s[f"{P}.checks.content_unchanged.n"] = len(raw)
    s[f"{P}.checks.content_unchanged.n_mismatch"] = int(content_bad)
    s[f"{P}.checks.content_unchanged.n_quality_detail_mismatch"] = int(detail_bad)
    s[f"{P}.checks.content_unchanged.fields"] = list(CONTENT_FIELDS) + ["quality_detail"]
    # changed FORMAT decisions by model x family x arm
    for (m, fam, arm), g in df.groupby(["model_key", "family", "arm"]):
        k = f"{P}.records.{m}.{fam}.{arm}"
        s[f"{k}.n_records"] = int(len(g))
        s[f"{k}.format_strict_pass"] = int(g["format"].sum())
        s[f"{k}.format_norm_pass"] = int(g.format_norm.sum())
        s[f"{k}.n_changed"] = int((g["format"] != g.format_norm).sum())
    for m in models:
        for arm in ARM_IDS:
            g = df[(df.model_key == m) & (df.arm == arm)]
            s[f"{P}.records.{m}.{arm}.n_changed"] = int((g["format"] != g.format_norm).sum())
    s[f"{P}.records.n_changed"] = int((df["format"] != df.format_norm).sum())
    return df


def write_records(df: pd.DataFrame) -> None:
    cols = ["model_key", "prompt_id", "task_id", "family", "arm", "condition_id", "format", "format_norm"]
    out = df[cols].rename(columns={"format": "format_strict"})
    _write_csv(OUT / "records_format.csv", list(out.columns), out.to_numpy().tolist())


# ---- step 3: analyses under the normalized policy ----------------------------------------------------------
def pcr_pairs(a: Analysis, prefix: str) -> None:
    """Post-hoc family: the six model pairs for mean PCR (order arm), paired over tasks, Benjamini-Hochberg across
    the six pairs. The family was set in the re-analysis specification before these tests were computed."""
    tv = {m: a.task_values("order", m) for m in a.models}
    ests, pvals = {}, {}
    for x, y in itertools.combinations(a.models, 2):
        point, reps = a.bs.ratio((tv[x]["pcr"] - tv[y]["pcr"]).to_numpy())
        lo, hi = a.bs.percentile_ci(reps)
        ests[(x, y)] = {"mean": point, "ci_low": lo, "ci_high": hi, "p": bootstrap_p(reps)}
        pvals[(x, y)] = ests[(x, y)]["p"]
    q = bh(pvals)
    for (x, y), e in ests.items():
        _put(a.s, f"{prefix}.{x}_vs_{y}.pcr_diff", {**e, "q": q[(x, y)]})


def subset_norm(a: Analysis, prefix: str) -> None:
    """CSR, PCR and PS among the outputs that pass normalized FORMAT (the analogue of the strict-FORMAT subset)."""
    keep = a.df[a.df.format_norm == 1]
    for arm in ARM_IDS:
        for name, ms in a.model_sets():
            sub = keep[(keep.arm == arm) & keep.model_key.isin(ms)]
            key = f"{prefix}.{arm}.{name}"
            a.s[f"{key}.n_outputs"] = int(len(sub))
            if sub.empty:
                a.s[f"{key}.status"] = "no output passes normalized FORMAT"
                continue
            _put(a.s, f"{key}.csr", a.bs.estimate(*a._sum_count(sub, "_csr")))
            _put(a.s, f"{key}.pcr", a.bs.estimate(*a._sum_count(sub, "_pcr")))
            complete = sub.groupby(["task_id", "model_key"]).size()
            complete = complete[complete == 10].reset_index()[["task_id", "model_key"]]
            a.s[f"{key}.n_complete_task_model_pairs"] = int(len(complete))
            if len(complete):
                full = sub.merge(complete, on=["task_id", "model_key"])
                ps = full.groupby(["task_id", "model_key"])._csr.agg(lambda x: x.max() - x.min()).groupby("task_id")
                _put(a.s, f"{key}.ps", a.bs.estimate(a.bs.align(ps.sum()), a.bs.align(ps.count())))


def failure_composition(a: Analysis, prefix: str) -> None:
    """Normalized FORMAT failures by type, and the raw-output code_fence tag kept as a separate raw property."""
    for arm in ARM_IDS:
        for m in a.models:
            sub = a.arm(arm, m)
            k = f"{prefix}.{arm}.{m}"
            a.s[f"{k}.n_records"] = int(len(sub))
            a.s[f"{k}.format_failure_rate"] = float((sub.format_norm == 0).mean())
            fail = sub[sub.format_norm == 0]
            types = ["fenced, content fails" if r == "fence" else failure_type(r, t)
                     for r, t in zip(fail.parse_rule, fail.error_tags)]
            for t in ("invalid_json", "missing_or_extra_key", "fenced, content fails", "other"):
                a.s[f"{k}.format_failure.{t.replace(', ', '_').replace(' ', '_')}"] = int(types.count(t))
            a.s[f"{k}.code_fence_raw"] = float(sub.error_tags.apply(lambda tags: "code_fence" in tags).mean())


def pilot_difficulties_norm(models: list[str]) -> dict:
    """E3 difficulties from the batch-1 order-arm pilot outputs, with FORMAT scored by the normalized rule."""
    out = pilot_difficulties(models)
    for m in models:
        phase, run_id = out[m]["phase"], out[m]["run_id"]
        fmt = {pid: format_normalized(g["output_text"])
               for g in read_jsonl(RUNS_DIR / phase / run_id / m / "generations.jsonl") for pid in g["prompt_ids"]}
        df = load_eval(phase, run_id, [m])
        df = df[df.arm == "order"]
        out[m]["difficulty"] = {**out[m]["difficulty"], "format": float(1 - np.mean([fmt[p] for p in df.prompt_id]))}
    return out


def normalized_analysis(df: pd.DataFrame, models: list[str], n_boot: int, seed: int, s: dict) -> Analysis:
    a = Analysis(df, models, n_boot, seed, flags=FLAGS_NORM)
    a.s1(prefix=P)
    a.positions(prefix=f"{P}.order")
    a.gee_family(f"{P}.p1", interaction=False)
    excluded = a.s.get(f"{P}.p1.format.excluded_models") or {}
    keep = [m for m in models if m not in excluded]
    a.s[f"{P}.p1.format.sample_models"] = keep
    if excluded:
        order = a.arm("order")
        sub = order[order.model_key.isin(keep)]
        for k in range(1, 6):
            _put(a.s, f"{P}.order.gee_sample.position.format.{k}",
                 a.bs.estimate(*a._sum_count(sub[sub.pos_format == k], "format_norm")))
    a.gee_family(f"{P}.robustness.p1_independence", interaction=False, working="independence",
                 exclude_constant_families=True)
    a.p2(prefix=f"{P}.tests")
    kendall_companion(a, prefix=f"{P}.kendall_w")
    a.p3(prefix=f"{P}.p3")
    a.s2(prefix=f"{P}.s2", interaction=False)
    pcr_pairs(a, f"{P}.s2")
    order_level(a, prefix=f"{P}.order_level")
    a.constraint_instability(prefix=f"{P}.robustness.constraint_instability")
    a.e3(pilot_difficulties_norm(models), prefix=f"{P}.exploratory.e3")
    subset_norm(a, f"{P}.robustness.norm_format_subset")
    failure_composition(a, f"{P}.e5")
    cascade = Analysis(df, models, n_boot, seed, flags={c: f"cascade_norm_{c}" for c in CONSTRAINTS})
    cascade.s1(prefix=f"{P}.robustness.cascade")
    cascade.p2(prefix=f"{P}.robustness.cascade.tests")
    cascade.p3(prefix=f"{P}.robustness.cascade.p3")
    s.update(a.s)
    s.update(cascade.s)
    labels = {
        "label": STATUS,
        "p1.label": "exchangeable GEE with the pre-specified mean model and the constant-compliance rule, applied to the "
                    "normalized flags (post-hoc)",
        "robustness.p1_independence.label": "independence-correlation GEE, constant models and constant family levels "
                                            "left out before fitting, normalized flags (post-hoc sensitivity analysis)",
        "s2.label": "paired task-clustered bootstrap differences between models, order arm, normalized flags; CSR and "
                    "PS_order: Benjamini-Hochberg across the six pairs per outcome; PCR: a separate post-hoc family of "
                    "the six pairs set before the tests were computed",
        "robustness.constraint_instability.label": "share of tasks whose flag varies across the arm's 10 prompts, "
                                                   "normalized flags (post-hoc, descriptive)",
        "robustness.cascade.label": "cascade scoring with normalized FORMAT: a response that fails normalized FORMAT "
                                    "scores 0 on all five constraints (post-hoc, exploratory)",
        "robustness.norm_format_subset.label": "outputs that pass normalized FORMAT only (post-hoc, exploratory)",
        "exploratory.e3.label": "hard-to-easy index with pilot difficulties in which FORMAT is scored by the "
                                "normalized rule (post-hoc, exploratory; ten fixed orders, not a test)",
        "e5.label": "normalized FORMAT failures by type; code_fence_raw is a property of the raw output and is not a "
                    "failure under normalized scoring",
        "order_level.label": "order-level profiles, spans and rankings, normalized flags (post-hoc, descriptive)",
        "kendall_w.label": "constant-CSR task counts and Kendall's W among the variable tasks, normalized flags "
                           "(post-hoc, descriptive)",
    }
    for k, v in labels.items():
        s[f"{P}.{k}"] = v
    return a


# ---- checks against the strict results ---------------------------------------------------------------------
def consistency_checks(df: pd.DataFrame, a: Analysis, strict: dict, models: list[str], s: dict) -> None:
    def compare(pairs: list[tuple[str, str]], name: str, tol: float | None = None) -> None:
        def equal(a, b) -> bool:
            return abs(a - b) < tol if tol is not None else _same(a, b)

        bad = [nk for nk, sk in pairs if nk not in s or sk not in strict or not equal(s[nk], strict[sk])]
        s[f"{P}.checks.{name}.n"] = len(pairs)
        s[f"{P}.checks.{name}.n_mismatch"] = len(bad)
        if bad:
            s[f"{P}.checks.{name}.mismatches"] = bad[:20]

    stats = ("mean", "ci_low", "ci_high")
    names = models + ["pooled"]
    compare([(f"{P}.{arm}.{m}.compliance.{c}.{x}", f"main.{arm}.{m}.compliance.{c}.{x}")
             for arm in ARM_IDS for m in names for c in OTHER for x in stats]
            + [(f"{P}.order.{m}.position.{c}.{k}.{x}", f"main.order.{m}.position.{c}.{k}.{x}")
               for m in names for c in OTHER for k in range(1, 6) for x in stats]
            + [(f"{P}.p1.{c}.status", f"main.p1.{c}.status") for c in OTHER], "other_constraints_unchanged")
    q_keys = [k for k in strict if k.startswith("main.quality.")]
    tmp = Analysis(df, models, a.bs.counts.shape[0], 0, flags=FLAGS_NORM)
    tmp.bs = a.bs
    tmp.s3()
    bad = [k for k in q_keys if not _same(tmp.s.get(k), strict[k])]
    s[f"{P}.checks.quality_unchanged.n"] = len(q_keys)
    s[f"{P}.checks.quality_unchanged.n_mismatch"] = len(bad)
    compare([(f"{P}.{arm}.{m}.{mn}.{x}", f"main.posthoc_r1.fence_tolerant.{arm}.{m}.{ft}.{x}")
             for arm in ARM_IDS for m in names for mn, ft in (("compliance.format", "format"), ("csr", "csr"),
                                                               ("pcr", "pcr")) for x in stats],
            "earlier_fence_tolerant_values")
    g = df[df.model_key == "gemma4e4b"]
    if len(g):
        s[f"{P}.checks.gemma4e4b.format_changed"] = int((g["format"] != g.format_norm).sum())
        s[f"{P}.checks.gemma4e4b.n_records"] = int(len(g))
        compare([(f"{P}.{arm}.gemma4e4b.{mt}.{x}", f"main.{arm}.gemma4e4b.{mt}.{x}")
                 for arm in ARM_IDS for mt in ("ps", "vsr", "flip_rate") for x in stats], "gemma4e4b_range_unchanged",
                tol=1e-12)  # PS is a difference of CSRs that all moved by 0.2: equal up to floating-point rounding
        s[f"{P}.checks.gemma4e4b.csr_shift_max_deviation"] = float(max(
            abs(s[f"{P}.{arm}.gemma4e4b.csr.mean"] - strict[f"main.{arm}.gemma4e4b.csr.mean"] - 0.2) for arm in ARM_IDS))
    counts = [k for k in s if k.startswith(f"{P}.checks.") and k.endswith("n_mismatch")]
    passed = all(s[k] == 0 for k in counts) and s[f"{P}.checks.format_direction.n_strict_pass_norm_fail"] == 0
    if f"{P}.checks.gemma4e4b.csr_shift_max_deviation" in s:
        passed = passed and s[f"{P}.checks.gemma4e4b.csr_shift_max_deviation"] < 1e-12
    s[f"{P}.checks.all_passed"] = bool(passed)


# ---- step 4: outputs with a policy audit -------------------------------------------------------------------
class Tracked(dict):
    """A key dictionary that records every key read, for the policy audit."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.read: set[str] = set()

    def __getitem__(self, key):
        self.read.add(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self.read.add(key)
        return super().get(key, default)


def norm_view(norm: dict) -> tuple[Tracked, dict]:
    """The normalized keys renamed to the strict key scheme, so that the existing figure code draws them. The view
    holds no strict value: a figure that asked for one would fail."""
    view, source = {}, {}
    for k, v in norm.items():
        if not k.startswith(P + "."):
            continue
        rest = k[len(P) + 1:]
        vk = ("main.posthoc_r1." + rest) if rest.startswith("order_level.") else ("main." + rest)
        view[vk], source[vk] = v, k
    return Tracked(view), source


class Audit:
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def record(self, output: str, policy: str, keys: set[str], source: dict | None = None) -> None:
        origin = {"normalized": 0, "strict": 0, "neutral": 0}
        for k in keys:
            k = (source or {}).get(k, k)
            origin["neutral" if k == "_meta" else "normalized" if k.startswith(P + ".") else "strict"] += 1
        ok = origin["strict"] == 0 if policy == "normalized" else (origin["strict"] > 0 and origin["normalized"] > 0)
        self.rows.append({"output": output, "policy": policy, "keys_read": len(keys), **origin, "ok": ok})

    def write(self) -> bool:
        ok = all(r["ok"] for r in self.rows)
        write_json(OUT / "policy_audit.json", {"rule": "a normalized output reads no strict key; only an output "
                                                        "labelled 'comparison' reads both", "all_ok": ok,
                                               "outputs": self.rows})
        return ok


def est(n: dict, key: str, kind: str = "pct") -> str:
    f = pct if kind == "pct" else dec
    return f"{f(n.get(key + '.mean'))} [{f(n.get(key + '.ci_low'))}, {f(n.get(key + '.ci_high'))}]"


def peq(p) -> str:
    text = pval(p)
    return text if text.startswith("<") or text == "n/a" else f"= {text}"


def write_table(name: str, title: str, header: list[str], rows: list[list[str]], csv_rows: list[list],
                csv_header: list[str], note: str = "") -> str:
    md = f"{title}\n\n" + _md_table(header, rows) + (f"\n\n{note}" if note else "") + "\n"
    atomic_write_text(OUT / "tables" / f"{name}.md", md)
    _write_csv(OUT / "tables" / f"{name}.csv", csv_header, csv_rows)
    return md


def tables(n: Tracked, models: list[str], audit: Audit) -> dict[str, str]:
    md = {}
    names = models + ["pooled"]
    label = lambda m: NAMES.get(m, "Pooled")  # noqa: E731

    def done(name: str) -> None:
        audit.record(f"tables/{name}.md", "normalized", set(n.read))
        n.read.clear()

    # N1 overall
    rows, crows = [], []
    for m in names:
        rows.append([label(m)] + [est(n, f"{P}.order.{m}.{k}") for k in ("compliance.format", "csr", "pcr")]
                    + [est(n, f"{P}.{arm}.{m}.ps", "dec") for arm in ARM_IDS])
        crows += [[m, "order", k] + [n.get(f"{P}.order.{m}.{k}.{x}") for x in ("mean", "ci_low", "ci_high")]
                  for k in ("compliance.format", "csr", "pcr")]
        crows += [[m, arm, "ps"] + [n.get(f"{P}.{arm}.{m}.ps.{x}") for x in ("mean", "ci_low", "ci_high")] for arm in ARM_IDS]
    md["tableN1_overall"] = write_table(
        "tableN1_overall", "Table N1. Normalized scoring (post-hoc): FORMAT, CSR and PCR (order arm) and PS in both arms "
        "(mean [95% CI], task-clustered bootstrap).", ["Model", "FORMAT", "CSR", "PCR", "PS_order", "PS_format"], rows,
        crows, ["model", "arm", "metric", "mean", "ci_low", "ci_high"],
        "PS is a range of CSR (0-1). CSR, PCR and FORMAT are shown as percentages.")
    done("tableN1_overall")
    rows, crows = [], []
    for m in names:
        rows.append([label(m)] + [est(n, f"{P}.{arm}.{m}.{k}") for arm in ARM_IDS for k in ("vsr", "flip_rate")])
        crows += [[m, arm, k] + [n.get(f"{P}.{arm}.{m}.{k}.{x}") for x in ("mean", "ci_low", "ci_high")]
                  for arm in ARM_IDS for k in ("vsr", "flip_rate")]
    md["tableN1b_stability"] = write_table(
        "tableN1b_stability", "Table N1b. Normalized scoring (post-hoc): vector stability rate (VSR) and pairwise flip "
        "rate by arm (mean [95% CI]).", ["Model", "VSR, order arm", "Flip rate, order arm", "VSR, format arm",
                                         "Flip rate, format arm"], rows, crows,
        ["model", "arm", "metric", "mean", "ci_low", "ci_high"])
    done("tableN1b_stability")
    rows, crows = [], []
    for m in names:
        rows.append([label(m)] + [est(n, f"{P}.format.{m}.{k}") for k in ("compliance.format", "csr", "pcr")])
        crows += [[m, "format", k] + [n.get(f"{P}.format.{m}.{k}.{x}") for x in ("mean", "ci_low", "ci_high")]
                  for k in ("compliance.format", "csr", "pcr")]
    md["tableN1c_format_arm"] = write_table(
        "tableN1c_format_arm", "Table N1c. Normalized scoring (post-hoc): FORMAT, CSR and PCR in the format arm "
        "(mean [95% CI]).", ["Model", "FORMAT", "CSR", "PCR"], rows, crows,
        ["model", "arm", "metric", "mean", "ci_low", "ci_high"])
    done("tableN1c_format_arm")
    # N2 order tests
    rows, crows = [], []
    for m in models:
        f, c, kw = f"{P}.tests.friedman.{m}", f"{P}.tests.cochran_q.{m}", f"{P}.kendall_w.{m}"
        fr = (f"{dec(n.get(f + '.chi2'), 2)} ({n.get(f + '.df')})", pval(n.get(f + ".p")), pval(n.get(f + ".q_bh")),
              dec(n.get(f + ".kendall_w"))) if n.get(f + ".status") == "estimated" else (n.get(f + ".status"), "", "", "")
        cq = (f"{dec(n.get(c + '.q'), 2)} ({n.get(c + '.df')})", pval(n.get(c + ".p")), pval(n.get(c + ".q_bh"))) \
            if n.get(c + ".status") == "estimated" else (n.get(c + ".status"), "", "")
        rows.append([NAMES[m], *fr, *cq, str(n.get(kw + ".n_constant_tasks")), dec(n.get(kw + ".kendall_w_nonconstant"))])
        crows.append([m, n.get(f + ".chi2"), n.get(f + ".df"), n.get(f + ".p"), n.get(f + ".q_bh"), n.get(f + ".kendall_w"),
                      n.get(c + ".status"), n.get(c + ".q"), n.get(c + ".df"), n.get(c + ".p"), n.get(c + ".q_bh"),
                      n.get(kw + ".n_constant_tasks"), n.get(kw + ".kendall_w_nonconstant")])
    n_cq = sum(n.get(f"{P}.tests.cochran_q.{m}.status") == "estimated" for m in models)
    md["tableN2_order_tests"] = write_table(
        "tableN2_order_tests", "Table N2. Normalized scoring (post-hoc): tests of systematic order effects across the "
        "ten orders (100 tasks per model). Friedman test on CSR; Cochran's Q on PCR.",
        ["Model", "Friedman χ² (df)", "p", "q", "Kendall's W", "Cochran's Q (df)", "p", "q", "Constant-CSR tasks",
         "W, variable-CSR tasks"], rows, crows,
        ["model", "friedman_chi2", "friedman_df", "friedman_p", "friedman_q_bh", "kendall_w", "cochran_status",
         "cochran_q", "cochran_df", "cochran_p", "cochran_q_bh", "n_constant_csr_tasks", "kendall_w_variable_tasks"],
        f"q: Benjamini-Hochberg across the four Friedman tests, and separately across the {n_cq} estimable Cochran's Q "
        "tests.")
    done("tableN2_order_tests")
    # N3 position (FORMAT) and GEE
    rows, crows = [], []
    for m in names + (["gee_sample"] if n.get(f"{P}.order.gee_sample.position.format.1.mean") is not None else []):
        lab = "GEE sample (" + ", ".join(NAMES[x] for x in n.get(f"{P}.p1.format.sample_models")) + ")" \
            if m == "gee_sample" else label(m)
        rows.append([lab] + [est(n, f"{P}.order.{m}.position.format.{k}") for k in range(1, 6)])
        crows += [[m, k] + [n.get(f"{P}.order.{m}.position.format.{k}.{x}") for x in ("mean", "ci_low", "ci_high")]
                  for k in range(1, 6)]
    gee_lines = []
    for prefix, name in ((f"{P}.p1", "Exchangeable GEE"), (f"{P}.robustness.p1_independence", "Independence GEE "
                                                                                                "(sensitivity)")):
        for c in CONSTRAINTS:
            g = f"{prefix}.{c}"
            excl = n.get(g + ".excluded_models") or {}
            excl_txt = "; excluded (constant): " + ", ".join(f"{NAMES[x]} {pct(v)}" for x, v in excl.items()) if excl else ""
            fam = n.get(g + ".excluded_families") or {}
            fam_txt = "; constant families left out: " + ", ".join(FNAMES[x] for x in fam) if fam else ""
            if n.get(g + ".status") == "estimated":
                ors = ", ".join(f"position {k}: {dec(n.get(f'{g}.or.{k}.estimate'), 2)} [{dec(n.get(f'{g}.or.{k}.ci_low'), 2)}, "
                                f"{dec(n.get(f'{g}.or.{k}.ci_high'), 2)}]" for k in range(2, 6))
                gee_lines.append(f"- {name}, {CNAMES[c]}: Wald χ²({n.get(g + '.df')}) = {dec(n.get(g + '.wald_chi2'), 2)}, "
                                 f"p {peq(n.get(g + '.p'))}, q {peq(n.get(g + '.q'))}, n = {n.get(g + '.n')}{excl_txt}"
                                 f"{fam_txt}. Odds ratios against position 1: {ors}.")
            else:
                gee_lines.append(f"- {name}, {CNAMES[c]}: {n.get(g + '.status')} ({n.get(g + '.reason')}){excl_txt}.")
    md["tableN3_position_format"] = write_table(
        "tableN3_position_format", "Table N3. Normalized scoring (post-hoc): FORMAT compliance by instruction position "
        "(order arm; mean [95% CI]). Each position is realized by two orders.", ["Model", "Position 1", "Position 2",
                                                                                 "Position 3", "Position 4",
                                                                                 "Position 5"], rows, crows,
        ["model", "position", "mean", "ci_low", "ci_high"],
        "The pooled row includes every model; the GEE-sample row includes only the models in the FORMAT GEE.\n\n"
        + "\n".join(gee_lines))
    done("tableN3_position_format")
    crows = [[m, c, k] + [n.get(f"{P}.order.{m}.position.{c}.{k}.{x}") for x in ("mean", "ci_low", "ci_high")]
             for m in names for c in CONSTRAINTS for k in range(1, 6)]
    _write_csv(OUT / "tables" / "tableN3b_position_all.csv", ["model", "constraint", "position", "mean", "ci_low", "ci_high"],
               crows)
    audit.record("tables/tableN3b_position_all.csv", "normalized", set(n.read))
    n.read.clear()
    # N4 order versus formatting
    rows, crows = [], []
    for m in models:
        p = f"{P}.p3.{m}"
        rows.append([NAMES[m], f"{dec(n.get(p + '.mean_diff'))} [{dec(n.get(p + '.ci_low'))}, {dec(n.get(p + '.ci_high'))}]",
                     f"{n.get(p + '.n_pos')} / {n.get(p + '.n_neg')} / {n.get(p + '.n_zero')}",
                     dec(n.get(p + ".wilcoxon_stat"), 1), pval(n.get(p + ".p")), pval(n.get(p + ".q"))]
                    if n.get(p + ".status") == "estimated" else [NAMES[m], str(n.get(p + ".status")), "", "", "", ""])
        crows.append([m] + [n.get(f"{p}.{x}") for x in ("mean_diff", "ci_low", "ci_high", "n_pos", "n_neg", "n_zero",
                                                         "wilcoxon_stat", "p", "q", "status")])
    md["tableN4_order_vs_format"] = write_table(
        "tableN4_order_vs_format", "Table N4. Normalized scoring (post-hoc): PS_order − PS_format per model (100 tasks; "
        "paired task-clustered bootstrap CI; Wilcoxon signed-rank test, Pratt zero handling, normal approximation; "
        "q: Benjamini-Hochberg across the four models).", ["Model", "Mean difference [95% CI]",
                                                          "Tasks + / − / 0", "Wilcoxon statistic", "p", "q"], rows, crows,
        ["model", "mean_diff", "ci_low", "ci_high", "n_pos", "n_neg", "n_zero", "wilcoxon_stat", "p", "q", "status"])
    done("tableN4_order_vs_format")
    # N5 model pairs
    rows, crows = [], []
    for x, y in itertools.combinations(models, 2):
        cells = []
        for mt, kind in (("csr", "pct"), ("ps", "dec"), ("pcr", "pct")):
            k = f"{P}.s2.{x}_vs_{y}.{mt}_diff"
            cells.append(f"{est(n, k, kind)}, q {peq(n.get(k + '.q'))}")
            crows.append([x, y, mt] + [n.get(f"{k}.{z}") for z in ("mean", "ci_low", "ci_high", "p", "q")])
        rows.append([f"{NAMES[x]} − {NAMES[y]}"] + cells)
    md["tableN5_model_pairs"] = write_table(
        "tableN5_model_pairs", "Table N5. Normalized scoring (post-hoc): paired differences between models, order arm "
        "(difference a − b, mean [95% CI], bootstrap q).", ["Pair", "Mean CSR", "Mean PS_order", "Mean PCR"], rows,
        crows, ["model_a", "model_b", "metric", "mean", "ci_low", "ci_high", "p", "q"],
        "Each column is its own Benjamini-Hochberg family of six pairs. The PCR family is an additional post-hoc family.")
    done("tableN5_model_pairs")
    # N6 order level
    rows, crows = [], []
    for m in models:
        csr = {cid: n.get(f"{P}.order_level.order.{m}.{cid}.csr.mean") for cid in ORDER_IDS}
        lo, hi = min(csr, key=csr.get), max(csr, key=csr.get)
        rows.append([NAMES[m], f"{pct(csr[lo])} ({olabel(lo)})", f"{pct(csr[hi])} ({olabel(hi)})",
                     est(n, f"{P}.order_level.order.{m}.span.csr", "dec"), est(n, f"{P}.order_level.order.{m}.span.pcr", "dec"),
                     est(n, f"{P}.order_level.format.{m}.span.csr", "dec")])
        for arm, ids in ARM_IDS.items():
            for cid in ids:
                for mt in ("csr", "pcr", "format"):
                    crows.append([m, arm, cid, olabel(cid) if arm == "order" else cid, mt]
                                 + [n.get(f"{P}.order_level.{arm}.{m}.{cid}.{mt}.{z}") for z in ("mean", "ci_low", "ci_high")])
    rank_lines = []
    for arm in ARM_IDS:
        for mt in ("csr", "pcr"):
            k = f"{P}.order_level.{arm}.rank.overall.{mt}"
            rank_lines.append(f"- {mt.upper()}, {arm} arm: " + " > ".join(NAMES[x] for x in n.get(k + ".ranking"))
                              + f" (mean over the ten conditions) in {n.get(k + '.n_conditions_reproducing')} of 10 conditions.")
    for x, y in itertools.combinations(models, 2):
        k = f"{P}.order_level.order.rank.{x}_vs_{y}"
        rank_lines.append(f"- {NAMES[x]} vs {NAMES[y]}, order arm: CSR {n.get(k + '.csr.n_a_higher')} / "
                          f"{n.get(k + '.csr.n_b_higher')} / {n.get(k + '.csr.n_ties')}; PCR {n.get(k + '.pcr.n_a_higher')} / "
                          f"{n.get(k + '.pcr.n_b_higher')} / {n.get(k + '.pcr.n_ties')} (higher / lower / tied).")
    md["tableN6_order_level"] = write_table(
        "tableN6_order_level", "Table N6. Normalized scoring (post-hoc): mean CSR across the ten orders, with the span "
        "(max − min over the ten conditions; bootstrap 95% CI) of CSR and PCR, and the span of CSR across the ten "
        "formatting variants. Per-order values with CIs are in the CSV file.",
        ["Model", "Lowest CSR (order)", "Highest CSR (order)", "CSR span, order arm", "PCR span, order arm",
         "CSR span, format arm"], rows, crows, ["model", "arm", "condition_id", "label", "metric", "mean", "ci_low", "ci_high"],
        "Rankings:\n\n" + "\n".join(rank_lines) + "\n\n" + tie_note(n, models))
    done("tableN6_order_level")
    # N7 record-level changes
    rows, crows = [], []
    for m in models:
        for arm in ARM_IDS:
            cells = [f"{n.get(f'{P}.records.{m}.{fam}.{arm}.n_changed')} / {n.get(f'{P}.records.{m}.{fam}.{arm}.n_records')}"
                     for fam in FAMILIES]
            rows.append([NAMES[m], arm, *cells, str(n.get(f"{P}.records.{m}.{arm}.n_changed"))])
            for fam in FAMILIES:
                k = f"{P}.records.{m}.{fam}.{arm}"
                crows.append([m, arm, fam] + [n.get(f"{k}.{z}") for z in ("n_records", "format_strict_pass",
                                                                         "format_norm_pass", "n_changed")])
    md["tableN7_format_changes"] = write_table(
        "tableN7_format_changes", "Table N7. FORMAT decisions that differ between the pre-specified strict rule and the "
        "normalized rule, by model, arm and family (changed / evaluation records).",
        ["Model", "Arm"] + [FNAMES[f] for f in FAMILIES] + ["Total changed"], rows, crows,
        ["model", "arm", "family", "n_records", "format_strict_pass", "format_norm_pass", "n_changed"],
        f"Every change is from fail to pass. Records whose FORMAT changed from pass to fail: "
        f"{n.get(f'{P}.checks.format_direction.n_strict_pass_norm_fail')}.")
    done("tableN7_format_changes")
    # N8 constraint profile
    rows, crows = [], []
    for m in names:
        rows.append([label(m)] + [est(n, f"{P}.order.{m}.compliance.{c}") for c in CONSTRAINTS] + [est(n, f"{P}.order.{m}.pcr")])
        crows += [[m, c] + [n.get(f"{P}.order.{m}.compliance.{c}.{z}") for z in ("mean", "ci_low", "ci_high")] for c in CONSTRAINTS]
        crows.append([m, "pcr"] + [n.get(f"{P}.order.{m}.pcr.{z}") for z in ("mean", "ci_low", "ci_high")])
    md["tableN8_constraints"] = write_table(
        "tableN8_constraints", "Table N8. Normalized scoring (post-hoc): compliance with each constraint and PCR, order "
        "arm (mean [95% CI]). Only FORMAT differs from the strict scoring.", ["Model"] + [CNAMES[c] for c in CONSTRAINTS]
        + ["PCR"], rows, crows, ["model", "metric", "mean", "ci_low", "ci_high"])
    done("tableN8_constraints")
    # N9 exploratory and robustness
    lines, crows = [], []
    for m in models:
        c = f"{P}.robustness.cascade"
        lines.append(f"- {NAMES[m]}: cascade CSR {est(n, f'{c}.order.{m}.csr')}; cascade PS_order − PS_format "
                     + (f"{dec(n.get(f'{c}.p3.{m}.mean_diff'))} [{dec(n.get(f'{c}.p3.{m}.ci_low'))}, "
                        f"{dec(n.get(f'{c}.p3.{m}.ci_high'))}], p {peq(n.get(f'{c}.p3.{m}.p'))}"
                        if n.get(f"{c}.p3.{m}.status") == "estimated" else str(n.get(f"{c}.p3.{m}.status")))
                     + f"; subset passing normalized FORMAT: n = {n.get(f'{P}.robustness.norm_format_subset.order.{m}.n_outputs')}, "
                       f"CSR {est(n, f'{P}.robustness.norm_format_subset.order.{m}.csr')}.")
        crows.append([m, n.get(f"{c}.order.{m}.csr.mean"), n.get(f"{c}.p3.{m}.mean_diff"), n.get(f"{c}.p3.{m}.p"),
                      n.get(f"{P}.robustness.norm_format_subset.order.{m}.n_outputs"),
                      n.get(f"{P}.robustness.norm_format_subset.order.{m}.csr.mean")])
    e3 = []
    for m in models:
        e = f"{P}.exploratory.e3.{m}"
        diffs = ", ".join(f"{CNAMES[c]} {dec(n.get(f'{e}.difficulty.{c}'), 2)}" for c in CONSTRAINTS)
        parts = []
        for oc in ("csr", "pcr"):
            k = f"{e}.he_vs_{oc}"
            parts.append(f"ρ(HE, order-level {oc.upper()}) = {dec(n.get(k + '.rho'), 2)} [{dec(n.get(k + '.ci_low'), 2)}, "
                         f"{dec(n.get(k + '.ci_high'), 2)}]" if n.get(k + ".status") == "estimated" else
                         f"ρ(HE, order-level {oc.upper()}): {n.get(k + '.status')}")
        e3.append(f"- {NAMES[m]}: difficulties {diffs}; " + "; ".join(parts) + ".")
    fails = []
    for m in models:
        k = f"{P}.e5.order.{m}"
        fails.append(f"- {NAMES[m]}: normalized FORMAT failures {pct(n.get(k + '.format_failure_rate'))} of "
                     f"{n.get(k + '.n_records')} order-arm records (invalid JSON {n.get(k + '.format_failure.invalid_json')}, "
                     f"missing or extra key {n.get(k + '.format_failure.missing_or_extra_key')}, fenced with failing "
                     f"content {n.get(k + '.format_failure.fenced_content_fails')}, other {n.get(k + '.format_failure.other')}); "
                     f"raw-output code_fence tag {pct(n.get(k + '.code_fence_raw'))}.")
    inst = []
    for m in models:
        inst.append(f"- {NAMES[m]}: " + ", ".join(f"{CNAMES[c]} {pct(n.get(f'{P}.robustness.constraint_instability.order.{m}.{c}.mean'))}"
                                                  for c in CONSTRAINTS) + ".")
    text = ("Table N9. Normalized scoring (post-hoc): exploratory and robustness analyses.\n\n"
            "**Cascade scoring with normalized FORMAT and the subset passing normalized FORMAT** (order arm):\n\n"
            + "\n".join(lines) + "\n\n**Hard-to-easy index with normalized pilot difficulties** (ten fixed orders, not a "
            "test):\n\n" + "\n".join(e3) + "\n\n**Normalized FORMAT failures by type, with the raw-output code_fence tag** "
            "(order arm):\n\n" + "\n".join(fails) + "\n\n**Share of tasks whose flag varies across the ten orders**:\n\n"
            + "\n".join(inst) + "\n")
    atomic_write_text(OUT / "tables" / "tableN9_exploratory.md", text)
    _write_csv(OUT / "tables" / "tableN9_exploratory.csv", ["model", "cascade_csr", "cascade_p3_mean_diff", "cascade_p3_p",
                                                             "norm_subset_n", "norm_subset_csr"], crows)
    md["tableN9_exploratory"] = text
    done("tableN9_exploratory")
    return md


def tie_note(n: dict, models: list[str]) -> str:
    """Document ties and verify the corrected counts instead of accepting misclassified ties."""
    cases = []
    for arm, ids in ARM_IDS.items():
        for metric in ("csr", "pcr"):
            for x, y in itertools.combinations(models, 2):
                k = f"{P}.order_level.{arm}.rank.{x}_vs_{y}.{metric}"
                vals = [(cid, round(n.get(f"{P}.order_level.{arm}.{x}.{cid}.{metric}.mean"), 9),
                         round(n.get(f"{P}.order_level.{arm}.{y}.{cid}.{metric}.mean"), 9)) for cid in ids]
                exact = (sum(a > b for _, a, b in vals), sum(a < b for _, a, b in vals), sum(a == b for _, a, b in vals))
                stored = (n.get(k + ".n_a_higher"), n.get(k + ".n_b_higher"), n.get(k + ".n_ties"))
                assert exact == stored, (k, exact, stored)
                if exact[2]:
                    tied = [olabel(c) if arm == "order" else c for c, a, b in vals if a == b]
                    cases.append(
                        f"{NAMES[x]} and {NAMES[y]} have exactly equal mean {metric.upper()} in "
                        f"{', '.join(tied[:-1]) + ' and ' + tied[-1] if len(tied) > 1 else tied[0]} ({arm} "
                        f"arm). Counts are {' / '.join(map(str, stored))} (higher / lower / tied).")
    head = ("Ties: the counts compare the per-condition means. A ranking holds in a condition only if every adjacent "
            "pair is strictly ordered, and `n_ties` counts equal means. Means are canonicalized to 12 decimal places "
            "before comparisons to remove machine-precision artifacts (v3.1 numerical correction).")
    return head + (" " + " ".join(cases) if cases else " No ties occur.")


def comparison_table(c: Tracked, models: list[str], audit: Audit) -> str:
    rows, crows = [], []
    for m in models + ["pooled"]:
        cells = []
        for strict_key, norm_key in (("compliance.format", "compliance.format"), ("csr", "csr"), ("pcr", "pcr")):
            cells += [est(c, f"main.order.{m}.{strict_key}"), est(c, f"{P}.order.{m}.{norm_key}")]
            crows.append([m, strict_key] + [c.get(f"main.order.{m}.{strict_key}.{z}") for z in ("mean", "ci_low", "ci_high")]
                         + [c.get(f"{P}.order.{m}.{norm_key}.{z}") for z in ("mean", "ci_low", "ci_high")])
        rows.append([NAMES.get(m, "Pooled")] + cells)
    md = write_table(
        "tableN10_strict_vs_norm", "Table N10. Comparison (labelled): pre-specified strict scoring and normalized scoring "
        "(post-hoc), order arm (mean [95% CI]). This is the data of the strict-versus-normalized figure.",
        ["Model", "FORMAT, strict", "FORMAT, normalized", "CSR, strict", "CSR, normalized", "PCR, strict",
         "PCR, normalized"], rows, crows,
        ["model", "metric", "strict_mean", "strict_ci_low", "strict_ci_high", "norm_mean", "norm_ci_low", "norm_ci_high"])
    audit.record("tables/tableN10_strict_vs_norm.md", "comparison", set(c.read))
    c.read.clear()
    return md


def figures(norm: dict, strict: dict, models: list[str], audit: Audit) -> list[Path]:
    from analysis import figures as F

    F.setup()
    out = OUT / "figures"
    paths = []
    view, source = norm_view(norm)

    def draw(name: str, fn, *args, **kwargs) -> None:
        paths.extend(fn(view, models, out, *args, name=name, **kwargs))
        audit.record(f"figures/{name}.png", "normalized", set(view.read), source)
        view.read.clear()

    draw("fig_order_level_norm", F.figR1_order_level, note="Gemma 4 E4B: 100% in every order")
    draw("fig_noise_floor_norm", F.fig4_noise_floor)
    draw("fig_position_norm", F.fig3_position, note="Gemma 4 E4B: 100% at every position")
    draw("fig_constraints_norm", F.fig2_compliance, note=None)
    comp = Tracked({**strict, **{k: v for k, v in norm.items() if k.startswith(P + ".")}})
    paths += F.fig7_fence_tolerant(comp, models, out, name="fig_overall_strict_vs_norm",
                                   open_key={"format": P + ".order.{m}.compliance.format", "csr": P + ".order.{m}.csr",
                                             "pcr": P + ".order.{m}.pcr"},
                                   fill_labels=("Filled: pre-specified strict scoring", "Open: normalized scoring (post-hoc)"))
    audit.record("figures/fig_overall_strict_vs_norm.png", "comparison", set(comp.read))
    return paths


def key_index() -> list[str]:
    return [
        f"`{P}.<arm>.<model>.{{csr,pcr,ps,vsr,flip_rate}}.<stat>` and `{P}.<arm>.<model>.compliance.<c>.<stat>`: S1 "
        "metrics and constraint rates (both arms; `<model>` includes `pooled`)",
        f"`{P}.order.<model>.position.<c>.<k>.<stat>`; `{P}.order.gee_sample.position.format.<k>.<stat>`: position rates",
        f"`{P}.p1.<c>.{{status,wald_chi2,df,p,q,n,excluded_models,reason,or.<k>.*}}`, `{P}.p1.format.sample_models`: "
        "exchangeable GEE",
        f"`{P}.robustness.p1_independence.<c>.*`: independence GEE (sensitivity)",
        f"`{P}.tests.friedman.<model>.{{chi2,df,p,q_bh,kendall_w,status}}`, `{P}.tests.cochran_q.<model>.{{q,df,p,q_bh,"
        "status}`: order tests",
        f"`{P}.kendall_w.<model>.{{n_constant_tasks,n_nonconstant_tasks,kendall_w_nonconstant}}`: constant-CSR tasks and "
        "W among the variable tasks",
        f"`{P}.p3.<model>.{{mean_diff,ci_low,ci_high,wilcoxon_stat,p,q,n,n_pos,n_neg,n_zero,status}}`: PS_order − PS_format",
        f"`{P}.s2.<a>_vs_<b>.{{csr,ps,pcr}}_diff.{{mean,ci_low,ci_high,p,q}}`: model pairs",
        f"`{P}.order_level.<arm>.<model>.<condition>.{{csr,pcr,format}}.<stat>`, `.span.{{csr,pcr}}.<stat>`, "
        f"`{P}.order_level.<arm>.rank.*`: order-level profiles",
        f"`{P}.order_level.<arm>.rank.<a>_vs_<b>.<metric>.{{n_a_higher,n_b_higher,n_ties}}` and "
        f"`{P}.order_level.<arm>.rank.overall.<metric>.n_conditions_reproducing`: counts over the ten conditions; the "
        "per-condition means are canonicalized to 12 decimal places before comparison; exact ties count as ties "
        "(normalized format arm, CSR, Phi-4-mini and Gemma 4 E4B tie in V07 and V09)",
        f"`{P}.robustness.constraint_instability.<arm>.<model>.<c>.<stat>`: constraint-level instability",
        f"`{P}.robustness.cascade.*`, `{P}.robustness.norm_format_subset.*`: cascade and subset analyses",
        f"`{P}.exploratory.e3.<model>.*`: hard-to-easy index with normalized pilot difficulties",
        f"`{P}.e5.<arm>.<model>.{{format_failure_rate,format_failure.<type>,code_fence_raw,n_records}}`: failure types",
        f"`{P}.records.<model>.<family>.<arm>.{{n_records,format_strict_pass,format_norm_pass,n_changed}}`: record level",
        f"`{P}.inventory.*`, `{P}.checks.*`: inventory and checks",
    ]


def summary_md(n: dict, models: list[str], md: dict, audit_ok: bool) -> str:
    correction = n['_meta'].get('recomputation_mode') == 'stored-evaluation-records'
    records_check = ("Strict FORMAT rechecked from raw outputs against the stored evaluation records" if correction
                     else "Fresh evaluation of the raw outputs against the stored evaluation records")
    content_check = ("Other four flags and task quality retained from the stored records; parsed objects before and "
                     "after normalization checked for equality" if correction else
                     "Other four flags and task quality after normalization (each output evaluated as generated and "
                     "after the fence is removed)")
    L = ["# SUMMARY_NORM — normalized FORMAT scoring (post-hoc re-analysis)", "",
         f"Run `{n['_meta']['run_id']}`; bootstrap {n['_meta']['n_boot']} task-clustered replicates stratified by family, "
         f"seed {n['_meta']['seed']}; generated {n['_meta']['generated_utc']}. Every value is a key of "
         "`results/posthoc_norm/summary_norm.json`. These results are a post-hoc re-analysis. The pre-specified strict "
         "results are in `results/metrics/summary.json`; both policies include the documented v3.1 numerical "
         "correction, with pre-correction summaries archived separately.", "", "## Rule", "", FENCE_RULE, "",
         "Rejected (strict value kept): " + "; ".join(REJECTED_CASES) + ".", "", "## Inventory", ""]
    for m in models:
        forms = {k.split(".fence_form.")[1]: v for k, v in n.items() if k.startswith(f"{P}.inventory.{m}.fence_form.")}
        L.append(f"- {NAMES[m]}: {n[f'{P}.inventory.{m}.unique_generations']} unique generations, "
                 f"{n[f'{P}.inventory.{m}.evaluation_records']} evaluation records "
                 f"({n[f'{P}.inventory.{m}.shared_generations']} generations shared by O01 and V01); "
                 + "; ".join(f"{k}: {v}" for k, v in forms.items()) + ".")
    ck = lambda k: n.get(f"{P}.checks.{k}")  # noqa: E731
    L += ["", "## Checks", "",
          f"- {records_check}: {ck('strict_records.n')} records, "
          f"{ck('strict_records.n_mismatch')} differences.",
          f"- Strict results recomputed against `summary.json`: {ck('strict_keys.n')} keys, "
          f"{ck('strict_keys.n_mismatch')} differences ({ck('strict_keys.scope')}).",
          f"- {content_check}: {ck('content_unchanged.n')} records, {ck('content_unchanged.n_mismatch')} differences in "
          f"the flags and quality scores, {ck('content_unchanged.n_quality_detail_mismatch')} in the quality details.",
          f"- FORMAT changed from pass to fail: {ck('format_direction.n_strict_pass_norm_fail')} records.",
          f"- Constraint rates, position rates and GEE status of LENGTH, CARDINALITY, NO_COMMA and VERBATIM equal the "
          f"strict values: {ck('other_constraints_unchanged.n')} keys, {ck('other_constraints_unchanged.n_mismatch')} "
          "differences.",
          f"- Task quality (Q and TQS) equals the strict values: {ck('quality_unchanged.n')} keys, "
          f"{ck('quality_unchanged.n_mismatch')} differences.",
          f"- FORMAT, CSR and PCR equal the earlier fence-tolerant values: {ck('earlier_fence_tolerant_values.n')} keys, "
          f"{ck('earlier_fence_tolerant_values.n_mismatch')} differences.",
          f"- Gemma 4 E4B: FORMAT changed in {ck('gemma4e4b.format_changed')} of {ck('gemma4e4b.n_records')} records; "
          f"PS, VSR and flip rate equal the strict values up to floating-point rounding (|difference| < 1e-12; "
          f"{ck('gemma4e4b_range_unchanged.n_mismatch')} differences of {ck('gemma4e4b_range_unchanged.n')}); largest "
          f"deviation of the CSR shift from 0.2: {ck('gemma4e4b.csr_shift_max_deviation'):.1e}.",
          f"- Policy audit (`policy_audit.json`): {'passed' if audit_ok else 'FAILED'}.",
          f"- All checks passed: {ck('all_passed')}.", ""]
    for name in ("tableN7_format_changes", "tableN1_overall", "tableN1b_stability", "tableN1c_format_arm",
                 "tableN2_order_tests", "tableN3_position_format", "tableN4_order_vs_format", "tableN5_model_pairs",
                 "tableN6_order_level", "tableN8_constraints", "tableN9_exploratory"):
        L += ["## " + md[name].split("\n", 1)[0].split(".", 1)[0], "", md[name], ""]
    L += ["## Figures", "", "In `results/posthoc_norm/figures/` (300 dpi PNG and PDF, 16 cm wide):", ""]
    L += [f"- `{stem}`: {fig} of the v2.9 numbering; {what}" for stem, (fig, what) in FIGURES.items()]
    L += ["", "## Key index", ""] + [f"- {line}" for line in key_index()] + [""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-boot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20261003)
    args = ap.parse_args(argv)
    models = main_models()
    run_id = imported_run("main", analysis_eligible=True)
    strict_path = RESULTS_DIR / "metrics" / "summary.json"
    strict = json.loads(strict_path.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    s: dict = {}
    raw, norm_recs, gens = reevaluate(run_id, models)
    inventory_and_reproduction(run_id, models, raw, gens, strict, args.n_boot, args.seed, s)
    df = normalized_frame(raw, norm_recs, models, s)
    write_records(df)
    a = normalized_analysis(df, models, args.n_boot, args.seed, s)
    consistency_checks(df, a, strict, models, s)
    nan = [k for k, v in s.items() if isinstance(v, float) and v != v]
    assert not nan, f"NaN values would make the file invalid JSON: {nan[:5]}"
    meta = {"status": STATUS, "rule": FENCE_RULE, "run_id": run_id, "n_boot": args.n_boot, "seed": args.seed,
            "generated_utc": utc_now(), "models": models,
            "strict_summary_sha256": sha256_file(strict_path),
            "eval_files_sha256": {m: sha256_file(RESULTS_DIR / "eval" / "main" / run_id / f"{m}.jsonl") for m in models},
            "code_sha256": sha256_file(Path(__file__))}
    norm = {"_meta": meta, **dict(sorted(s.items()))}
    write_json(OUT / "summary_norm.json", norm)
    audit = Audit()
    md = tables(Tracked(norm), models, audit)
    comparison_table(Tracked({**strict, **norm}), models, audit)
    figures(norm, strict, models, audit)
    audit_ok = audit.write()
    atomic_write_text(OUT / "SUMMARY_NORM.md", summary_md(norm, models, md, audit_ok))
    print(f"summary_norm.json: {len(s)} keys; checks passed: {s[f'{P}.checks.all_passed']}; policy audit: {audit_ok}")
    return 0 if (s[f"{P}.checks.all_passed"] and audit_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())

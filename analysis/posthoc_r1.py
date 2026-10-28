"""Analyses requested in review round 1 (design decision R1 §3). Main run only; the frozen plan is unchanged.

Labels: order-level results (§3.2), the fence-tolerant FORMAT (§3.3) and the parsed-only TQS (§3.5) are
**post-hoc (decision R1)**; the Kendall's W companion (§3.6), evidence lengths (§3.7) and FORMAT failure types
(§3.8) are descriptive and post-hoc; the secondary outcomes (§3.4) are pre-specified outcomes of ANALYSIS_PLAN §3
that had not been reported yet. Keys: `main.posthoc_r1.*` and `main.secondary.*`. Display labels follow decision
R1 (orders O01-O10 = P01-P10; NO_COMMA; families QA, CLS, SUM, EXT, TRF); keys keep the data ids (P01-P10, V01-V10,
F1_QA ...).
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import scipy.stats as st

from analysis.bootstrap import bootstrap_p
from analysis.compute import Analysis, _put
from analysis.data import ARM_IDS, CONSTRAINTS, FAMILIES, ORDER_IDS
from analysis.stats import NOT_APPLICABLE, p2_tests
from src.common import RUNS_DIR, read_jsonl
from src.evaluators.format import _FENCE_RE, format_strict, lenient_parse

P = "main.posthoc_r1"
LABEL = "post-hoc (decision R1)"
FENCE_TYPES = ("invalid_json", "missing_or_extra_key", "fenced", "other")


# ---- raw outputs -----------------------------------------------------------------------------------
def format_fence_tolerant(output: str) -> int:
    """R1 §3.3: strict FORMAT after removing exactly one enclosing ``` or ```json fence and surrounding whitespace;
    otherwise the strict FORMAT value."""
    s = output.strip()
    m = _FENCE_RE.match(s)
    if m and "```" not in m.group(1):
        return int(format_strict(m.group(1)))
    return int(format_strict(s))


def raw_columns(run_id: str, models: list[str], runs_root=RUNS_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per (model, prompt id): the fence-tolerant FORMAT flag. Per unique generation: evidence-item lengths."""
    rows, items = [], []
    for m in models:
        for g in read_jsonl(runs_root / "main" / run_id / m / "generations.jsonl"):
            ft = format_fence_tolerant(g["output_text"])
            for pid in g["prompt_ids"]:
                rows.append({"model_key": m, "prompt_id": pid, "format_ft": ft})
            obj = lenient_parse(g["output_text"]).obj
            ev = obj.get("evidence") if isinstance(obj, dict) else None
            if isinstance(ev, list):
                items += [{"model_key": m, "n_tokens": len(x.split())} for x in ev if isinstance(x, str)]
    return pd.DataFrame(rows), pd.DataFrame(items)


# ---- §3.2 order level ------------------------------------------------------------------------------
def _per_condition(a: Analysis, arm: str, m: str, col: str) -> np.ndarray:
    sub = a.arm(arm, m)
    mat = sub.pivot(index="task_id", columns="condition_id", values=col).reindex(a.tasks)[list(ARM_IDS[arm])]
    return mat.to_numpy(dtype=float)


def order_level(a: Analysis, prefix: str = f"{P}.order_level") -> None:
    for arm, ids in ARM_IDS.items():
        means = {}
        for m in a.models:
            for metric, col in (("csr", "_csr"), ("pcr", "_pcr"), ("format", a.flags["format"])):
                mat = _per_condition(a, arm, m, col)
                for j, cid in enumerate(ids):
                    _put(a.s, f"{prefix}.{arm}.{m}.{cid}.{metric}", a.bs.estimate(mat[:, j]))
                if metric in ("csr", "pcr"):
                    point = mat.mean(axis=0)
                    means[(m, metric)] = point
                    reps = (a.bs.counts @ mat) / a.bs.counts.sum(axis=1, keepdims=True)
                    span_reps = reps.max(axis=1) - reps.min(axis=1)
                    lo, hi = a.bs.percentile_ci(span_reps)
                    _put(a.s, f"{prefix}.{arm}.{m}.span.{metric}",
                         {"mean": float(point.max() - point.min()), "ci_low": lo, "ci_high": hi})
        for metric in ("csr", "pcr"):
            # the arm-level ranking (mean over the ten conditions) and the number of conditions that reproduce it
            # strictly (a tie between any two models does not reproduce it)
            overall = sorted(a.models, key=lambda m: -means[(m, metric)].mean())
            k = f"{prefix}.{arm}.rank.overall.{metric}"
            a.s[f"{k}.ranking"] = overall
            a.s[f"{k}.n_conditions_reproducing"] = int(sum(
                all(means[(overall[i], metric)][j] > means[(overall[i + 1], metric)][j] for i in range(len(overall) - 1))
                for j in range(len(ids))))
        for x, y in itertools.combinations(a.models, 2):
            for metric in ("csr", "pcr"):
                dx, dy = means[(x, metric)], means[(y, metric)]
                k = f"{prefix}.{arm}.rank.{x}_vs_{y}.{metric}"
                a.s.update({f"{k}.n_a_higher": int((dx > dy).sum()), f"{k}.n_b_higher": int((dx < dy).sum()),
                            f"{k}.n_ties": int((dx == dy).sum())})
    if prefix == f"{P}.order_level":
        a.s[f"{P}.order_level.label"] = LABEL


# ---- §3.3 fence-tolerant FORMAT -----------------------------------------------------------------------
def paired_difference(a: Analysis, x: pd.Series, y: pd.Series) -> dict:
    """Paired task-clustered bootstrap of mean(x − y) over tasks, as in S2: point estimate, percentile 95% CI and
    the two-sided bootstrap p (decision D05 §3). x and y are per-task values indexed by task_id."""
    d = (x.reindex(a.tasks) - y.reindex(a.tasks)).to_numpy(dtype=float)
    point, reps = a.bs.ratio(d)
    lo, hi = a.bs.percentile_ci(reps)
    return {"mean": point, "ci_low": lo, "ci_high": hi, "p": bootstrap_p(reps)}


def fence_tolerant(a: Analysis, ft: pd.DataFrame) -> None:
    df = a.df.merge(ft, on=["model_key", "prompt_id"], how="left", validate="one_to_one")
    assert df.format_ft.notna().all()
    # the fence rule can only add passes, and only for fenced outputs
    assert (df.format_ft >= df["format"]).all() and (df.format_ft == df["format"])[df.parse_rule != "fence"].all()
    others = [c for c in CONSTRAINTS if c != "format"]
    df["csr_ft"] = (df.format_ft + df[others].sum(axis=1)) / 5
    df["pcr_ft"] = df[others].min(axis=1).clip(upper=df.format_ft)
    for arm in ARM_IDS:
        ranking = {}
        for name, ms in a.model_sets():
            sub = df[(df.arm == arm) & df.model_key.isin(ms)]
            for metric in ("format_ft", "csr_ft", "pcr_ft"):
                g = sub.groupby("task_id")[metric]
                est = a.bs.estimate(a.bs.align(g.sum()), a.bs.align(g.count()))
                _put(a.s, f"{P}.fence_tolerant.{arm}.{name}.{metric.replace('_ft', '')}", est)
                if name != "pooled":
                    ranking.setdefault(metric, {})[name] = est["mean"]
        for metric in ("csr_ft", "pcr_ft"):
            a.s[f"{P}.fence_tolerant.{arm}.ranking.{metric.replace('_ft', '')}"] = sorted(
                ranking[metric], key=ranking[metric].get, reverse=True)
    # decision R2 §3.1 (M9 d): Gemma 4 E4B minus Phi-4-mini under the fence-tolerant reading, order arm
    if {"gemma4e4b", "phi4mini"} <= set(a.models):
        order = df[df.arm == "order"]
        for metric in ("csr_ft", "pcr_ft"):
            per_task = {m: order[order.model_key == m].groupby("task_id")[metric].mean() for m in ("gemma4e4b", "phi4mini")}
            _put(a.s, f"{P}.fence_tolerant.paired.gemma4e4b_vs_phi4mini.{metric.replace('_ft', '')}",
                 paired_difference(a, per_task["gemma4e4b"], per_task["phi4mini"]))
        a.s[f"{P}.fence_tolerant.paired.label"] = (
            "post-hoc (decision R2): paired task-clustered bootstrap difference Gemma 4 E4B − Phi-4-mini of the "
            "per-task mean CSR_ft and PCR_ft over the ten orders, order arm; same bootstrap as S2 (percentile CI, "
            "two-sided bootstrap p)")
    g = df[(df.arm == "order") & (df.model_key == "gemma4e4b")]
    if not g.empty:
        pcr = g.pivot(index="task_id", columns="condition_id", values="pcr_ft").reindex(a.tasks)[list(ORDER_IDS)]
        csr = g.pivot(index="task_id", columns="condition_id", values="csr_ft").reindex(a.tasks)[list(ORDER_IDS)]
        r = p2_tests(csr.to_numpy(dtype=float), pcr.to_numpy(dtype=float))["cochran_q"]
        k = f"{P}.fence_tolerant.cochran_q.gemma4e4b"
        a.s[f"{k}.status"] = r["status"]
        if r["status"] == "estimated":
            a.s.update({f"{k}.q": r["q"], f"{k}.df": r["df"], f"{k}.p": r["p"]})
    a.s[f"{P}.fence_tolerant.definition"] = (
        "FORMAT_ft = strict FORMAT after removing exactly one enclosing ``` or ```json fence and surrounding "
        "whitespace (valid JSON, no duplicate keys, key set exactly {answer, evidence}); otherwise strict FORMAT. "
        "The other four constraints are unchanged.")
    a.s[f"{P}.fence_tolerant.label"] = LABEL


# ---- §3.4 secondary outcomes (pre-specified, not reported before) ---------------------------------------
def secondary(a: Analysis) -> None:
    for arm in ARM_IDS:
        rows = a.arm(arm)
        for m in a.models:
            sub = rows[rows.model_key == m]
            p = f"main.secondary.{arm}"
            qa = sub[sub.family == "F1_QA"].assign(v=lambda x: x.q_secondary.fillna(0.0).astype(float))
            _put(a.s, f"{p}.F1_QA.{m}.max_token_f1", a.bs.estimate(*a._sum_count(qa, "v")))
            cls = sub[(sub.family == "F2_CLASSIFICATION") & sub.label_status.notna()]
            cls = cls.assign(unres=(cls.label_status == "unresolved").astype(float),
                             nolabel=(cls.label_status == "none").astype(float))
            _put(a.s, f"{p}.F2_CLASSIFICATION.{m}.unresolved_rate", a.bs.estimate(*a._sum_count(cls, "unres")))
            _put(a.s, f"{p}.F2_CLASSIFICATION.{m}.no_label_rate", a.bs.estimate(*a._sum_count(cls, "nolabel")))
            a.s[f"{p}.F2_CLASSIFICATION.{m}.n_with_answer"] = int(len(cls))
            a.s[f"{p}.F2_CLASSIFICATION.{m}.n_unresolved"] = int(cls.unres.sum())
            for fam in ("F4_EXTRACTION", "F5_TRANSFORMATION"):
                ex = sub[sub.family == fam].assign(v=lambda x: x.q_secondary.fillna(0.0).astype(float))
                _put(a.s, f"{p}.{fam}.{m}.exact_all_fields", a.bs.estimate(*a._sum_count(ex, "v")))
    a.s["main.secondary.label"] = ("pre-specified secondary outcomes (ANALYSIS_PLAN §3; src/evaluators/README.md), per "
                                   "arm, first reported after review round 1; Q-type outcomes count 0 when no answer is "
                                   "parsed; unresolved and no-label rates among CLS outputs with a parsed answer; the "
                                   "no-label rate is post-hoc (decision R2, Q10)")
    a.s["main.secondary.no_label_rate.label"] = (
        "post-hoc (decision R2, Q10): the frozen ANALYSIS_PLAN.md and src/evaluators/README.md name only the "
        "unresolved-label rate as reported ('the unresolved rate is reported', README, F2); the no-label rate "
        "(label_status = none) is not named as a reported outcome")


# ---- §3.5 parsed-only TQS ----------------------------------------------------------------------------
def tqs_parsed(a: Analysis) -> None:
    order = a.arm("order")
    for fam in FAMILIES:
        for m in a.models:
            sub = order[(order.model_key == m) & (order.family == fam)]
            parsed = sub[sub.q_answer_available == 1]
            g = parsed.groupby("task_id").q_primary
            n_parsed = g.count()[g.count() >= 2]
            rng = (g.max() - g.min())[g.count() >= 2]
            num = a.bs.align(rng)
            den = (~np.isnan(num)).astype(float)
            k = f"{P}.tqs_parsed.{fam}.{m}"
            a.s[f"{k}.n_task_model_pairs"] = int(den.sum())
            if den.sum() == 0:
                a.s[f"{k}.status"] = "not computable: no task has at least 2 orders with a parsed answer"
                a.s[f"{k}.differs_from_prespecified"] = False
                continue
            est = a.bs.estimate(np.nan_to_num(num), den)
            a.s[f"{k}.status"] = "estimated"
            # decision R2 §3.2 (m19): parsed orders per qualifying task (a range over fewer orders is a lower bound)
            a.s[f"{k}.n_orders_median"] = float(n_parsed.median())
            a.s[f"{k}.n_orders_min"] = int(n_parsed.min())
            _put(a.s, k, est)
            pre = a.s.get(f"main.quality.{fam}.{m}.tqs.mean")
            a.s[f"{k}.differs_from_prespecified"] = bool(pre is not None and abs(pre - est["mean"]) > 0.05)
    a.s[f"{P}.tqs_parsed.definition"] = ("per task and model, the range of Q over the orders whose answer could be "
                                         "parsed (q_answer_available = 1), at least 2 such orders; flagged where it "
                                         "differs from the pre-specified TQS by more than 0.05")
    a.s[f"{P}.tqs_parsed.label"] = LABEL


# ---- §3.6 Kendall's W companion ------------------------------------------------------------------------
def kendall_companion(a: Analysis, prefix: str = f"{P}.kendall_w") -> None:
    for m in a.models:
        mat = _per_condition(a, "order", m, "_csr")
        constant = np.all(mat == mat[:, :1], axis=1)
        k = f"{prefix}.{m}"
        a.s.update({f"{k}.n_constant_tasks": int(constant.sum()), f"{k}.n_nonconstant_tasks": int((~constant).sum())})
        sub = mat[~constant]
        if len(sub) >= 2:
            chi2, _ = st.friedmanchisquare(*[sub[:, j] for j in range(sub.shape[1])])  # tie-corrected
            a.s[f"{k}.kendall_w_nonconstant"] = float(chi2 / (len(sub) * (sub.shape[1] - 1)))
    if prefix == f"{P}.kendall_w":
        a.s[f"{P}.kendall_w.label"] = "descriptive companion to P2 (decision R1 §3.6); tie-corrected Friedman statistic"


# ---- §3.7 evidence length -------------------------------------------------------------------------------
def evidence_length(a: Analysis, items: pd.DataFrame) -> None:
    for m in a.models:
        t = items[items.model_key == m].n_tokens
        k = f"{P}.evidence_length.{m}"
        a.s.update({f"{k}.n_items": int(len(t)), f"{k}.median_tokens": float(t.median()),
                    f"{k}.share_1_token": float((t == 1).mean()), f"{k}.share_2_tokens": float((t == 2).mean())})
    a.s[f"{P}.evidence_length.label"] = ("descriptive (decision R1 §3.7): string items of list evidence in the 1,900 "
                                         "unique generations per model; tokens are \\S+ runs")


# ---- §3.8 FORMAT failure types --------------------------------------------------------------------------
def failure_type(parse_rule: str, tags: tuple) -> str:
    if parse_rule == "fence":
        return "fenced"
    if parse_rule == "none":
        return "invalid_json"
    if {"missing_answer", "missing_evidence", "extra_keys"} & set(tags):
        return "missing_or_extra_key"
    return "other"


def format_failures(a: Analysis, models=("smollm2", "qwen25")) -> None:
    order = a.arm("order")
    for m in models:
        sub = order[(order.model_key == m) & (order["format"] == 0)]
        sub = sub.assign(ftype=[failure_type(r, t) for r, t in zip(sub.parse_rule, sub.error_tags)])
        for k in range(1, 6):
            at = order[(order.model_key == m) & (order.pos_format == k)]
            fk = sub[sub.pos_format == k]
            a.s[f"{P}.format_failures.{m}.{k}.n_outputs"] = int(len(at))
            for t in FENCE_TYPES:
                a.s[f"{P}.format_failures.{m}.{k}.{t}"] = int((fk.ftype == t).sum())
        if m == "qwen25":
            for fam in FAMILIES:
                ff = sub[sub.family == fam]
                a.s[f"{P}.format_failures.{m}.by_family.{fam}.n_outputs"] = int(((order.model_key == m) & (order.family == fam)).sum())
                for t in FENCE_TYPES:
                    a.s[f"{P}.format_failures.{m}.by_family.{fam}.{t}"] = int((ff.ftype == t).sum())
    a.s[f"{P}.format_failures.label"] = ("descriptive, post-hoc (decision R1 §3.8): strict FORMAT failures in the order "
                                         "arm by type (fenced; invalid_json = no JSON object; missing_or_extra_key; "
                                         "other = surrounding text or duplicate keys) and FORMAT position")


def cascade_check(a: Analysis) -> None:
    """R1 §3.1 (Q1, m16): in the format arm, how cascade scoring changes outputs and per-task PS."""
    fmt = a.arm("format")
    for m in a.models:
        sub = fmt[fmt.model_key == m]
        csr_c = sub[[f"cascade_{c}" for c in CONSTRAINTS]].mean(axis=1)
        g_p = sub.assign(v=sub._csr).groupby("task_id").v
        g_c = sub.assign(v=csr_c).groupby("task_id").v
        ps_p, ps_c = g_p.max() - g_p.min(), g_c.max() - g_c.min()
        d = (ps_c - ps_p).round(9)
        k = f"{P}.cascade_check.format.{m}"
        a.s.update({f"{k}.n_outputs_changed": int((abs(csr_c - sub._csr) > 1e-12).sum()),
                    f"{k}.n_tasks_ps_up": int((d > 0).sum()), f"{k}.n_tasks_ps_down": int((d < 0).sum()),
                    f"{k}.ps_primary": float(ps_p.mean()), f"{k}.ps_cascade": float(ps_c.mean()),
                    f"{k}.families_changed": sorted(sub[abs(csr_c - sub._csr) > 1e-12].family.unique().tolist())})
    a.s[f"{P}.cascade_check.label"] = "check of the E6a P3 contrast (decision R1 §3.1): no analysis error found"


def run_all(a: Analysis, run_id: str) -> None:
    cascade_check(a)
    ft, items = raw_columns(run_id, a.models)
    order_level(a)
    fence_tolerant(a, ft)
    secondary(a)
    tqs_parsed(a)
    kendall_companion(a)
    evidence_length(a, items)
    format_failures(a)

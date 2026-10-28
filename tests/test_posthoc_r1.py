"""Post-hoc analyses of review round 1 (design decision R1 §3) on synthetic data whose answers are known,
and a regression test for the cascade P3 contrast (R1 §3.1, Q1)."""

from __future__ import annotations

import json

import numpy as np
import pytest

from analysis.compute import Analysis, robustness
from analysis.edit_distance import levenshtein
from analysis.posthoc_r1 import (cascade_check, failure_type, format_fence_tolerant, kendall_companion, order_level,
                                 paired_difference, tqs_parsed)
from src.orders import ORDERS
from tests.test_analysis import synthetic

OK = '{"answer": "x", "evidence": ["y"]}'
P = "main.posthoc_r1"


def test_format_fence_tolerant():
    assert format_fence_tolerant(OK) == 1
    assert format_fence_tolerant(f"```json\n{OK}\n```") == 1
    assert format_fence_tolerant(f"  ```\n{OK}\n```  \n") == 1
    assert format_fence_tolerant(f"```JSON\n{OK}```") == 1
    assert format_fence_tolerant(f"```json\n```json\n{OK}\n```\n```") == 0  # more than one fence
    assert format_fence_tolerant(f"Here it is:\n```json\n{OK}\n```") == 0  # surrounding text
    assert format_fence_tolerant('```json\n{"answer": "x", "evidence": ["y"], "note": 1}\n```') == 0  # key set
    assert format_fence_tolerant('```json\n{"answer": "x", "answer": "z", "evidence": ["y"]}\n```') == 0  # duplicate
    assert format_fence_tolerant("```json\n[1, 2]\n```") == 0
    assert format_fence_tolerant('{"answer": "x"}') == 0  # unfenced: strict FORMAT


def test_failure_type():
    assert failure_type("fence", ()) == "fenced"
    assert failure_type("fence", ("missing_evidence",)) == "fenced"
    assert failure_type("none", ()) == "invalid_json"
    assert failure_type("strict", ("missing_evidence",)) == "missing_or_extra_key"
    assert failure_type("strict", ("extra_keys",)) == "missing_or_extra_key"
    assert failure_type("first_object", ()) == "other"  # surrounding text
    assert failure_type("strict", ("duplicate_keys",)) == "other"


def _format_last_fails(model="m1", family_prefix=""):
    return lambda c, pos, m, task, rng: not (c == "format" and pos["format"] == 5 and m == model
                                             and task.startswith(family_prefix))


def test_order_level_span_and_rank_counts():
    a = Analysis(synthetic(_format_last_fails()), ["m1", "m2"], n_boot=200)
    order_level(a)
    last = [oid for oid, seq in ORDERS.items() if seq[-1] == "A"]  # FORMAT (letter A) last
    assert len(last) == 2
    for oid in ORDERS:
        assert a.s[f"{P}.order_level.order.m1.{oid}.csr.mean"] == pytest.approx(0.8 if oid in last else 1.0)
        assert a.s[f"{P}.order_level.order.m1.{oid}.format.mean"] == (0.0 if oid in last else 1.0)
    assert a.s[f"{P}.order_level.order.m1.span.csr.mean"] == pytest.approx(0.2)
    assert a.s[f"{P}.order_level.order.m1.span.pcr.mean"] == pytest.approx(1.0)
    assert a.s[f"{P}.order_level.order.m2.span.csr.mean"] == 0.0
    assert a.s[f"{P}.order_level.format.m1.span.csr.mean"] == 0.0
    assert a.s[f"{P}.order_level.order.rank.overall.csr.ranking"] == ["m2", "m1"]
    assert a.s[f"{P}.order_level.order.rank.overall.csr.n_conditions_reproducing"] == 2  # ties in the other 8
    r = f"{P}.order_level.order.rank.m1_vs_m2.csr"
    assert (a.s[f"{r}.n_a_higher"], a.s[f"{r}.n_b_higher"], a.s[f"{r}.n_ties"]) == (0, 2, 8)
    ci = (a.s[f"{P}.order_level.order.m1.span.csr.ci_low"], a.s[f"{P}.order_level.order.m1.span.csr.ci_high"])
    assert ci == pytest.approx((0.2, 0.2))  # every task has the same profile


def test_tqs_parsed_drops_unparsed_orders():
    df = synthetic(lambda c, pos, m, task, rng: True)
    sel = (df.model_key == "m1") & (df.arm == "order")
    t0 = sel & (df.task_id == "F1__0") & df.condition_id.isin(["P01", "P02", "P03"])
    df.loc[t0, ["q_answer_available", "q_primary"]] = [0, 0.0]  # unparsed orders score 0
    t1 = sel & (df.task_id == "F1__1") & (df.condition_id != "P01")
    df.loc[t1, ["q_answer_available", "q_primary"]] = [0, 0.0]  # only one parsed order: does not qualify
    a = Analysis(df, ["m1", "m2"], n_boot=100)
    a.s["main.quality.F1_QA.m1.tqs.mean"] = 0.5  # pre-specified TQS (ranges 1, 1, 0, 0)
    a.s["main.quality.F1_QA.m2.tqs.mean"] = 0.0
    tqs_parsed(a)
    k = f"{P}.tqs_parsed.F1_QA"
    assert a.s[f"{k}.m1.n_task_model_pairs"] == 3 and a.s[f"{k}.m1.mean"] == 0.0
    assert a.s[f"{k}.m1.differs_from_prespecified"] is True
    assert a.s[f"{k}.m2.n_task_model_pairs"] == 4 and a.s[f"{k}.m2.differs_from_prespecified"] is False
    assert a.s[f"{k}.m1.status"] == "estimated"
    # decision R2 (m19): parsed orders per qualifying task: 7, 10, 10 (F1__1 does not qualify)
    assert a.s[f"{k}.m1.n_orders_median"] == 10.0 and a.s[f"{k}.m1.n_orders_min"] == 7
    df.loc[(df.model_key == "m1") & (df.family == "F2_CLASSIFICATION"), "q_answer_available"] = 0
    b = Analysis(df, ["m1", "m2"], n_boot=50)
    tqs_parsed(b)  # no qualifying task: a status, no NaN values
    assert b.s[f"{P}.tqs_parsed.F2_CLASSIFICATION.m1.status"].startswith("not computable")
    assert f"{P}.tqs_parsed.F2_CLASSIFICATION.m1.mean" not in b.s


def test_kendall_companion_counts_constant_tasks():
    a = Analysis(synthetic(_format_last_fails(family_prefix="F1_")), ["m1", "m2"], n_boot=50)
    kendall_companion(a)
    assert a.s[f"{P}.kendall_w.m1.n_constant_tasks"] == 16 and a.s[f"{P}.kendall_w.m1.n_nonconstant_tasks"] == 4
    assert a.s[f"{P}.kendall_w.m1.kendall_w_nonconstant"] == pytest.approx(1.0)  # identical rankings
    assert a.s[f"{P}.kendall_w.m2.n_constant_tasks"] == 20 and f"{P}.kendall_w.m2.kendall_w_nonconstant" not in a.s


def _dp(a, b):
    d = np.arange(len(b) + 1)
    for i, x in enumerate(a, start=1):
        prev, d[0] = d.copy(), i
        for j, y in enumerate(b, start=1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (x != y))
    return int(d[-1])


def test_levenshtein():
    assert levenshtein([1, 2, 3], [1, 2, 3]) == 0
    assert levenshtein([], [1, 2]) == 2 and levenshtein([1, 2], []) == 2
    assert levenshtein(list(b"kitten"), list(b"sitting")) == 3
    assert levenshtein([1, 2, 3, 4, 5], [1, 2, 9, 4, 5]) == 1
    rng = np.random.default_rng(3)
    for _ in range(200):
        a, b = rng.integers(0, 4, rng.integers(0, 12)).tolist(), rng.integers(0, 4, rng.integers(0, 12)).tolist()
        assert levenshtein(a, b) == _dp(a, b)


def _cascade_df():
    """m1 fails FORMAT in V02 with valid JSON: primary CSR 0.8 there, cascade CSR 0 (all five flags 0)."""
    df = synthetic(lambda c, pos, m, task, rng: True)
    sel = (df.model_key == "m1") & (df.condition_id == "V02")
    df.loc[sel, "format"] = 0
    df.loc[sel, [f"cascade_{c}" for c in ("format", "length", "cardinality", "t4", "verbatim")]] = 0
    return df


def test_cascade_check_counts_changed_outputs():
    a = Analysis(_cascade_df(), ["m1", "m2"], n_boot=50)
    cascade_check(a)
    k = f"{P}.cascade_check.format.m1"
    assert a.s[f"{k}.n_outputs_changed"] == 20 and a.s[f"{k}.n_tasks_ps_up"] == 20 and a.s[f"{k}.n_tasks_ps_down"] == 0
    assert a.s[f"{k}.ps_primary"] == pytest.approx(0.2) and a.s[f"{k}.ps_cascade"] == pytest.approx(1.0)
    assert a.s[f"{P}.cascade_check.format.m2.n_outputs_changed"] == 0


def test_cascade_p3_uses_cascade_ps_in_both_arms():
    """Regression for R1 §3.1 (Q1): the E6a P3 contrast is cascade PS_order minus cascade PS_format."""
    df = _cascade_df()
    s = robustness(df, ["m1", "m2"], n_boot=50, seed=1)
    assert s["main.robustness.cascade.format.m1.ps.mean"] == pytest.approx(1.0)  # primary would be 0.2
    assert s["main.robustness.cascade.p3.m1.mean_diff"] == pytest.approx(0.0 - 1.0)
    primary = Analysis(df, ["m1", "m2"], n_boot=50, seed=1)
    primary.p3()
    assert primary.s["main.p3.m1.mean_diff"] == pytest.approx(-0.2)


def test_cascade_p3_matches_cascade_ps_in_the_main_run():
    from src.common import RESULTS_DIR

    path = RESULTS_DIR / "metrics" / "summary.json"
    if not path.exists():
        pytest.skip("no main-run summary")
    text = path.read_text(encoding="utf-8")
    s = json.loads(text, parse_constant=lambda c: pytest.fail(f"non-standard JSON constant {c} in summary.json"))
    for m in s["_meta"]["models"]:
        diff = s[f"main.robustness.cascade.order.{m}.ps.mean"] - s[f"main.robustness.cascade.format.{m}.ps.mean"]
        assert s[f"main.robustness.cascade.p3.{m}.mean_diff"] == pytest.approx(diff, abs=1e-12)
        assert s[f"main.robustness.cascade.format.{m}.ps.mean"] == pytest.approx(
            s[f"{P}.cascade_check.format.{m}.ps_cascade"], abs=1e-12)


def test_paired_difference_matches_s2():
    """Decision R2 §3.1: the paired difference uses the S2 bootstrap; with strict flags it reproduces S2 exactly."""
    df = synthetic(lambda c, pos, m, task, rng: rng.random() < (0.6 if m == "m1" else 0.75), seed=5)
    a = Analysis(df, ["m1", "m2"], n_boot=300, seed=11)
    a.s2()
    tv = {m: a.task_values("order", m)["csr"] for m in ("m1", "m2")}
    r = paired_difference(a, tv["m2"], tv["m1"])  # m2 − m1 = −(m1 − m2)
    s2 = "main.s2.m1_vs_m2.csr_diff"
    assert r["mean"] == pytest.approx(-a.s[f"{s2}.mean"])
    assert (r["ci_low"], r["ci_high"]) == pytest.approx((-a.s[f"{s2}.ci_high"], -a.s[f"{s2}.ci_low"]))
    assert r["p"] == pytest.approx(a.s[f"{s2}.p"])


def test_fig7_reads_strict_and_fence_tolerant_keys(tmp_path):
    """Decision GV §3.1: Fig. 7 plots existing keys only (strict primary keys, fence-tolerant post-hoc keys)."""
    from PIL import Image

    from analysis import figures
    from src.common import RESULTS_DIR

    path = RESULTS_DIR / "metrics" / "summary.json"
    if not path.exists():
        pytest.skip("no main-run summary")
    s = json.loads(path.read_text(encoding="utf-8"))
    models = s["_meta"]["models"]
    vals = figures.fence_tolerant_values(s, models)
    assert len(vals) == 3 * len(models) * 2
    assert vals[("format", "gemma4e4b", "strict")] == (0.0, 0.0, 0.0)
    assert vals[("format", "gemma4e4b", "fence_tolerant")] == pytest.approx((100.0, 100.0, 100.0))
    for metric, _, key in figures.FT_METRICS:
        for m in models:
            assert vals[(metric, m, "strict")][0] == pytest.approx(100 * s[key.format(m=m) + ".mean"])
            assert vals[(metric, m, "fence_tolerant")][0] == pytest.approx(
                100 * s[f"{P}.fence_tolerant.order.{m}.{metric}.mean"])
    figures.setup()
    first = figures.fig7_fence_tolerant(s, models, tmp_path / "a")
    second = figures.fig7_fence_tolerant(s, models, tmp_path / "b")
    assert [p.read_bytes() for p in first] == [p.read_bytes() for p in second]  # deterministic
    png = next(p for p in first if p.suffix == ".png")
    assert Image.open(png).size[0] == 1889  # 16 cm at 300 dpi

"""C4 analysis package (analysis/): the bootstrap, the tests of ANALYSIS_PLAN §4-§5 and the exploratory E2/E3
computations on synthetic data whose answers are known (E2 unit test required by decision D03 §3)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from analysis.bootstrap import TaskBootstrap, bootstrap_p
from analysis.compute import Analysis
from analysis.data import CONSTRAINTS, FAMILIES
from analysis.stats import NOT_APPLICABLE, NOT_ESTIMABLE, bh, gee_position, p2_tests, p3_test
from src.orders import ORDERS

LETTER = {"A": "format", "B": "length", "C": "cardinality", "D": "t4", "E": "verbatim"}


def synthetic(rule, n_per_family: int = 4, models=("m1", "m2"), seed: int = 0) -> pd.DataFrame:
    """Order and format arms for 5 families × n tasks × models; flag = rule(constraint, positions, model, task, rng)."""
    rng = np.random.default_rng(seed)
    rows = []
    canonical = {LETTER[ch]: i + 1 for i, ch in enumerate(ORDERS["P01"])}
    for f in FAMILIES:
        for t in range(n_per_family):
            task = f"{f[:3]}_{t}"
            for m in models:
                conds = [(oid, "order", {LETTER[ch]: i + 1 for i, ch in enumerate(seq)}) for oid, seq in ORDERS.items()]
                conds += [(f"V{i:02d}", "format", canonical) for i in range(1, 11)]
                for cid, arm, pos in conds:
                    flags = {c: int(rule(c, pos, m, task, rng)) for c in CONSTRAINTS}
                    row = {"prompt_id": f"{task}__{cid}", "task_id": task, "family": f, "arm": arm, "condition_id": cid,
                           "model_key": m, "q_primary": float(flags["length"]), "q_answer_available": 1,
                           "parse_rule": "strict", "evaluable": 1, "finish_reason": "eos", "verbatim_min3": flags["verbatim"],
                           "verbatim_case_insensitive": flags["verbatim"], "containment_char": None, "error_tags": ()}
                    for c in CONSTRAINTS:
                        row[c] = flags[c]
                        row[f"pos_{c}"] = pos[c]
                        row[f"cascade_{c}"] = flags[c] if flags["format"] else 0
                    row["csr"] = float(np.mean([flags[c] for c in CONSTRAINTS]))
                    row["pcr"] = int(min(flags.values()))
                    row["cascade_csr"] = row["csr"] if flags["format"] else 0.0
                    row["cascade_pcr"] = row["pcr"] if flags["format"] else 0
                    rows.append(row)
    return pd.DataFrame(rows)


def test_bootstrap_resamples_within_family_and_is_reproducible():
    tasks = [f"t{i}" for i in range(10)]
    fams = ["a"] * 4 + ["b"] * 6
    b1, b2 = TaskBootstrap(tasks, fams, n_boot=500, seed=7), TaskBootstrap(tasks, fams, n_boot=500, seed=7)
    assert (b1.counts[:, :4].sum(axis=1) == 4).all() and (b1.counts[:, 4:].sum(axis=1) == 6).all()
    assert np.array_equal(b1.counts, b2.counts)
    est = b1.estimate(np.arange(10.0), np.ones(10))
    assert est["mean"] == 4.5 and est["ci_low"] <= 4.5 <= est["ci_high"]
    point, reps = b1.ratio(np.array([1.0, np.nan] + [1.0] * 8), np.array([2.0, np.nan] + [2.0] * 8))
    assert point == 0.5 and np.allclose(reps, 0.5)  # a task without observations contributes 0 / 0


def test_bootstrap_p_and_bh():
    assert bootstrap_p(np.array([1.0, 2.0, 3.0])) == pytest.approx(2 * 1 / 4)
    assert bootstrap_p(np.array([-1.0, 1.0])) == 1.0
    q = bh({"a": 0.01, "b": 0.04, "c": None})
    assert q["c"] is None and q["a"] == pytest.approx(0.02) and q["b"] == pytest.approx(0.04)


def test_task_values_ps_vsr_flip():
    df = synthetic(lambda c, pos, m, task, rng: not (c == "format" and pos["format"] == 5))
    a = Analysis(df, ["m1", "m2"], n_boot=50)
    tv = a.task_values("order", "m1")
    # FORMAT fails only in the 2 orders with FORMAT last: CSR 0.8 there, 1.0 elsewhere
    assert np.allclose(tv["ps"], 0.2) and (tv["vsr"] == 0).all()
    assert np.allclose(tv["flip_rate"], (2 * 8) / 45)  # pairs between the 2 failing and the 8 passing orders
    assert (a.task_values("format", "m1")["ps"] == 0).all()


def test_e2_stratified_difference_is_recovered():
    """D03 §3: LENGTH passes only when it precedes FORMAT (expected difference 1); CARDINALITY always passes
    (expected 0); VERBATIM passes when it precedes FORMAT at position 3 and at random elsewhere (expected 1, since
    only position 3 informs VERBATIM)."""

    def rule(c, pos, m, task, rng):
        before = pos[c] < pos["format"]
        if c == "length":
            return before
        if c == "verbatim":
            return before if pos[c] == 3 else rng.random() < 0.5
        return True

    a = Analysis(synthetic(rule), ["m1", "m2"], n_boot=200)
    a.e2()
    assert a.s["main.exploratory.e2.length.pooled.diff.mean"] == pytest.approx(1.0)
    assert a.s["main.exploratory.e2.cardinality.pooled.diff.mean"] == pytest.approx(0.0)
    assert a.s["main.exploratory.e2.verbatim.m1.diff.mean"] == pytest.approx(1.0)
    assert a.s["main.exploratory.e2.t4.informative_positions"] == [3]


def test_e3_hard_to_easy_index_signs():
    df = synthetic(lambda c, pos, m, task, rng: pos[c] <= 2)  # early instructions pass
    a = Analysis(df, ["m1", "m2"], n_boot=100)
    diff = {"difficulty": {"format": 0.9, "length": 0.7, "cardinality": 0.5, "t4": 0.3, "verbatim": 0.1},
            "phase": "x", "run_id": "y"}
    a.e3({"m1": diff, "m2": {**diff, "difficulty": {c: 0.5 for c in CONSTRAINTS}}})
    assert a.s["main.exploratory.e3.m1.he.P01"] == pytest.approx(1.0)  # A B C D E: hardest first
    assert a.s["main.exploratory.e3.m1.he.P06"] == pytest.approx(-1.0)  # E D C B A: easiest first
    assert a.s["main.exploratory.e3.m2.status"].startswith("HE not estimable")


def test_p1_constant_compliance_exclusion_and_edge_cases():
    df = synthetic(lambda c, pos, m, task, rng: (m == "m1") or rng.random() < (0.3 + 0.1 * pos[c]), seed=3)
    order = df[df.arm == "order"]
    r = gee_position(order, "length", ["m1", "m2"])
    assert r["excluded_models"] == {"m1": 1.0} and r["models_included"] == ["m2"]
    assert r["status"] == "estimated" and "C(model)" not in r["formula"] and r["df"] == 4
    none = gee_position(df[(df.arm == "order") & (df.model_key == "m1")], "length", ["m1"])
    assert none["status"] == NOT_APPLICABLE
    inter = gee_position(order, "length", ["m1", "m2"], interaction=True)
    assert inter["status"] == NOT_APPLICABLE  # fewer than two models vary


def test_p1_separation_is_not_estimable():
    df = synthetic(lambda c, pos, m, task, rng: task.startswith("F5_") or rng.random() < 0.5, seed=4)
    r = gee_position(df[df.arm == "order"], "length", ["m1", "m2"])
    assert r["status"] == NOT_ESTIMABLE and "family=F5_TRANSFORMATION: all pass" in r["reason"]


def test_p1_detects_a_position_effect():
    df = synthetic(lambda c, pos, m, task, rng: rng.random() < (0.9 if pos[c] == 1 else 0.3), n_per_family=8, seed=5)
    r = gee_position(df[df.arm == "order"], "t4", ["m1", "m2"])
    assert r["status"] == "estimated" and r["p"] < 0.001 and r["odds_ratios"][2]["estimate"] < 1


def test_p2_and_p3_rules():
    csr = np.tile(np.linspace(0, 1, 10), (20, 1))
    out = p2_tests(csr, np.zeros((20, 10)))
    assert out["cochran_q"]["status"] == NOT_APPLICABLE
    assert out["friedman"]["kendall_w"] == pytest.approx(out["friedman"]["chi2"] / (20 * 9))
    assert out["friedman"]["kendall_w"] == pytest.approx(1.0)
    assert p2_tests(np.ones((5, 10)), np.ones((5, 10)))["friedman"]["status"] == NOT_APPLICABLE
    assert p3_test(np.zeros(10))["status"] == "no difference; test not applicable"
    r = p3_test(np.array([0.2, 0.0, -0.2, 0.4, 0.4, 0.2, 0.6]))
    assert (r["n_zero"], r["n_pos"], r["n_neg"]) == (1, 5, 1) and r["status"] == "estimated"


def test_option_b_leaves_out_constant_models_and_families_before_fitting():
    """Decision G4a §2.1: independence working correlation; constant models and constant family levels excluded."""
    df = synthetic(lambda c, pos, m, task, rng: (m == "m1") or task.startswith("F5_") or rng.random() < 0.2 + 0.12 * pos[c],
                   n_per_family=6, seed=8)
    order = df[df.arm == "order"]
    r = gee_position(order, "length", ["m1", "m2"], working="independence", exclude_constant_families=True)
    assert r["excluded_models"] == {"m1": 1.0} and r["excluded_families"] == {"F5_TRANSFORMATION": 1.0}
    assert r["status"] == "estimated" and r["n"] == 4 * 6 * 10 and r["df"] == 4
    pre = gee_position(order, "length", ["m1", "m2"])  # the pre-specified estimator keeps the family: separation
    assert pre["status"] == NOT_ESTIMABLE and "F5_TRANSFORMATION" in pre["reason"]


def test_constraint_instability_and_presentation_keys():
    df = synthetic(lambda c, pos, m, task, rng: not (c == "format" and pos["format"] == 5 and m == "m1"))
    a = Analysis(df, ["m1", "m2"], n_boot=100)
    a.constraint_instability()
    assert a.s["main.robustness.constraint_instability.order.m1.format.mean"] == 1.0  # varies in every task
    assert a.s["main.robustness.constraint_instability.order.m2.format.mean"] == 0.0
    assert a.s["main.robustness.constraint_instability.format.m1.format.mean"] == 0.0  # format arm: FORMAT is first
    a.gee_family("main.p1", interaction=False, constraints=("format",))
    a.presentation()
    assert a.s["main.order.m1.evaluable_rate.mean"] == 1.0


def test_zero_width_note_prefers_an_interior_example():
    from analysis.report import zero_width_note

    s = {"a.mean": 1.0, "a.ci_low": 1.0, "a.ci_high": 1.0, "b.mean": 0.6, "b.ci_low": 0.6, "b.ci_high": 0.6,
         "c.mean": 0.5, "c.ci_low": 0.4, "c.ci_high": 0.6}
    note = zero_width_note(s, [("A", "a"), ("B", "b"), ("C", "c")])
    assert "B: 60.0% [60.0%, 60.0%]" in note
    assert zero_width_note(s, [("C", "c")]) == ""


def test_figures_render_from_the_summary(tmp_path):
    import json

    from analysis import figures
    from src.common import RESULTS_DIR

    path = RESULTS_DIR / "metrics" / "summary.json"
    if not path.exists():
        pytest.skip("no main-run summary")
    figures.setup()
    s = json.loads(path.read_text(encoding="utf-8"))
    out = figures.fig3_position(s, s["_meta"]["models"], tmp_path)
    assert {p.suffix for p in out} == {".png", ".pdf"} and all(p.stat().st_size > 10_000 for p in out)


def test_comma_spillover_matching():
    """Decision G4b §2.1 (Q-C2): an item is comma-only if it has no comma and is a span of the comma-free INPUT."""
    from analysis.spillover import comma_only, failing_items, strip_commas
    from src.evaluators.constraints import normalize_verbatim

    inp = "On 4 January 2025, Priya Nair visited the site. Total: 1,000 units, all tested."
    stripped = strip_commas(normalize_verbatim(inp))
    assert stripped == "On 4 January 2025 Priya Nair visited the site. Total: 1000 units all tested."
    items = ["On 4 January 2025 Priya Nair visited the site.", "Priya Nair visited the site.", "1000 units all tested",
             "Priya visited, the site", "a paraphrase", 7]
    fails = failing_items(items, inp)
    assert fails == ["On 4 January 2025 Priya Nair visited the site.", "1000 units all tested", "Priya visited, the site",
                     "a paraphrase", 7]
    assert [comma_only(x, stripped) for x in fails] == [True, True, False, False, False]

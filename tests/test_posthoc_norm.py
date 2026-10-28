"""Normalized FORMAT scoring (post-hoc re-analysis): the rule and its edge cases, the analysis on synthetic data
whose answers are known, and the checks of the main-run re-analysis when its outputs exist."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from analysis.compute import Analysis
from analysis.posthoc_norm import FLAGS_NORM, P, fence_form, format_normalized, norm_view, normalize_output, pcr_pairs
from analysis.posthoc_r1 import format_fence_tolerant
from analysis.stats import bh
from tests.test_analysis import synthetic

OK = '{"answer": "x", "evidence": ["a", "b"]}'
CASES = [  # (response, normalized FORMAT, case)
    (OK, 1, "valid bare JSON"),
    (f"  {OK}\n", 1, "valid bare JSON with surrounding whitespace"),
    (f"```json\n{OK}\n```", 1, "one fence with the json tag"),
    (f"```\n{OK}\n```", 1, "one fence without a tag"),
    (f"```JSON\n{OK}\n```", 1, "tag in upper case"),
    (f"```json \n{OK}\n```", 1, "space after the tag"),
    (f"```json{OK}```", 1, "fence on one line"),
    (f"\n```json\n{OK}\n```\n", 1, "fence with surrounding whitespace"),
    ('```json\n{"answer": "x", "evidence": ["a", "b"]\n```', 0, "broken JSON inside the fence"),
    ('{"answer": "x", "evidence": ["a"', 0, "broken bare JSON"),
    (f"Here is the JSON:\n```json\n{OK}\n```", 0, "commentary before the fence"),
    (f"```json\n{OK}\n```\nHope this helps.", 0, "commentary after the fence"),
    (f"Answer: {OK}", 0, "commentary before bare JSON"),
    ('```json\n{"answer": "x", "answer": "y", "evidence": ["a", "b"]}\n```', 0, "duplicate keys"),
    ('```json\n{"answer": "x", "evidence": ["a", "b"], "note": 1}\n```', 0, "extra key"),
    ('```json\n{"answer": "x"}\n```', 0, "missing key"),
    (f"```json\n{OK}\n", 0, "unclosed fence"),
    (f"```json\n{OK}\n```\n```json\n{OK}\n```", 0, "two fenced blocks"),
    (f"```python\n{OK}\n```", 0, "other language tag"),
    (f"```jsonc\n{OK}\n```", 0, "json-like tag"),
    (f"~~~json\n{OK}\n~~~", 0, "tilde fence"),
    (f"````json\n{OK}\n````", 0, "four-backtick fence"),
    ("```json\n[1, 2]\n```", 0, "fenced JSON that is not an object"),
]


@pytest.mark.parametrize("text, expected, case", CASES)
def test_normalized_format_rule(text, expected, case):
    assert format_normalized(text) == expected, case
    assert format_fence_tolerant(text) == expected, case  # the earlier fence-tolerant reading uses the same rule


def test_normalization_removes_only_the_fence():
    inner = '{"answer": "a, b", "evidence": ["x, y", "z"]}'
    assert normalize_output(f"```json\n{inner}\n```") == inner
    for text in (inner, f"Note: {inner}", f"```json\n{inner}\n```\nmore", f"```json\n{inner}"):
        assert normalize_output(text) == text  # anything else is left exactly as generated
    assert fence_form(inner) == "no fence"
    assert fence_form(f"```json\n{inner}\n```") == "one enclosing fence, tag 'json'"
    assert fence_form(f"```\n{inner}\n```") == "one enclosing fence, no tag"
    assert fence_form(f"Note:\n```json\n{inner}\n```") == "fence present but not one enclosing fence"


def _fenced_model_data(models=("m1", "m2")):
    """m1 passes FORMAT at random; m2 fails strict FORMAT everywhere but passes once its fence is removed."""
    def rule(c, pos, m, task, rng):
        if c == "format":
            return rng.random() < 0.7 if m == "m1" else False
        return rng.random() < 0.8

    df = synthetic(rule, models=models, seed=3)
    df["format_norm"] = df["format"]
    df.loc[df.model_key == "m2", "format_norm"] = 1
    return df


def test_normalized_scoring_on_synthetic_data():
    df = _fenced_model_data()
    strict = Analysis(df, ["m1", "m2"], n_boot=100)
    norm = Analysis(df, ["m1", "m2"], n_boot=100, flags=FLAGS_NORM)
    strict.s1()
    norm.s1(prefix=P)
    for arm in ("order", "format"):
        assert norm.s[f"{P}.{arm}.m2.csr.mean"] - strict.s[f"main.{arm}.m2.csr.mean"] == pytest.approx(0.2)
        for metric in ("ps", "vsr", "flip_rate"):  # every m2 flag moved the same way: ranges and vectors keep
            assert norm.s[f"{P}.{arm}.m2.{metric}.mean"] == pytest.approx(strict.s[f"main.{arm}.m2.{metric}.mean"])
        assert norm.s[f"{P}.{arm}.m1.csr.mean"] == strict.s[f"main.{arm}.m1.csr.mean"]
    assert strict.s["main.order.m2.pcr.mean"] == 0 and norm.s[f"{P}.order.m2.pcr.mean"] > 0
    norm.gee_family(f"{P}.p1", interaction=False, constraints=("format",))
    assert norm.s[f"{P}.p1.format.excluded_models"] == {"m2": 1.0}  # a ceiling is constant compliance too


def test_pcr_pairs_form_one_family():
    df = _fenced_model_data(models=("m1", "m2", "m3"))
    a = Analysis(df, ["m1", "m2", "m3"], n_boot=200, flags=FLAGS_NORM)
    pcr_pairs(a, f"{P}.s2")
    pairs = [("m1", "m2"), ("m1", "m3"), ("m2", "m3")]
    q = bh({pr: a.s[f"{P}.s2.{pr[0]}_vs_{pr[1]}.pcr_diff.p"] for pr in pairs})
    for x, y in pairs:
        assert a.s[f"{P}.s2.{x}_vs_{y}.pcr_diff.q"] == pytest.approx(q[(x, y)])


def test_norm_view_holds_only_normalized_values():
    norm = {"_meta": {}, f"{P}.order.m1.csr.mean": 0.5, f"{P}.order_level.order.m1.P01.csr.mean": 0.4,
            "main.order.m1.csr.mean": 0.3}
    view, source = norm_view(norm)
    assert dict(view) == {"main.order.m1.csr.mean": 0.5, "main.posthoc_r1.order_level.order.m1.P01.csr.mean": 0.4}
    assert all(v.startswith(P + ".") for v in source.values())


def test_main_run_reanalysis_checks():
    from src.common import RESULTS_DIR

    out = RESULTS_DIR / "posthoc_norm"
    if not (out / "summary_norm.json").exists():
        pytest.skip("no normalized re-analysis of the main run")
    n = json.loads((out / "summary_norm.json").read_text(encoding="utf-8"),
                   parse_constant=lambda c: pytest.fail(f"non-standard JSON constant {c}"))
    assert n[f"{P}.checks.all_passed"] is True
    assert all(k == "_meta" or k.startswith(P + ".") for k in n)  # no strict key is written by the re-analysis
    for k in ("strict_records", "strict_keys", "content_unchanged", "other_constraints_unchanged", "quality_unchanged",
              "earlier_fence_tolerant_values"):
        assert n[f"{P}.checks.{k}.n"] > 0 and n[f"{P}.checks.{k}.n_mismatch"] == 0, k
    audit = json.loads((out / "policy_audit.json").read_text(encoding="utf-8"))
    assert audit["all_ok"]
    for row in audit["outputs"]:
        if row["policy"] == "normalized":
            assert row["strict"] == 0, row
        else:
            assert row["policy"] == "comparison" and "strict_vs_norm" in row["output"], row
    rec = pd.read_csv(out / "records_format.csv")
    assert len(rec) == 8000 and (rec.format_norm >= rec.format_strict).all()
    changed = rec[rec.format_norm != rec.format_strict]
    assert set(changed.model_key) <= {"gemma4e4b", "qwen25"}

"""Evaluation records of the main run as one table, and the batch-1 pilot difficulties for E3.

ANALYSIS_PLAN §1 (data), §3 (outcomes) and §6 E3 (difficulty source, decision G2 §2.3).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common import RESULTS_DIR, RUNS_DIR, load_experiment, read_json, read_jsonl

CONSTRAINTS = ("format", "length", "cardinality", "t4", "verbatim")
FLAG = {"format": "format_strict", "length": "length", "cardinality": "cardinality", "t4": "t4", "verbatim": "verbatim"}
SLOT = {"T1": "format", "T2": "length", "T3": "cardinality", "T4": "t4", "T5": "verbatim"}
ORDER_IDS = tuple(f"P{i:02d}" for i in range(1, 11))
FORMAT_IDS = tuple(f"V{i:02d}" for i in range(1, 11))
FAMILIES = ("F1_QA", "F2_CLASSIFICATION", "F3_SUMMARIZATION", "F4_EXTRACTION", "F5_TRANSFORMATION")
ARM_IDS = {"order": ORDER_IDS, "format": FORMAT_IDS}


def main_models() -> list[str]:
    return list(load_experiment()["phases"]["main"]["models"])


def imported_run(phase: str, runs_root: Path = RUNS_DIR, analysis_eligible: bool | None = None) -> str:
    """The single imported run of a phase (the analysis refuses to guess between several)."""
    records = [read_json(p) for p in sorted((runs_root / phase).glob("*.import.json"))]
    ok = [r["run_id"] for r in records if r.get("passed") and not r.get("fixture")
          and (analysis_eligible is None or bool(r.get("analysis_eligible")) == analysis_eligible)]
    if len(ok) != 1:
        raise SystemExit(f"expected exactly one imported run in runs/{phase}/, found {ok}")
    return ok[0]


def _row(r: dict) -> dict:
    row = {k: r[k] for k in ("prompt_id", "task_id", "family", "arm", "condition_id", "model_key", "csr", "pcr",
                             "q_primary", "q_answer_available", "parse_rule", "evaluable", "finish_reason")}
    for c in CONSTRAINTS:
        row[c] = int(r[FLAG[c]])
        row[f"pos_{c}"] = int(r["positions"][c])
        row[f"cascade_{c}"] = int(r[f"cascade_{c}"])
    row.update({"cascade_csr": r["cascade_csr"], "cascade_pcr": int(r["cascade_pcr"]),
                "verbatim_min3": int(r["verbatim_min3"]), "verbatim_case_insensitive": int(r["verbatim_case_insensitive"]),
                "containment_char": (r.get("quality_detail") or {}).get("containment_char"),
                "q_secondary": r.get("q_secondary"),
                "label_status": (r.get("quality_detail") or {}).get("label_status"),
                "error_tags": tuple(r["error_tags"])})
    return row


def load_eval(phase: str, run_id: str, models: list[str], results_root: Path = RESULTS_DIR) -> pd.DataFrame:
    rows = [_row(r) for m in models for r in read_jsonl(results_root / "eval" / phase / run_id / f"{m}.jsonl")]
    return pd.DataFrame(rows)


def check_main_table(df: pd.DataFrame, models: list[str]) -> None:
    """The analysed data must be complete: every model has 100 tasks (20 per family) × 20 prompt ids, and CSR/PCR
    agree with the five flags (ANALYSIS_PLAN §1, §3)."""
    for m in models:
        sub = df[df.model_key == m]
        assert len(sub) == 2000 and sub.prompt_id.is_unique, m
        assert sub.groupby("task_id").size().eq(20).all() and sub.task_id.nunique() == 100, m
        assert sub.groupby("family").task_id.nunique().eq(20).all(), m
        for arm, ids in ARM_IDS.items():
            assert sorted(sub[sub.arm == arm].condition_id.unique()) == sorted(ids), (m, arm)
    flags = df[list(CONSTRAINTS)]
    assert (abs(flags.mean(axis=1) - df.csr) < 1e-9).all(), "CSR differs from the mean of the five flags"
    assert (flags.min(axis=1) == df.pcr).all(), "PCR differs from 'all five flags pass'"


def pilot_difficulties(models: list[str], runs_root: Path = RUNS_DIR, results_root: Path = RESULTS_DIR) -> dict:
    """E3 difficulty d(m, c) = 1 - compliance in the batch-1 order-arm pilot outputs (decision G2 §2.3):
    `pilot_bs1` for the three original models, the order arm of `pilot_gemma` for Gemma."""
    phases = load_experiment()["phases"]["main"]["determinism_check"]["reference_phases"]
    out = {}
    for m in models:
        phase = phases[m]
        run_id = imported_run(phase, runs_root)
        df = load_eval(phase, run_id, [m], results_root)
        df = df[df.arm == "order"]
        assert len(df) == 100, (m, phase, len(df))
        out[m] = {"phase": phase, "run_id": run_id, "n": len(df),
                  "difficulty": {c: float(1 - df[c].mean()) for c in CONSTRAINTS}}
    return out

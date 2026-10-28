"""Comma spill-over into the evidence spans (exploratory, descriptive; decision G4b §2.1, question Q-C2).

Main run only. An evidence item that fails VERBATIM counts as comma-only if it contains no comma and, after the
VERBATIM normalization (NFC, straightened quotes, collapsed whitespace), is a contiguous substring of the INPUT from
which every comma ("," and "，") has been removed and whitespace re-collapsed. Reported per model and arm:

* items: the share of non-verbatim evidence items that are comma-only;
* outputs_all / outputs_any: among outputs tagged `evidence_not_verbatim`, the share whose non-verbatim items are
  all / at least one comma-only.

Shares use the task-clustered bootstrap of the main analysis (ratio estimators). No test.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from analysis.compute import Analysis, _put
from src.common import BENCH_DIR, RUNS_DIR, read_jsonl
from src.evaluators.constraints import normalize_verbatim, verbatim_ok
from src.evaluators.format import lenient_parse

COMMAS = (",", "，")
PROCEDURE = ("An evidence item that fails VERBATIM counts as comma-only if it contains no comma and, after the VERBATIM "
             "normalization (NFC, straightened quotes, collapsed whitespace), is a contiguous substring of the INPUT from "
             "which every comma (',' and '，') has been removed and whitespace re-collapsed.")


def strip_commas(text: str) -> str:
    for c in COMMAS:
        text = text.replace(c, "")
    return re.sub(r"\s+", " ", text).strip()


def failing_items(evidence: list, input_text: str) -> list:
    """The items that make `verbatim_ok` fail (non-strings, items without a letter or digit, non-substrings)."""
    return [s for s in evidence if not isinstance(s, str) or not verbatim_ok([s], input_text)]


def comma_only(item, stripped_input: str) -> bool:
    if not isinstance(item, str):
        return False
    norm = normalize_verbatim(item)
    return bool(norm) and not any(c in norm for c in COMMAS) and norm in stripped_input


def output_rows(run_id: str, models: list[str], runs_root=RUNS_DIR, bench=BENCH_DIR) -> pd.DataFrame:
    """One row per (prompt id, model) for outputs whose evidence fails VERBATIM, with their item counts."""
    inputs = {t["task_id"]: t["input_text"] for t in read_jsonl(bench / "tasks_main.jsonl")}
    rows = []
    for m in models:
        for g in read_jsonl(runs_root / "main" / run_id / m / "generations.jsonl"):
            obj = lenient_parse(g["output_text"]).obj
            ev = obj.get("evidence") if isinstance(obj, dict) else None
            if not isinstance(ev, list) or not ev or verbatim_ok(ev, inputs[g["task_id"]]):
                continue
            stripped = strip_commas(normalize_verbatim(inputs[g["task_id"]]))
            fails = failing_items(ev, inputs[g["task_id"]])
            n_comma = sum(comma_only(s, stripped) for s in fails)
            for pid in g["prompt_ids"]:  # P01 and V01 share one generation; each prompt id is one output of its arm
                rows.append({"model_key": m, "prompt_id": pid, "task_id": g["task_id"],
                             "arm": "order" if "__P" in pid else "format", "n_fail": len(fails), "n_comma": n_comma})
    return pd.DataFrame(rows)


def comma_spillover(a: Analysis, run_id: str, prefix: str = "main.exploratory.e5") -> None:
    rows = output_rows(run_id, a.models)
    tagged = a.df[a.df.error_tags.apply(lambda t: "evidence_not_verbatim" in t)][["model_key", "prompt_id"]]
    assert set(map(tuple, tagged.to_numpy())) == set(map(tuple, rows[["model_key", "prompt_id"]].to_numpy())), \
        "comma spill-over rows differ from the outputs tagged evidence_not_verbatim"
    rows = rows.assign(all_comma=(rows.n_comma == rows.n_fail).astype(float), any_comma=(rows.n_comma > 0).astype(float))
    for arm in ("order", "format"):
        for name, ms in a.model_sets():
            sub = rows[(rows.arm == arm) & rows.model_key.isin(ms)]
            p = f"{prefix}.{arm}.{name}.evidence_comma_only"
            g = sub.groupby("task_id")
            _put(a.s, f"{p}.items", a.bs.estimate(a.bs.align(g.n_comma.sum()), a.bs.align(g.n_fail.sum())))
            _put(a.s, f"{p}.outputs_all", a.bs.estimate(a.bs.align(g.all_comma.sum()), a.bs.align(g.size())))
            _put(a.s, f"{p}.outputs_any", a.bs.estimate(a.bs.align(g.any_comma.sum()), a.bs.align(g.size())))
            a.s.update({f"{p}.n_items_not_verbatim": int(sub.n_fail.sum()), f"{p}.n_items_comma_only": int(sub.n_comma.sum()),
                        f"{p}.n_outputs_not_verbatim": int(len(sub))})
    a.s[f"{prefix}.evidence_comma_only.procedure"] = PROCEDURE
    a.s[f"{prefix}.evidence_comma_only.label"] = "exploratory, descriptive (decision G4b §2.1, Q-C2); main run only"

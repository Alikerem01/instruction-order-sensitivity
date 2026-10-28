"""Assemble one evaluation record (implementation specification §6.2) from a raw output string."""

from __future__ import annotations

from typing import Any

from src.evaluators.constraints import (
    cardinality_ok,
    evidence_duplicate,
    length_ok,
    lowercase_ok,
    no_comma_ok,
    verbatim_ok,
)
from src.evaluators.format import format_strict, lenient_parse
from src.evaluators.quality import task_quality
from src.evaluators.tags import error_tags

FLAG_NAMES = ("format", "length", "cardinality", "t4", "verbatim")
# Instruction key -> constraint flag (the active keys appear in each prompt record).
KEY_TO_FLAG = {
    "T1_FORMAT": "format",
    "T2_LENGTH": "length",
    "T2_LENGTH_20": "length",
    "T3_CARDINALITY": "cardinality",
    "T4_NO_COMMA": "t4",
    "T4_LOWERCASE": "t4",
    "T5_VERBATIM": "verbatim",
}
LENGTH_LIMITS = {"T2_LENGTH": 25, "T2_LENGTH_20": 20}


def rule_settings(instruction_keys: list[str]) -> tuple[int, str]:
    """Length limit and T4 mode implied by the instruction keys of a prompt."""
    length_keys = [k for k in instruction_keys if k in LENGTH_LIMITS]
    t4_keys = [k for k in instruction_keys if k.startswith("T4_")]
    if len(length_keys) != 1 or len(t4_keys) != 1:
        raise ValueError(f"cannot infer rule settings from {instruction_keys}")
    return LENGTH_LIMITS[length_keys[0]], t4_keys[0]


def evaluate_output(output_text: str, finish_reason: str | None, task: dict, prompt: dict, model_key: str) -> dict:
    """Evaluate one output for one prompt id. ``task`` and ``prompt`` are records from the benchmark files."""
    length_limit, t4_key = rule_settings(prompt["instruction_order"])
    input_text = task["input_text"]

    fmt = format_strict(output_text)
    parse = lenient_parse(output_text)
    obj: dict[str, Any] | None = parse.obj
    answer = obj.get("answer") if obj is not None else None
    evidence = obj.get("evidence") if obj is not None else None

    t4_check = no_comma_ok if t4_key == "T4_NO_COMMA" else lowercase_ok
    flags = {
        "format": int(fmt),
        "length": int(length_ok(answer, length_limit)),
        "cardinality": int(cardinality_ok(evidence)),
        "t4": int(t4_check(answer)),
        "verbatim": int(verbatim_ok(evidence, input_text, case_sensitive=True)),
    }
    verbatim_ci = int(verbatim_ok(evidence, input_text, case_sensitive=False))
    verbatim_min3 = int(verbatim_ok(evidence, input_text, case_sensitive=True, min_tokens=3))  # diagnostic (R2)
    dup = evidence_duplicate(evidence)
    quality = task_quality(task["family"], answer, task)
    tags = error_tags(output_text, parse, input_text, dup, finish_reason)
    cascade = {f"cascade_{k}": (v if fmt else 0) for k, v in flags.items()}

    positions = {KEY_TO_FLAG[k]: p for k, p in prompt["instruction_positions"].items()}
    csr = sum(flags.values()) / len(flags)
    cascade_csr = sum(cascade.values()) / len(cascade)
    return {
        "prompt_id": prompt["prompt_id"],
        "task_id": prompt["task_id"],
        "family": prompt["family"],
        "arm": prompt["arm"],
        "condition_id": prompt["condition_id"],
        "model_key": model_key,
        "positions": {name: positions[name] for name in FLAG_NAMES},
        "format_strict": flags["format"],
        "parse_rule": parse.rule,
        "evaluable": int(parse.evaluable),
        "length": flags["length"],
        "cardinality": flags["cardinality"],
        "t4": flags["t4"],
        "verbatim": flags["verbatim"],
        "verbatim_case_insensitive": verbatim_ci,
        "verbatim_min3": verbatim_min3,
        "csr": csr,
        "pcr": int(all(flags.values())),
        "q_primary": quality.q_primary,
        "q_secondary": quality.q_secondary,
        "q_answer_available": int(quality.answer_available),
        "quality_detail": quality.detail,
        "error_tags": tags,
        "evidence_duplicate": int(dup),
        "finish_reason": finish_reason,
        **cascade,
        "cascade_csr": cascade_csr,
        "cascade_pcr": int(all(cascade.values())),
        "t4_rule": t4_key,
        "length_limit": length_limit,
    }

"""Non-exclusive error tags (brief §5.8)."""

from __future__ import annotations

import re
from typing import Any

from src.evaluators.constraints import verbatim_ok
from src.evaluators.format import REQUIRED_KEYS, ParseResult

TAG_ORDER = (
    "empty_output", "code_fence", "leading_text", "trailing_text", "invalid_json", "duplicate_keys",
    "extra_keys", "missing_answer", "missing_evidence", "answer_not_string", "evidence_not_list",
    "evidence_count_0", "evidence_count_1", "evidence_count_3plus", "evidence_not_verbatim",
    "evidence_duplicate", "truncated",
)
_FENCE_MARKER_RE = re.compile(r"```(?:json)?", re.I)


def _outside_text(parse: ParseResult) -> tuple[str, str]:
    s = parse.stripped
    if parse.span is None:
        return s, ""
    start, end = parse.span
    return s[:start], s[end:]


def error_tags(
    output: str,
    parse: ParseResult,
    input_text: str,
    evidence_is_duplicate: bool,
    finish_reason: str | None,
) -> list[str]:
    tags: set[str] = set()
    s = parse.stripped
    if s == "":
        tags.add("empty_output")
    before, after = _outside_text(parse)
    if "```" in before or "```" in after:
        tags.add("code_fence")
    if parse.evaluable:
        if _FENCE_MARKER_RE.sub("", before).strip():
            tags.add("leading_text")
        if _FENCE_MARKER_RE.sub("", after).strip():
            tags.add("trailing_text")
    elif s:
        tags.add("invalid_json")

    obj: dict[str, Any] | None = parse.obj
    if obj is not None:
        if parse.duplicate_keys:
            tags.add("duplicate_keys")
        if set(obj) - REQUIRED_KEYS:
            tags.add("extra_keys")
        if "answer" not in obj:
            tags.add("missing_answer")
        elif not isinstance(obj["answer"], str):
            tags.add("answer_not_string")
        if "evidence" not in obj:
            tags.add("missing_evidence")
        else:
            evidence = obj["evidence"]
            if not isinstance(evidence, list):
                tags.add("evidence_not_list")
            else:
                n = len(evidence)
                if n == 0:
                    tags.add("evidence_count_0")
                elif n == 1:
                    tags.add("evidence_count_1")
                elif n >= 3:
                    tags.add("evidence_count_3plus")
                if n > 0 and not verbatim_ok(evidence, input_text):
                    tags.add("evidence_not_verbatim")
        if evidence_is_duplicate:
            tags.add("evidence_duplicate")
    if finish_reason == "length":
        tags.add("truncated")
    return [t for t in TAG_ORDER if t in tags]

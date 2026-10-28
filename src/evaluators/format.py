"""T1 FORMAT (strict) and the lenient parse used by every other check (brief §5.8).

Strict FORMAT: ``s = o.strip()``; ``json.loads(s)`` succeeds without duplicate keys, the result is a dict
and its key set is exactly {"answer", "evidence"}. Code fences, surrounding text or extra keys fail.

Lenient parse (never used for the FORMAT score): (1) ``json.loads(s)`` gives a dict -> rule "strict";
(2) else, if all of ``s`` is one fenced block (``` or ```json), its content parses to a dict -> "fence";
(3) else, for each "{" from left to right, ``json.JSONDecoder().raw_decode(s, i)``; the first dict -> "first_object";
(4) else no object -> "none". No other repair of any kind.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

REQUIRED_KEYS = frozenset({"answer", "evidence"})

# One fenced block covering all of s: ```, optionally followed by the language tag "json" (any case).
_FENCE_RE = re.compile(r"\A```(?:json)?[ \t]*\n?(.*?)\n?[ \t]*```\Z", re.DOTALL | re.IGNORECASE)


@dataclass
class ParseResult:
    obj: dict | None
    rule: str  # strict | fence | first_object | none
    span: tuple[int, int] | None = None  # character span of the parsed object inside s = o.strip()
    duplicate_keys: bool = False
    stripped: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def evaluable(self) -> bool:
        return self.obj is not None


class _DuplicateTracker:
    """object_pairs_hook that builds dicts like json does (last value wins) and records duplicates."""

    def __init__(self) -> None:
        self.found = False

    def __call__(self, pairs: list[tuple[str, Any]]) -> dict:
        keys = [k for k, _ in pairs]
        if len(keys) != len(set(keys)):
            self.found = True
        return dict(pairs)


def _loads(text: str) -> tuple[Any, bool]:
    tracker = _DuplicateTracker()
    obj = json.loads(text, object_pairs_hook=tracker)
    return obj, tracker.found


def format_strict(output: str) -> bool:
    """Strict FORMAT pass/fail on the raw output string."""
    s = output.strip()
    try:
        obj, dup = _loads(s)
    except (ValueError, RecursionError):
        return False
    return (not dup) and isinstance(obj, dict) and set(obj.keys()) == REQUIRED_KEYS


def lenient_parse(output: str) -> ParseResult:
    s = output.strip()
    # (1) the whole stripped output is a JSON object
    try:
        obj, dup = _loads(s)
    except (ValueError, RecursionError):
        obj, dup = None, False
    if isinstance(obj, dict):
        return ParseResult(obj, "strict", (0, len(s)), dup, s)

    # (2) the whole stripped output is exactly one fenced block whose content is a JSON object
    m = _FENCE_RE.match(s)
    if m and "```" not in m.group(1):
        content = m.group(1)
        try:
            obj, dup = _loads(content.strip())
        except (ValueError, RecursionError):
            obj, dup = None, False
        if isinstance(obj, dict):
            lead = len(content) - len(content.lstrip())
            start = m.start(1) + lead
            end = start + len(content.strip())
            return ParseResult(obj, "fence", (start, end), dup, s)

    # (3) the first "{" (left to right) at which raw_decode yields a dict
    for i, ch in enumerate(s):
        if ch != "{":
            continue
        tracker = _DuplicateTracker()
        decoder = json.JSONDecoder(object_pairs_hook=tracker)
        try:
            obj, end = decoder.raw_decode(s, i)
        except (ValueError, RecursionError):
            continue
        if isinstance(obj, dict):
            return ParseResult(obj, "first_object", (i, end), tracker.found, s)

    # (4) nothing parseable
    return ParseResult(None, "none", None, False, s)

"""T2-T5 constraint checks on the lenient-parsed object (brief §5.8).

All checks take the values found under "answer" and "evidence" (``None`` when the key is missing or the
output is not evaluable) and return a bool.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

WORD_RE = re.compile(r"\S+")
_WS_RE = re.compile(r"\s+")

# Typographic quotes mapped to straight quotes for VERBATIM matching.
_QUOTE_TABLE = str.maketrans(
    {
        "‘": "'", "’": "'", "‚": "'", "‛": "'",
        "“": '"', "”": '"', "„": '"', "‟": '"',
    }
)
FULLWIDTH_COMMA = "，"
MIN3_TOKENS = 3  # only for the diagnostic verbatim_min3 (the rule before design decision G1, R2)


def n_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def length_ok(answer: Any, limit: int) -> bool:
    """LENGTH: answer is a string with at most ``limit`` \\S+ tokens."""
    return isinstance(answer, str) and n_words(answer) <= limit


def cardinality_ok(evidence: Any) -> bool:
    """CARDINALITY: evidence is a list of exactly 2 strings, each non-empty after stripping."""
    return (
        isinstance(evidence, list)
        and len(evidence) == 2
        and all(isinstance(item, str) and item.strip() != "" for item in evidence)
    )


def no_comma_ok(answer: Any) -> bool:
    """T4 NO_COMMA: answer is a string containing neither ',' nor the fullwidth comma U+FF0C."""
    return isinstance(answer, str) and "," not in answer and FULLWIDTH_COMMA not in answer


def lowercase_ok(answer: Any) -> bool:
    """T4 LOWERCASE (calibration fallback only): a string with at least one letter, equal to its lowercase."""
    return isinstance(answer, str) and any(ch.isalpha() for ch in answer) and answer == answer.lower()


def straighten_quotes(text: str) -> str:
    """Typographic single and double quotes -> straight quotes (shared by VERBATIM and the F1 metric)."""
    return text.translate(_QUOTE_TABLE)


def normalize_verbatim(text: str) -> str:
    """NFC, typographic quotes -> straight quotes, whitespace runs -> one space, strip."""
    text = unicodedata.normalize("NFC", text)
    text = straighten_quotes(text)
    return _WS_RE.sub(" ", text).strip()


def verbatim_ok(evidence: Any, input_text: str, case_sensitive: bool = True, min_tokens: int = 0) -> bool:
    """VERBATIM: a non-empty list whose every item is a string that, after normalization, contains at least
    one letter or digit and is a substring of the normalized INPUT text. The item count is CARDINALITY's job.

    ``min_tokens=3`` gives the diagnostic ``verbatim_min3`` (each item must also have >= 3 \\S+ tokens)."""
    if not isinstance(evidence, list) or not evidence:
        return False
    source = normalize_verbatim(input_text)
    if not case_sensitive:
        source = source.lower()
    for item in evidence:
        if not isinstance(item, str):
            return False
        norm = normalize_verbatim(item)
        if not any(ch.isalnum() for ch in norm):
            return False
        if n_words(norm) < min_tokens:
            return False
        if not case_sensitive:
            norm = norm.lower()
        if norm not in source:
            return False
    return True


def evidence_duplicate(evidence: Any) -> bool:
    """True if at least two string items of the evidence list are identical after normalization."""
    if not isinstance(evidence, list):
        return False
    items = [normalize_verbatim(x) for x in evidence if isinstance(x, str)]
    return len(items) != len(set(items))

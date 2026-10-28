"""Task quality per family (brief §5.8), computed from the lenient-parsed "answer" when it is a string.

F1 QA            primary: whole-token containment of any gold answer (design decision G1, R1);
                 secondary: max token F1; diagnostic: the brief's character-substring containment.
F2 classification primary: label extracted with the synonym and cue rules equals the gold label.
F3 summarization primary: ROUGE-L F1 (rouge-score, use_stemmer=True) against the XSum reference.
F4/F5 synthetic  primary: field accuracy (fraction of the 5 gold fields found); secondary: exact-all-fields.
Quality is never averaged across families.
"""

from __future__ import annotations

import re
import string
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from typing import Any

from src.evaluators.constraints import straighten_quotes

# ---------------------------------------------------------------------------------------------
# F1: SQuAD normalization, containment and token F1
# ---------------------------------------------------------------------------------------------
_PUNCT = frozenset(string.punctuation)
_ARTICLES_RE = re.compile(r"\b(a|an|the)\b")
_POSSESSIVE_RE = re.compile(r"(?<=\w)'s(?!\w)", re.IGNORECASE)


def squad_normalize(text: str) -> str:
    """Official SQuAD v1.1 normalization: lowercase, drop ASCII punctuation, drop a/an/the, collapse spaces."""
    text = text.lower()
    text = "".join(ch for ch in text if ch not in _PUNCT)
    text = _ARTICLES_RE.sub(" ", text)
    return " ".join(text.split())


def qa_tokens(text: str) -> list[str]:
    """Normalization of the primary F1 metric (R1): Unicode NFC; typographic quotes straightened (the VERBATIM
    mapping); possessive "'s" after a word character removed (case-insensitive); SQuAD normalization; split."""
    text = unicodedata.normalize("NFC", text)
    text = straighten_quotes(text)
    text = _POSSESSIVE_RE.sub("", text)
    return squad_normalize(text).split()


def _contains_subsequence(tokens: list[str], needle: list[str]) -> bool:
    n = len(needle)
    return n > 0 and any(tokens[i : i + n] == needle for i in range(len(tokens) - n + 1))


def qa_containment(answer: str, golds: list[str]) -> int:
    """Primary F1 metric: the token sequence of some gold answer is a contiguous subsequence of the answer's."""
    answer_tokens = qa_tokens(answer)
    return int(any(_contains_subsequence(answer_tokens, qa_tokens(g)) for g in golds))


def qa_containment_char(answer: str, golds: list[str]) -> int:
    """Diagnostic only (robustness appendix): the brief's rule, a normalized gold answer is a character
    substring of the normalized answer."""
    a = squad_normalize(answer)
    return int(any(g and g in a for g in (squad_normalize(x) for x in golds)))


def token_f1(prediction: str, gold: str) -> float:
    p_tokens = squad_normalize(prediction).split()
    g_tokens = squad_normalize(gold).split()
    common = Counter(p_tokens) & Counter(g_tokens)
    n_same = sum(common.values())
    if n_same == 0:
        return 0.0
    precision = n_same / len(p_tokens)
    recall = n_same / len(g_tokens)
    return 2 * precision * recall / (precision + recall)


def qa_max_token_f1(answer: str, golds: list[str]) -> float:
    return max((token_f1(answer, g) for g in golds), default=0.0)


# ---------------------------------------------------------------------------------------------
# F2: label extraction
# ---------------------------------------------------------------------------------------------
LABEL_SYNONYMS: dict[str, tuple[str, ...]] = {
    "World": ("world",),
    "Sports": ("sports", "sport"),
    "Business": ("business",),
    "Sci/Tech": (
        "sci/tech", "sci-tech", "scitech", "sci tech",
        "science/technology", "science and technology", "science & technology",
        "technology", "tech", "science",  # added by design decision G1, R3
    ),
}
# Cue phrases (brief §5.8). A label "directly follows a cue within three tokens" when its first token is
# the 1st, 2nd or 3rd token after the cue's last token.
CUE_PHRASES: tuple[tuple[str, ...], ...] = (
    ("category", "is"), ("category", "was"), ("classified", "as"), ("belongs", "to"),
    ("falls", "under"), ("falls", "into"), ("is",), ("as",), ("under",), ("into",),
)
CUE_WINDOW = 3

_LABEL_RES = [
    (label, re.compile(r"(?<![a-z0-9])" + re.escape(syn) + r"(?![a-z0-9])"))
    for label, syns in LABEL_SYNONYMS.items()
    for syn in syns
]
_TOKEN_RE = re.compile(r"\S+")
_EDGE_PUNCT = string.punctuation + "“”‘’"


@dataclass
class LabelResult:
    prediction: str | None
    status: str  # none | single | cue_resolved | unresolved
    labels_found: list[str] = field(default_factory=list)


def extract_label(answer: str) -> LabelResult:
    text = " ".join(answer.lower().split())
    mentions = []  # (start, label)
    for label, rx in _LABEL_RES:
        for m in rx.finditer(text):
            mentions.append((m.start(), label))
    labels = sorted({label for _, label in mentions})
    if not labels:
        return LabelResult(None, "none", [])
    if len(labels) == 1:
        return LabelResult(labels[0], "single", labels)

    tokens = [(m.start(), m.end(), m.group().strip(_EDGE_PUNCT)) for m in _TOKEN_RE.finditer(text)]

    def token_index(pos: int) -> int:
        for idx, (start, end, _) in enumerate(tokens):
            if start <= pos < end:
                return idx
        raise ValueError("position outside tokens")

    words = [t[2] for t in tokens]
    cue_ends = set()
    for cue in CUE_PHRASES:
        n = len(cue)
        for i in range(len(words) - n + 1):
            if tuple(words[i : i + n]) == cue:
                cue_ends.add(i + n - 1)
    following = set()
    for pos, label in mentions:
        ti = token_index(pos)
        if any(1 <= ti - c <= CUE_WINDOW for c in cue_ends):
            following.add(label)
    if len(following) == 1:
        return LabelResult(next(iter(following)), "cue_resolved", labels)
    return LabelResult(None, "unresolved", labels)


# ---------------------------------------------------------------------------------------------
# F3: ROUGE-L
# ---------------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _rouge_scorer():
    from rouge_score import rouge_scorer

    return rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)


def rouge_l_f1(prediction: str, reference: str) -> float:
    return float(_rouge_scorer().score(reference, prediction)["rougeL"].fmeasure)


# ---------------------------------------------------------------------------------------------
# F4/F5: field matching with date canonicalization and number normalization
# ---------------------------------------------------------------------------------------------
_MONTHS_FULL = ("january", "february", "march", "april", "may", "june", "july", "august",
                "september", "october", "november", "december")
_MONTHS_ABBR = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
_MONTH_NUM = {name: i + 1 for i, name in enumerate(_MONTHS_FULL)}
_MONTH_NUM.update({name: i + 1 for i, name in enumerate(_MONTHS_ABBR)})
_FULL = "|".join(_MONTHS_FULL)
_ABBR = "|".join(_MONTHS_ABBR)

# Accepted forms (brief §5.8): "14 March 2025", "March 14 2025", "March 14, 2025", "14 Mar 2025",
# "Mar 14 2025", "2025-03-14", "14/03/2025" (day first). Month names are case-insensitive.
_DATE_PATTERNS: tuple[tuple[str, re.Pattern, tuple[str, str, str]], ...] = (
    ("d_month_y", re.compile(rf"(?<!\w)(\d{{1,2}}) ({_FULL}) (\d{{4}})(?!\w)", re.I), ("d", "m", "y")),
    ("month_d_y", re.compile(rf"(?<!\w)({_FULL}) (\d{{1,2}}) (\d{{4}})(?!\w)", re.I), ("m", "d", "y")),
    ("month_d_comma_y", re.compile(rf"(?<!\w)({_FULL}) (\d{{1,2}}), (\d{{4}})(?!\w)", re.I), ("m", "d", "y")),
    ("d_mon_y", re.compile(rf"(?<!\w)(\d{{1,2}}) ({_ABBR}) (\d{{4}})(?!\w)", re.I), ("d", "m", "y")),
    ("mon_d_y", re.compile(rf"(?<!\w)({_ABBR}) (\d{{1,2}}) (\d{{4}})(?!\w)", re.I), ("m", "d", "y")),
    ("iso", re.compile(r"(?<![\w-])(\d{4})-(\d{1,2})-(\d{1,2})(?![\w-])"), ("y", "m", "d")),
    ("dmy_slash", re.compile(r"(?<![\w/])(\d{1,2})/(\d{1,2})/(\d{4})(?![\w/])"), ("d", "m", "y")),
)
_THOUSANDS_RE = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
_CURRENCY_RE = re.compile(r"US\$|\$|€|£|USD|dollars", re.I)
_NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?!\w|\.\d)")

FIELD_KINDS: dict[str, dict[str, str]] = {
    "F4_EXTRACTION": {"person": "phrase", "organization": "phrase", "city": "phrase", "date": "date",
                      "amount": "number"},
    "F5_TRANSFORMATION": {"project": "phrase", "owner": "phrase", "status": "phrase", "deadline": "date",
                          "budget": "number"},
}


def _ws(text: str) -> str:
    return " ".join(text.split())


def find_dates(text: str) -> list[tuple[int, int, date]]:
    """All accepted date mentions in ``text`` as (start, end, date); invalid calendar dates are ignored.

    "May" is both a full month name and an abbreviation, so "12 May 2025" matches two patterns with the same
    span and date; such identical mentions are reported once (found by the golden-output test, R6)."""
    text = _ws(text)
    found = set()
    for _, rx, order in _DATE_PATTERNS:
        for m in rx.finditer(text):
            parts = dict(zip(order, m.groups()))
            month = parts["m"]
            month_num = int(month) if month.isdigit() else _MONTH_NUM[month.lower()]
            try:
                found.add((m.start(), m.end(), date(int(parts["y"]), month_num, int(parts["d"]))))
            except ValueError:
                continue
    return sorted(found)


def canonical_date(value: str) -> date:
    dates = find_dates(value)
    if len(dates) != 1 or dates[0][0] != 0 or dates[0][1] != len(_ws(value)):
        raise ValueError(f"gold date is not in an accepted form: {value!r}")
    return dates[0][2]


def find_numbers(text: str) -> set[Decimal]:
    """Standalone numbers outside accepted date mentions, after dropping thousands separators,
    currency symbols and the words "USD" and "dollars"."""
    text = _ws(text)
    chars = list(text)
    for start, end, _ in find_dates(text):
        chars[start:end] = " " * (end - start)
    masked = "".join(chars)
    masked = _THOUSANDS_RE.sub("", masked)
    masked = _CURRENCY_RE.sub(" ", masked)
    out = set()
    for tok in _NUMBER_RE.findall(masked):
        try:
            out.add(Decimal(tok))
        except InvalidOperation:
            continue
    return out


def canonical_number(value: str) -> Decimal:
    nums = find_numbers(value)
    if len(nums) != 1:
        raise ValueError(f"gold number is not a single number: {value!r}")
    return next(iter(nums))


def phrase_in(value: str, text: str) -> bool:
    """Case-insensitive whole-phrase match after whitespace normalization."""
    rx = re.compile(r"(?<!\w)" + re.escape(_ws(value)) + r"(?!\w)", re.I)
    return rx.search(_ws(text)) is not None


def field_matches(family: str, answer: str, gold: dict[str, str]) -> dict[str, bool]:
    kinds = FIELD_KINDS[family]
    dates_in_answer = {d for _, _, d in find_dates(answer)}
    numbers_in_answer = find_numbers(answer)
    out = {}
    for key, kind in kinds.items():
        value = gold[key]
        if kind == "phrase":
            out[key] = phrase_in(value, answer)
        elif kind == "date":
            out[key] = canonical_date(value) in dates_in_answer
        else:
            out[key] = canonical_number(value) in numbers_in_answer
    return out


# ---------------------------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------------------------
@dataclass
class QualityResult:
    q_primary: float
    q_secondary: float | None
    answer_available: bool
    detail: dict[str, Any]


def task_quality(family: str, answer: Any, task: dict) -> QualityResult:
    gold = task["gold"]
    if not isinstance(answer, str):
        secondary = None if family in ("F2_CLASSIFICATION", "F3_SUMMARIZATION") else 0.0
        return QualityResult(0.0, secondary, False, {})
    if family == "F1_QA":
        golds = gold["answers"]
        return QualityResult(
            float(qa_containment(answer, golds)),
            qa_max_token_f1(answer, golds),
            True,
            {"containment_char": qa_containment_char(answer, golds)},
        )
    if family == "F2_CLASSIFICATION":
        res = extract_label(answer)
        return QualityResult(
            float(res.prediction == gold["label"]),
            None,
            True,
            {"label_prediction": res.prediction, "label_status": res.status, "labels_found": res.labels_found},
        )
    if family == "F3_SUMMARIZATION":
        return QualityResult(rouge_l_f1(answer, gold["summary"]), None, True, {})
    if family in FIELD_KINDS:
        matches = field_matches(family, answer, gold)
        n = sum(matches.values())
        return QualityResult(n / len(matches), float(n == len(matches)), True, {"fields_matched": matches})
    raise ValueError(f"unknown family {family}")

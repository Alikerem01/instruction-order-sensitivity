"""LENGTH, CARDINALITY, T4 and VERBATIM checks plus the assembled evaluation record."""

import json

import pytest

from src.evaluators import evaluate_output
from src.evaluators.constraints import (
    cardinality_ok,
    evidence_duplicate,
    length_ok,
    lowercase_ok,
    no_comma_ok,
    normalize_verbatim,
    verbatim_ok,
)

INPUT = (
    "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged "
    "terrain such as the Arctic. Engineers called it “the hardest frontier” in 1974."
)

QA_TASK = {
    "task_id": "qa_t01",
    "family": "F1_QA",
    "input_text": INPUT,
    "gold": {"answers": ["the Arctic", "Arctic"]},
}


def prompt(keys=("T1_FORMAT", "T2_LENGTH", "T3_CARDINALITY", "T4_NO_COMMA", "T5_VERBATIM")):
    keys = list(keys)
    return {
        "prompt_id": "qa_t01__P01", "task_id": "qa_t01", "family": "F1_QA", "arm": "order",
        "condition_id": "P01", "instruction_order": keys,
        "instruction_positions": {k: i for i, k in enumerate(keys, 1)},
    }


# ---- answer and evidence types ---------------------------------------------------------------
@pytest.mark.parametrize("answer", [["Arctic"], 42, None, {"a": 1}])
def test_non_string_answer_fails_length_and_t4_and_gives_q0(answer):
    assert not length_ok(answer, 25)
    assert not no_comma_ok(answer)
    assert not lowercase_ok(answer)
    out = json.dumps({"answer": answer, "evidence": ["searching for new ways", "rugged terrain such as"]})
    rec = evaluate_output(out, "eos", QA_TASK, prompt(), "m")
    assert rec["length"] == 0 and rec["t4"] == 0 and rec["q_primary"] == 0.0
    assert rec["q_answer_available"] == 0
    if answer is not None:
        assert "answer_not_string" in rec["error_tags"]


@pytest.mark.parametrize(
    "evidence, ok",
    [
        ([], False),
        (["one item here"], False),
        (["a b c", "d e f", "g h i"], False),
        (["a b c", 3], False),
        (["a b c", ""], False),
        (["a b c", "   "], False),
        ("a b c", False),
        (["a b c", "d e f"], True),
    ],
)
def test_cardinality(evidence, ok):
    assert cardinality_ok(evidence) is ok


def test_missing_evidence_fails_cardinality_and_verbatim():
    rec = evaluate_output('{"answer": "It is the Arctic."}', "eos", QA_TASK, prompt(), "m")
    assert rec["format_strict"] == 0 and rec["evaluable"] == 1
    assert rec["cardinality"] == 0 and rec["verbatim"] == 0
    assert "missing_evidence" in rec["error_tags"]


def test_extra_key_other_constraints_still_evaluated():
    out = json.dumps({"answer": "It is the Arctic.", "evidence": ["searching for new ways", "rugged terrain such as"],
                      "confidence": "high"})
    rec = evaluate_output(out, "eos", QA_TASK, prompt(), "m")
    assert rec["format_strict"] == 0
    assert (rec["length"], rec["cardinality"], rec["t4"], rec["verbatim"]) == (1, 1, 1, 1)
    assert rec["q_primary"] == 1.0 and "extra_keys" in rec["error_tags"]


# ---- VERBATIM -------------------------------------------------------------------------------------
def test_typographic_vs_straight_quotes_pass():
    assert verbatim_ok(['called it "the hardest frontier" in', "such as the Arctic."], INPUT)
    assert verbatim_ok(["called it “the hardest frontier” in"], INPUT.replace("“", '"').replace("”", '"'))


def test_typographic_single_quotes_normalized():
    assert normalize_verbatim("it’s a ‘test’") == "it's a 'test'"


def test_case_only_difference_fails_strict_passes_case_insensitive():
    ev = ["THE EMBARGO LEFT oil companies", "rugged terrain such as"]
    assert not verbatim_ok(ev, INPUT, case_sensitive=True)
    assert verbatim_ok(ev, INPUT, case_sensitive=False)


# R2 (design decision G1): no hidden length minimum; an item needs at least one letter or digit.
def test_two_word_item_passes_but_fails_min3_diagnostic():
    assert verbatim_ok(["the Arctic"], INPUT)
    assert verbatim_ok(["the Arctic", "rugged terrain such as"], INPUT)
    assert not verbatim_ok(["the Arctic"], INPUT, min_tokens=3)
    assert verbatim_ok(["as the Arctic."], INPUT, min_tokens=3)


def test_single_token_item_passes():
    assert verbatim_ok(["Arctic."], INPUT) and verbatim_ok(["1974."], INPUT)


@pytest.mark.parametrize("item", ["", "   ", ".", ", ", "\u201c\u201d", "--"])
def test_items_without_letters_or_digits_fail(item):
    assert not verbatim_ok([item, "rugged terrain such as"], INPUT)
    assert not verbatim_ok([item], INPUT, case_sensitive=False)


def test_min3_diagnostic_in_record():
    out = json.dumps({"answer": "The Arctic.", "evidence": ["the Arctic", "rugged terrain such as"]})
    rec = evaluate_output(out, "eos", QA_TASK, prompt(), "m")
    assert rec["verbatim"] == 1 and rec["verbatim_min3"] == 0 and rec["verbatim_case_insensitive"] == 1


def test_item_from_question_not_in_context_fails():
    # The question is in the TASK block, never in INPUT; matching is against INPUT only.
    question_span = "caused oil companies to increase"
    assert not verbatim_ok([question_span, "rugged terrain such as"], INPUT)


def test_whitespace_differences_pass():
    assert verbatim_ok(["oil  companies\nsearching   for", "rugged\tterrain such"], INPUT)


def test_non_contiguous_span_fails():
    assert not verbatim_ok(["oil companies searching new ways"], INPUT)


def test_duplicate_items_pass_and_are_flagged():
    ev = ["rugged terrain such as", "rugged terrain such as"]
    assert verbatim_ok(ev, INPUT) and cardinality_ok(ev) and evidence_duplicate(ev)
    out = json.dumps({"answer": "The Arctic.", "evidence": ev})
    rec = evaluate_output(out, "eos", QA_TASK, prompt(), "m")
    assert rec["verbatim"] == 1 and rec["evidence_duplicate"] == 1 and "evidence_duplicate" in rec["error_tags"]


def test_verbatim_ignores_item_count():
    assert verbatim_ok(["rugged terrain such as"], INPUT)
    assert verbatim_ok(["rugged terrain such as", "searching for new ways", "even in rugged"], INPUT)


def test_verbatim_non_string_or_empty_list_fails():
    assert not verbatim_ok([], INPUT)
    assert not verbatim_ok(["rugged terrain such as", 7], INPUT)
    assert not verbatim_ok("rugged terrain such as", INPUT)


def test_verbatim_nfc_normalization():
    composed = "Café owners met in the square"
    decomposed = "Café owners met"
    assert verbatim_ok([decomposed], composed)


# ---- LENGTH, T4 -------------------------------------------------------------------------------------
def test_length_boundary():
    assert length_ok(" ".join(["w"] * 25), 25)
    assert not length_ok(" ".join(["w"] * 26), 25)
    assert length_ok(" ".join(["w"] * 20), 20) and not length_ok(" ".join(["w"] * 21), 20)


def test_length_counts_whitespace_tokens():
    assert length_ok("The answer - is: Arctic.", 5) and not length_ok("The answer - is: Arctic.", 4)


def test_no_comma():
    assert no_comma_ok("No commas here.")
    assert not no_comma_ok("Paris, France")
    assert not no_comma_ok("Paris， France")


def test_lowercase():
    assert lowercase_ok("the arctic in 1974")
    assert not lowercase_ok("The arctic")
    assert not lowercase_ok("12345 ...")
    assert not lowercase_ok("")


def test_lowercase_fallback_used_when_prompt_has_t4_lowercase():
    keys = ("T1_FORMAT", "T2_LENGTH_20", "T3_CARDINALITY", "T4_LOWERCASE", "T5_VERBATIM")
    out = json.dumps({"answer": "it is the arctic, in the north", "evidence": ["rugged terrain such as", "even in rugged"]})
    rec = evaluate_output(out, "eos", QA_TASK, prompt(keys), "m")
    assert rec["t4_rule"] == "T4_LOWERCASE" and rec["t4"] == 1 and rec["length_limit"] == 20


# ---- finish reason and cascade ----------------------------------------------------------------------
def test_truncated_output_is_tagged():
    rec = evaluate_output('{"answer": "The Arctic', "length", QA_TASK, prompt(), "m")
    assert "truncated" in rec["error_tags"] and rec["evaluable"] == 0
    assert rec["finish_reason"] == "length"
    assert rec["csr"] == 0.0


def test_fenced_output_decoupled_versus_cascade():
    obj = {"answer": "It is the Arctic.", "evidence": ["searching for new ways", "rugged terrain such as"]}
    rec = evaluate_output("```json\n" + json.dumps(obj) + "\n```", "eos", QA_TASK, prompt(), "m")
    assert rec["parse_rule"] == "fence" and rec["format_strict"] == 0
    assert rec["csr"] == pytest.approx(0.8) and rec["pcr"] == 0
    assert rec["cascade_csr"] == 0.0 and rec["cascade_verbatim"] == 0
    assert "code_fence" in rec["error_tags"] and "leading_text" not in rec["error_tags"]


def test_perfect_output():
    obj = {"answer": "The oil companies looked to the Arctic.", "evidence": ["searching for new ways", "rugged terrain such as the Arctic."]}
    rec = evaluate_output(json.dumps(obj), "eos", QA_TASK, prompt(), "m")
    assert rec["pcr"] == 1 and rec["csr"] == 1.0 and rec["cascade_pcr"] == 1 and rec["error_tags"] == []
    assert rec["positions"] == {"format": 1, "length": 2, "cardinality": 3, "t4": 4, "verbatim": 5}

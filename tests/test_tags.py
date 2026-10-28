"""Error tags (brief §5.8)."""

import json

from src.evaluators.constraints import evidence_duplicate
from src.evaluators.format import lenient_parse
from src.evaluators.tags import error_tags

INPUT = "Alpha beta gamma delta epsilon zeta eta theta."


def tags(output, finish="eos"):
    p = lenient_parse(output)
    ev = p.obj.get("evidence") if p.obj else None
    return error_tags(output, p, INPUT, evidence_duplicate(ev), finish)


def test_clean_output_has_no_tags():
    assert tags(json.dumps({"answer": "a", "evidence": ["alpha beta gamma", "delta epsilon zeta"]})) == [
        "evidence_not_verbatim"]  # case-sensitive: "alpha" != "Alpha"
    assert tags(json.dumps({"answer": "a", "evidence": ["Alpha beta gamma", "delta epsilon zeta"]})) == []


def test_empty_output():
    assert tags("") == ["empty_output"]
    assert tags("   \n") == ["empty_output"]


def test_fence_only():
    out = "```json\n" + json.dumps({"answer": "a", "evidence": ["Alpha beta gamma", "zeta eta theta."]}) + "\n```"
    assert tags(out) == ["code_fence"]


def test_leading_and_trailing_text_with_fence():
    out = "Here:\n```json\n" + json.dumps({"answer": "a", "evidence": ["Alpha beta gamma", "zeta eta theta."]}) + "\n```\nDone."
    assert tags(out) == ["code_fence", "leading_text", "trailing_text"]


def test_invalid_json():
    assert tags("I cannot answer that.") == ["invalid_json"]
    assert tags('{"answer": "a", "evidence": ["x', finish="length") == ["invalid_json", "truncated"]


def test_structural_tags():
    out = '{"answer": 3, "answer": 4, "extra": 1}'
    assert tags(out) == ["duplicate_keys", "extra_keys", "missing_evidence", "answer_not_string"]
    assert tags('{"evidence": "Alpha beta gamma"}') == ["missing_answer", "evidence_not_list"]


def test_evidence_counts():
    assert "evidence_count_0" in tags('{"answer": "a", "evidence": []}')
    assert "evidence_count_1" in tags('{"answer": "a", "evidence": ["Alpha beta gamma"]}')
    t = tags('{"answer": "a", "evidence": ["Alpha beta gamma", "Alpha beta gamma", "zeta eta theta."]}')
    assert "evidence_count_3plus" in t and "evidence_duplicate" in t and "evidence_not_verbatim" not in t


def test_braces_in_code_fence_inside_string_do_not_tag_fence():
    out = json.dumps({"answer": "use ``` here", "evidence": ["Alpha beta gamma", "zeta eta theta."]})
    assert "code_fence" not in tags(out)

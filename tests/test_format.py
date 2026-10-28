"""Strict FORMAT and the lenient parse (brief §5.8; implementation specification §6.4)."""

from src.evaluators.format import format_strict, lenient_parse

VALID = '{"answer": "Paris is the capital.", "evidence": ["Paris is the capital of France", "the capital of France is Paris"]}'


def test_valid_json_passes_strict():
    assert format_strict(VALID)
    p = lenient_parse(VALID)
    assert p.rule == "strict" and p.obj["answer"] == "Paris is the capital."


def test_surrounding_whitespace_still_passes_strict():
    assert format_strict("\n\n  " + VALID + "  \n\t")
    assert lenient_parse("  " + VALID + "\n").rule == "strict"


def test_json_fence_fails_strict_and_parses_with_fence():
    out = "```json\n" + VALID + "\n```"
    assert not format_strict(out)
    p = lenient_parse(out)
    assert p.rule == "fence" and p.obj["answer"] == "Paris is the capital."


def test_plain_fence_fails_strict_and_parses_with_fence():
    out = "```\n" + VALID + "\n```"
    assert not format_strict(out)
    assert lenient_parse(out).rule == "fence"


def test_uppercase_json_fence_tag_parses_with_fence():
    assert lenient_parse("```JSON\n" + VALID + "\n```").rule == "fence"


def test_prose_before_fails_strict_and_parses_first_object():
    out = "Here is the JSON you asked for:\n" + VALID
    assert not format_strict(out)
    p = lenient_parse(out)
    assert p.rule == "first_object" and p.obj["evidence"][0].startswith("Paris")


def test_prose_after_fails_strict_and_parses_first_object():
    out = VALID + "\nI hope this helps!"
    assert not format_strict(out)
    assert lenient_parse(out).rule == "first_object"


def test_prose_and_fence_parses_first_object():
    out = "Sure! Here it is:\n```json\n" + VALID + "\n```\nLet me know."
    assert not format_strict(out)
    assert lenient_parse(out).rule == "first_object"


def test_braces_inside_string_values():
    out = 'Result: {"answer": "use {x} and {y}", "evidence": ["a {b} c d", "e f g"]} done'
    p = lenient_parse(out)
    assert p.rule == "first_object" and p.obj["answer"] == "use {x} and {y}"


def test_braces_in_prose_before_the_object_are_skipped():
    out = 'The set {a, b} is irrelevant. {"answer": "x", "evidence": []}'
    p = lenient_parse(out)
    assert p.rule == "first_object" and p.obj == {"answer": "x", "evidence": []}


def test_two_objects_first_is_used():
    out = '{"answer": "first", "evidence": []}\n{"answer": "second", "evidence": []}'
    assert not format_strict(out)
    p = lenient_parse(out)
    assert p.rule == "first_object" and p.obj["answer"] == "first"


def test_single_quoted_pseudo_json_is_not_evaluable():
    out = "{'answer': 'Paris', 'evidence': ['a b c', 'd e f']}"
    assert not format_strict(out)
    p = lenient_parse(out)
    assert p.rule == "none" and not p.evaluable and p.obj is None


def test_duplicate_keys_fail_strict():
    out = '{"answer": "a", "answer": "b", "evidence": ["x y z", "u v w"]}'
    assert not format_strict(out)
    p = lenient_parse(out)
    assert p.evaluable and p.duplicate_keys and p.obj["answer"] == "b"


def test_nested_duplicate_keys_fail_strict():
    out = '{"answer": "a", "evidence": [{"k": 1, "k": 2}]}'
    assert not format_strict(out)


def test_extra_key_fails_strict_but_is_evaluable():
    out = '{"answer": "a", "evidence": ["x y z", "u v w"], "note": "n"}'
    assert not format_strict(out)
    p = lenient_parse(out)
    assert p.rule == "strict" and p.evaluable and p.obj["answer"] == "a"


def test_missing_key_fails_strict():
    assert not format_strict('{"answer": "a"}')


def test_non_object_json_fails_strict():
    assert not format_strict('["answer", "evidence"]')
    assert not format_strict('"just a string"')


def test_empty_output():
    assert not format_strict("")
    assert lenient_parse("   ").rule == "none"


def test_truncated_json_is_not_evaluable():
    out = '{"answer": "Paris is", "evidence": ["Paris is the capital'
    assert not format_strict(out)
    assert lenient_parse(out).rule == "none"


def test_raw_newline_inside_string_is_invalid_json():
    out = '{"answer": "line one\nline two", "evidence": ["a b c", "d e f"]}'
    assert not format_strict(out)
    assert lenient_parse(out).rule == "none"

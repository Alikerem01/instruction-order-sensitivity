"""Williams orders, prompt rendering, format variants and canonicalize()."""

import pytest

from src.common import all_instruction_strings, load_prompt_strings
from src.orders import ORDERS, e2_informative_positions, order_slots, verify_orders
from src.prompt_builder import (
    FORMAT_VARIANTS,
    VARIANT_IDS,
    canonicalize,
    instruction_lines_removed,
    parse_user_prompt,
    render_canonical,
    render_user_prompt,
)

PS = load_prompt_strings()
STRINGS = all_instruction_strings(PS)
INSTR = [STRINGS[k] for k in ("T1_FORMAT", "T2_LENGTH", "T3_CARDINALITY", "T4_NO_COMMA", "T5_VERBATIM")]
TASK = PS["task_directives"]["F1_QA"].replace("{question}", "Who proved that air is necessary for combustion?")
INPUT = "Robert Boyle proved that air is necessary for combustion.\nA second line follows here."


def test_verify_orders_passes():
    assert verify_orders()["n_orders"] == 10


def test_orders_are_hard_coded_as_in_the_brief():
    assert ORDERS == {"P01": "ABCDE", "P02": "BDAEC", "P03": "DEBCA", "P04": "ECDAB", "P05": "CAEBD",
                      "P06": "EDCBA", "P07": "CEADB", "P08": "ACBED", "P09": "BADCE", "P10": "DBEAC"}
    assert order_slots("P02") == ["T2", "T4", "T1", "T5", "T3"]


@pytest.mark.parametrize(
    "bad",
    [
        {**ORDERS, "P10": "DBEAA"},                     # not a permutation
        {**ORDERS, "P10": "BDEAC"},                     # breaks position balance
        {k: v for k, v in ORDERS.items() if k != "P10"},  # wrong number of orders
    ],
)
def test_verify_orders_detects_violations(bad):
    with pytest.raises(ValueError):
        verify_orders(bad)


def test_cyclic_orders_of_the_original_plan_fail_adjacency_balance():
    cyclic = {"P01": "ABCDE", "P02": "BCDEA", "P03": "CDEAB", "P04": "DEABC", "P05": "EABCD",
              "P06": "EDCBA", "P07": "AEDCB", "P08": "BAEDC", "P09": "CBAED", "P10": "DCBAE"}
    with pytest.raises(ValueError, match="adjacency"):
        verify_orders(cyclic)


def test_canonical_template_is_exact():
    expected = (
        "INSTRUCTIONS:\n- " + "\n- ".join(INSTR) + "\n\nTASK:\n" + TASK + "\n\nINPUT:\n" + INPUT
    )
    assert render_canonical(INSTR, TASK, INPUT) == expected
    assert not expected.endswith("\n")


def test_variant_renderings():
    v = {vid: render_user_prompt(INSTR, TASK, INPUT, spec) for vid, spec in FORMAT_VARIANTS.items()}
    assert v["V02"].startswith("INSTRUCTIONS:\n* Return only")
    assert v["V03"].startswith("INSTRUCTIONS:\n• Return only")
    assert v["V04"].startswith("Instructions:\n- ") and "\n\nTask:\n" in v["V04"] and "\n\nInput:\n" in v["V04"]
    assert v["V05"].startswith("instructions:\n- ") and "\n\ntask:\n" in v["V05"] and "\n\ninput:\n" in v["V05"]
    assert "\n\n\nTASK:\n" in v["V06"] and "\n\n\nINPUT:\n" in v["V06"]
    assert v["V07"].count("\n\n- ") == 4
    assert v["V08"].startswith("INSTRUCTIONS:\n  - Return only")
    assert v["V09"].startswith("INSTRUCTIONS\n- ") and "\n\nTASK\n" in v["V09"] and "\n\nINPUT\n" in v["V09"]
    assert v["V10"].startswith("Instructions:\n* Return only") and "\n\nTask:\n" in v["V10"]
    assert len(set(v.values())) == 10
    for text in v.values():
        assert all(line == line.rstrip() for line in text.split("\n"))


@pytest.mark.parametrize("vid", VARIANT_IDS)
def test_canonicalize_maps_every_variant_to_v01(vid):
    text = render_user_prompt(INSTR, TASK, INPUT, FORMAT_VARIANTS[vid])
    assert canonicalize(text) == render_canonical(INSTR, TASK, INPUT)


def test_parse_keeps_input_verbatim_even_with_header_like_lines():
    tricky_input = "Line one.\n\nTASK:\nnot a header inside input\n- not a bullet"
    text = render_user_prompt(INSTR, TASK, tricky_input, FORMAT_VARIANTS["V06"])
    parsed = parse_user_prompt(text)
    assert parsed.input == tricky_input and parsed.task == TASK and parsed.instructions == INSTR


def test_instruction_lines_removed_is_order_invariant():
    a = render_canonical(INSTR, TASK, INPUT)
    b = render_canonical(list(reversed(INSTR)), TASK, INPUT)
    assert a != b and instruction_lines_removed(a) == instruction_lines_removed(b)


def test_render_rejects_untrimmed_parts():
    with pytest.raises(ValueError):
        render_canonical(INSTR, TASK + " ", INPUT)


def test_e2_informative_positions_match_decision_d03():
    """D03 §3: LENGTH and CARDINALITY 2-4, T4 and VERBATIM 3 only; each precedes FORMAT in 5 of 10 orders."""
    assert e2_informative_positions() == {"T2": [2, 3, 4], "T3": [2, 3, 4], "T4": [3], "T5": [3]}
    for letter in "BCDE":
        assert sum(seq.index(letter) < seq.index("A") for seq in ORDERS.values()) == 5

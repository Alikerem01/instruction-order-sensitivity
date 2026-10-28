"""Golden-output cases (design decision G1, R6): hand-written outputs and hand-written expected values.

Each case is one model output for the prompt group of ``prompt_id`` (prompts.jsonl; tasks are the pilot tasks in
tasks.jsonl). ``expected`` holds the five constraint flags, the parse rule, the diagnostics, task quality and
the error tags, all derived by hand from the rules in src/evaluators/README.md; the derivation of every
non-obvious value is in the comment above the case. CSR, PCR and the cascade values are checked as the mean /
conjunction of the hand-written flags. Fields not listed in ``expected`` are not asserted.
"""

from __future__ import annotations

ALL_PASS = {"format_strict": 1, "evaluable": 1, "length": 1, "cardinality": 1, "t4": 1, "verbatim": 1,
            "verbatim_case_insensitive": 1, "verbatim_min3": 1, "evidence_duplicate": 0}
NOTHING = {"format_strict": 0, "parse_rule": "none", "evaluable": 0, "length": 0, "cardinality": 0, "t4": 0,
           "verbatim": 0, "verbatim_case_insensitive": 0, "verbatim_min3": 0, "evidence_duplicate": 0,
           "q_primary": 0.0, "q_answer_available": 0}


def exp(base: dict, **kw) -> dict:
    return {**base, **kw}


CASES = [
    # ---------------- F1 qa_p01 (gold "Arctic", "the Arctic") ----------------
    # Strictly valid and correct; the group also contains qa_p01__V01 (identical text), so this one output is
    # evaluated for both ids. Answer: 13 words. Token F1: answer tokens (SQuAD) = 12, 1 shared -> 2/13.
    {"case_id": "c01_f1_correct_shared_p01_v01", "prompt_id": "qa_p01__P01", "finish_reason": "eos",
     "output_text": '{"answer": "Oil companies searched for new supplies in rugged terrain such as the Arctic.", '
                    '"evidence": ["The embargo left oil companies searching for new ways to increase oil supplies", '
                    '"even in rugged terrain such as the Arctic."]}',
     "expected": exp(ALL_PASS, parse_rule="strict", q_primary=1.0, q_secondary=2 / 13, q_answer_available=1,
                     containment_char=1, error_tags=[])},
    # Fenced output: FORMAT 0, the other four constraints from the fence content. Token F1: 5 tokens -> 1/3.
    {"case_id": "c02_fence", "prompt_id": "qa_p01__P02", "finish_reason": "eos",
     "output_text": '```json\n{"answer": "The oil companies looked to the Arctic.", "evidence": '
                    '["increase oil supplies, even in rugged terrain", "such as the Arctic."]}\n```',
     "expected": exp(ALL_PASS, format_strict=0, parse_rule="fence", q_primary=1.0, q_secondary=1 / 3,
                     q_answer_available=1, containment_char=1, error_tags=["code_fence"])},
    # Prose before the object. Token F1: 5 tokens ("rugged terrain such as arctic") -> 1/3.
    {"case_id": "c03_first_object_leading_text", "prompt_id": "qa_p01__P03", "finish_reason": "eos",
     "output_text": 'Here is the JSON object you requested:\n{"answer": "Rugged terrain such as the Arctic.", '
                    '"evidence": ["searching for new ways to increase oil supplies", '
                    '"rugged terrain such as the Arctic."]}',
     "expected": exp(ALL_PASS, format_strict=0, parse_rule="first_object", q_primary=1.0, q_secondary=1 / 3,
                     q_answer_available=1, containment_char=1, error_tags=["leading_text"])},
    # Prose after the object. Token F1: 6 tokens ("in rugged terrain such as arctic") -> 2/7.
    {"case_id": "c04_first_object_trailing_text", "prompt_id": "qa_p01__P04", "finish_reason": "eos",
     "output_text": '{"answer": "In rugged terrain such as the Arctic.", "evidence": '
                    '["even in rugged terrain such as the Arctic.", '
                    '"The embargo left oil companies searching for new ways"]}\nThis answer is based only on the passage.',
     "expected": exp(ALL_PASS, format_strict=0, parse_rule="first_object", q_primary=1.0, q_secondary=2 / 7,
                     q_answer_available=1, containment_char=1, error_tags=["trailing_text"])},
    # No JSON at all: not evaluable; quality 0 because there is no answer string.
    {"case_id": "c05_none", "prompt_id": "qa_p01__P05", "finish_reason": "eos",
     "output_text": "The oil companies increased their supplies in the Arctic.",
     "expected": exp(NOTHING, q_secondary=0.0, error_tags=["invalid_json"])},
    # Cut off at the 512-token limit in the middle of the evidence list.
    {"case_id": "c06_truncated", "prompt_id": "qa_p01__P06", "finish_reason": "length", "n_output_tokens": 512,
     "output_text": '{"answer": "The oil companies searched for supplies in rugged terrain such as the Arctic", '
                    '"evidence": ["The embargo left oil companies searching for new ways to increase',
     "expected": exp(NOTHING, q_secondary=0.0, error_tags=["invalid_json", "truncated"])},

    # ---------------- F1 qa_p02 (gold "Robert Boyle", "Boyle") ----------------
    # Duplicate "answer" key: FORMAT 0; json.loads keeps the last value ("Robert Boyle proved it.").
    # Token F1: [robert boyle proved it] vs [robert boyle] -> P 1/2, R 1 -> 2/3.
    {"case_id": "c07_duplicate_keys", "prompt_id": "qa_p02__P01", "finish_reason": "eos",
     "output_text": '{"answer": "John Mayow proved it.", "answer": "Robert Boyle proved it.", "evidence": '
                    '["Robert Boyle proved that air is necessary for combustion.", "In the late 17th century"]}',
     "expected": exp(ALL_PASS, format_strict=0, parse_rule="strict", q_primary=1.0, q_secondary=2 / 3,
                     q_answer_available=1, containment_char=1, error_tags=["duplicate_keys"])},
    # Extra key: FORMAT 0, everything else evaluated and passing.
    {"case_id": "c08_extra_key", "prompt_id": "qa_p02__P02", "finish_reason": "eos",
     "output_text": '{"answer": "Robert Boyle proved it.", "evidence": '
                    '["Robert Boyle proved that air is necessary for combustion.", "In the late 17th century"], '
                    '"confidence": "high"}',
     "expected": exp(ALL_PASS, format_strict=0, parse_rule="strict", q_primary=1.0, q_secondary=2 / 3,
                     q_answer_available=1, containment_char=1, error_tags=["extra_keys"])},
    # One evidence item: CARDINALITY 0, VERBATIM 1 (the item count is CARDINALITY's job).
    # Token F1: 8 answer tokens, 2 shared with "Robert Boyle" -> P 1/4, R 1 -> 0.4.
    {"case_id": "c09_evidence_one_item", "prompt_id": "qa_p02__P03", "finish_reason": "eos",
     "output_text": '{"answer": "Robert Boyle proved it in the late 17th century.", "evidence": '
                    '["Robert Boyle proved that air is necessary for combustion."]}',
     "expected": exp(ALL_PASS, cardinality=0, parse_rule="strict", q_primary=1.0, q_secondary=0.4,
                     q_answer_available=1, containment_char=1, error_tags=["evidence_count_1"])},
    # Three evidence items, all verbatim. Token F1 against "Robert Boyle" = 1.
    {"case_id": "c10_evidence_three_items", "prompt_id": "qa_p02__P04", "finish_reason": "eos",
     "output_text": '{"answer": "Robert Boyle", "evidence": ["Robert Boyle proved that air is necessary for '
                    'combustion.", "English chemist John Mayow", "refined this work"]}',
     "expected": exp(ALL_PASS, cardinality=0, parse_rule="strict", q_primary=1.0, q_secondary=1.0,
                     q_answer_available=1, containment_char=1, error_tags=["evidence_count_3plus"])},
    # R1 and R2. Curly possessive "Boyle’s": the primary metric straightens the quote and drops "'s" -> token
    # "boyle" -> 1. The official token F1 keeps "boyle’s" (not ASCII punctuation) -> 0. The character diagnostic
    # finds "boyle" inside "boyle’s" -> 1. Evidence "Robert Boyle" has 2 tokens: VERBATIM 1, verbatim_min3 0.
    {"case_id": "c11_possessive_and_two_token_evidence", "prompt_id": "qa_p02__P05", "finish_reason": "eos",
     "output_text": '{"answer": "It was Boyle’s experiment.", "evidence": ["Robert Boyle", '
                    '"necessary for combustion."]}',
     "expected": exp(ALL_PASS, verbatim_min3=0, parse_rule="strict", q_primary=1.0, q_secondary=0.0,
                     q_answer_available=1, containment_char=1, error_tags=[])},
    # Empty output.
    {"case_id": "c12_empty_output", "prompt_id": "qa_p02__P06", "finish_reason": "eos", "n_output_tokens": 1,
     "output_text": "",
     "expected": exp(NOTHING, q_secondary=0.0, error_tags=["empty_output"])},

    # ---------------- F2 cls_p01 (gold World) and cls_p02 (gold Business) ----------------
    {"case_id": "c13_f2_correct", "prompt_id": "cls_p01__P01", "finish_reason": "eos",
     "output_text": '{"answer": "The article belongs to the World category.", "evidence": ["Japan has confirmed '
                    'that the headless body found in Baghdad", "An armed group in Iraq had on Tuesday threatened"]}',
     "expected": exp(ALL_PASS, parse_rule="strict", q_primary=1.0, q_secondary=None, q_answer_available=1,
                     label_status="single", error_tags=[])},
    # NO_COMMA failure (comma after "Iraq"); the label is still World.
    {"case_id": "c14_no_comma_failure", "prompt_id": "cls_p01__V02", "finish_reason": "eos",
     "output_text": '{"answer": "Iraq, Japan and Baghdad make this a World story.", "evidence": ["Japan confirms '
                    'captive in Iraq beheaded", "pulled its troops out of Iraq."]}',
     "expected": exp(ALL_PASS, t4=0, parse_rule="strict", q_primary=1.0, q_secondary=None, q_answer_available=1,
                     label_status="single", error_tags=[])},
    # Ambiguous: Business and World, no cue ("be" is not a cue) -> unresolved -> 0.
    {"case_id": "c15_f2_ambiguous", "prompt_id": "cls_p02__P01", "finish_reason": "eos",
     "output_text": '{"answer": "It could be Business or World news.", "evidence": ["Walt Disney Co. chief '
                    'executive Michael D. Eisner", "their corporate partnership was dissolving"]}',
     "expected": exp(ALL_PASS, parse_rule="strict", q_primary=0.0, q_secondary=None, q_answer_available=1,
                     label_status="unresolved", error_tags=[])},
    # 26 words: LENGTH 0. Only "business" matches a label -> Business.
    {"case_id": "c16_26_word_answer", "prompt_id": "cls_p02__P02", "finish_reason": "eos",
     "output_text": '{"answer": "The article reports on the Disney executives Michael Eisner and Michael Ovitz and their '
                    'failing corporate partnership so this news article belongs to the Business category.", '
                    '"evidence": ["Disney President Michael S. Ovitz appeared on", "their corporate partnership was '
                    'dissolving into an acrimonious disaster."]}',
     "expected": exp(ALL_PASS, length=0, parse_rule="strict", q_primary=1.0, q_secondary=None,
                     q_answer_available=1, label_status="single", error_tags=[])},
    # R3: "high-tech" now matches the Sci/Tech synonym "tech"; "Business" follows the cue "belongs to" and
    # "tech" follows no cue -> Business (cue_resolved).
    {"case_id": "c17_f2_tech_synonym_cue", "prompt_id": "cls_p02__P03", "finish_reason": "eos",
     "output_text": '{"answer": "An article about a high-tech firm\'s profits belongs to Business.", "evidence": '
                    '["Eisner Continues Defense of Hiring", "Disney President Michael S. Ovitz"]}',
     "expected": exp(ALL_PASS, parse_rule="strict", q_primary=1.0, q_secondary=None, q_answer_available=1,
                     label_status="cue_resolved", error_tags=[])},

    # ---------------- F3 sum_p01, sum_p02 ----------------
    # The answer is the reference summary itself (22 words, no comma) -> ROUGE-L F1 = 1.
    {"case_id": "c18_f3_correct", "prompt_id": "sum_p01__P01", "finish_reason": "eos",
     "output_text": '{"answer": "Torquay United manager Kevin Nicholson says his side\'s attitude in training ahead of '
                    'their loss to Tranmere Rovers contributed to the result.", "evidence": ["Nicholson was unhappy '
                    'with the attitude afterwards.", "Torquay have not beaten Tranmere since 1998"]}',
     "expected": exp(ALL_PASS, parse_rule="strict", q_primary=1.0, q_secondary=None, q_answer_available=1,
                     error_tags=[])},
    # Evidence with typographic quotes and a curly apostrophe; the INPUT has straight ones -> VERBATIM 1.
    {"case_id": "c19_typographic_quotes", "prompt_id": "sum_p01__P02", "finish_reason": "eos",
     "output_text": '{"answer": "Torquay United manager Kevin Nicholson says his side\'s attitude in training ahead of '
                    'their loss to Tranmere Rovers contributed to the result.", "evidence": ["“We came in after '
                    'beating Solihull and too many of the team looked like they’d made it,” Nicholson told BBC '
                    'Devon.", "Torquay have not beaten Tranmere since 1998"]}',
     "expected": exp(ALL_PASS, parse_rule="strict", q_primary=1.0, q_secondary=None, q_answer_available=1,
                     error_tags=[])},
    # Paraphrased evidence -> VERBATIM 0. ROUGE-L: LCS 8 of 9 answer tokens and 10 reference tokens
    # -> P 8/9, R 4/5 -> F1 = 16/19.
    {"case_id": "c20_evidence_not_verbatim", "prompt_id": "sum_p02__P01", "finish_reason": "eos",
     "output_text": '{"answer": "Calvapilosa is a prehistoric relative of modern sea slugs.", "evidence": '
                    '["Researchers found fossils in Morocco", "The creature was four inches long"]}',
     "expected": exp(ALL_PASS, verbatim=0, verbatim_case_insensitive=0, verbatim_min3=0, parse_rule="strict",
                     q_primary=16 / 19, q_secondary=None, q_answer_available=1, error_tags=["evidence_not_verbatim"])},

    # ---------------- F4 ext_p01, ext_p02 ----------------
    {"case_id": "c21_f4_correct", "prompt_id": "ext_p01__P01", "finish_reason": "eos",
     "output_text": '{"answer": "Priya Nair from Willow Creek Pharma visited Rotterdam on 4 January 2025 and 299 '
                    'samples were tested.", "evidence": ["Priya Nair from Willow Creek Pharma visited the Rotterdam '
                    'facility.", "299 samples were tested before the team closed the report."]}',
     "expected": exp(ALL_PASS, parse_rule="strict", q_primary=1.0, q_secondary=1.0, q_answer_available=1,
                     fields_matched={"person": True, "organization": True, "city": True, "date": True,
                                     "amount": True}, error_tags=[])},
    # Alternative date form "Oct 15 2025" for gold "15 October 2025".
    {"case_id": "c22_f4_alternative_date", "prompt_id": "ext_p02__P01", "finish_reason": "eos",
     "output_text": '{"answer": "Tomas Novak of Cedar Grove Health reported 48 contracts signed in Tampere on Oct 15 '
                    '2025.", "evidence": ["Tomas Novak of Cedar Grove Health reported that 48 contracts were signed", '
                    '"at the Tampere site on 15 October 2025."]}',
     "expected": exp(ALL_PASS, parse_rule="strict", q_primary=1.0, q_secondary=1.0, q_answer_available=1,
                     fields_matched={"person": True, "organization": True, "city": True, "date": True,
                                     "amount": True}, error_tags=[])},

    # ---------------- F5 trf_p01, trf_p02 ----------------
    # 23 words; evidence "Project: Meridian." has 2 tokens -> VERBATIM 1 (R2), verbatim_min3 0.
    {"case_id": "c23_f5_correct", "prompt_id": "trf_p01__P01", "finish_reason": "eos",
     "output_text": '{"answer": "Project Meridian owned by Marcus Hale is on track with a deadline of 12 May 2025 and an '
                    'approved budget of 733000 USD.", "evidence": ["Project: Meridian.", "Approved budget: 733000 '
                    'USD."]}',
     "expected": exp(ALL_PASS, verbatim_min3=0, parse_rule="strict", q_primary=1.0, q_secondary=1.0,
                     q_answer_available=1, fields_matched={"project": True, "owner": True, "status": True,
                                                           "deadline": True, "budget": True}, error_tags=[])},
    # Budget written with a thousands separator: the field matches (840,500 -> 840500) but NO_COMMA fails.
    {"case_id": "c24_f5_thousands_separator", "prompt_id": "trf_p02__P01", "finish_reason": "eos",
     "output_text": '{"answer": "Project Nimbus led by Diego Alvarez is on track for 21 July 2027 with a budget of '
                    '840,500 USD.", "evidence": ["Owner: Diego Alvarez.", "Deadline: 21 July 2027."]}',
     "expected": exp(ALL_PASS, t4=0, parse_rule="strict", q_primary=1.0, q_secondary=1.0, q_answer_available=1,
                     fields_matched={"project": True, "owner": True, "status": True, "deadline": True,
                                     "budget": True}, error_tags=[])},
]

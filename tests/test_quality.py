"""Task-quality rules: F1 containment, F2 label extraction, F3 ROUGE-L, F4/F5 fields (brief §5.8)."""

from datetime import date
from decimal import Decimal

import pytest

from src.evaluators.quality import (
    canonical_date,
    extract_label,
    field_matches,
    find_numbers,
    qa_containment,
    qa_containment_char,
    qa_max_token_f1,
    qa_tokens,
    rouge_l_f1,
    squad_normalize,
    task_quality,
)


# ---- F1 --------------------------------------------------------------------------------------------
def test_squad_normalization():
    assert squad_normalize("The  Anglo-Saxons!") == "anglosaxons"
    assert squad_normalize("an apple, a pear and THE fig.") == "apple pear and fig"


# R1 (design decision G1): whole-token containment is the primary F1 metric.
@pytest.mark.parametrize(
    "gold, answer, expected",
    [
        ("Arctic", "Antarctic", 0),
        ("4", "1994", 0),
        ("1,000", "1000", 1),
        ("1000", "1,000", 1),
        ("Beyonc\u00e9", "Beyonc\u00e9's", 1),
        ("Beyonc\u00e9", "Beyonc\u00e9\u2019s", 1),
        ("Normans", "The Normans", 1),
        ("Battle of Hastings", "\u2026 at the Battle of Hastings in 1066", 1),
        ("Hastings", "Hastingsville", 0),
    ],
)
def test_r1_whole_token_containment(gold, answer, expected):
    assert qa_containment(answer, [gold]) == expected


def test_r1_normalization_steps():
    decomposed = "Beyonce\u0301\u2019S album"  # NFC, curly apostrophe, possessive in upper case
    assert qa_tokens(decomposed) == ["beyonc\u00e9", "album"]
    assert qa_tokens("The \u201cAnglo-Saxons\u201d ruled.") == ["anglosaxons", "ruled"]
    assert qa_containment("Before the Normans, Anglo-Saxons ruled.", ["the Anglo-Saxons", "Anglo-Saxons"]) == 1
    assert qa_containment("The Anglo Saxons ruled.", ["Anglo-Saxons"]) == 0  # hyphen removed: one token, not two
    assert qa_containment("It was a $216000 payment.", ["$216,000"]) == 1
    assert qa_containment("anything", [""]) == 0


def test_containment_char_diagnostic_is_the_brief_rule():
    assert qa_containment_char("The Antarctic.", ["the Arctic"]) == 1
    assert qa_containment_char("In 1994.", ["4"]) == 1
    assert qa_containment_char("Hastingsville", ["Hastings"]) == 1
    assert qa_containment_char("The Normans", ["Normans"]) == 1


def test_f1_quality_detail_reports_both():
    task = {"family": "F1_QA", "gold": {"answers": ["Arctic", "the Arctic"]}}
    q = task_quality("F1_QA", "The Antarctic.", task)
    assert q.q_primary == 0.0 and q.detail == {"containment_char": 1}


def test_token_f1():
    assert qa_max_token_f1("the Arctic", ["Arctic"]) == pytest.approx(1.0)
    assert qa_max_token_f1("rugged Arctic terrain", ["the Arctic"]) == pytest.approx(0.5)
    assert qa_max_token_f1("nothing", ["Arctic"]) == 0.0


# ---- F2 --------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "answer, expected, status",
    [
        ("This article belongs to the Sports category.", "Sports", "single"),
        ("The article about the World Cup belongs to the Sports category.", "Sports", "cue_resolved"),
        ("This World Cup report is classified as Sports.", "Sports", "cue_resolved"),
        ("The category is World.", "World", "single"),
        ("Category: business", "Business", "single"),
        ("It is a sport story.", "Sports", "single"),
        ("Sci/Tech", "Sci/Tech", "single"),
        ("This is sci-tech news.", "Sci/Tech", "single"),
        ("This is SciTech news.", "Sci/Tech", "single"),
        ("This is sci tech news.", "Sci/Tech", "single"),
        ("The topic is science/technology.", "Sci/Tech", "single"),
        ("The topic is Science and Technology.", "Sci/Tech", "single"),
        ("The topic is science & technology.", "Sci/Tech", "single"),
        ("The article falls under Business although analysts around the world react.", "Business", "cue_resolved"),
        # R3 (design decision G1): technology, tech and science are Sci/Tech synonyms (whole words).
        ("It belongs to the Technology category.", "Sci/Tech", "single"),
        ("A tech story.", "Sci/Tech", "single"),
        ("This is science news.", "Sci/Tech", "single"),
        ("An article about a high-tech firm's profits belongs to Business.", "Business", "cue_resolved"),
    ],
)
def test_label_extraction(answer, expected, status):
    res = extract_label(answer)
    assert res.prediction == expected and res.status == status


@pytest.mark.parametrize(
    "answer",
    [
        "It could be World or Sports.",                       # several labels, no cue ("be" is not a cue)
        "The category is World and also is Sports.",          # two labels each follow a cue
        "It falls under Business although world markets react.",  # "world" is the 3rd token after "under"
        "World and Business news.",                           # no cue at all
        "It could be Business or Technology.",                # R3 synonym, no cue
    ],
)
def test_ambiguous_multilabel_answers_are_unresolved(answer):
    res = extract_label(answer)
    assert res.prediction is None and res.status == "unresolved"


def test_ambiguous_multilabel_scores_zero():
    task = {"family": "F2_CLASSIFICATION", "gold": {"label": "World"}}
    q = task_quality("F2_CLASSIFICATION", "World and Business news.", task)
    assert q.q_primary == 0.0 and q.detail["label_status"] == "unresolved"


def test_no_label_scores_zero():
    task = {"family": "F2_CLASSIFICATION", "gold": {"label": "Sci/Tech"}}
    q = task_quality("F2_CLASSIFICATION", "This is about computers and the internet.", task)
    assert q.q_primary == 0.0 and q.detail["label_status"] == "none"


def test_label_is_whole_word():
    assert extract_label("A worldwide sporting businessman.").status == "none"
    assert extract_label("Biotechnology and neuroscience in technical colleges.").status == "none"


def test_r3_ambiguous_answer_scores_zero():
    task = {"family": "F2_CLASSIFICATION", "gold": {"label": "Business"}}
    q = task_quality("F2_CLASSIFICATION", "It could be Business or Technology.", task)
    assert q.q_primary == 0.0 and q.detail["label_status"] == "unresolved"


# ---- F3 --------------------------------------------------------------------------------------------
def test_rouge_l():
    ref = "The council has approved plans for a new bridge."
    assert rouge_l_f1(ref, ref) == pytest.approx(1.0)
    assert 0.0 < rouge_l_f1("Plans for a bridge were approved.", ref) < 1.0
    assert rouge_l_f1("", ref) == 0.0


# ---- F4/F5 -----------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    ["14 March 2025", "March 14 2025", "March 14, 2025", "14 Mar 2025", "Mar 14 2025", "2025-03-14", "14/03/2025",
     "14 MARCH 2025", "on march 14, 2025."],
)
def test_every_accepted_date_form(text):
    gold = {"person": "Daniel Reed", "organization": "Northbridge Labs", "city": "Leeds", "date": "14 March 2025",
            "amount": "47"}
    answer = f"Daniel Reed of Northbridge Labs inspected 47 devices in Leeds on {text}"
    assert field_matches("F4_EXTRACTION", answer, gold)["date"] is True


@pytest.mark.parametrize("text", ["14th March 2025", "03/14/2025", "March 2025", "14 March 25", "Mar. 14 2025"])
def test_unaccepted_date_forms(text):
    gold = {"person": "Daniel Reed", "organization": "Northbridge Labs", "city": "Leeds", "date": "14 March 2025",
            "amount": "47"}
    assert field_matches("F4_EXTRACTION", f"Seen on {text}.", gold)["date"] is False


def test_may_is_both_a_month_name_and_an_abbreviation():
    # Regression found by the golden-output test (R6): "12 May 2025" matched two patterns and the gold
    # date could not be canonicalized.
    assert canonical_date("12 May 2025") == date(2025, 5, 12)
    gold = {"project": "Meridian", "owner": "Marcus Hale", "status": "on track", "deadline": "12 May 2025",
            "budget": "733000 USD"}
    for form in ("12 May 2025", "May 12 2025", "May 12, 2025", "2025-05-12", "12/05/2025"):
        assert field_matches("F5_TRANSFORMATION", f"Due {form}.", gold)["deadline"] is True


def test_canonical_date():
    assert canonical_date("14 March 2025") == date(2025, 3, 14)
    with pytest.raises(ValueError):
        canonical_date("sometime in March")


@pytest.mark.parametrize("answer", ["$120,000", "120000 USD", "120,000 dollars", "USD 120000", "€120000",
                                    "120000USD", "budget of 120000.00"])
def test_budget_number_forms(answer):
    gold = {"project": "Orion", "owner": "Mira Chen", "status": "delayed", "deadline": "30 June 2026",
            "budget": "120000 USD"}
    assert field_matches("F5_TRANSFORMATION", f"Project Orion has {answer}.", gold)["budget"] is True


def test_number_inside_a_date_does_not_count():
    gold = {"person": "Daniel Reed", "organization": "Northbridge Labs", "city": "Leeds", "date": "14 March 2025",
            "amount": "14"}
    assert field_matches("F4_EXTRACTION", "Daniel Reed visited on 14 March 2025.", gold)["amount"] is False
    assert field_matches("F4_EXTRACTION", "Daniel Reed counted 14 items on 14 March 2025.", gold)["amount"] is True


def test_numbers_are_standalone():
    assert find_numbers("47th place and 470 units") == {Decimal(470)}
    assert find_numbers("1,250,000 and 3.5") == {Decimal(1250000), Decimal("3.5")}


def test_missing_field_and_field_accuracy():
    gold = {"project": "Orion", "owner": "Mira Chen", "status": "on hold", "deadline": "30 June 2026",
            "budget": "120000 USD"}
    task = {"family": "F5_TRANSFORMATION", "gold": gold}
    q = task_quality("F5_TRANSFORMATION", "Project Orion led by mira chen is on hold until June 30 2026.", task)
    assert q.detail["fields_matched"] == {"project": True, "owner": True, "status": True, "deadline": True,
                                          "budget": False}
    assert q.q_primary == pytest.approx(0.8) and q.q_secondary == 0.0
    q_all = task_quality("F5_TRANSFORMATION",
                         "Project Orion led by Mira Chen is on hold with a 120000 USD budget due 30 June 2026.", task)
    assert q_all.q_primary == 1.0 and q_all.q_secondary == 1.0


def test_phrase_matching_is_whole_phrase_and_case_insensitive():
    gold = {"person": "Daniel Reed", "organization": "Northbridge Labs", "city": "Leeds", "date": "14 March 2025",
            "amount": "47"}
    m = field_matches("F4_EXTRACTION", "daniel reed's team at NORTHBRIDGE LABS in Leedsville", gold)
    assert m["person"] and m["organization"] and not m["city"]


def test_non_string_answer_quality_zero():
    task = {"family": "F4_EXTRACTION", "gold": {}}
    q = task_quality("F4_EXTRACTION", ["Daniel Reed"], task)
    assert q.q_primary == 0.0 and q.q_secondary == 0.0 and not q.answer_available

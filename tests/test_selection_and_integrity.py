"""Selection determinism, synthetic data, and integrity tests that must catch broken prompt files."""

import json
import shutil

import pytest

from src import build_prompts, prepare_tasks, validate_integrity
from src.common import BENCH_DIR, read_jsonl, sha256_file, write_jsonl
from src.generate_synthetic import generate_f4, generate_f5
from src.prepare_tasks import (
    has_encoding_artifacts,
    has_list_like_lines,
    has_short_unterminated_lines,
    join_xsum_lines,
    leaks,
)

FILES = ["tasks_main.jsonl", "tasks_pilot.jsonl", "prompts_main.jsonl", "prompts_pilot.jsonl", "prompts_smoke.jsonl"]


# ---- synthetic data --------------------------------------------------------------------------------
def test_synthetic_generation_is_deterministic_distinct_and_comma_free():
    for fn in (generate_f4, generate_f5):
        a, b = fn(20261003, 22), fn(20261003, 22)
        assert a == b
        assert len({r["input_text"] for r in a}) == 22
        for r in a:
            assert all("," not in v for v in r["gold"].values())
            assert all(v in r["input_text"] for v in r["gold"].values())
    assert generate_f4(20261003, 22) != generate_f4(1, 22)


def test_synthetic_amounts_avoid_instruction_numbers_and_dates():
    for r in generate_f4(20261003, 22):
        assert 32 <= int(r["gold"]["amount"]) <= 980
    for r in generate_f5(20261003, 22):
        assert r["gold"]["status"] != "approved" and r["gold"]["budget"].endswith(" USD")


# ---- artifact detectors and leakage ------------------------------------------------------------------
def test_artifact_detectors():
    assert has_encoding_artifacts("price Â£100")          # "Â£" mojibake
    assert has_encoding_artifacts("itâ€™s")           # "â€™" mojibake
    assert has_encoding_artifacts("bad � char")
    assert has_encoding_artifacts("zero​width")
    assert not has_encoding_artifacts("Café in São Paulo costs £5.\nNew line.")
    assert has_list_like_lines("Intro.\n- item one\nOutro.") and has_list_like_lines("1. First")
    assert not has_list_like_lines("A sentence - with a dash inside.")
    assert has_short_unterminated_lines("A full sentence here.\nAge: 24\nAnother sentence.")
    assert not has_short_unterminated_lines("Short line.\nThe trial continues.")
    assert join_xsum_lines("First line.\n\n Second line. \n") == "First line. Second line."


def test_leakage_is_whole_token():
    assert leaks("two", "with exactly two keys")
    assert not leaks("one", "the phone rang")
    assert leaks("the Arctic", "areas such as Arctic")
    assert not leaks("", "anything")


# ---- determinism of selection and prompts --------------------------------------------------------------
@pytest.mark.data
def test_building_twice_gives_identical_hashes(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    for d in (a, b):
        prepare_tasks.build(d)
        build_prompts.build(d)
    for name in FILES:
        assert sha256_file(a / name) == sha256_file(b / name), name
        assert sha256_file(a / name) == sha256_file(BENCH_DIR / name), f"{name} differs from the committed file"


# ---- integrity tests must fail on broken inputs -------------------------------------------------------
@pytest.fixture()
def bench_copy(tmp_path):
    for name in FILES:
        shutil.copy(BENCH_DIR / name, tmp_path / name)
    return tmp_path


def _failed(results):
    return {i["id"] for i in results.items if not i["passed"]}


def test_integrity_passes_on_committed_files():
    assert validate_integrity.run(BENCH_DIR, skip_rebuild=True).ok


def test_integrity_detects_swapped_instruction_lines(bench_copy):
    recs = read_jsonl(bench_copy / "prompts_main.jsonl")
    r = recs[1]  # qa_001__P02
    lines = r["user_prompt"].split("\n")
    lines[1], lines[2] = lines[2], lines[1]
    r["user_prompt"] = "\n".join(lines)
    write_jsonl(bench_copy / "prompts_main.jsonl", recs)
    failed = _failed(validate_integrity.run(bench_copy, skip_rebuild=True))
    assert {"3", "X2"} <= failed


def test_integrity_detects_changed_input_and_reworded_instruction(bench_copy):
    recs = read_jsonl(bench_copy / "prompts_main.jsonl")
    recs[3]["user_prompt"] = recs[3]["user_prompt"] + " extra"
    recs[5]["user_prompt"] = recs[5]["user_prompt"].replace("at most 25 words", "at most 25 words or fewer")
    write_jsonl(bench_copy / "prompts_main.jsonl", recs)
    failed = _failed(validate_integrity.run(bench_copy, skip_rebuild=True))
    assert {"4", "5", "6"} <= failed


def test_integrity_detects_gold_leakage(bench_copy):
    tasks = read_jsonl(bench_copy / "tasks_main.jsonl")
    recs = read_jsonl(bench_copy / "prompts_main.jsonl")
    gold = tasks[0]["gold"]["answers"][0]
    for r in recs:
        if r["task_id"] == tasks[0]["task_id"]:
            r["user_prompt"] = r["user_prompt"].replace("\nQuestion: ", f"\nQuestion ({gold}): ")
    write_jsonl(bench_copy / "prompts_main.jsonl", recs)
    assert "8" in _failed(validate_integrity.run(bench_copy, skip_rebuild=True))


def test_integrity_detects_broken_format_variant(bench_copy):
    recs = read_jsonl(bench_copy / "prompts_pilot.jsonl")
    for r in recs:
        if r["prompt_id"] == "qa_p01__V04":
            r["user_prompt"] = r["user_prompt"].replace("Task:\n", "Task:\nPlease ")
    write_jsonl(bench_copy / "prompts_pilot.jsonl", recs)
    assert {"4", "7"} <= _failed(validate_integrity.run(bench_copy, skip_rebuild=True))


def test_integrity_detects_wrong_counts(bench_copy):
    recs = read_jsonl(bench_copy / "prompts_pilot.jsonl")
    write_jsonl(bench_copy / "prompts_pilot.jsonl", recs[:-1])
    assert "11" in _failed(validate_integrity.run(bench_copy, skip_rebuild=True))

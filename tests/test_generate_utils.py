"""Pure helpers of the generation and run modules (no model needed)."""

import json

from src.generate import batch_file_name, dedup_prompts, make_batches, split_generated, validate_batch_file
from src.runs import FINGERPRINT_KEYS, env_fingerprint, fingerprint_diff


def _p(pid, sha, task="t1"):
    return {"prompt_id": pid, "prompt_sha256": sha, "task_id": task, "family": "F1_QA", "system_prompt": "s",
            "user_prompt": f"u-{sha}"}


def test_dedup_groups_identical_texts():
    groups = dedup_prompts([_p("t1__P01", "a"), _p("t1__P02", "b"), _p("t1__V01", "a")])
    assert [g["prompt_ids"] for g in groups] == [["t1__P01", "t1__V01"], ["t1__P02"]]


def test_batches_sorted_by_length_then_id():
    items = [{"prompt_ids": [pid], "n_input_tokens": n} for pid, n in
             [("b", 5), ("a", 5), ("c", 3), ("d", 9), ("e", 1)]]
    batches = make_batches(items, 2)
    assert [[it["prompt_ids"][0] for it in b] for b in batches] == [["e", "c"], ["a", "b"], ["d"]]


def test_split_generated():
    assert split_generated([5, 6, 2, 0, 0], {2}) == ([5, 6], 3, "eos")
    assert split_generated([5, 6, 7], {2}) == ([5, 6, 7], 3, "length")
    assert split_generated([200020, 199999], {200020, 199999}) == ([], 1, "eos")
    assert split_generated([9, 199999, 199999], {200020, 199999}) == ([9], 2, "eos")


def test_validate_batch_file(tmp_path):
    path = tmp_path / batch_file_name(3)
    recs = [{"prompt_sha256": "a", "finish_reason": "eos", "output_text": "x"},
            {"prompt_sha256": "b", "finish_reason": "length", "output_text": ""}]
    path.write_text("".join(json.dumps(r) + "\n" for r in recs))
    assert path.name == "batch_00003.jsonl"
    assert validate_batch_file(path, ["a", "b"])
    assert not validate_batch_file(path, ["b", "a"])
    path.write_text(json.dumps(recs[0]) + "\n" + '{"prompt_sha256": "b", "fin')
    assert not validate_batch_file(path, ["a", "b"])


def test_fingerprint_diff():
    a = {k: "x" for k in FINGERPRINT_KEYS}
    b = dict(a, torch_version="y", driver_version="ignored")
    assert fingerprint_diff(env_fingerprint(a), env_fingerprint(b)) == {"torch_version": ("x", "y")}

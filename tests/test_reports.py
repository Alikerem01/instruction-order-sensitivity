"""G2 tooling: A1/A3 comparisons, the calibration rule, the pilot report and the audit sample."""

from pathlib import Path

import pytest

from scripts.compare_runs import batch_invariance, determinism
from scripts.import_run import run_import
from scripts.pilot_report import audit_sample, build, calibration, unique_text_ids
from src.common import write_json, write_jsonl
from src.evaluate import evaluate_run
from tests.test_golden_integration import RUN_ID, materialize

VEC = ("format_strict", "length", "cardinality", "t4", "verbatim")


def fake_run(root: Path, phase: str, run_id: str, records: list[dict], evals: list[dict] | None = None,
             env: dict | None = None):
    """A minimal imported run of model "m": generations, run_meta, import record (and evaluation records)."""
    d = root / "runs" / phase / run_id / "m"
    write_jsonl(d / "generations.jsonl", records)
    write_json(d / "run_meta.json", {"environment_fingerprint": env or {"gpu_name": "A100"}})
    write_json(root / "runs" / phase / f"{run_id}.import.json", {"passed": True, "models": {"m": {}}})
    if evals is not None:
        write_jsonl(root / "results" / "eval" / phase / run_id / "m.jsonl", evals)


def gen(sha: str, text: str, pid: str, n: int = 10, finish: str = "eos") -> dict:
    return {"prompt_sha256": sha, "prompt_ids": [pid], "output_text": text, "n_output_tokens": n, "finish_reason": finish}


def ev(pid: str, flags=(1, 1, 1, 1, 1), csr=None) -> dict:
    rec = dict(zip(VEC, flags))
    rec.update({"prompt_id": pid, "csr": csr if csr is not None else sum(flags) / 5})
    return rec


def test_a1_determinism(tmp_path):
    a = [gen("s1", "x", "t__P01"), gen("s2", "y", "t__P02")]
    fake_run(tmp_path, "smoke", "r1", a)
    fake_run(tmp_path, "smoke", "r2", [gen("s1", "x", "t__P01"), gen("s2", "y ", "t__P02")])
    fake_run(tmp_path, "smoke", "r3", a)
    res = determinism("smoke", "r1", "r2", tmp_path / "runs")["models"]["m"]
    assert res["byte_identical"] is False and res["differing_prompt_ids"] == ["t__P02"]
    assert determinism("smoke", "r1", "r3", tmp_path / "runs")["models"]["m"]["byte_identical"] is True


def test_a3_batch_invariance_rule(tmp_path):
    pids = [f"t{i:02d}__P01" for i in range(50)]
    gens16 = [gen(f"s{i}", "out", p) for i, p in enumerate(pids)]
    gens1 = [gen(f"s{i}", "out" if i else "other", p) for i, p in enumerate(pids)]
    evals16 = [ev(p) for p in pids]
    evals1 = [ev(p, (1, 1, 1, 1, 0) if i == 0 else (1, 1, 1, 1, 1)) for i, p in enumerate(pids)]
    fake_run(tmp_path, "pilot", "p", gens16, evals16)
    fake_run(tmp_path, "pilot_bs1", "b", gens1, evals1)
    res = batch_invariance("p", "b", tmp_path / "runs", tmp_path / "results")
    m = res["models"]["m"]
    assert m["exact_output_agreement"] == pytest.approx(49 / 50) and m["vector_agreement"] == pytest.approx(49 / 50)
    assert res["keep_batch_size_16"] is True  # 98% >= 98%
    assert m["first_difference_char"] == {"median": 1, "min": 1, "max": 1, "n_at_first_char": 0}  # "out" / "other"
    assert m["constraint_flips"]["verbatim"] == {"batch16_pass_batch1_fail": 1, "batch1_pass_batch16_fail": 0}
    assert m["csr_change_batch1_minus_batch16"]["n_lower_batch1"] == 1
    evals1[1] = ev(pids[1], (0, 1, 1, 1, 1))
    fake_run(tmp_path, "pilot_bs1", "b2", gens1, evals1)
    assert batch_invariance("p", "b2", tmp_path / "runs", tmp_path / "results")["keep_batch_size_16"] is False


def _records(n: int, length: int, t4: int, truncated: int, rule: str = "T4_NO_COMMA") -> list[dict]:
    return [{"length": int(i < length), "t4": int(i < t4), "t4_rule": rule,
             "finish_reason": "length" if i < truncated else "eos"} for i in range(n)]


@pytest.mark.parametrize(
    "length, t4, truncated, expected",
    [
        (95, 50, 2, ("keep T2_LENGTH", "keep the current T4", "keep max_new_tokens 512")),      # exactly at limits
        (96, 50, 2, ("replace T2_LENGTH with T2_LENGTH_20", "keep the current T4", "keep max_new_tokens 512")),
        (50, 4, 0, ("keep T2_LENGTH", "replace T4_NO_COMMA with T4_LOWERCASE", "keep max_new_tokens 512")),
        (50, 96, 0, ("keep T2_LENGTH", "replace T4_NO_COMMA with T4_LOWERCASE", "keep max_new_tokens 512")),
        (50, 5, 3, ("keep T2_LENGTH", "keep the current T4", "raise max_new_tokens from 512 to 768")),
    ],
)
def test_calibration_rule(length, t4, truncated, expected):
    cal = calibration({"a": _records(100, length, t4, truncated)}, 512)
    assert (cal["decisions"]["T2"], cal["decisions"]["T4"], cal["decisions"]["max_new_tokens"]) == expected


def test_calibration_never_applies_twice():
    cal = calibration({"a": _records(100, 50, 2, 0, rule="T4_LOWERCASE")}, 768)
    assert cal["decisions"]["T4"] == "keep the current T4"
    assert cal["decisions"]["max_new_tokens"] == "keep max_new_tokens 768"


def test_unique_texts_count_p01_and_v01_once():
    prompts = [{"prompt_id": "t__P01", "prompt_sha256": "a"}, {"prompt_id": "t__V01", "prompt_sha256": "a"},
               {"prompt_id": "t__V02", "prompt_sha256": "b"}]
    assert unique_text_ids(prompts) == {"t__P01", "t__V02"}


def test_pilot_report_and_audit_sample_on_the_golden_fixture(tmp_path):
    runs = tmp_path / "Colab Notebooks" / "runs"
    ctx, _, _ = materialize(runs)
    assert run_import(ctx, RUN_ID) == 0
    evaluate_run(ctx, RUN_ID, results_root=tmp_path / "results")
    text, summary = build(ctx, RUN_ID, results_root=tmp_path / "results", calibration_models=["fixture_model"])
    cal = summary["calibration"]
    # hand-derived from tests/fixtures/golden/cases.py (24 unique texts):
    assert cal["n_outputs_pooled"] == 24
    assert cal["length_pass_rate"] == pytest.approx(20 / 24) and cal["t4_pass_rate"] == pytest.approx(19 / 24)
    assert cal["truncation_rate"] == pytest.approx(1 / 24)
    assert cal["decisions"] == {"T2": "keep T2_LENGTH", "T4": "keep the current T4",
                                "max_new_tokens": "raise max_new_tokens from 512 to 768"}
    assert summary["f2_label_status"] == {"single": 3, "unresolved": 1, "cue_resolved": 1}
    assert "P02" not in text.split("## 1.")[0]  # no order-wise comparison anywhere
    sample = audit_sample(ctx, RUN_ID, results_root=tmp_path / "results")
    assert sample.count("\n## ") == 10  # 5 families × 2 for the one fixture model
    assert sample == audit_sample(ctx, RUN_ID, results_root=tmp_path / "results")  # deterministic


def test_import_extracts_run_zips_safely(tmp_path):
    import zipfile as zf_mod

    from scripts.import_run import extract_run_zip, pending_runs

    phase_dir = tmp_path / "runs" / "smoke"
    phase_dir.mkdir(parents=True)
    with zf_mod.ZipFile(phase_dir / "smoke_20260101-0000_abcdef1.zip", "w") as zf:
        zf.writestr("smoke_20260101-0000_abcdef1/run_info.json", "{}")
    assert pending_runs(phase_dir) == ["smoke_20260101-0000_abcdef1"]
    assert extract_run_zip(phase_dir, "smoke_20260101-0000_abcdef1") is True
    assert (phase_dir / "smoke_20260101-0000_abcdef1" / "run_info.json").is_file()
    assert extract_run_zip(phase_dir, "smoke_20260101-0000_abcdef1") is False  # already extracted
    with zf_mod.ZipFile(phase_dir / "smoke_evil.zip", "w") as zf:
        zf.writestr("smoke_evil/../../escape.txt", "x")
    with pytest.raises(SystemExit, match="unexpected path"):
        extract_run_zip(phase_dir, "smoke_evil")
    assert not (tmp_path / "escape.txt").exists()


def test_calibration_uses_only_the_calibration_models():
    """Decision D06 §4: the rule is decided on the three original models; a later model never changes strings."""
    evals = {"smollm2": _records(100, 50, 50, 0), "gemma4e4b": _records(100, 100, 100, 50)}
    cal = calibration(evals, 512, ["smollm2", "qwen25", "phi4mini"])
    assert cal["models_used"] == ["smollm2"] and cal["n_outputs_pooled"] == 100
    assert cal["decisions"]["T2"] == "keep T2_LENGTH" and cal["decisions"]["max_new_tokens"] == "keep max_new_tokens 512"
    only_gemma = calibration({"gemma4e4b": _records(100, 100, 100, 50)}, 512, ["smollm2", "qwen25", "phi4mini"])
    assert only_gemma["applicable"] is False and only_gemma["any_string_change"] is False


def test_first_difference():
    from scripts.compare_runs import first_difference

    assert first_difference("abc", "abd") == 2 and first_difference("abc", "abcdef") == 3
    assert first_difference("x", "y") == 0 and first_difference("same", "same") == 4

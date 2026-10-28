"""R6 (design decision G1): golden outputs through the real import -> evaluate path.

The run folder is written to a temporary directory (never under runs/) in exactly the format src/generate.py
writes; only the bundle-commit and file-hash checks are skipped (fixture flag). Every expected value in
tests/fixtures/golden/cases.py is asserted.
"""

import importlib.util
import json
from pathlib import Path

import pytest

from scripts.import_run import run_import
from src.common import dumps_record, read_json, read_jsonl, sha256_file, write_json
from src.evaluate import evaluate_run
from src.generate import dedup_prompts
from src.phases import context_for_fixture
from src.runs import FINGERPRINT_KEYS

FIXTURE = Path(__file__).parent / "fixtures" / "golden"
RUN_ID = "golden_fixture_run"
QUALITY_DETAIL_KEYS = ("containment_char", "label_status", "fields_matched")
FLAG_KEYS = ("format_strict", "length", "cardinality", "t4", "verbatim")


def load_cases() -> list[dict]:
    spec = importlib.util.spec_from_file_location("golden_cases", FIXTURE / "cases.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CASES


def materialize(runs_root: Path, override: dict[str, str] | None = None):
    """Write the fixture as a complete run folder of the fictitious model, like src/generate.py would.
    ``override`` replaces the output text of the case with that prompt id (negative tests)."""
    ctx = context_for_fixture(FIXTURE, runs_root)
    cases = load_cases()
    groups = dedup_prompts(ctx.prompts)
    group_of = {pid: g for g in groups for pid in g["prompt_ids"]}
    case_of = {}
    for c in cases:
        g = group_of[c["prompt_id"]]
        assert g["prompt_sha256"] not in case_of, f"two cases for the prompt group of {c['prompt_id']}"
        case_of[g["prompt_sha256"]] = c
    assert len(case_of) == len(groups), "every prompt group of the fixture needs exactly one case"

    model_key = ctx.expected_models[0]
    spec = ctx.model_specs[model_key]
    run_dir = runs_root / ctx.phase / RUN_ID
    batches_dir = run_dir / model_key / "batches"
    batches_dir.mkdir(parents=True)
    env = {k: "fixture" for k in FINGERPRINT_KEYS}
    env["gpu_name"] = "fixture (hand-written outputs)"
    stamp = "2026-10-04T00:00:00Z"
    write_json(run_dir / "run_info.json", {"run_id": RUN_ID, "phase": ctx.phase, "gitsha": None, "gitsha7": "fixture",
                                           "bundle": None, "created_utc": stamp, "models": [model_key],
                                           "replicate_of": None, "pass": 1})
    write_json(run_dir / "bundle_manifest.json", {"fixture": True, "gitsha": None, "files": {}})
    write_json(run_dir / "env.json", {"written_utc": stamp, "fingerprint": env, "environment": env})
    gen_config = {"do_sample": False, "num_beams": 1, "max_new_tokens": ctx.max_new_tokens, "repetition_penalty": 1.0,
                  "temperature": 1.0, "top_p": 1.0, "top_k": 50, "min_new_tokens": None, "no_repeat_ngram_size": 0,
                  "length_penalty": 1.0, "eos_token_id": list(spec["eos_token_ids"]),
                  "pad_token_id": spec["pad_token_id"], "use_cache": True}
    batches = [groups[i : i + ctx.batch_size] for i in range(0, len(groups), ctx.batch_size)]
    for bi, batch in enumerate(batches):
        lines = []
        for g in batch:
            c = dict(case_of[g["prompt_sha256"]])
            if override and c["prompt_id"] in override:
                c["output_text"] = override[c["prompt_id"]]
            lines.append(dumps_record({
                "run_id": RUN_ID, "phase": ctx.phase, "model_key": model_key, "model_id": spec["hf_id"],
                "model_revision": spec["revision"], "prompt_sha256": g["prompt_sha256"], "prompt_ids": g["prompt_ids"],
                "task_id": g["task_id"], "family": g["family"], "rendered_prompt_sha256": "fixture",
                "n_input_tokens": 1, "output_text": c["output_text"],
                "n_output_tokens": c.get("n_output_tokens", len(c["output_text"].split()) + 1),
                "finish_reason": c["finish_reason"], "batch_size": ctx.batch_size, "batch_index": bi,
                "dtype": "fixture", "device": env["device"], "gpu_name": env["gpu_name"],
                "torch_version": env["torch_version"], "transformers_version": env["transformers_version"],
                "cuda_version": env["cuda_version"], "generation_config": gen_config, "timestamp_utc": stamp,
            }))
        (batches_dir / f"batch_{bi:05d}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    gen_path = run_dir / model_key / "generations.jsonl"
    gen_path.write_text("".join((batches_dir / f"batch_{i:05d}.jsonl").read_text(encoding="utf-8")
                                for i in range(len(batches))), encoding="utf-8")
    write_json(run_dir / model_key / "batch_plan.json", {
        "model_key": model_key, "batch_size": ctx.batch_size, "n_unique_prompts": len(groups),
        "n_prompt_ids": len(ctx.prompts), "n_batches": len(batches),
        "batches": [{"batch_index": i, "prompt_sha256": [g["prompt_sha256"] for g in b]} for i, b in enumerate(batches)],
    })
    write_json(run_dir / model_key / "run_meta.json", {
        "run_id": RUN_ID, "phase": ctx.phase, "model_key": model_key, "status": "complete",
        "environment_fingerprint": env, "sessions": [{"started_utc": stamp, "environment": env, "ended_utc": stamp}],
        "counts": {"n_prompt_ids": len(ctx.prompts), "n_unique_prompts": len(groups), "n_batches": len(batches),
                   "n_batches_done": len(batches), "n_records": len(groups)},
        "r4_check": {"passed": True, "config_violations": [], "batches_checked": len(batches),
                     "logits_processors": [], "stopping_criteria": ["MaxLengthCriteria", "EosTokenCriteria"]},
        "generations_sha256": sha256_file(gen_path), "retries": [],
    })
    return ctx, cases, groups


def test_golden_outputs_through_import_and_evaluate(tmp_path):
    ctx, cases, groups = materialize(tmp_path / "Colab Notebooks" / "runs")
    assert run_import(ctx, RUN_ID) == 0
    record = read_json(tmp_path / "Colab Notebooks" / "runs" / ctx.phase / f"{RUN_ID}.import.json")
    assert record["passed"] and record["fixture"] is True and record["analysis_eligible"] is False
    skipped = [c["check"] for c in record["checks"] if "skipped" in c["check"]]
    assert skipped == ["fixture run: bundle-commit and file-hash checks skipped"]
    assert not any("bundle commit" in c["check"] or "bundled file" in c["check"] for c in record["checks"])
    assert any("R4 fail-fast" in c["check"] for c in record["checks"])

    out_dir = evaluate_run(ctx, RUN_ID, results_root=tmp_path / "Colab Notebooks" / "results")
    summary = read_json(out_dir / "summary.json")
    assert summary["analysis_eligible"] is False and summary["fixture"] is True
    evals = {r["prompt_id"]: r for r in read_jsonl(out_dir / "fixture_model.jsonl")}
    assert len(evals) == len(ctx.prompts) == 25

    group_of = {pid: g for g in groups for pid in g["prompt_ids"]}
    checked = 0
    for case in cases:
        exp = case["expected"]
        for pid in group_of[case["prompt_id"]]["prompt_ids"]:
            r = evals[pid]
            where = f"{case['case_id']} ({pid})"
            for key, value in exp.items():
                actual = r["quality_detail"].get(key) if key in QUALITY_DETAIL_KEYS else r[key]
                if isinstance(value, float):
                    assert actual == pytest.approx(value, abs=1e-9), f"{where}: {key}={actual!r}, expected {value!r}"
                else:
                    assert actual == value, f"{where}: {key}={actual!r}, expected {value!r}"
            flags = [exp[k] for k in FLAG_KEYS]
            assert r["csr"] == pytest.approx(sum(flags) / 5), where
            assert r["pcr"] == int(all(flags)), where
            assert r["cascade_csr"] == pytest.approx(sum(flags) / 5 if exp["format_strict"] else 0.0), where
            assert r["finish_reason"] == case["finish_reason"], where
            checked += 1
    assert checked == 25  # 24 cases; c01 covers two prompt ids (P01 = V01)
    assert {evals["qa_p01__P01"]["condition_id"], evals["qa_p01__V01"]["condition_id"]} == {"P01", "V01"}


def test_fixture_import_still_runs_the_other_checks(tmp_path):
    ctx, _, _ = materialize(tmp_path / "Colab Notebooks" / "runs")
    gen_path = tmp_path / "Colab Notebooks" / "runs" / ctx.phase / RUN_ID / "fixture_model" / "generations.jsonl"
    lines = gen_path.read_text(encoding="utf-8").splitlines(keepends=True)
    gen_path.write_text("".join(lines[:-1]), encoding="utf-8")  # drop one record
    assert run_import(ctx, RUN_ID) == 1
    assert not (tmp_path / "Colab Notebooks" / "runs" / ctx.phase / f"{RUN_ID}.import.json").exists()


def test_fixture_cases_cover_the_required_situations():
    cases = load_cases()
    rules = {c["expected"]["parse_rule"] for c in cases}
    tags = {t for c in cases for t in c["expected"]["error_tags"]}
    assert {"strict", "fence", "first_object", "none"} <= rules
    assert {"leading_text", "trailing_text", "truncated", "duplicate_keys", "extra_keys", "evidence_count_1",
            "evidence_count_3plus", "evidence_not_verbatim", "code_fence", "empty_output"} <= tags
    families = {json.loads(l)["prompt_id"].split("_")[0] for l in (FIXTURE / "prompts.jsonl").read_text().splitlines()}
    assert families == {"qa", "cls", "sum", "ext", "trf"}
    assert any(c["expected"].get("label_status") == "unresolved" for c in cases)
    assert any(c["expected"]["t4"] == 0 for c in cases) and any(c["expected"]["length"] == 0 for c in cases)


def test_import_rejects_thinking_markers_in_outputs(tmp_path):
    """Decision D06: for a model with a thinking mode, no thinking marker may appear in any output."""
    thought = '<|channel>thought\nLet me think.<channel|>{"answer": "x", "evidence": ["a b c", "d e f"]}'
    ctx, _, _ = materialize(tmp_path / "runs", override={"qa_p01__P02": thought})
    ctx.model_specs["fixture_model"]["thinking_markers"] = ["<|think|>", "<|channel>", "<channel|>"]
    assert run_import(ctx, RUN_ID) == 1
    ctx2, _, _ = materialize(tmp_path / "runs2")
    ctx2.model_specs["fixture_model"]["thinking_markers"] = ["<|think|>", "<|channel>", "<channel|>"]
    assert run_import(ctx2, RUN_ID) == 0

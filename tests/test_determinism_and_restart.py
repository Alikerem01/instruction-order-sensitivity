"""Decision G2: the A6 determinism check at batch size 1 (§3.2) and the regeneration of a model whose partial
run cannot resume because the environment changed (§3.3).

Unit tests cover the comparison, the reference builder, the bundle precondition and the importer checks. The
end-to-end tests run the real generation code with the cached dry-run model on the CPU, from an unzipped bundle
whose experiment.yaml is adapted in the temporary work folder only.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import types
import zipfile
from pathlib import Path

import pytest
import yaml

from scripts import make_a6_reference
from scripts.import_run import Checks, verify_a6, verify_superseded
from scripts.make_bundle import a6_reference_problems
from scripts.make_bundle import build as build_bundle
from src.common import REPO_ROOT, load_experiment, load_models, read_json, read_jsonl, sha256_file, sha256_text, write_json, write_jsonl
from src.generate import A6_FILE, EXIT_DETERMINISM, EXIT_ENV_MISMATCH, a6_compare, dedup_prompts, supersede_model_dir

SMOKE = "data/benchmark_v1/prompts_smoke.jsonl"
DRYRUN_MODEL = "smollm2_135m"
FP = {"gpu_name": "A100", "torch_version": "2.11.0"}


def check_hashes() -> list[str]:
    return [g["prompt_sha256"] for g in dedup_prompts(read_jsonl(REPO_ROOT / SMOKE))]


def gen_records(texts: dict[str, str] | None = None, batch_size: int = 1) -> list[dict]:
    texts = texts or {}
    return [{"prompt_sha256": h, "prompt_ids": [f"p{i}__P01"], "output_text": texts.get(h, f"out {i}"),
             "n_output_tokens": 3, "finish_reason": "eos", "rendered_prompt_sha256": f"r{i}", "batch_size": batch_size}
            for i, h in enumerate(check_hashes())]


def reference_for(records: list[dict], fingerprint: dict = FP) -> dict:
    return {"phase": "pilot_bs1", "run_id": "ref_run", "batch_size": 1, "environment_fingerprint": fingerprint,
            "outputs": {r["prompt_sha256"]: {"prompt_id": r["prompt_ids"][0], "output_sha256": sha256_text(r["output_text"]),
                                             "n_output_tokens": r["n_output_tokens"], "finish_reason": r["finish_reason"],
                                             "rendered_prompt_sha256": r["rendered_prompt_sha256"]} for r in records}}


# ---- A6 comparison -------------------------------------------------------------------------------
def test_a6_compare_identical_differing_and_environment():
    recs = gen_records()
    ref = reference_for(recs)
    res = a6_compare(recs, ref, FP)
    assert res["passed"] and res["n_identical"] == 5 and res["same_environment_as_reference"]
    changed = gen_records({recs[2]["prompt_sha256"]: "another output"})
    res = a6_compare(changed, ref, FP)
    assert not res["passed"] and res["differing_prompt_ids"] == ["p2__P01"] and res["n_identical"] == 4
    assert a6_compare(recs, ref, {**FP, "gpu_name": "A100-40GB"})["same_environment_as_reference"] is False
    assert not a6_compare(recs[:4], ref, FP)["passed"]  # a missing check prompt never passes
    recs[0]["n_output_tokens"] = 4  # same text, different token count
    assert a6_compare(recs, ref, FP)["differing_prompt_ids"] == ["p0__P01"]


# ---- reference builder and bundle precondition -----------------------------------------------------
def _fake_imported_run(runs_root: Path, phase: str, run_id: str, model: str, records: list[dict]) -> None:
    write_jsonl(runs_root / phase / run_id / model / "generations.jsonl", records)
    write_json(runs_root / phase / run_id / model / "run_meta.json", {"environment_fingerprint": FP})
    write_json(runs_root / phase / f"{run_id}.import.json", {"run_id": run_id, "passed": True, "fixture": False})


def test_reference_builder_and_bundle_precondition(tmp_path):
    root, runs_root = tmp_path / "repo", tmp_path / "runs"
    (root / SMOKE).parent.mkdir(parents=True)
    (root / SMOKE).write_bytes((REPO_ROOT / SMOKE).read_bytes())
    exp = load_experiment()
    assert a6_reference_problems(exp, "main", root) == [
        "results/qc/a6_reference.json is missing (run scripts/make_a6_reference.py after Gemma's pilot import)"]
    for m in ("smollm2", "qwen25", "phi4mini"):
        _fake_imported_run(runs_root, "pilot_bs1", "pilot_bs1_run", m, gen_records())
    with pytest.raises(SystemExit, match="pilot_gemma"):
        make_a6_reference.build("main", runs_root, root)
    out = make_a6_reference.build("main", runs_root, root, allow_missing=True)
    assert sorted(out["models"]) == ["phi4mini", "qwen25", "smollm2"]
    assert a6_reference_problems(exp, "main", root) == ["no A6 reference for gemma4e4b"]
    _fake_imported_run(runs_root, "pilot_gemma", "pilot_gemma_run", "gemma4e4b", gen_records(batch_size=16))
    with pytest.raises(SystemExit, match="batch size 1"):
        make_a6_reference.build("main", runs_root, root)
    _fake_imported_run(runs_root, "pilot_gemma", "pilot_gemma_run", "gemma4e4b", gen_records())
    out = make_a6_reference.build("main", runs_root, root)
    ref = out["models"]["gemma4e4b"]
    assert ref["run_id"] == "pilot_gemma_run" and sorted(ref["outputs"]) == sorted(check_hashes())
    assert a6_reference_problems(exp, "main", root) == []
    assert a6_reference_problems(exp, "pilot", root) == []  # phases without the check are not affected


def test_main_bundle_is_refused_without_a_complete_reference(tmp_path, monkeypatch):
    monkeypatch.setattr("scripts.make_bundle.a6_reference_problems", lambda exp, phase: ["no A6 reference for x"])
    with pytest.raises(SystemExit, match="A6 reference incomplete"):
        build_bundle("main", allow_dirty=True, skip_integrity=True, out_dir=tmp_path)
    assert not list(tmp_path.glob("*.zip"))


# ---- importer checks -----------------------------------------------------------------------------
def _a6_model_dir(tmp_path: Path, passed: bool, same_env: bool) -> tuple[Path, dict]:
    mdir = tmp_path / "m"
    recs = [{**r, "record_type": "a6_replicate"} for r in gen_records()]
    write_jsonl(mdir / A6_FILE, recs)
    meta = {"a6_check": {"passed": passed, "n": 5, "n_identical": 5 if passed else 4,
                         "same_environment_as_reference": same_env, "reference_phase": "pilot_bs1",
                         "reference_run_id": "r", "replicate_sha256": sha256_file(mdir / A6_FILE)}}
    return mdir, meta


@pytest.mark.parametrize("passed,same_env,ok", [(True, True, True), (False, False, True), (False, True, False)])
def test_importer_a6_check(tmp_path, passed, same_env, ok):
    mdir, meta = _a6_model_dir(tmp_path, passed, same_env)
    ctx = types.SimpleNamespace(determinism_check={"prompts_file": SMOKE})
    checks = Checks()
    out = verify_a6(checks, ctx, mdir, meta, "m")
    assert checks.ok is ok and out["passed"] is passed
    assert verify_a6(Checks(), types.SimpleNamespace(determinism_check=None), mdir, meta, "m") is None


def test_importer_a6_check_rejects_a_modified_replicate_file(tmp_path):
    mdir, meta = _a6_model_dir(tmp_path, True, True)
    (mdir / A6_FILE).write_text((mdir / A6_FILE).read_text() + "\n")
    checks = Checks()
    verify_a6(checks, types.SimpleNamespace(determinism_check={"prompts_file": SMOKE}), mdir, meta, "m")
    assert not checks.ok


def test_supersede_keeps_the_partial_run_and_the_importer_lists_it(tmp_path):
    run_dir = tmp_path / "run"
    write_json(run_dir / "m" / "batches" / "batch_00000.jsonl", {"x": 1})
    old = {"environment_fingerprint": FP, "counts": {"n_batches_done": 1, "n_batches": 3}}
    new_fp = {**FP, "gpu_name": "A100-40GB"}
    rec = supersede_model_dir(run_dir, "m", old, new_fp)
    kept = run_dir / rec["path"]
    assert not (run_dir / "m").exists() and (kept / "batches" / "batch_00000.jsonl").exists()
    assert read_json(kept / "SUPERSEDED.json")["environment_diff"] == {"gpu_name": ["A100", "A100-40GB"]}
    checks = Checks()
    listed = verify_superseded(checks, run_dir, "m", {"environment_fingerprint": new_fp, "supersedes": [rec]})
    assert checks.ok and listed[0]["path"] == rec["path"]
    checks = Checks()
    verify_superseded(checks, run_dir, "m", {"environment_fingerprint": new_fp})  # not listed in run_meta
    assert not checks.ok
    assert verify_superseded(Checks(), run_dir, "other", {"environment_fingerprint": FP}) == []


# ---- end to end with the dry-run model -----------------------------------------------------------
def _model_cached() -> bool:
    from huggingface_hub import try_to_load_from_cache

    spec = load_models()["dryrun_models"][DRYRUN_MODEL]
    return all(isinstance(try_to_load_from_cache(spec["hf_id"], f, revision=spec["revision"]), str)
               for f in ("config.json", "model.safetensors", "tokenizer.json"))


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    if not _model_cached():
        pytest.skip("dry-run model not in the local Hugging Face cache")
    base = tmp_path_factory.mktemp("g2")
    bundle = build_bundle("smoke", allow_dirty=True, skip_integrity=True, out_dir=base / "bundles")
    work = base / "local work"
    with zipfile.ZipFile(bundle) as zf:
        zf.extractall(work)
    return work


def _set_dryrun(work: Path, **changes) -> None:
    path = work / "configs" / "experiment.yaml"
    exp = yaml.safe_load(path.read_text(encoding="utf-8"))
    exp["phases"]["dryrun"].update(changes)
    for key in [k for k, v in changes.items() if v is None]:
        del exp["phases"]["dryrun"][key]
    path.write_text(yaml.safe_dump(exp, sort_keys=False), encoding="utf-8")


def _cli(work: Path, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "HF_HUB_OFFLINE": "1", **(env_extra or {})}
    return subprocess.run([sys.executable, "-m", *args], cwd=work, capture_output=True, text=True, env=env)


def _new_run(work: Path, runs_root: Path) -> Path:
    out = _cli(work, "src.runs", "resolve", "--runs-root", str(runs_root), "--phase", "dryrun", "--manifest",
               str(work / "manifest_bundle.json"), "--run-id", "new", "--models", DRYRUN_MODEL)
    assert out.returncode == 0, out.stderr
    run_dir = Path(out.stdout.strip().splitlines()[-1])
    assert _cli(work, "src.runs", "env", "--run-dir", str(run_dir), "--device", "cpu").returncode == 0
    return run_dir


def _generate(work: Path, run_dir: Path, *extra: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    return _cli(work, "src.generate", "run", "--phase", "dryrun", "--model", DRYRUN_MODEL, "--run-dir", str(run_dir),
                *extra, env_extra=env_extra)


OTHER_ENV = {"IOS_TEST_ENV_OVERRIDE": json.dumps({"torch_version": "0.0.0-simulated"})}  # dry-run phase only (R5)


def test_a6_end_to_end_passes_stops_or_records(work, tmp_path):
    runs_root = tmp_path / "runs"
    _set_dryrun(work, batch_size=1, determinism_check=None)
    first = _new_run(work, runs_root)
    gen = _generate(work, first)
    assert gen.returncode == 0, gen.stdout + gen.stderr
    hashes = [g["prompt_sha256"] for g in dedup_prompts(read_jsonl(work / SMOKE))]
    ref = make_a6_reference.model_reference(runs_root, "dryrun", first.name, DRYRUN_MODEL, hashes)
    ref_rel = "results/qc/a6_reference_test.json"
    write_json(work / ref_rel, {"models": {DRYRUN_MODEL: ref}})
    _set_dryrun(work, determinism_check={"prompts_file": SMOKE, "reference_file": ref_rel,
                                         "reference_phases": {DRYRUN_MODEL: "dryrun"}})

    second = _new_run(work, runs_root)  # identical environment: byte-identical, then the main batches
    gen = _generate(work, second)
    assert gen.returncode == 0, gen.stdout + gen.stderr
    meta = read_json(second / DRYRUN_MODEL / "run_meta.json")
    assert meta["a6_check"]["passed"] and meta["a6_check"]["completed"] and meta["status"] == "complete"
    assert len(read_jsonl(second / DRYRUN_MODEL / A6_FILE)) == 5 and "A6 check passed" in gen.stdout
    resumed = _generate(work, second)  # complete: the check is not repeated
    assert resumed.returncode == 0 and "already complete" in resumed.stdout

    tampered = json.loads((work / ref_rel).read_text())
    tampered["models"][DRYRUN_MODEL]["outputs"][hashes[0]]["output_sha256"] = "0" * 64
    write_json(work / ref_rel, tampered)
    third = _new_run(work, runs_root)  # a difference in an identical environment stops before any batch
    gen = _generate(work, third)
    assert gen.returncode == EXIT_DETERMINISM, gen.stdout + gen.stderr
    meta = read_json(third / DRYRUN_MODEL / "run_meta.json")
    assert meta["a6_check"]["passed"] is False and meta["a6_check"]["same_environment_as_reference"] is True
    assert not list((third / DRYRUN_MODEL / "batches").glob("batch_*.jsonl")) and "STOP (A6)" in gen.stdout

    fourth = _new_run(work, runs_root)  # in another environment the difference is recorded and the run goes on
    gen = _generate(work, fourth, env_extra=OTHER_ENV)
    assert gen.returncode == 0, gen.stdout + gen.stderr
    a6 = read_json(fourth / DRYRUN_MODEL / "run_meta.json")["a6_check"]
    assert a6["passed"] is False and a6["same_environment_as_reference"] is False and a6["completed"] is True


def test_environment_change_restart_end_to_end(work, tmp_path):
    runs_root = tmp_path / "runs"
    _set_dryrun(work, batch_size=2, determinism_check=None)
    run_dir = _new_run(work, runs_root)
    mdir = run_dir / DRYRUN_MODEL
    gen = _generate(work, run_dir, "--stop-after-batches", "1")
    assert gen.returncode == 3 and len(list((mdir / "batches").glob("batch_*.jsonl"))) == 1

    refused = _generate(work, run_dir, env_extra=OTHER_ENV)  # without the parameter: refused, nothing moved
    assert refused.returncode == EXIT_ENV_MISMATCH and 'RESTART_MODELS = "smollm2_135m"' in refused.stdout
    assert not (run_dir / "superseded").exists()

    gen = _generate(work, run_dir, "--restart-if-environment-changed", env_extra=OTHER_ENV)
    assert gen.returncode == 0, gen.stdout + gen.stderr
    kept = list((run_dir / "superseded").iterdir())
    assert len(kept) == 1 and (kept[0] / "batches" / "batch_00000.jsonl").exists()
    meta = read_json(mdir / "run_meta.json")
    assert meta["status"] == "complete" and meta["environment_fingerprint"]["torch_version"] == "0.0.0-simulated"
    assert meta["supersedes"][0]["path"] == f"superseded/{kept[0].name}"
    checks = Checks()
    verify_superseded(checks, run_dir, DRYRUN_MODEL, meta)
    assert checks.ok

    for env_extra in (OTHER_ENV, None):  # a complete model is never regenerated, in any environment
        again = _generate(work, run_dir, "--restart-if-environment-changed", env_extra=env_extra)
        assert again.returncode == 0 and "already complete" in again.stdout
    assert len(list((run_dir / "superseded").iterdir())) == 1

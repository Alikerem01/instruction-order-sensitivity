"""Verify and register a generation run copied to runs/<phase>/<run_id>/ (``make import PHASE=.. RUN=..``).

Checks: provenance (bundle files == git commit), completeness (one record per unique prompt text, exact id
groups, hashes), environment consistency within each model, model revisions, greedy generation settings,
the R4 fail-fast record, the R5 test-hook rule and record sanity. Decision G2: the A6 determinism records of
phases with a ``determinism_check`` (batch-1 replicates, never analysed) and any partial model run kept under
``superseded/`` after an environment change (listed, never analysed, never deleted). On success the run is
registered (runs/<phase>/<run_id>.import.json, runs/registry.jsonl) and its raw files, superseded runs and A6
records are made read-only. A failed check registers nothing.

The golden-output fixture (tests/fixtures/golden, design decision G1, R6) goes through the same code with
``PhaseContext.fixture = True``, which skips only the bundle-commit and file-hash checks that need a real bundle.

A run may be given as the folder or as the zip downloaded from Drive (``runs/<phase>/<run_id>.zip``); a zip is
extracted first, after checking that every entry lies inside ``<run_id>/``. ``--run all`` imports every run of
the phase that is present (folder or zip) and not yet imported. The run id is the folder or zip name, e.g.
``smoke_20261004-1558_51d293c`` (phase, UTC date and time of creation, bundle commit).

Usage: python scripts/import_run.py --phase PHASE --run RUN_ID|all [--models a,b] [--verify-rendered]
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common import (  # noqa: E402
    REPO_ROOT,
    load_experiment,
    read_json,
    read_jsonl,
    sha256_bytes,
    sha256_file,
    write_json,
)
from src.generate import A6_FILE, SUPERSEDED_DIR, dedup_prompts  # noqa: E402
from src.phases import PhaseContext, context_for_phase  # noqa: E402
from src.runs import env_fingerprint, utc_now  # noqa: E402

RECORD_ENV_KEYS = ("device", "gpu_name", "torch_version", "transformers_version", "cuda_version", "dtype",
                   "batch_size", "model_id", "model_revision", "run_id", "phase")


class Checks:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.items.append({"check": name, "passed": bool(ok), "detail": detail})
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))

    @property
    def ok(self) -> bool:
        return all(i["passed"] for i in self.items)


def git_blob_sha256(commit: str, rel: str) -> str | None:
    try:
        data = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT, capture_output=True, check=True).stdout
    except subprocess.CalledProcessError:
        return None
    return sha256_bytes(data)


def verify_a6(checks: Checks, ctx: PhaseContext, mdir: Path, meta: dict, model_key: str) -> dict | None:
    """Decision G2 §3.2 (A6): the batch-1 replicate records exist, match run_meta and cover the check prompts; the
    outputs are byte-identical to the pilot, or the difference is documented as an environment difference."""
    cfg = ctx.determinism_check
    if not cfg:
        return None
    a6 = meta.get("a6_check") or {}
    path = mdir / A6_FILE
    expected = {g["prompt_sha256"] for g in dedup_prompts(read_jsonl(REPO_ROOT / cfg["prompts_file"]))}
    records = read_jsonl(path) if path.exists() else []
    ok_file = path.exists() and sha256_file(path) == a6.get("replicate_sha256") and all(
        r.get("record_type") == "a6_replicate" and r.get("batch_size") == 1 for r in records)
    checks.add(f"{model_key}: A6 replicate records present, hash matches run_meta, batch size 1", ok_file,
               f"{len(records)} records")
    checks.add(f"{model_key}: A6 records cover the check prompts exactly once",
               sorted(r["prompt_sha256"] for r in records) == sorted(expected), f"{len(expected)} prompts")
    outcome = ("byte-identical" if a6.get("passed") else "differs; environment differs from the reference"
               if a6.get("same_environment_as_reference") is False else "differs in an identical environment")
    checks.add(f"{model_key}: A6 outputs byte-identical to the batch-1 pilot, or an environment difference is "
               "documented", bool(a6.get("passed")) or a6.get("same_environment_as_reference") is False,
               f"{a6.get('n_identical')}/{a6.get('n')} identical to {a6.get('reference_phase')}/"
               f"{a6.get('reference_run_id')}; {outcome}")
    return {"passed": a6.get("passed"), "n_identical": a6.get("n_identical"), "n": a6.get("n"),
            "same_environment_as_reference": a6.get("same_environment_as_reference"),
            "reference": f"{a6.get('reference_phase')}/{a6.get('reference_run_id')}"}


def verify_superseded(checks: Checks, run_dir: Path, model_key: str, meta: dict) -> list[dict]:
    """Decision G2 §3.3: partial runs moved to superseded/ after an environment change are all listed in the
    final run_meta, kept with their record and from an environment other than the final one."""
    root = run_dir / SUPERSEDED_DIR
    found = sorted(d.relative_to(run_dir).as_posix() for d in root.iterdir()
                   if d.is_dir() and d.name.startswith(f"{model_key}__")) if root.is_dir() else []
    listed = sorted(s["path"] for s in meta.get("supersedes", []))
    if not found and not listed:
        return []
    records = [read_json(run_dir / p / "SUPERSEDED.json") if (run_dir / p / "SUPERSEDED.json").exists() else {}
               for p in found]
    checks.add(f"{model_key}: superseded partial runs are kept and listed in run_meta", found == listed,
               f"kept={found}; listed={listed}")
    checks.add(f"{model_key}: every superseded run comes from another environment than the final one",
               all(r.get("environment_fingerprint") and r["environment_fingerprint"] != meta["environment_fingerprint"]
                   for r in records), "; ".join(f"{p}: {r.get('environment_diff')}" for p, r in zip(found, records)))
    return [{"path": p, "n_batches_done": r.get("n_batches_done"), "environment_diff": r.get("environment_diff")}
            for p, r in zip(found, records)]


def verify_model(checks: Checks, ctx: PhaseContext, run_dir: Path, model_key: str, groups: list[dict],
                 verify_rendered: bool) -> dict:
    spec = ctx.model_specs[model_key]
    mdir = run_dir / model_key
    meta = read_json(mdir / "run_meta.json")
    plan = read_json(mdir / "batch_plan.json")
    checks.add(f"{model_key}: run_meta status is complete", meta.get("status") == "complete", meta.get("status", ""))
    gen_path = mdir / "generations.jsonl"
    checks.add(f"{model_key}: generations.jsonl present and hash matches run_meta",
               gen_path.exists() and sha256_file(gen_path) == meta.get("generations_sha256"))
    batch_text = "".join((mdir / "batches" / f"batch_{i:05d}.jsonl").read_text(encoding="utf-8")
                         for i in range(plan["n_batches"]))
    checks.add(f"{model_key}: generations.jsonl equals the concatenated batch files",
               gen_path.exists() and gen_path.read_text(encoding="utf-8") == batch_text, f"{plan['n_batches']} batches")
    records = read_jsonl(gen_path)
    expected = {g["prompt_sha256"]: g for g in groups}
    hashes = [r["prompt_sha256"] for r in records]
    dup = [h for h, c in Counter(hashes).items() if c > 1]
    checks.add(f"{model_key}: one record per unique prompt text (0 missing, 0 extra, 0 duplicate)",
               set(hashes) == set(expected) and not dup and len(records) == len(expected),
               f"{len(records)} records, {len(expected)} expected, missing={len(set(expected) - set(hashes))}, "
               f"extra={len(set(hashes) - set(expected))}, duplicates={len(dup)}")
    bad_ids = [r["prompt_sha256"][:12] for r in records if r["prompt_sha256"] in expected and (
        r["prompt_ids"] != expected[r["prompt_sha256"]]["prompt_ids"]
        or r["task_id"] != expected[r["prompt_sha256"]]["task_id"])]
    checks.add(f"{model_key}: prompt id groups and task ids match the prompts file", not bad_ids,
               f"{sum(len(r['prompt_ids']) for r in records)} prompt ids covered")
    env_values = {k: sorted({json.dumps(r.get(k)) for r in records}) for k in RECORD_ENV_KEYS}
    multi = {k: v for k, v in env_values.items() if len(v) != 1}
    checks.add(f"{model_key}: one environment and one setting for all records", not multi,
               "; ".join(f"{k}={v[0]}" for k, v in env_values.items() if k in ("gpu_name", "torch_version",
                                                                                "transformers_version", "dtype")))
    fp = meta["environment_fingerprint"]
    session_diffs = [s["started_utc"] for s in meta["sessions"] if env_fingerprint(s["environment"]) != fp]
    checks.add(f"{model_key}: every session ran in the run's first environment", not session_diffs,
               f"{len(meta['sessions'])} session(s)")
    if ctx.experimental:
        hooked = [s["started_utc"] for s in meta["sessions"] if s["environment"].get("test_env_override")]
        checks.add(f"{model_key}: no session used the environment-override test hook (R5)", not hooked)
    rec0 = records[0] if records else {}
    checks.add(f"{model_key}: records agree with run_meta environment",
               all(rec0.get(k) == fp.get(k) for k in ("device", "gpu_name", "torch_version", "transformers_version",
                                                       "cuda_version")))
    checks.add(f"{model_key}: model id and revision match the pinned specification",
               rec0.get("model_id") == spec["hf_id"] and rec0.get("model_revision") == spec["revision"],
               f"{spec['hf_id']}@{spec['revision'][:12]}")
    gcs = {json.dumps(r["generation_config"], sort_keys=True) for r in records}
    gc = rec0.get("generation_config", {})
    greedy = (len(gcs) == 1 and gc.get("do_sample") is False and gc.get("num_beams") == 1
              and gc.get("repetition_penalty") == 1.0 and gc.get("max_new_tokens") == ctx.max_new_tokens
              and sorted(gc.get("eos_token_id") or []) == sorted(spec["eos_token_ids"]))
    checks.add(f"{model_key}: greedy generation config, identical for all records", greedy,
               f"max_new_tokens={gc.get('max_new_tokens')}, eos={gc.get('eos_token_id')}")
    r4 = meta.get("r4_check") or {}
    checks.add(f"{model_key}: R4 fail-fast checks passed for every batch",
               r4.get("passed") is True and not r4.get("config_violations")
               and r4.get("batches_checked") == plan["n_batches"],
               f"batches checked={r4.get('batches_checked')}/{plan['n_batches']}; "
               f"logits processors={r4.get('logits_processors')}; stopping={r4.get('stopping_criteria')}")
    markers = spec.get("thinking_markers", [])
    if markers:
        thinking = [r["prompt_ids"][0] for r in records if any(m in r["output_text"] for m in markers)]
        checks.add(f"{model_key}: no thinking markers in the outputs (thinking disabled, D06)", not thinking,
                   f"markers {markers}" + (f"; found in {thinking[:5]}" if thinking else ""))
    mx = ctx.max_new_tokens
    sane = all(isinstance(r["output_text"], str) and r["finish_reason"] in ("eos", "length")
               and 0 < r["n_output_tokens"] <= mx and (r["finish_reason"] == "eos" or r["n_output_tokens"] == mx)
               for r in records)
    checks.add(f"{model_key}: output text, token counts and finish reasons are consistent", sane)
    checks.add(f"{model_key}: batch size as configured for the phase ({ctx.batch_size})",
               rec0.get("batch_size") == ctx.batch_size and plan.get("batch_size") == ctx.batch_size)
    if ctx.experimental:
        checks.add(f"{model_key}: experimental phase ran on A100 in bfloat16",
                   "A100" in (rec0.get("gpu_name") or "") and rec0.get("dtype") == "bfloat16")
    if verify_rendered:
        from src.common import sha256_text
        from src.generate import load_tokenizer, render

        tok = load_tokenizer(spec, ctx.padding_side)
        mismatch = 0
        for r in records:
            rendered, ids = render(tok, expected[r["prompt_sha256"]], spec)
            mismatch += sha256_text(rendered) != r["rendered_prompt_sha256"] or len(ids) != r["n_input_tokens"]
        checks.add(f"{model_key}: chat-template rendering re-computed locally matches", mismatch == 0,
                   f"{mismatch} mismatches")
    a6 = verify_a6(checks, ctx, mdir, meta, model_key)
    superseded = verify_superseded(checks, run_dir, model_key, meta)
    finish = Counter(r["finish_reason"] for r in records)
    out = {"n_records": len(records), "finish_reason": dict(finish), "environment": fp,
           "generation_seconds_total": meta.get("generation_seconds_total"),
           "n_sessions": len(meta["sessions"]), "retries": len(meta.get("retries", []))}
    if a6 is not None:
        out["a6_check"] = a6
    if superseded:
        out["superseded"] = superseded
    return out


def extract_run_zip(phase_dir: Path, run_id: str) -> bool:
    """Extract ``<run_id>.zip`` (as downloaded from Drive) if the run folder does not exist yet."""
    run_dir, archive = phase_dir / run_id, phase_dir / f"{run_id}.zip"
    if run_dir.exists() or not archive.is_file():
        return False
    with zipfile.ZipFile(archive) as zf:
        for name in zf.namelist():
            if not name.startswith(f"{run_id}/") or name.startswith("/") or ".." in Path(name).parts:
                raise SystemExit(f"STOP: unexpected path {name!r} in {archive.name}; nothing extracted")
        zf.extractall(phase_dir)
    print(f"Extracted {archive.name}")
    return True


def pending_runs(phase_dir: Path) -> list[str]:
    """Run ids present in the phase folder (folders with run_info.json, or zips) that are not imported yet."""
    ids = {p.name for p in phase_dir.iterdir() if (p / "run_info.json").is_file()} if phase_dir.is_dir() else set()
    ids |= {p.stem for p in phase_dir.glob("*.zip")} if phase_dir.is_dir() else set()
    return sorted(r for r in ids if not (phase_dir / f"{r}.import.json").exists())


def run_import(ctx: PhaseContext, run_id: str, models: list[str] | None = None, verify_rendered: bool = False) -> int:
    extract_run_zip(ctx.runs_root / ctx.phase, run_id)
    run_dir = ctx.runs_root / ctx.phase / run_id
    print(f"Importing {run_dir}")
    checks = Checks()
    if not run_dir.is_dir():
        raise SystemExit(f"{run_dir} not found")
    info = read_json(run_dir / "run_info.json")
    manifest = read_json(run_dir / "bundle_manifest.json")
    checks.add("run_info phase and id match", info["phase"] == ctx.phase and info["run_id"] == run_id)
    if ctx.fixture:
        checks.add("fixture run: bundle-commit and file-hash checks skipped", bool(manifest.get("fixture")),
                   "golden-output fixture (R6)")
    else:
        commit_ok = subprocess.run(["git", "cat-file", "-e", f"{manifest['gitsha']}^{{commit}}"], cwd=ROOT,
                                   capture_output=True).returncode == 0
        checks.add("bundle commit exists in this repository", commit_ok, manifest["gitsha"][:12])
        if commit_ok:
            bad = [rel for rel, d in manifest["files"].items() if git_blob_sha256(manifest["gitsha"], rel) != d]
            checks.add("every bundled file matches the commit (SHA-256)", not bad and not manifest.get("dirty"),
                       f"{len(manifest['files'])} files" + (f"; mismatches: {bad[:5]}" if bad else ""))
        checks.add("local prompts file equals the bundled one",
                   manifest["files"].get(ctx.prompts_rel) == ctx.prompts_file_sha256, ctx.prompts_rel)
    checks.add("env.json present", (run_dir / "env.json").exists())
    groups = dedup_prompts(ctx.prompts)
    present = sorted(p.name for p in run_dir.iterdir() if (p / "run_meta.json").exists())
    selected = models or present
    missing = [m for m in ctx.expected_models if m not in present]
    checks.add("models present in the run",
               set(selected) <= set(present) and not set(selected) - set(ctx.expected_models),
               f"present={present}; not in this run={missing}")
    summary = {}
    for m in selected:
        if m in ctx.model_specs:
            summary[m] = verify_model(checks, ctx, run_dir, m, groups, verify_rendered)

    if not checks.ok:
        print("\nIMPORT FAILED: nothing registered.")
        return 1
    files = {p.relative_to(run_dir).as_posix(): sha256_file(p) for p in sorted(run_dir.rglob("*")) if p.is_file()}
    record_path = ctx.runs_root / ctx.phase / f"{run_id}.import.json"
    previous = read_json(record_path) if record_path.exists() else None
    if previous:
        changed = [k for k, v in previous["raw_files_sha256"].items() if files.get(k) != v]
        if changed:
            print(f"\nIMPORT FAILED: raw files changed since the first import: {changed[:10]}")
            return 1
    raw = {k: v for k, v in files.items() if "/batches/" in f"/{k}" or k.endswith("generations.jsonl")
           or k.endswith(f"/{A6_FILE}") or k.startswith(f"{SUPERSEDED_DIR}/")}
    record = {
        "run_id": run_id, "phase": ctx.phase, "imported_utc": previous["imported_utc"] if previous else utc_now(),
        "verified_utc": utc_now(), "passed": True, "bundle_gitsha": manifest.get("gitsha"), "fixture": ctx.fixture,
        "replicate_of": info.get("replicate_of"), "models": summary, "models_not_in_run": missing,
        "checks": checks.items, "raw_files_sha256": raw, "all_files_sha256": files,
        "analysis_eligible": ctx.analysis_eligible,
    }
    write_json(record_path, record)
    if not previous:
        with open(ctx.runs_root / "registry.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"run_id": run_id, "phase": ctx.phase, "imported_utc": record["imported_utc"],
                                 "models": sorted(summary), "bundle_gitsha": manifest.get("gitsha"),
                                 "replicate_of": info.get("replicate_of"),
                                 "analysis_eligible": ctx.analysis_eligible}) + "\n")
    for rel in raw:
        p = run_dir / rel
        os.chmod(p, os.stat(p).st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    print(f"\nIMPORT OK: {len(checks.items)} checks passed; registered in {record_path}; "
          f"{len(raw)} raw files made read-only.")
    return 0


def main(argv: list[str] | None = None) -> int:
    exp = load_experiment()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", required=True, choices=sorted(exp["phases"]))
    ap.add_argument("--run", required=True)
    ap.add_argument("--models", default="")
    ap.add_argument("--verify-rendered", action="store_true",
                    help="re-render every prompt with the pinned tokenizer (downloads tokenizer files only)")
    args = ap.parse_args(argv)
    models = [m for m in args.models.split(",") if m] or None
    ctx = context_for_phase(args.phase)
    run_ids = pending_runs(ctx.runs_root / ctx.phase) if args.run == "all" else [args.run]
    if not run_ids:
        print(f"No run to import in runs/{args.phase}/ (put the zip or folder there first).")
        return 1
    codes = [run_import(ctx, rid, models, args.verify_rendered) for rid in run_ids]
    print("\nImported:" if not any(codes) else "\nResults:", ", ".join(f"{r} ({'ok' if c == 0 else 'FAILED'})"
                                                                     for r, c in zip(run_ids, codes)))
    return max(codes)


if __name__ == "__main__":
    raise SystemExit(main())

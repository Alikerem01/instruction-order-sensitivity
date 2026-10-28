"""Run folders, run ids and environment fingerprints shared by generation, the notebook and the importer.

Run folder layout (``runs/<phase>/<run_id>/``)::

    run_info.json          run id, phase, git sha of the bundle, creation time, pass number (written once)
    bundle_manifest.json   copy of the bundle's manifest_bundle.json (written once)
    env.json               environment of the first session; env_<timestamp>.json for later sessions that differ
    <model_key>/run_meta.json       counts, sessions, environment, effective generation config, template hash
    <model_key>/batch_plan.json     deterministic batch composition (written once)
    <model_key>/batches/batch_NNNNN.jsonl   raw generation records, one file per batch (created atomically)
    <model_key>/generations.jsonl   all batch files concatenated in batch order (created at completion)

Run ids: ``<phase>_<YYYYMMDD-HHMM>_<gitsha7>`` (a suffix ``-2``, ``-3`` ... only if that id already exists).
``--run-id auto`` reuses the newest run made from the same bundle commit (a finished model is then skipped by
generation, so re-running the notebook never repeats work); ``new`` always starts a new run. A replicate run
(``--replicate-of RUN_ID``, the second smoke pass of design addition A1) is a separate run id.

Usage (notebook):
    python -m src.runs resolve --runs-root DIR --phase PHASE --manifest FILE [--run-id auto|new|ID]
                               [--replicate-of RUN_ID]
    python -m src.runs env --run-dir DIR
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from src.common import read_json, write_json

# Environment fields that must be identical for every output of one model within one phase.
FINGERPRINT_KEYS = (
    "device", "gpu_name", "cuda_version", "cudnn_version", "python_version", "torch_version",
    "transformers_version", "tokenizers_version", "accelerate_version", "safetensors_version",
    "huggingface_hub_version",
)
# Test hook: simulates a changed environment. Honored only in the dry-run phase (design decision G1, R5).
TEST_ENV_VAR = "IOS_TEST_ENV_OVERRIDE"
TEST_HOOK_PHASES = ("dryrun",)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M")


def guard_test_hook(phase: str | None) -> None:
    """Abort if the environment-override test hook is set outside the dry-run phase."""
    if os.environ.get(TEST_ENV_VAR) and phase not in TEST_HOOK_PHASES:
        raise SystemExit(f"STOP: {TEST_ENV_VAR} is set. It is honored only in the dry-run phase, never in "
                         f"phase {phase!r}. Unset it and start again.")


def _nvidia_smi(query: str) -> str | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader"], capture_output=True,
                             text=True, timeout=30, check=True).stdout.strip()
        return out.splitlines()[0].strip() if out else None
    except (subprocess.SubprocessError, OSError):
        return None


def collect_env(device: str | None = None, phase: str | None = None) -> dict:
    """Software and hardware environment of the current process.

    The test hook ``IOS_TEST_ENV_OVERRIDE`` is applied only when ``phase`` is the dry-run phase; in every other
    case its presence aborts the process."""
    guard_test_hook(phase)
    import accelerate
    import huggingface_hub
    import safetensors
    import tokenizers
    import torch
    import transformers

    cuda = torch.cuda.is_available()
    if device is None:
        device = "cuda" if cuda else "cpu"
    env = {
        "device": device,
        "gpu_name": torch.cuda.get_device_name(0) if (cuda and device == "cuda") else None,
        "gpu_count": torch.cuda.device_count() if cuda else 0,
        "gpu_memory_total_mib": _nvidia_smi("memory.total"),
        "driver_version": _nvidia_smi("driver_version"),
        "cuda_version": torch.version.cuda if device == "cuda" else None,
        "cudnn_version": (torch.backends.cudnn.version() if device == "cuda" else None),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "transformers_version": transformers.__version__,
        "tokenizers_version": tokenizers.__version__,
        "accelerate_version": accelerate.__version__,
        "safetensors_version": safetensors.__version__,
        "huggingface_hub_version": huggingface_hub.__version__,
        "platform": platform.platform(),
    }
    override = os.environ.get(TEST_ENV_VAR)
    if override:  # reached only in the dry-run phase (guard_test_hook above)
        env.update(json.loads(override))
        env["test_env_override"] = True
    return env


def env_fingerprint(env: dict) -> dict:
    return {k: env.get(k) for k in FINGERPRINT_KEYS}


def fingerprint_diff(a: dict, b: dict) -> dict:
    return {k: (a.get(k), b.get(k)) for k in FINGERPRINT_KEYS if a.get(k) != b.get(k)}


# ---------------------------------------------------------------------------------------------
# Run ids and folders
# ---------------------------------------------------------------------------------------------
def new_run_id(phase: str, gitsha7: str, phase_dir: Path | None = None) -> str:
    base = f"{phase}_{utc_stamp()}_{gitsha7}"
    rid, k = base, 1
    while phase_dir is not None and (phase_dir / rid).exists():
        k += 1
        rid = f"{base}-{k}"
    return rid


def run_is_complete(run_dir: Path, models: list[str]) -> bool:
    for m in models:
        meta = run_dir / m / "run_meta.json"
        if not meta.exists() or read_json(meta).get("status") != "complete":
            return False
    return True


def resolve_run_dir(runs_root: Path, phase: str, manifest: dict, run_id: str, models: list[str],
                    replicate_of: str | None = None) -> Path:
    """Create or find the run folder. ``run_id``: "auto" (reuse the newest run made from the same bundle commit
    with the same ``replicate_of``, else start a new one), "new", or an explicit existing id."""
    phase_dir = runs_root / phase
    phase_dir.mkdir(parents=True, exist_ok=True)
    gitsha7 = manifest["gitsha7"]
    if run_id not in ("auto", "new"):
        run_dir = phase_dir / run_id
        if not run_dir.exists():
            raise SystemExit(f"Run folder {run_dir} does not exist.")
        info = read_json(run_dir / "run_info.json")
        if info["gitsha7"] != gitsha7:
            raise SystemExit(f"Run {run_id} was made from bundle {info['gitsha7']}, not {gitsha7}. Use the same bundle.")
        if info.get("replicate_of") != replicate_of:
            raise SystemExit(f"Run {run_id} has replicate_of={info.get('replicate_of')!r}, expected {replicate_of!r}.")
        return run_dir
    if run_id == "auto":
        candidates = []
        for d in sorted(phase_dir.iterdir()):
            info_path = d / "run_info.json"
            if d.is_dir() and info_path.exists():
                info = read_json(info_path)
                if (info.get("gitsha7") == gitsha7 and info.get("phase") == phase
                        and info.get("replicate_of") == replicate_of):
                    candidates.append((info["created_utc"], d.name, d))
        if candidates:
            return sorted(candidates)[-1][2]
    rid = new_run_id(phase, gitsha7, phase_dir)
    run_dir = phase_dir / rid
    run_dir.mkdir(parents=True, exist_ok=False)
    write_json(run_dir / "run_info.json", {
        "run_id": rid, "phase": phase, "gitsha": manifest["gitsha"], "gitsha7": gitsha7,
        "bundle": manifest.get("bundle_name"), "created_utc": utc_now(), "models": models,
        "replicate_of": replicate_of, "pass": 1 if replicate_of is None else 2,
    })
    write_json(run_dir / "bundle_manifest.json", manifest)
    return run_dir


def write_or_check_env(run_dir: Path, env: dict) -> int:
    """Write env.json for the first session; for later sessions compare and record any difference."""
    path = run_dir / "env.json"
    if not path.exists():
        write_json(path, {"written_utc": utc_now(), "fingerprint": env_fingerprint(env), "environment": env})
        print(f"env.json written: {env.get('gpu_name') or env.get('device')}, torch {env['torch_version']}, "
              f"transformers {env['transformers_version']}")
        return 0
    first = read_json(path)
    diff = fingerprint_diff(first["fingerprint"], env_fingerprint(env))
    if not diff:
        print("Environment matches env.json of this run.")
        return 0
    other = run_dir / f"env_{utc_stamp()}.json"
    write_json(other, {"written_utc": utc_now(), "fingerprint": env_fingerprint(env), "environment": env,
                       "differs_from_env_json": diff})
    print("WARNING: this session's environment differs from the one that started this run:")
    for k, (a, b) in diff.items():
        print(f"  {k}: run={a!r} now={b!r}")
    print("Models already started in this run will refuse to resume. See COLAB_RUNBOOK.md.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("resolve", help="create or find the run folder and print its path")
    r.add_argument("--runs-root", type=Path, required=True)
    r.add_argument("--phase", required=True)
    r.add_argument("--manifest", type=Path, required=True)
    r.add_argument("--run-id", default="auto")
    r.add_argument("--models", default="")
    r.add_argument("--replicate-of", default=None, help="run id of the first pass (second smoke pass, A1)")
    e = sub.add_parser("env", help="write or check env.json of a run")
    e.add_argument("--run-dir", type=Path, required=True)
    e.add_argument("--device", default=None)
    args = ap.parse_args(argv)
    if args.cmd == "resolve":
        guard_test_hook(args.phase)
        manifest = read_json(args.manifest)
        models = [m for m in args.models.split(",") if m]
        run_dir = resolve_run_dir(args.runs_root, args.phase, manifest, args.run_id, models, args.replicate_of)
        print(run_dir)
        return 0
    phase = read_json(args.run_dir / "run_info.json")["phase"]
    return write_or_check_env(args.run_dir, collect_env(args.device, phase))


if __name__ == "__main__":
    sys.exit(main())

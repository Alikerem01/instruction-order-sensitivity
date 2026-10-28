"""Pipeline dry-run on the Mac with HuggingFaceTB/SmolLM2-135M-Instruct (implementation specification C1 step 9).

Exercises the same path as Colab, using the smoke bundle and the 5 smoke prompts on the CPU:
  1. build the smoke bundle, unzip it to dist/dryrun_work/ and verify every SHA-256;
  2. create a run folder under runs/dryrun/ and write env.json;
  3. session 1: start generation and kill the process (SIGKILL) as soon as the first batch file exists;
  4. session 2: try to resume with a simulated environment change -> must be refused (exit code 2);
  5. session 3: resume normally -> completes the remaining batches;
  6. session 4: run again -> "already complete";
  7. import the run (with chat-template re-rendering) and evaluate it.
Outputs are pipeline checks only and are excluded from every analysis.

Usage: python scripts/dryrun.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.make_bundle import build as build_bundle, verify_bundle_dir  # noqa: E402

MODEL = "smollm2_135m"
WORK = ROOT / "dist" / "dryrun_work"
LOG_LINES: list[str] = []


def _redact(text: str) -> str:
    """Logs are committed: show repository paths relative to the repository and no home directory (D01)."""
    return text.replace(str(ROOT), "<repo>").replace(str(Path.home()), "~")


def log(msg: str) -> None:
    msg = _redact(msg)
    print(msg, flush=True)
    LOG_LINES.append(msg)


def run(args: list[str], cwd: Path, env_extra: dict | None = None, ok=(0,)) -> tuple[int, str]:
    env = dict(os.environ, **(env_extra or {}))
    log(f"$ {' '.join(args)}" + (f"   [env {env_extra}]" if env_extra else ""))
    proc = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)
    out = (proc.stdout + proc.stderr).rstrip()
    for line in out.splitlines():
        if "unauthenticated requests" not in line:
            log("  " + line)
    log(f"  -> exit code {proc.returncode}")
    if proc.returncode not in ok:
        raise SystemExit(f"unexpected exit code {proc.returncode}")
    return proc.returncode, proc.stdout


def main() -> int:
    py = sys.executable
    log("== Dry-run (pipeline check only; never analysed) ==")
    bundle = build_bundle("smoke")
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    with zipfile.ZipFile(bundle) as zf:
        zf.extractall(WORK)
    manifest = verify_bundle_dir(WORK)
    log(f"Bundle {bundle.name} unzipped to {WORK.relative_to(ROOT)}; {len(manifest['files'])} SHA-256 verified")

    _, out = run([py, "-m", "src.runs", "resolve", "--runs-root", str(ROOT / "runs"), "--phase", "dryrun",
                  "--manifest", "manifest_bundle.json", "--run-id", "new", "--models", MODEL], cwd=WORK)
    run_dir = Path(out.strip().splitlines()[-1])
    run_id = run_dir.name
    run([py, "-m", "src.runs", "env", "--run-dir", str(run_dir), "--device", "cpu"], cwd=WORK)
    gen_cmd = [py, "-m", "src.generate", "run", "--phase", "dryrun", "--model", MODEL, "--run-dir", str(run_dir)]

    log("\n-- Session 1: start, then kill (SIGKILL) after the first batch file appears --")
    log(f"$ {' '.join(gen_cmd)}  (background)")
    proc = subprocess.Popen(gen_cmd, cwd=WORK, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    first_batch = run_dir / MODEL / "batches" / "batch_00000.jsonl"
    t0 = time.time()
    while not first_batch.exists():
        if proc.poll() is not None:
            raise SystemExit("generation ended before the first batch file appeared:\n" + proc.stdout.read())
        if time.time() - t0 > 1800:
            proc.kill()
            raise SystemExit("timeout waiting for the first batch")
        time.sleep(0.2)
    proc.kill()
    proc.wait()
    for line in proc.stdout.read().splitlines():
        if "unauthenticated requests" not in line:
            log("  " + line)
    done = sorted(p.name for p in (run_dir / MODEL / "batches").glob("batch_*.jsonl"))
    log(f"  -> killed with SIGKILL; batch files on disk: {done}")

    log("\n-- Session 2: resume attempt in a simulated different environment (must be refused) --")
    run(gen_cmd, cwd=WORK, env_extra={"IOS_TEST_ENV_OVERRIDE": json.dumps({"torch_version": "0.0.0-simulated"})},
        ok=(2,))
    after = sorted(p.name for p in (run_dir / MODEL / "batches").glob("batch_*.jsonl"))
    log(f"  -> batch files unchanged: {after == done} {after}")

    log("\n-- Session 3: normal resume --")
    run(gen_cmd, cwd=WORK)

    log("\n-- Session 4: run again (nothing left to do) --")
    run(gen_cmd, cwd=WORK)

    log("\n-- Import (from the repository) --")
    run([py, "scripts/import_run.py", "--phase", "dryrun", "--run", run_id, "--verify-rendered"], cwd=ROOT)

    log("\n-- Evaluate (pipeline check) --")
    run([py, "-m", "src.evaluate", "--phase", "dryrun", "--run", run_id], cwd=ROOT)

    log_path = ROOT / "runs" / "dryrun" / f"{run_id}.dryrun_log.txt"
    log_path.write_text("\n".join(LOG_LINES) + "\n", encoding="utf-8")
    print(f"\nDry-run complete: {run_id}\nLog: {log_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

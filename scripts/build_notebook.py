"""Write colab/run_generation.ipynb. The notebook stays thin: all logic lives in tested modules under src/.

Every code cell carries a metadata tag (helpers, gpu, mount, unzip, ...) so that tests can run the cells that
handle paths (tests/test_paths_with_spaces.py). All paths are pathlib objects and every command is an argument
list (never a shell string), because the Drive root contains a space ("Colab Notebooks", decision D02).

Usage: python scripts/build_notebook.py
"""

from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DRIVE_ROOT = "/content/drive/MyDrive/Colab Notebooks/emel_hoca_konf_colab"
WORK_DIR = "/content/work"

INTRO = """# Instruction-order study: generation on Colab (A100)

Run the cells **from top to bottom** (Runtime > Run all). Step-by-step instructions in Turkish:
`colab/COLAB_RUNBOOK.md`.

* Drive folder: `MyDrive/Colab Notebooks/emel_hoca_konf_colab/` with `bundles/` (upload the bundle zip here)
  and `runs/` (the notebook writes the outputs here). It is set by `DRIVE_ROOT` in the next cell.
* Change only the parameters in the next cell.
* After a disconnect, reconnect to an **A100** runtime and run all cells again: the run resumes where it stopped.
  Finished models are skipped, so running all cells again never repeats work.
* The smoke phases (smoke, smoke_gemma) run twice in this session (two run folders): the second pass checks run-to-run determinism.
* Main run (decision G2): batch size 1; run the models in separate sessions with `MODELS` (runbook). Each model
  starts with the A6 check (5 texts compared with its batch-1 pilot outputs).
* The notebook stops with a message starting with `STOP` if something is wrong. Do not edit any other cell."""

PARAMETERS = f'''# ======================================================================================
# DRIVE_ROOT (decision D02): the Google Drive folder that holds bundles/ and runs/.
# The name contains a space ("Colab Notebooks"); keep the quotes. Do not change it unless told to.
DRIVE_ROOT = "{DEFAULT_DRIVE_ROOT}"
# ======================================================================================

# ---- Other parameters ----
PHASE = "smoke"      # "smoke", "pilot", "pilot_bs1", "main"; Gemma 4 (D06): "smoke_gemma", "pilot_gemma"
BUNDLE = "auto"      # "auto" = the only colab_bundle_<PHASE>_*.zip in bundles/, or an exact file name
RUN_ID = "auto"      # "auto" = continue the run of this bundle (or start one); "new"; or an exact run id
MODELS = "all"       # "all" or a comma-separated subset, e.g. "qwen25,phi4mini"
RESTART_MODELS = ""  # only after a "refused to resume ... environment" STOP: the model(s) to regenerate from the
                     # start; the partial outputs are kept under superseded/ (runbook section 4). Otherwise "".'''

HELPERS = '''# ---- 1. Helpers (paths are pathlib objects; commands are argument lists, never shell strings) ----
import hashlib, json, os, pathlib, re, shutil, subprocess, sys, zipfile

def run_cmd(args, ok_codes=(0,)):
    """Run a command (a list of arguments), stream its output into the notebook, return its exit code."""
    proc = subprocess.Popen([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1)
    for line in proc.stdout:
        print(line, end="")
    code = proc.wait()
    if code not in ok_codes:
        raise RuntimeError(f"STOP: command failed with exit code {code}: {args}")
    return code'''

GPU_CHECK = '''# ---- 2. GPU check: must be an A100 ----
import torch
print(subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout)
assert torch.cuda.is_available(), "STOP: no GPU. Runtime > Change runtime type > A100 GPU."
GPU_NAME = torch.cuda.get_device_name(0)
print("GPU:", GPU_NAME, "| preinstalled torch", torch.__version__, "| CUDA", torch.version.cuda)
assert "A100" in GPU_NAME, f"STOP: this notebook must run on an A100 GPU, found {GPU_NAME!r}."
TORCH_PREINSTALLED = torch.__version__'''

MOUNT = '''# ---- 3. Mount Google Drive ----
from google.colab import drive
drive.mount("/content/drive")
DRIVE = pathlib.Path(DRIVE_ROOT)
BUNDLES = DRIVE / "bundles"
RUNS = DRIVE / "runs"
assert BUNDLES.is_dir(), f"STOP: folder {str(BUNDLES)!r} not found. Create it and upload the bundle there (runbook step 0)."
RUNS.mkdir(parents=True, exist_ok=True)
print("Drive root:", DRIVE)
print("Bundles:", sorted(p.name for p in BUNDLES.glob("*.zip")))'''

UNZIP = f'''# ---- 4. Unzip the bundle to the local work folder and verify every SHA-256 ----
WORK = pathlib.Path("{WORK_DIR}")
if BUNDLE == "auto":
    # exact phase match: "pilot" must not pick up a pilot_bs1 bundle
    pattern = re.compile("colab_bundle_" + re.escape(PHASE) + r"_[0-9a-f]{{7}}(-dirty)?\.zip")
    candidates = sorted(p for p in BUNDLES.glob("colab_bundle_*.zip") if pattern.fullmatch(p.name))
    assert candidates, f"STOP: no colab_bundle_{{PHASE}}_<commit>.zip in {{str(BUNDLES)!r}}."
    assert len(candidates) == 1, (
        f"STOP: several bundles for phase {{PHASE}}: {{[p.name for p in candidates]}}. Delete the superseded ones "
        "from the bundles folder (the analyst tells you which one is current) or set BUNDLE to the exact name.")
    bundle_path = candidates[0]
else:
    bundle_path = BUNDLES / BUNDLE
assert bundle_path.is_file(), f"STOP: bundle {{str(bundle_path)!r}} not found."
WORK.parent.mkdir(parents=True, exist_ok=True)
os.chdir(WORK.parent)
if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)
with zipfile.ZipFile(bundle_path) as zf:
    zf.extractall(WORK)
manifest = json.loads((WORK / "manifest_bundle.json").read_text())
assert manifest["phase"] == PHASE, f"STOP: bundle is for phase {{manifest['phase']!r}}, but PHASE = {{PHASE!r}}."
bad = [rel for rel, digest in manifest["files"].items()
       if hashlib.sha256((WORK / rel).read_bytes()).hexdigest() != digest]
assert not bad, f"STOP: SHA-256 mismatch for {{bad}}. Upload the bundle again."
os.chdir(WORK)
print(f"Bundle {{bundle_path.name}} verified: {{len(manifest['files'])}} files, commit {{manifest['gitsha7']}}, "
      f"{{manifest['n_unique_texts']}} unique prompts per model.")'''

INSTALL = '''# ---- 5. Install pinned libraries (Colab's preinstalled torch is kept) ----
run_cmd([sys.executable, "-m", "pip", "install", "-q", "-r", WORK / "requirements-colab.txt"])
versions = subprocess.run([sys.executable, "-c",
    "import torch, transformers, accelerate, tokenizers; "
    "print(torch.__version__, transformers.__version__, accelerate.__version__, tokenizers.__version__)"],
    capture_output=True, text=True, check=True).stdout.split()
print("torch", versions[0], "| transformers", versions[1], "| accelerate", versions[2], "| tokenizers", versions[3])
assert versions[0] == TORCH_PREINSTALLED, (
    f"STOP: pip changed torch from {TORCH_PREINSTALLED} to {versions[0]}. Report this to the analyst.")
torch_major_minor = tuple(int(x) for x in versions[0].split("+")[0].split(".")[:2])
assert torch_major_minor >= (2, 5), f"STOP: torch {versions[0]} is older than 2.5. Report this to the analyst."
pinned = dict(line.strip().split("==") for line in (WORK / "requirements-colab.txt").read_text().splitlines()
              if "==" in line and not line.startswith("#"))
assert versions[1] == pinned["transformers"], (
    f"STOP: transformers {versions[1]} is installed but {pinned['transformers']} is pinned. Report this to the analyst.")'''

TOKEN = '''# ---- 6. Optional Hugging Face token from Colab Secrets (not needed: all four models are public) ----
try:
    from google.colab import userdata
    token = userdata.get("HF_TOKEN")
    if token:
        os.environ["HF_TOKEN"] = token
        print("HF_TOKEN loaded from Colab Secrets (used only for downloads from huggingface.co).")
except Exception:
    print("No HF_TOKEN secret; downloads are anonymous.")'''

RUN_FOLDERS = '''# ---- 7. Run folders (new or resumed) and environment record ----
models = manifest["models"] if MODELS == "all" else [m.strip() for m in MODELS.split(",") if m.strip()]
assert set(models) <= set(manifest["models"]), f"STOP: MODELS must be among {manifest['models']}."
RESTART = [m.strip() for m in RESTART_MODELS.split(",") if m.strip()]
assert set(RESTART) <= set(models), f"STOP: RESTART_MODELS must be among the models of this session {models}."
PASSES = manifest.get("passes", 1)  # smoke: 2 passes in this session (design addition A1)

def prepare_run(run_id, replicate_of=None):
    """Create or find a run folder, record the environment, return the folder (a pathlib.Path)."""
    args = [sys.executable, "-m", "src.runs", "resolve", "--runs-root", str(RUNS), "--phase", PHASE,
            "--manifest", str(WORK / "manifest_bundle.json"), "--run-id", run_id, "--models", ",".join(models)]
    if replicate_of:
        args += ["--replicate-of", replicate_of]
    out = subprocess.run(args, capture_output=True, text=True, cwd=WORK)
    assert out.returncode == 0, "STOP: " + out.stderr + out.stdout
    run_dir = pathlib.Path(out.stdout.strip().splitlines()[-1])
    assert run_dir.is_dir(), f"STOP: run folder {str(run_dir)!r} was not created."
    print("Run folder:", run_dir)
    run_cmd([sys.executable, "-m", "src.runs", "env", "--run-dir", str(run_dir)])
    return run_dir

print(f"Phase {PHASE}: models {models}, {PASSES} pass(es), batch size {manifest.get('batch_size')}, "
      f"{manifest['n_unique_texts']} unique prompts per model.")'''

GENERATE = '''# ---- 8. Generate, one model after the other (finished batches and models are skipped) ----
RUN_DIRS = []
for p in range(1, PASSES + 1):
    run_dir = prepare_run(RUN_ID) if p == 1 else prepare_run("auto", replicate_of=RUN_DIRS[0].name)
    RUN_DIRS.append(run_dir)
    print(f"\\n#################### pass {p}/{PASSES}: {run_dir.name} ####################")
    for m in models:
        print(f"\\n========== {m} ==========")
        args = [sys.executable, "-m", "src.generate", "run", "--phase", PHASE, "--model", m, "--run-dir", str(run_dir)]
        if m in RESTART:
            args.append("--restart-if-environment-changed")  # decision G2 §3.3: partial run kept under superseded/
        code = run_cmd(args, ok_codes=(0, 2, 5))
        if code == 2:
            raise RuntimeError(f"STOP: {m} refused to resume because the environment or settings changed. "
                               "See COLAB_RUNBOOK.md (section 4).")
        if code == 5:
            raise RuntimeError(f"STOP (A6): {m}: the check outputs differ from its batch-1 pilot outputs in an "
                               "identical environment. Do not run again; report the message above to the analyst.")
print("\\nAll requested models are complete.")'''

SUMMARY = '''# ---- 9. Summary and one zip per run folder ----
for run_dir in RUN_DIRS:
    print(f"\\nRun {run_dir.name}")
    for m in models:
        meta = json.loads((run_dir / m / "run_meta.json").read_text())
        c, r4, a6 = meta["counts"], meta.get("r4_check", {}), meta.get("a6_check")
        a6_text = "" if a6 is None else (" A6=passed" if a6.get("passed") else " A6=differs (other environment)"
                                         if a6.get("same_environment_as_reference") is False else " A6=FAILED")
        print(f"  {m:10s} status={meta['status']:9s} records={c['n_records']}/{c['n_unique_prompts']} "
              f"R4 check={'passed' if r4.get('passed') else 'NOT PASSED'}{a6_text} "
              f"time={(meta.get('generation_seconds_total') or 0) / 60:.1f} min")
    archive = shutil.make_archive(str(run_dir), "zip", root_dir=run_dir.parent, base_dir=run_dir.name)
    print("  zip:", archive)
print("\\nDownload every zip listed above and follow COLAB_RUNBOOK.md, step 5.")'''

FLUSH = '''# ---- 10. Make sure Google Drive has saved everything (run last) ----
drive.flush_and_unmount()
print("Drive flushed and unmounted.")'''

CELLS = [
    ("md", "intro", INTRO), ("code", "parameters", PARAMETERS), ("code", "helpers", HELPERS),
    ("code", "gpu", GPU_CHECK), ("code", "mount", MOUNT), ("code", "unzip", UNZIP), ("code", "install", INSTALL),
    ("code", "token", TOKEN), ("code", "run_folders", RUN_FOLDERS), ("code", "generate", GENERATE),
    ("code", "summary", SUMMARY), ("code", "flush", FLUSH),
]


def build() -> Path:
    nb = new_notebook()
    nb.metadata = {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "A100", "machine_shape": "hm"},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    }
    cells = []
    for i, (kind, tag, src) in enumerate(CELLS):
        cell = new_markdown_cell(src) if kind == "md" else new_code_cell(src)
        cell["id"] = f"cell-{i:02d}-{tag}"
        cell["metadata"]["tags"] = [tag]
        cells.append(cell)
    nb.cells = cells
    nbformat.validate(nb)
    out = ROOT / "colab" / "run_generation.ipynb"
    out.write_text(nbformat.writes(nb) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build().relative_to(ROOT))

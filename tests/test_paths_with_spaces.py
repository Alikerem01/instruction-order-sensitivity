"""Decision D02: the Drive root contains a space ("MyDrive/Colab Notebooks/emel_hoca_konf_colab").

These tests run the bundle logic and the run-folder logic in directories whose names contain spaces:
(1) the modules (bundle build and verification, src.runs resolve/env, replicate pass, zip, and a real generation
with the cached dry-run model), and (2) the notebook's own cells, executed with a stand-in for google.colab.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import types
import zipfile
from pathlib import Path

import nbformat
import pytest

from scripts.make_bundle import build as build_bundle
from scripts.make_bundle import verify_bundle_dir
from src.common import REPO_ROOT, load_models, read_json, read_jsonl, write_json

COLAB_DRIVE_ROOT = "/content/drive/MyDrive/Colab Notebooks/emel_hoca_konf_colab"
DRYRUN_MODEL = "smollm2_135m"


@pytest.fixture(scope="module")
def spaced_drive(tmp_path_factory):
    """A Drive-like tree with spaces in its names and one smoke bundle in bundles/."""
    root = tmp_path_factory.mktemp("drive") / "My Drive" / "Colab Notebooks" / "emel_hoca_konf_colab"
    bundles = root / "bundles"
    bundle = build_bundle("smoke", allow_dirty=True, skip_integrity=True, out_dir=bundles)
    (root / "runs").mkdir(parents=True)
    return root, bundle


def _cli(work: Path, *args: str, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", *args], cwd=work, capture_output=True, text=True,
                          env={**os.environ, **(env_extra or {})})


def _unzip(bundle: Path, work: Path) -> dict:
    with zipfile.ZipFile(bundle) as zf:
        zf.extractall(work)
    return verify_bundle_dir(work)


def _model_cached() -> bool:
    from huggingface_hub import try_to_load_from_cache

    spec = load_models()["dryrun_models"][DRYRUN_MODEL]
    return all(isinstance(try_to_load_from_cache(spec["hf_id"], f, revision=spec["revision"]), str)
               for f in ("config.json", "model.safetensors", "tokenizer.json"))


# ---- (1) modules ---------------------------------------------------------------------------------
def test_bundle_and_run_folders_in_directories_with_spaces(spaced_drive, tmp_path):
    root, bundle = spaced_drive
    assert " " in str(bundle) and bundle.is_file()
    work = tmp_path / "local work dir"
    manifest = _unzip(bundle, work)
    assert manifest["phase"] == "smoke" and manifest["passes"] == 2

    runs_root = root / "runs"
    out = _cli(work, "src.runs", "resolve", "--runs-root", str(runs_root), "--phase", "smoke", "--manifest",
               str(work / "manifest_bundle.json"), "--run-id", "auto", "--models", "smollm2,qwen25,phi4mini")
    assert out.returncode == 0, out.stderr
    first = Path(out.stdout.strip().splitlines()[-1])
    assert first.is_dir() and first.parent == runs_root / "smoke" and "Colab Notebooks" in str(first)
    assert _cli(work, "src.runs", "env", "--run-dir", str(first)).returncode == 0
    assert read_json(first / "env.json")["fingerprint"]["python_version"]

    out2 = _cli(work, "src.runs", "resolve", "--runs-root", str(runs_root), "--phase", "smoke", "--manifest",
                str(work / "manifest_bundle.json"), "--run-id", "auto", "--models", "smollm2",
                "--replicate-of", first.name)
    second = Path(out2.stdout.strip().splitlines()[-1])
    assert out2.returncode == 0 and second.is_dir() and second != first
    assert read_json(second / "run_info.json")["replicate_of"] == first.name

    archive = Path(shutil.make_archive(str(first), "zip", root_dir=first.parent, base_dir=first.name))
    assert archive.parent == runs_root / "smoke"
    assert f"{first.name}/run_info.json" in zipfile.ZipFile(archive).namelist()


def test_generation_in_a_run_folder_with_spaces(spaced_drive, tmp_path):
    if not _model_cached():
        pytest.skip("dry-run model not in the local Hugging Face cache")
    root, bundle = spaced_drive
    work = tmp_path / "local work dir"
    _unzip(bundle, work)
    runs_root = root / "runs"
    out = _cli(work, "src.runs", "resolve", "--runs-root", str(runs_root), "--phase", "dryrun", "--manifest",
               str(work / "manifest_bundle.json"), "--run-id", "new", "--models", DRYRUN_MODEL)
    run_dir = Path(out.stdout.strip().splitlines()[-1])
    assert out.returncode == 0 and " " in str(run_dir)
    assert _cli(work, "src.runs", "env", "--run-dir", str(run_dir), "--device", "cpu").returncode == 0
    gen = _cli(work, "src.generate", "run", "--phase", "dryrun", "--model", DRYRUN_MODEL, "--run-dir", str(run_dir),
               env_extra={"HF_HUB_OFFLINE": "1"})
    assert gen.returncode == 0, gen.stdout + gen.stderr
    assert len(read_jsonl(run_dir / DRYRUN_MODEL / "generations.jsonl")) == 5
    meta = read_json(run_dir / DRYRUN_MODEL / "run_meta.json")
    assert meta["status"] == "complete" and meta["r4_check"]["passed"] is True


# ---- (2) the notebook's own cells ------------------------------------------------------------------
def _cells() -> dict[str, str]:
    nb = nbformat.read(REPO_ROOT / "colab" / "run_generation.ipynb", as_version=4)
    return {c.metadata["tags"][0]: c.source for c in nb.cells}


def _fake_colab(monkeypatch) -> None:
    colab = types.ModuleType("google.colab")
    colab.drive = types.SimpleNamespace(mount=lambda path: None, flush_and_unmount=lambda: None)
    colab.userdata = types.SimpleNamespace(get=lambda key: None)
    if "google" in sys.modules:
        monkeypatch.setattr(sys.modules["google"], "colab", colab, raising=False)
    else:
        google = types.ModuleType("google")
        google.colab = colab
        monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.colab", colab)


def _run(ns: dict, source: str, tag: str) -> None:
    exec(compile(source, f"<notebook cell {tag}>", "exec"), ns)


def test_notebook_cells_with_the_spaced_drive_root(spaced_drive, tmp_path, monkeypatch):
    root, _ = spaced_drive
    cells = _cells()
    _fake_colab(monkeypatch)
    monkeypatch.chdir(tmp_path)  # the cells change the working directory; restored afterwards
    ns: dict = {"__name__": "__main__"}
    _run(ns, cells["parameters"], "parameters")
    assert ns["DRIVE_ROOT"] == COLAB_DRIVE_ROOT  # D02 default
    ns["DRIVE_ROOT"] = str(root)  # same structure, on the local disk
    _run(ns, cells["helpers"], "helpers")
    _run(ns, cells["mount"], "mount")
    work = tmp_path / "content dir" / "work"
    unzip = cells["unzip"]
    assert unzip.count('pathlib.Path("/content/work")') == 1
    _run(ns, unzip.replace('pathlib.Path("/content/work")', f"pathlib.Path({str(work)!r})"), "unzip")
    assert ns["manifest"]["phase"] == "smoke" and Path.cwd() == work

    _run(ns, cells["run_folders"], "run_folders")
    assert ns["PASSES"] == 2 and ns["models"] == ["smollm2", "qwen25", "phi4mini"]
    first = ns["prepare_run"](ns["RUN_ID"])
    second = ns["prepare_run"]("auto", replicate_of=first.name)
    assert ns["prepare_run"](ns["RUN_ID"]) == first  # auto reuses the run of this bundle
    assert first != second and all("Colab Notebooks" in str(d) and d.is_dir() for d in (first, second))

    for run_dir in (first, second):  # stand-in for the generate cell, which needs an A100
        for m in ns["models"]:
            write_json(run_dir / m / "run_meta.json", {"status": "complete", "counts": {"n_records": 5,
                       "n_unique_prompts": 5}, "r4_check": {"passed": True}, "generation_seconds_total": 60.0})
    ns["RUN_DIRS"] = [first, second]
    _run(ns, cells["summary"], "summary")
    for run_dir in (first, second):
        archive = run_dir.parent / f"{run_dir.name}.zip"
        assert archive.is_file()
        assert f"{run_dir.name}/smollm2/run_meta.json" in zipfile.ZipFile(archive).namelist()


def test_notebook_refuses_ambiguous_or_wrong_phase_bundles(spaced_drive, tmp_path, monkeypatch):
    root, bundle = spaced_drive
    cells = _cells()
    _fake_colab(monkeypatch)
    monkeypatch.chdir(tmp_path)
    drive = tmp_path / "Second Drive" / "Colab Notebooks" / "emel_hoca_konf_colab"
    (drive / "bundles").mkdir(parents=True)
    shutil.copy(bundle, drive / "bundles" / bundle.name)
    shutil.copy(bundle, drive / "bundles" / "colab_bundle_smoke_0000000.zip")  # a superseded bundle
    shutil.copy(bundle, drive / "bundles" / "colab_bundle_pilot_bs1_0000000.zip")
    unzip = cells["unzip"].replace('pathlib.Path("/content/work")', f"pathlib.Path({str(tmp_path / 'w')!r})")
    ns: dict = {"__name__": "__main__"}
    _run(ns, cells["parameters"], "parameters")
    ns["DRIVE_ROOT"] = str(drive)
    _run(ns, cells["helpers"], "helpers")
    _run(ns, cells["mount"], "mount")
    with pytest.raises(AssertionError, match="several bundles for phase smoke"):
        _run(ns, unzip, "unzip")
    ns["PHASE"] = "pilot"  # must not pick up the pilot_bs1 bundle
    with pytest.raises(AssertionError, match="no colab_bundle_pilot_"):
        _run(ns, unzip, "unzip")

"""Run folders (auto/new/replicate, A1) and the environment-override test hook (R5)."""

import json

import pytest

from src import generate, runs
from src.common import write_json
from src.runs import TEST_ENV_VAR, collect_env, guard_test_hook, resolve_run_dir

MANIFEST = {"gitsha": "a" * 40, "gitsha7": "aaaaaaa", "bundle_name": "colab_bundle_smoke_aaaaaaa.zip", "files": {}}


# ---- R5: the test hook is honored only in the dry-run phase ----------------------------------------
@pytest.mark.parametrize("phase", ["smoke", "pilot", "pilot_bs1", "main", None])
def test_test_hook_aborts_outside_dryrun(monkeypatch, phase):
    monkeypatch.setenv(TEST_ENV_VAR, json.dumps({"torch_version": "0.0.0-simulated"}))
    with pytest.raises(SystemExit, match="honored only in the dry-run phase"):
        collect_env("cpu", phase)
    with pytest.raises(SystemExit):
        guard_test_hook(phase)


def test_test_hook_is_honored_in_dryrun(monkeypatch):
    monkeypatch.setenv(TEST_ENV_VAR, json.dumps({"torch_version": "0.0.0-simulated"}))
    env = collect_env("cpu", "dryrun")
    assert env["torch_version"] == "0.0.0-simulated" and env["test_env_override"] is True


def test_no_hook_no_override(monkeypatch):
    monkeypatch.delenv(TEST_ENV_VAR, raising=False)
    guard_test_hook("main")
    assert "test_env_override" not in collect_env("cpu", "main")


def test_generation_aborts_before_anything_when_hook_set(monkeypatch, tmp_path):
    monkeypatch.setenv(TEST_ENV_VAR, "{}")
    for phase in ("smoke", "pilot", "pilot_bs1", "main"):
        with pytest.raises(SystemExit, match="honored only in the dry-run phase"):
            generate.run(phase, "smollm2", tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_env_command_aborts_for_experimental_run(monkeypatch, tmp_path):
    write_json(tmp_path / "run_info.json", {"phase": "pilot"})
    monkeypatch.setenv(TEST_ENV_VAR, "{}")
    with pytest.raises(SystemExit):
        runs.main(["env", "--run-dir", str(tmp_path), "--device", "cpu"])
    assert not (tmp_path / "env.json").exists()


# ---- run folders -------------------------------------------------------------------------------------
def test_new_auto_and_replicate(tmp_path):
    first = resolve_run_dir(tmp_path, "smoke", MANIFEST, "auto", ["m"])
    info = json.loads((first / "run_info.json").read_text())
    assert info["pass"] == 1 and info["replicate_of"] is None and first.name.startswith("smoke_")
    assert (first / "bundle_manifest.json").exists()
    # auto reuses the existing run (finished models are skipped by generation)
    assert resolve_run_dir(tmp_path, "smoke", MANIFEST, "auto", ["m"]) == first
    # the second smoke pass is a separate run id that points to the first
    second = resolve_run_dir(tmp_path, "smoke", MANIFEST, "auto", ["m"], replicate_of=first.name)
    info2 = json.loads((second / "run_info.json").read_text())
    assert second != first and info2["replicate_of"] == first.name and info2["pass"] == 2
    assert resolve_run_dir(tmp_path, "smoke", MANIFEST, "auto", ["m"], replicate_of=first.name) == second
    assert resolve_run_dir(tmp_path, "smoke", MANIFEST, "auto", ["m"]) == first
    # an explicit id must match the requested pass
    with pytest.raises(SystemExit):
        resolve_run_dir(tmp_path, "smoke", MANIFEST, second.name, ["m"])


def test_new_in_the_same_minute_gets_a_suffix(tmp_path):
    a = resolve_run_dir(tmp_path, "pilot", MANIFEST, "new", ["m"])
    b = resolve_run_dir(tmp_path, "pilot", MANIFEST, "new", ["m"])
    assert a != b and (b.name == f"{a.name}-2" or b.name[:-7] != a.name[:-7])


def test_auto_ignores_runs_of_other_bundles(tmp_path):
    old = resolve_run_dir(tmp_path, "pilot", {**MANIFEST, "gitsha7": "bbbbbbb"}, "new", ["m"])
    current = resolve_run_dir(tmp_path, "pilot", MANIFEST, "auto", ["m"])
    assert current != old
    with pytest.raises(SystemExit):
        resolve_run_dir(tmp_path, "pilot", MANIFEST, old.name, ["m"])

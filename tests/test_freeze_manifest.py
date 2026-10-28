"""G3 freeze (implementation specification C3): no frozen file may change after the freeze without a new manifest, which
requires a DESIGN_DEVIATIONS.md entry and a recorded design decision."""

import pytest

from scripts.freeze_manifest import MANIFEST, build, differences, frozen_files
from src.common import read_json


def test_frozen_files_match_the_manifest():
    if not MANIFEST.exists():
        pytest.skip("not frozen yet")
    manifest = read_json(MANIFEST)
    assert manifest["tag"] == "benchmark-v1.0.0"
    assert differences(manifest) == []


def test_manifest_covers_the_design_and_records_the_main_settings():
    files = frozen_files()
    for rel in ("data/benchmark_v1/tasks_main.jsonl", "data/benchmark_v1/prompts_main.jsonl", "configs/experiment.yaml",
                "configs/prompt_strings.yaml", "src/evaluators/constraints.py", "src/evaluate.py", "ANALYSIS_PLAN.md"):
        assert rel in files
    assert not any(f.startswith(("results/", "runs/", "tests/", "scripts/")) for f in files)
    m = build()
    assert m["counts"]["prompts_main_ids"] == 2000 and m["counts"]["prompts_main_unique_texts"] == 1900
    assert m["generation"]["main_batch_size"] == 1 and m["generation"]["max_new_tokens"] == 512
    assert m["calibration"]["round"] == 0

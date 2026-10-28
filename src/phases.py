"""Phase context shared by the importer (scripts/import_run.py) and the evaluator (src/evaluate.py).

A context is built from configs/experiment.yaml for a real phase, or from tests/fixtures/golden/fixture_config.json
for the golden-output fixture (design decision G1, R6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.common import (
    REPO_ROOT,
    RUNS_DIR,
    load_experiment,
    load_models,
    load_phase_prompts,
    read_jsonl,
    sha256_file,
)


@dataclass
class PhaseContext:
    """Everything the importer and the evaluator need to know about one phase."""

    phase: str
    runs_root: Path                 # runs live in runs_root/<phase>/<run_id>/
    prompts_rel: str                # prompts file as listed in the bundle manifest
    prompts: list[dict]             # prompt records of the phase (after any arm filter)
    prompts_file_sha256: str
    tasks: list[dict]
    expected_models: list[str]
    model_specs: dict[str, dict]
    experimental: bool              # A100 + bfloat16 required
    analysis_eligible: bool
    batch_size: int
    max_new_tokens: int
    padding_side: str
    fixture: bool = False           # golden-output fixture: skip bundle-commit and file-hash checks only
    notes: list[str] = field(default_factory=list)
    determinism_check: dict | None = None   # A6 settings of the phase (decision G2 §3.2), if any


def context_for_phase(phase: str, runs_root: Path | None = None) -> PhaseContext:
    """Context of a real phase; ``runs_root`` defaults to the repository's runs/ folder."""
    exp = load_experiment()
    models_cfg = load_models()
    ph = exp["phases"][phase]
    section = "models" if ph["experimental"] else "dryrun_models"
    prompts_path = REPO_ROOT / ph["prompts_file"]
    return PhaseContext(
        phase=phase, runs_root=Path(runs_root) if runs_root is not None else RUNS_DIR, prompts_rel=ph["prompts_file"],
        prompts=load_phase_prompts(exp, phase),
        prompts_file_sha256=sha256_file(prompts_path), tasks=read_jsonl(REPO_ROOT / ph["tasks_file"]),
        expected_models=list(ph["models"]), model_specs=models_cfg[section], experimental=bool(ph["experimental"]),
        analysis_eligible=bool(ph["analysis_eligible"]), batch_size=ph.get("batch_size", exp["generation"]["batch_size"]),
        max_new_tokens=exp["generation"]["max_new_tokens"], padding_side=exp["generation"]["padding_side"],
        determinism_check=ph.get("determinism_check"),
    )


def context_for_fixture(fixture_dir: Path, runs_root: Path) -> PhaseContext:
    """Context of the golden-output fixture (tests/fixtures/golden): hand-written outputs, never analysed."""
    import json

    cfg = json.loads((fixture_dir / "fixture_config.json").read_text(encoding="utf-8"))
    prompts_path = fixture_dir / cfg["prompts_file"]
    return PhaseContext(
        phase=cfg["phase"], runs_root=runs_root, prompts_rel=cfg["prompts_file"], prompts=read_jsonl(prompts_path),
        prompts_file_sha256=sha256_file(prompts_path), tasks=read_jsonl(fixture_dir / cfg["tasks_file"]),
        expected_models=list(cfg["models"]), model_specs=cfg["model_specs"], experimental=False,
        analysis_eligible=bool(cfg["analysis_eligible"]), batch_size=cfg["batch_size"],
        max_new_tokens=cfg["max_new_tokens"], padding_side="left", fixture=True,
        notes=["golden-output fixture: hand-written outputs (design decision G1, R6)"],
    )

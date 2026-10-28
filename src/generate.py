"""Greedy generation for one model and one phase, with resume (brief §5.7; implementation specification §6.1).

Experimental phases (smoke, pilot, pilot_bs1, main, and the Gemma phases) run only on a CUDA GPU whose name
contains "A100", in bf16, with the phase's batch size (16 for smoke and pilot; 1 for pilot_bs1, pilot_gemma and
main, decision G2). The dry-run phase runs the dry-run model on the Mac CPU and is never analysed.

* Identical prompt texts (same prompt_sha256) are generated once; the record lists every prompt id sharing it.
* Order: sort by rendered input length (tokens), then by prompt id; consecutive batches of the configured size.
* GenerationConfig built from scratch: do_sample=False, num_beams=1, max_new_tokens, repetition_penalty=1.0,
  the model's own end-of-turn token ids, its pad token; no temperature, top_p or top_k. It also replaces the
  model's Hub generation_config, so no Hub default can leak in.
* Fail-fast (design decision G1, R4): the effective generation config is checked against an allow-list
  before the first batch, and the logits processors and stopping criteria that generate() actually builds are
  checked for every batch before it is written (src/genconfig.py). Any violation aborts the run.
* Each finished batch is written atomically to batches/batch_NNNNN.jsonl. A restarted run skips finished
  batches; it refuses to continue if the environment or any setting differs from the first session. A model
  that is already complete is skipped in any environment and never regenerated.
* Environment change during a long run (decision G2 §3.3): with ``--restart-if-environment-changed`` a partial
  model run that cannot resume because the environment changed (settings unchanged) is moved, never deleted, to
  ``superseded/<model>__<UTC stamp>/`` and the model is regenerated from the start in the new environment.
* Determinism check A6 (decision G2 §3.2), for phases with ``determinism_check``: before the first batch of a
  model's run, the check prompts are generated one at a time and compared with the model's batch-1 pilot outputs
  (reference file). Records go to ``a6_replicate.jsonl`` (never analysed). A difference in an identical
  environment stops the run (exit code 5); in a different environment it is recorded.
* Infrastructure errors: at most ``max_infra_retries`` retries of the same batch. Never retried for content.

Usage: python -m src.generate run --phase PHASE --model KEY --run-dir DIR [--restart-if-environment-changed]
"""

from __future__ import annotations

import os

os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import argparse
import json
import shutil
import sys
import time
import traceback
from pathlib import Path

from src.common import (
    REPO_ROOT,
    atomic_write_text,
    dumps_record,
    load_experiment,
    load_models,
    load_phase_prompts,
    read_json,
    read_jsonl,
    sha256_file,
    sha256_text,
    write_json,
)
from src.genconfig import check_generation_config, check_processors, torch_version_ok
from src.runs import collect_env, env_fingerprint, fingerprint_diff, guard_test_hook, utc_now, utc_stamp

EXIT_ENV_MISMATCH = 2
EXIT_STOPPED_BY_FLAG = 3
EXIT_GENERATION_CHECK = 4
EXIT_DETERMINISM = 5
A6_FILE = "a6_replicate.jsonl"
SUPERSEDED_DIR = "superseded"
GEN_RECORD_KEYS = (
    "do_sample", "num_beams", "max_new_tokens", "repetition_penalty", "temperature", "top_p", "top_k",
    "min_new_tokens", "no_repeat_ngram_size", "length_penalty", "eos_token_id", "pad_token_id", "use_cache",
)


# ---------------------------------------------------------------------------------------------
# Pure helpers (unit-tested)
# ---------------------------------------------------------------------------------------------
def dedup_prompts(prompts: list[dict]) -> list[dict]:
    """Group prompt records by prompt_sha256; keep first-seen order of texts, ids sorted."""
    groups: dict[str, dict] = {}
    for p in prompts:
        g = groups.get(p["prompt_sha256"])
        if g is None:
            groups[p["prompt_sha256"]] = {
                "prompt_sha256": p["prompt_sha256"], "prompt_ids": [p["prompt_id"]], "task_id": p["task_id"],
                "family": p["family"], "system_prompt": p["system_prompt"], "user_prompt": p["user_prompt"],
            }
        else:
            if (g["system_prompt"], g["user_prompt"]) != (p["system_prompt"], p["user_prompt"]):
                raise ValueError(f"hash collision for {p['prompt_id']}")
            g["prompt_ids"].append(p["prompt_id"])
    for g in groups.values():
        g["prompt_ids"].sort()
    return list(groups.values())


def make_batches(items: list[dict], batch_size: int) -> list[list[dict]]:
    """Sort by (n_input_tokens, first prompt id) and cut into consecutive batches."""
    ordered = sorted(items, key=lambda it: (it["n_input_tokens"], it["prompt_ids"][0]))
    return [ordered[i : i + batch_size] for i in range(0, len(ordered), batch_size)]


def split_generated(new_ids: list[int], eos_ids: set[int]) -> tuple[list[int], int, str]:
    """Cut the generated ids at the first end-of-turn token.

    Returns (ids to decode without the end-of-turn token, number of generated tokens including it, finish reason).
    Padding after the end-of-turn token (batch generation) is discarded.
    """
    for i, tok in enumerate(new_ids):
        if tok in eos_ids:
            return new_ids[:i], i + 1, "eos"
    return list(new_ids), len(new_ids), "length"


def a6_compare(records: list[dict], reference: dict, fingerprint: dict) -> dict:
    """A6 (decision G2 §3.2): compare batch-1 replicate records with the reference outputs of the model's
    batch-1 pilot run. Output text (by SHA-256), token count, finish reason and rendered prompt must all agree."""
    expected = reference["outputs"]
    differing = []
    for r in records:
        e = expected.get(r["prompt_sha256"])
        same = e is not None and (sha256_text(r["output_text"]), r["n_output_tokens"], r["finish_reason"]) == (
            e["output_sha256"], e["n_output_tokens"], e["finish_reason"]) and (
            e.get("rendered_prompt_sha256") in (None, r.get("rendered_prompt_sha256")))
        if not same:
            differing.append(r["prompt_ids"][0])
    complete = sorted(r["prompt_sha256"] for r in records) == sorted(expected)
    return {
        "n": len(records), "n_identical": len(records) - len(differing), "differing_prompt_ids": sorted(differing),
        "passed": complete and not differing,
        "same_environment_as_reference": not fingerprint_diff(reference["environment_fingerprint"], fingerprint),
        "reference_phase": reference["phase"], "reference_run_id": reference["run_id"],
    }


def supersede_model_dir(run_dir: Path, model_key: str, meta: dict, new_fingerprint: dict) -> dict:
    """Decision G2 §3.3: move a partial model run that cannot resume because the environment changed to
    ``superseded/<model>__<UTC stamp>/`` inside the run folder. Nothing is deleted; returns the record."""
    root = run_dir / SUPERSEDED_DIR
    root.mkdir(exist_ok=True)
    dest = root / f"{model_key}__{utc_stamp()}"
    k = 1
    while dest.exists():
        k += 1
        dest = root / f"{model_key}__{utc_stamp()}-{k}"
    record = {
        "model_key": model_key, "path": dest.relative_to(run_dir).as_posix(),
        "reason": "environment changed; resume refused (decision G2 §3.3)", "moved_utc": utc_now(),
        "environment_fingerprint": meta["environment_fingerprint"], "new_environment_fingerprint": new_fingerprint,
        "environment_diff": {k_: list(v) for k_, v in fingerprint_diff(meta["environment_fingerprint"],
                                                                       new_fingerprint).items()},
        "n_batches_done": meta["counts"]["n_batches_done"], "n_batches": meta["counts"]["n_batches"],
    }
    shutil.move(str(run_dir / model_key), str(dest))  # a rename on the same file system
    write_json(dest / "SUPERSEDED.json", record)
    return record


def batch_file_name(index: int) -> str:
    return f"batch_{index:05d}.jsonl"


def validate_batch_file(path: Path, expected_hashes: list[str]) -> bool:
    try:
        records = read_jsonl(path)
    except (OSError, json.JSONDecodeError):
        return False
    return [r.get("prompt_sha256") for r in records] == expected_hashes and all(
        r.get("finish_reason") in ("eos", "length") and isinstance(r.get("output_text"), str) for r in records
    )


# ---------------------------------------------------------------------------------------------
# Model side
# ---------------------------------------------------------------------------------------------
def chat_template_sha256(tokenizer) -> str:
    tmpl = tokenizer.chat_template
    return sha256_text(tmpl if isinstance(tmpl, str) else json.dumps(tmpl, sort_keys=True))


def load_tokenizer(spec: dict, padding_side: str):
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(spec["hf_id"], revision=spec["revision"], trust_remote_code=False)
    digest = chat_template_sha256(tok)
    if digest != spec["chat_template_sha256"]:
        raise RuntimeError(f"chat template SHA-256 {digest} differs from models.yaml {spec['chat_template_sha256']}")
    if tok.pad_token_id is None:
        tok.pad_token_id = spec["pad_token_id"]
    if tok.pad_token_id != spec["pad_token_id"]:
        raise RuntimeError(f"pad token id {tok.pad_token_id} differs from models.yaml {spec['pad_token_id']}")
    tok.padding_side = padding_side
    return tok


def render(tokenizer, group: dict, spec: dict | None = None) -> tuple[str, list[int]]:
    """Official chat template with the model's template options (e.g. enable_thinking=False for Gemma 4,
    decision D06); the system and user messages must each appear exactly once and no thinking marker may appear."""
    spec = spec or {}
    messages = [{"role": "system", "content": group["system_prompt"]},
                {"role": "user", "content": group["user_prompt"]}]
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                             **spec.get("chat_template_kwargs", {}))
    if rendered.count(group["system_prompt"]) != 1 or rendered.count(group["user_prompt"]) != 1:
        raise RuntimeError(f"system or user message does not appear exactly once for {group['prompt_ids'][0]}")
    if any(marker in rendered for marker in spec.get("thinking_markers", [])):
        raise RuntimeError(f"a thinking marker appears in the rendered prompt for {group['prompt_ids'][0]}")
    ids = tokenizer(rendered, add_special_tokens=False)["input_ids"]
    return rendered, ids


def build_generation_config(spec: dict, gen: dict):
    from transformers import GenerationConfig

    return GenerationConfig(
        do_sample=gen["do_sample"],
        num_beams=gen["num_beams"],
        max_new_tokens=gen["max_new_tokens"],
        repetition_penalty=gen["repetition_penalty"],
        eos_token_id=list(spec["eos_token_ids"]),
        pad_token_id=spec["pad_token_id"],
    )


def effective_generation_config(model, gen_config) -> tuple[dict, dict]:
    """The configuration generate() will actually use (transformers merges global defaults into None fields).
    Returns (the record subset, the full dict). Raises if it cannot be computed: R4 needs it."""
    eff, _ = model._prepare_generation_config(gen_config)
    d = eff.to_dict()
    return {k: d.get(k) for k in GEN_RECORD_KEYS}, d


class ProcessorRecorder:
    """Wraps the model's builders of logits processors and stopping criteria to record what generate() uses."""

    def __init__(self, model) -> None:
        self.logits_processors: list[str] | None = None
        self.stopping_criteria: list[str] | None = None
        orig_lp, orig_sc = model._get_logits_processor, model._get_stopping_criteria

        def wrapped_lp(*args, **kwargs):
            out = orig_lp(*args, **kwargs)
            self.logits_processors = [type(p).__name__ for p in out]
            return out

        def wrapped_sc(*args, **kwargs):
            out = orig_sc(*args, **kwargs)
            self.stopping_criteria = [type(c).__name__ for c in out]
            return out

        model._get_logits_processor = wrapped_lp
        model._get_stopping_criteria = wrapped_sc

    def reset(self) -> None:
        self.logits_processors = None
        self.stopping_criteria = None


def load_model(spec: dict, dtype_name: str, device: str, attn: str):
    import torch
    from transformers import AutoModelForCausalLM

    dtype = {"bfloat16": torch.bfloat16, "float32": torch.float32, "float16": torch.float16}[dtype_name]
    model = AutoModelForCausalLM.from_pretrained(
        spec["hf_id"], revision=spec["revision"], dtype=dtype, trust_remote_code=False, attn_implementation=attn,
    )
    if type(model).__module__ != spec["native_class_module"]:
        raise RuntimeError(f"model class {type(model).__module__} != {spec['native_class_module']}")
    model.to(device)
    model.eval()
    return model


def generation_record(info: dict, phase: str, model_key: str, spec: dict, g: dict, output: tuple, batch_size: int,
                      batch_index: int, gen: dict, env: dict, gen_record: dict, stamp: str) -> dict:
    text, n_out, reason = output
    return {
        "run_id": info["run_id"], "phase": phase, "model_key": model_key, "model_id": spec["hf_id"],
        "model_revision": spec["revision"], "prompt_sha256": g["prompt_sha256"],
        "prompt_ids": g["prompt_ids"], "task_id": g["task_id"], "family": g["family"],
        "rendered_prompt_sha256": g["rendered_prompt_sha256"], "n_input_tokens": g["n_input_tokens"],
        "output_text": text, "n_output_tokens": n_out, "finish_reason": reason,
        "batch_size": batch_size, "batch_index": batch_index, "dtype": gen["dtype"],
        "device": env["device"], "gpu_name": env["gpu_name"], "torch_version": env["torch_version"],
        "transformers_version": env["transformers_version"], "cuda_version": env["cuda_version"],
        "generation_config": gen_record, "timestamp_utc": stamp,
    }


def generate_batch(model, tokenizer, gen_config, rendered: list[str], eos_ids: set[int], device: str):
    import torch

    enc = tokenizer(rendered, add_special_tokens=False, padding=True, return_tensors="pt").to(device)
    with torch.inference_mode():
        out = model.generate(**enc, generation_config=gen_config)
    prompt_len = enc["input_ids"].shape[1]
    results = []
    for row in out[:, prompt_len:].tolist():
        keep, n_tokens, reason = split_generated(row, eos_ids)
        text = tokenizer.decode(keep, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        results.append((text, n_tokens, reason))
    return results


# ---------------------------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------------------------
def phase_settings(exp: dict, models_cfg: dict, phase: str, model_key: str) -> tuple[dict, dict]:
    if phase not in exp["phases"]:
        raise SystemExit(f"unknown phase {phase}")
    ph = exp["phases"][phase]
    if model_key not in ph["models"]:
        raise SystemExit(f"model {model_key} is not part of phase {phase} ({ph['models']})")
    gen = dict(exp["generation"])
    gen["experimental"] = bool(ph["experimental"])
    gen["batch_size"] = ph.get("batch_size", gen["batch_size"])
    if not gen["experimental"]:
        spec = models_cfg["dryrun_models"][model_key]
        gen.update({"dtype": ph["dtype"], "device": ph["device"], "required_gpu_substring": None})
    else:
        spec = models_cfg["models"][model_key]
        gen["device"] = "cuda"
    return spec, gen


def check_hardware(phase: str, gen: dict, env: dict) -> None:
    if not gen["experimental"]:
        if env.get("device") != gen["device"]:
            raise SystemExit(f"phase {phase} expects device {gen['device']}, found {env.get('device')}")
        return
    if env.get("test_env_override"):
        raise SystemExit("STOP: the environment-override test hook is never honored in an experimental phase.")
    name = env.get("gpu_name") or ""
    if gen["required_gpu_substring"] not in name:
        raise SystemExit(f"STOP: phase {phase} must run on an {gen['required_gpu_substring']} GPU; found {name!r}.")
    if gen["dtype"] != "bfloat16":
        raise SystemExit("STOP: experimental phases run in bfloat16 only.")
    if not torch_version_ok(env.get("torch_version") or ""):
        raise SystemExit(f"STOP: torch {env.get('torch_version')} is older than 2.5; report it, do not upgrade silently.")


def determinism_check(cfg: dict, ctx: dict, model, tokenizer, gen_config, recorder, meta: dict, meta_path: Path,
                      log) -> int:
    """A6 (decision G2 §3.2): generate the check prompts one at a time (batch size 1) and compare them with the
    model's batch-1 pilot outputs. Returns 0 to continue, or an exit code that stops the run."""
    spec, env, model_key = ctx["spec"], ctx["env"], ctx["model_key"]
    ref_path = REPO_ROOT / cfg["reference_file"]
    reference = (read_json(ref_path).get("models") or {}).get(model_key) if ref_path.exists() else None
    if not reference:
        log(f"STOP (A6): no batch-1 reference for {model_key} in {cfg['reference_file']}; the bundle is incomplete.")
        return EXIT_DETERMINISM
    groups = dedup_prompts(read_jsonl(REPO_ROOT / cfg["prompts_file"]))
    records = []
    for g in groups:
        rendered, ids = render(tokenizer, g, spec)
        g["rendered_prompt_sha256"], g["n_input_tokens"] = sha256_text(rendered), len(ids)
        recorder.reset()
        output = generate_batch(model, tokenizer, gen_config, [rendered], set(spec["eos_token_ids"]), env["device"])[0]
        problems = check_processors(recorder.logits_processors, recorder.stopping_criteria)
        if problems:
            meta["r4_check"].update({"passed": False, "processor_violations": problems, "failed_batch": "A6"})
            write_json(meta_path, meta)
            log(f"STOP (R4): the A6 check generation used unexpected processors: {problems}")
            return EXIT_GENERATION_CHECK
        rec = generation_record(ctx["info"], ctx["phase"], model_key, spec, g, output, 1, -1, ctx["gen"], env,
                                ctx["gen_record"], utc_now())
        rec["record_type"] = "a6_replicate"  # never analysed
        records.append(rec)
    path = meta_path.parent / A6_FILE
    atomic_write_text(path, "".join(dumps_record(r) + "\n" for r in records))
    result = a6_compare(records, reference, env_fingerprint(env))
    result.update({"replicate_file": A6_FILE, "replicate_sha256": sha256_file(path), "checked_utc": utc_now(),
                   "completed": result["passed"] or not result["same_environment_as_reference"]})
    meta["a6_check"] = result
    write_json(meta_path, meta)
    ref = f"{reference['phase']}/{reference['run_id']}"
    if result["passed"]:
        log(f"A6 check passed: {result['n']}/{result['n']} outputs byte-identical to the batch-1 pilot run {ref}")
        return 0
    if not result["same_environment_as_reference"]:
        log(f"A6 check: {result['n'] - result['n_identical']} of {result['n']} outputs differ from {ref}, whose "
            "environment differs from this one; recorded (decision G2 §3.2), generation continues")
        return 0
    log(f"STOP (A6): outputs differ from the batch-1 pilot run {ref} in an identical environment: "
        f"{result['differing_prompt_ids']}. Nothing else was generated; report this to the analyst.")
    return EXIT_DETERMINISM


def run(phase: str, model_key: str, run_dir: Path, stop_after_batches: int | None = None,
        restart_if_environment_changed: bool = False) -> int:
    import torch

    guard_test_hook(phase)  # R5: the test hook aborts every phase except the dry-run
    exp = load_experiment()
    models_cfg = load_models()
    spec, gen = phase_settings(exp, models_cfg, phase, model_key)
    env = collect_env(gen["device"], phase)
    check_hardware(phase, gen, env)

    run_dir = Path(run_dir)
    info = read_json(run_dir / "run_info.json")
    if info["phase"] != phase:
        raise SystemExit(f"run folder belongs to phase {info['phase']}, not {phase}")
    model_dir = run_dir / model_key
    batches_dir = model_dir / "batches"
    batches_dir.mkdir(parents=True, exist_ok=True)
    log_path = model_dir / "generate.log"

    def log(msg: str) -> None:
        line = f"[{utc_now()}] {msg}"
        print(line, flush=True)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    prompts_file = REPO_ROOT / exp["phases"][phase]["prompts_file"]
    prompts = load_phase_prompts(exp, phase)
    groups = dedup_prompts(prompts)
    tokenizer = load_tokenizer(spec, gen["padding_side"])
    for g in groups:
        rendered, ids = render(tokenizer, g, spec)
        g["rendered"] = rendered
        g["rendered_prompt_sha256"] = sha256_text(rendered)
        g["n_input_tokens"] = len(ids)
    batches = make_batches(groups, gen["batch_size"])
    plan = {
        "model_key": model_key, "batch_size": gen["batch_size"], "sort_key": exp["generation"]["sort_key"],
        "n_unique_prompts": len(groups), "n_prompt_ids": len(prompts), "n_batches": len(batches),
        "batches": [{"batch_index": i, "prompt_sha256": [g["prompt_sha256"] for g in b],
                     "first_prompt_ids": [g["prompt_ids"][0] for g in b],
                     "n_input_tokens": [g["n_input_tokens"] for g in b]} for i, b in enumerate(batches)],
    }
    eos_ids = set(spec["eos_token_ids"])
    settings = {
        "phase": phase, "model_key": model_key, "model_id": spec["hf_id"], "model_revision": spec["revision"],
        "prompts_file": exp["phases"][phase]["prompts_file"], "prompts_file_sha256": sha256_file(prompts_file),
        "prompt_arms": exp["phases"][phase].get("prompt_arms"),
        "dtype": gen["dtype"], "batch_size": gen["batch_size"], "max_new_tokens": gen["max_new_tokens"],
        "do_sample": gen["do_sample"], "num_beams": gen["num_beams"], "repetition_penalty": gen["repetition_penalty"],
        "padding_side": gen["padding_side"], "attn_implementation": gen["attn_implementation"],
        "eos_token_ids": sorted(eos_ids), "pad_token_id": spec["pad_token_id"], "pad_token": tokenizer.pad_token,
        "chat_template_sha256": spec["chat_template_sha256"],
        "chat_template_kwargs": spec.get("chat_template_kwargs", {}),
    }

    meta_path = model_dir / "run_meta.json"
    plan_path = model_dir / "batch_plan.json"
    fingerprint = env_fingerprint(env)
    meta = read_json(meta_path) if meta_path.exists() else None
    supersedes: list[dict] = []
    if meta is not None:
        if meta.get("status") == "complete" and (model_dir / "generations.jsonl").exists():
            # A complete model is never regenerated, whatever the environment (decision G2 §3.3).
            log(f"{model_key}: already complete ({meta['counts']['n_records']} records). Nothing to do.")
            return 0
        diff = fingerprint_diff(meta["environment_fingerprint"], fingerprint)
        changed = {k: (meta["settings"].get(k), v) for k, v in settings.items() if meta["settings"].get(k) != v}
        plan_changed = not plan_path.exists() or read_json(plan_path) != plan
        if diff and restart_if_environment_changed and not changed and not plan_changed:
            record = supersede_model_dir(run_dir, model_key, meta, fingerprint)
            supersedes = meta.get("supersedes", []) + [record]
            batches_dir.mkdir(parents=True, exist_ok=True)
            log(f"{model_key}: the environment changed ({', '.join(record['environment_diff'])}); the partial run "
                f"({record['n_batches_done']}/{record['n_batches']} batches) was moved to {record['path']} "
                "(kept, never analysed); regenerating this model from the start (decision G2 §3.3)")
            meta = None
        elif diff:
            log("REFUSING TO RESUME: this model's run started in a different environment:")
            for k, (a, b) in diff.items():
                log(f"  {k}: started with {a!r}, now {b!r}")
            log(f"Nothing was generated. To regenerate {model_key} from the start in this environment, set "
                f'RESTART_MODELS = "{model_key}" in the notebook and run all cells again (COLAB_RUNBOOK.md, '
                "section 4); the partial outputs are kept under superseded/.")
            return EXIT_ENV_MISMATCH
        elif changed:
            log(f"REFUSING TO RESUME: settings differ from the first session: {changed}")
            return EXIT_ENV_MISMATCH
        elif plan_changed:
            log("REFUSING TO RESUME: the batch plan differs from the first session.")
            return EXIT_ENV_MISMATCH
        else:
            meta["sessions"].append({"started_utc": utc_now(), "environment": env})
            write_json(meta_path, meta)
            log(f"{model_key}: resuming run {info['run_id']}")
    if meta is None:
        write_json(plan_path, plan)
        meta = {
            "run_id": info["run_id"], "phase": phase, "model_key": model_key, "status": "running",
            "settings": settings, "environment_fingerprint": fingerprint,
            "sessions": [{"started_utc": utc_now(), "environment": env}],
            "counts": {"n_prompt_ids": len(prompts), "n_unique_prompts": len(groups), "n_batches": len(batches),
                       "n_batches_done": 0, "n_records": 0},
            "retries": [], "batch_seconds": {}, "started_utc": utc_now(), "ended_utc": None,
        }
        if supersedes:
            meta["supersedes"] = supersedes
        write_json(meta_path, meta)
        log(f"{model_key}: new run {info['run_id']}: {len(groups)} unique prompts ({len(prompts)} ids), "
            f"{len(batches)} batches of {gen['batch_size']}")

    def done_batches() -> set[int]:
        done = set()
        for i, b in enumerate(plan["batches"]):
            path = batches_dir / batch_file_name(i)
            if path.exists():
                if validate_batch_file(path, b["prompt_sha256"]):
                    done.add(i)
                else:
                    corrupt = path.with_name(path.name + f".invalid-{int(time.time())}")
                    os.replace(path, corrupt)
                    log(f"batch {i}: existing file failed validation; kept as {corrupt.name} and regenerating")
        return done

    done = done_batches()
    if done:
        log(f"{len(done)}/{len(batches)} batches already done; skipping them")

    if len(done) < len(batches):
        torch.manual_seed(exp["seed"])
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.use_deterministic_algorithms(True, warn_only=True)
        model = None
        for attempt in range(gen["max_infra_retries"] + 1):
            try:
                model = load_model(spec, gen["dtype"], gen["device"], gen["attn_implementation"])
                break
            except (OSError, RuntimeError) as e:
                meta["retries"].append({"what": "load_model", "attempt": attempt, "error": repr(e)[:500],
                                        "utc": utc_now()})
                write_json(meta_path, meta)
                if attempt == gen["max_infra_retries"]:
                    raise
                log(f"model load failed ({e!r}); retry {attempt + 1}/{gen['max_infra_retries']}")
                time.sleep(10)
        gen_config = build_generation_config(spec, gen)
        model.generation_config = gen_config  # replace the Hub defaults entirely
        gen_record, gen_full = effective_generation_config(model, gen_config)
        meta["generation_config_effective"] = gen_record
        meta["generation_config_effective_full"] = gen_full
        meta["generation_config_explicit"] = gen_config.to_diff_dict()
        problems = check_generation_config(gen_full, gen["max_new_tokens"], spec["eos_token_ids"], spec["pad_token_id"])
        meta["r4_check"] = {"config_violations": problems, "passed": not problems, "checked_utc": utc_now(),
                            "batches_checked": meta.get("r4_check", {}).get("batches_checked", 0)}
        write_json(meta_path, meta)
        if problems:
            log("STOP (R4): the effective generation config is not the approved greedy configuration:")
            for p_ in problems:
                log(f"  {p_}")
            return EXIT_GENERATION_CHECK
        log("R4 check passed: effective generation config matches the allow-list")
        recorder = ProcessorRecorder(model)
        meta["model_class"] = f"{type(model).__module__}.{type(model).__name__}"
        meta["deterministic_settings"] = {"torch.manual_seed": exp["seed"], "allow_tf32": False,
                                          "use_deterministic_algorithms": "True (warn_only)",
                                          "CUBLAS_WORKSPACE_CONFIG": os.environ.get("CUBLAS_WORKSPACE_CONFIG")}
        write_json(meta_path, meta)
        a6_cfg = exp["phases"][phase].get("determinism_check")
        if a6_cfg and not (meta.get("a6_check") or {}).get("completed"):
            ctx = {"spec": spec, "env": env, "model_key": model_key, "info": info, "phase": phase, "gen": gen,
                   "gen_record": gen_record}
            code = determinism_check(a6_cfg, ctx, model, tokenizer, gen_config, recorder, meta, meta_path, log)
            if code:
                return code

        generated_this_session = 0
        for i, batch in enumerate(batches):
            if i in done:
                continue
            t0 = time.time()
            for attempt in range(gen["max_infra_retries"] + 1):
                try:
                    recorder.reset()
                    outputs = generate_batch(model, tokenizer, gen_config, [g["rendered"] for g in batch], eos_ids,
                                             gen["device"])
                    break
                except (RuntimeError, OSError) as e:  # torch.OutOfMemoryError is a RuntimeError
                    meta["retries"].append({"what": f"batch {i}", "attempt": attempt, "error": repr(e)[:500],
                                            "utc": utc_now()})
                    write_json(meta_path, meta)
                    if attempt == gen["max_infra_retries"]:
                        log(f"batch {i} failed after {attempt + 1} attempts; stopping. Re-run the cell to resume.")
                        raise
                    log(f"batch {i}: infrastructure error {e!r}; retry {attempt + 1}/{gen['max_infra_retries']}")
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    time.sleep(5)
            seconds = time.time() - t0
            proc_problems = check_processors(recorder.logits_processors, recorder.stopping_criteria)
            if proc_problems:
                meta["r4_check"].update({"passed": False, "processor_violations": proc_problems,
                                         "failed_batch": i})
                write_json(meta_path, meta)
                log(f"STOP (R4): batch {i} was generated with unexpected processors; nothing written for it:")
                for p_ in proc_problems:
                    log(f"  {p_}")
                return EXIT_GENERATION_CHECK
            meta["r4_check"]["batches_checked"] += 1
            meta["r4_check"]["logits_processors"] = recorder.logits_processors
            meta["r4_check"]["stopping_criteria"] = recorder.stopping_criteria
            stamp = utc_now()
            lines = [dumps_record(generation_record(info, phase, model_key, spec, g, output, gen["batch_size"], i, gen,
                                                    env, gen_record, stamp)) for g, output in zip(batch, outputs)]
            atomic_write_text(batches_dir / batch_file_name(i), "\n".join(lines) + "\n")
            meta["batch_seconds"][str(i)] = round(seconds, 2)
            meta["counts"]["n_batches_done"] = len(done) + generated_this_session + 1
            write_json(meta_path, meta)
            generated_this_session += 1
            n_len = sum(1 for _, _, r in outputs if r == "length")
            log(f"batch {i + 1}/{len(batches)} done in {seconds:.1f}s ({len(batch)} prompts, {n_len} hit the length limit)")
            if stop_after_batches is not None and generated_this_session >= stop_after_batches:
                meta["sessions"][-1]["ended_utc"] = utc_now()
                meta["sessions"][-1]["stopped_by_flag"] = True
                write_json(meta_path, meta)
                log(f"stopping after {generated_this_session} batch(es) as requested (--stop-after-batches)")
                return EXIT_STOPPED_BY_FLAG

    # Completion: concatenate the batch files in batch order.
    parts = []
    n_records = 0
    for i, b in enumerate(plan["batches"]):
        path = batches_dir / batch_file_name(i)
        if not validate_batch_file(path, b["prompt_sha256"]):
            raise RuntimeError(f"batch file {path.name} missing or invalid at completion")
        text = path.read_text(encoding="utf-8")
        parts.append(text)
        n_records += len(b["prompt_sha256"])
    atomic_write_text(model_dir / "generations.jsonl", "".join(parts))
    meta["status"] = "complete"
    meta["ended_utc"] = utc_now()
    meta["sessions"][-1]["ended_utc"] = meta["ended_utc"]
    meta["counts"]["n_records"] = n_records
    meta["counts"]["n_batches_done"] = len(batches)
    meta["generations_sha256"] = sha256_file(model_dir / "generations.jsonl")
    meta["generation_seconds_total"] = round(sum(meta["batch_seconds"].values()), 2)
    write_json(meta_path, meta)
    log(f"{model_key}: complete -- {n_records} records in generations.jsonl")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--phase", required=True)
    r.add_argument("--model", required=True)
    r.add_argument("--run-dir", type=Path, required=True)
    r.add_argument("--stop-after-batches", type=int, default=None,
                   help="testing aid: stop after N batches of this session (dry-run interruption test)")
    r.add_argument("--restart-if-environment-changed", action="store_true",
                   help="decision G2 §3.3: if this model's partial run cannot resume because the environment changed, "
                        "move it to superseded/ (kept) and regenerate the model from the start")
    args = ap.parse_args(argv)
    try:
        return run(args.phase, args.model, args.run_dir, args.stop_after_batches, args.restart_if_environment_changed)
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

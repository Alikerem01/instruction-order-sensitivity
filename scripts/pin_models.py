"""Resolve and pin the Hub revision of every model and write configs/models.yaml (setup step C0).

For each model this script records the current commit hash, license, parameter count (safetensors metadata),
architecture, end-of-turn token ids, pad token and the SHA-256 of the chat template, and it checks (without
downloading weights) that the architecture is native to the pinned transformers version
(trust_remote_code=False) and that the chat template renders the system message exactly once.

Run once at setup; afterwards models.yaml is the source of truth and is never silently re-pinned.
``--add KEY`` pins a model added later (decision D06: gemma4e4b) and leaves every existing entry unchanged.

Usage: python scripts/pin_models.py [--out configs/models.yaml]
       python scripts/pin_models.py --add gemma4e4b
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MODELS = {
    "smollm2": {"hf_id": "HuggingFaceTB/SmolLM2-1.7B-Instruct", "parameters_nominal": "1.7B",
                "license": "Apache-2.0"},
    "qwen25": {"hf_id": "Qwen/Qwen2.5-3B-Instruct", "parameters_nominal": "3.1B",
               "license": "Qwen Research License (non-commercial)"},
    "phi4mini": {"hf_id": "microsoft/Phi-4-mini-instruct", "parameters_nominal": "3.8B", "license": "MIT"},
    # Fourth model, decision D06 (2026-10-04). Model card: "4.5B effective (8B with embeddings)", Apache 2.0;
    # multimodal checkpoint (text, image, audio) used for text-only inputs; thinking mode disabled.
    "gemma4e4b": {"hf_id": "google/gemma-4-E4B-it", "parameters_nominal": "E4B",
                  "parameters_effective": "4.5B effective (8B with embeddings), as stated in the model card",
                  "license": "Apache-2.0", "chat_template_kwargs": {"enable_thinking": False},
                  "thinking_markers": ["<|think|>", "<|channel>", "<channel|>"],
                  "usage_note": ("Official class Gemma4ForConditionalGeneration (multimodal: text, image, audio), "
                                 "loaded natively and used for text-only inputs (input_ids and attention_mask "
                                 "only); native system role; thinking disabled with enable_thinking=False.")},
}
DRYRUN_MODELS = {
    "smollm2_135m": {"hf_id": "HuggingFaceTB/SmolLM2-135M-Instruct", "parameters_nominal": "135M",
                     "license": "Apache-2.0"},
}
PROBE_USER = "INSTRUCTIONS:\n- probe\n\nTASK:\nprobe\n\nINPUT:\nprobe"


class _LiteralDumper(yaml.SafeDumper):
    """Writes multi-line strings (chat-template renderings) as literal blocks for readability."""


def _str_representer(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_LiteralDumper.add_representer(str, _str_representer)


def chat_template_sha256(tokenizer) -> str:
    tmpl = tokenizer.chat_template
    text = tmpl if isinstance(tmpl, str) else json.dumps(tmpl, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def inspect(key: str, spec: dict, system_prompt: str) -> dict:
    import torch
    from huggingface_hub import HfApi, hf_hub_download
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    api = HfApi()
    info = api.model_info(spec["hf_id"])
    rev = info.sha
    card = info.card_data.to_dict() if info.card_data else {}
    tok = AutoTokenizer.from_pretrained(spec["hf_id"], revision=rev, trust_remote_code=False)
    cfg = AutoConfig.from_pretrained(spec["hf_id"], revision=rev, trust_remote_code=False)
    with torch.device("meta"):
        model = AutoModelForCausalLM.from_config(cfg, trust_remote_code=False)
    module = type(model).__module__
    if not module.startswith("transformers.models."):
        raise RuntimeError(f"{key}: model class {module} is not native to transformers")
    gen_cfg = json.load(open(hf_hub_download(spec["hf_id"], "generation_config.json", revision=rev)))
    eos = gen_cfg.get("eos_token_id", cfg.eos_token_id)
    eos_ids = [int(x) for x in (eos if isinstance(eos, list) else [eos])]
    if tok.pad_token_id is None:
        raise RuntimeError(f"{key}: tokenizer has no pad token; set one explicitly before pinning")

    kwargs = spec.get("chat_template_kwargs", {})
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": PROBE_USER}]
    rendered = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, **kwargs)
    ids_template = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, **kwargs)
    if hasattr(ids_template, "keys"):
        ids_template = ids_template["input_ids"]
    ids_plain = tok(rendered, add_special_tokens=False)["input_ids"]
    no_system = tok.apply_chat_template(messages[1:], tokenize=False, add_generation_prompt=True, **kwargs)
    prefix_without_system = no_system.split(PROBE_USER)[0] if PROBE_USER in no_system else ""
    checks = {
        "system_message_count": rendered.count(system_prompt),
        "user_message_count": rendered.count(PROBE_USER),
        "template_tokens_equal_plain_tokenization": list(ids_template) == list(ids_plain),
        "end_of_turn_tokens_in_template_vocab": all(tok.convert_ids_to_tokens(i) is not None for i in eos_ids),
    }
    if spec.get("thinking_markers"):
        checks["no_thinking_markers_in_rendered_prompt"] = not any(m in rendered for m in spec["thinking_markers"])
        system_turn_end = rendered.find(system_prompt) + len(system_prompt)
        checks["system_message_in_its_own_turn"] = rendered.find(PROBE_USER) > system_turn_end and "user" in \
            rendered[system_turn_end:rendered.find(PROBE_USER)]
    if checks["system_message_count"] != 1 or checks["user_message_count"] != 1 or not all(checks.values()):
        raise RuntimeError(f"{key}: chat template check failed {checks}")
    entry = {
        "hf_id": spec["hf_id"],
        "revision": rev,
        "hub_last_modified": str(info.last_modified),
        "parameters_nominal": spec["parameters_nominal"],
        "parameters_safetensors": int(info.safetensors.total) if info.safetensors else None,
        "license": spec["license"],
        "license_hub_metadata": card.get("license_name") or card.get("license"),
        "architecture": (cfg.architectures or [None])[0],
        "model_type": cfg.model_type,
        "native_class_module": module,
        "trust_remote_code": False,
        "hub_has_remote_code": bool(getattr(cfg, "auto_map", None)),
        "torch_dtype_hub": str(getattr(cfg, "dtype", None) or getattr(cfg, "torch_dtype", None)),
        "eos_token_ids": eos_ids,
        "eos_tokens": tok.convert_ids_to_tokens(eos_ids),
        "pad_token_id": int(tok.pad_token_id),
        "pad_token": tok.pad_token,
        "tokenizer_class": type(tok).__name__,
        "chat_template_sha256": chat_template_sha256(tok),
        "chat_template_checks": checks,
        "render_prefix_without_system_message": prefix_without_system,
        "rendered_probe": rendered,
        "hub_generation_config_not_used": {k: v for k, v in gen_cfg.items() if k != "transformers_version"},
    }
    if "parameters_effective" in spec:  # models added later (D06) record a few more facts
        with torch.device("meta"):
            n_instantiated = sum(p.numel() for p in model.parameters())
        entry = {"pinned_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), **entry}
        entry.update({
            "parameters_effective": spec["parameters_effective"],
            "parameters_instantiated": int(n_instantiated),
            "hub_gated": bool(info.gated),
            "chat_template_kwargs": spec["chat_template_kwargs"],
            "thinking_markers": spec["thinking_markers"],
            "usage_note": spec["usage_note"],
        })
    return entry


def main(argv: list[str] | None = None) -> int:
    import huggingface_hub
    import transformers

    from src.common import load_prompt_strings

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "configs" / "models.yaml")
    ap.add_argument("--add", nargs="+", default=None, help="pin only these new model keys; keep every existing entry")
    args = ap.parse_args(argv)
    system_prompt = load_prompt_strings()["system"]
    if args.add:
        text = args.out.read_text(encoding="utf-8")
        header = "".join(line for line in text.splitlines(keepends=True) if line.startswith("#"))
        doc = yaml.safe_load(text[len(header):])
        for key in args.add:
            if key in doc["models"]:
                raise SystemExit(f"{key} is already pinned; existing entries are never re-pinned")
            doc["models"][key] = inspect(key, MODELS[key], system_prompt)
            v = doc["models"][key]
            print(f"{key:14s} {v['hf_id']:40s} {v['revision']}  params={v['parameters_safetensors']}  eos={v['eos_token_ids']}")
        args.out.write_text(header + yaml.dump(doc, Dumper=_LiteralDumper, sort_keys=False, allow_unicode=True,
                                               width=120), encoding="utf-8")
        return 0
    doc = {
        "pinned_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pinned_with": {"transformers": transformers.__version__, "huggingface_hub": huggingface_hub.__version__},
        "models": {k: inspect(k, v, system_prompt) for k, v in MODELS.items() if "parameters_effective" not in v},
        "dryrun_models": {k: inspect(k, v, system_prompt) for k, v in DRYRUN_MODELS.items()},
    }
    # an existing file keeps its header comment byte for byte; a new file gets the default header
    header = "".join(line for line in args.out.read_text(encoding="utf-8").splitlines(keepends=True)
                     if line.startswith("#")) if args.out.exists() else ""
    header = header or (
        "# Pinned model revisions. Written by scripts/pin_models.py; do not edit by hand.\n"
        "# Generation reads hf_id, revision, eos_token_ids, pad_token_id and chat_template_sha256 from here.\n"
        "# hub_generation_config_not_used: the Hub defaults, recorded for transparency; generation builds its\n"
        "# GenerationConfig from scratch (brief §5.7) and never uses these values.\n"
    )
    args.out.write_text(header + yaml.dump(doc, Dumper=_LiteralDumper, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    for section in ("models", "dryrun_models"):
        for k, v in doc[section].items():
            print(f"{k:14s} {v['hf_id']:40s} {v['revision']}  params={v['parameters_safetensors']}  eos={v['eos_token_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Render every unique main and pilot prompt with each pinned tokenizer (no model weights) and report checks.

For each model: chat-template SHA-256 equals models.yaml; the system and user messages appear exactly once in
every rendering; input-length statistics per family (tokens); no prompt exceeds the context window together
with max_new_tokens; the batch plan size per phase.

Usage: python scripts/check_chat_templates.py [--json-out FILE]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.common import load_experiment, load_models, read_jsonl  # noqa: E402
from src.generate import dedup_prompts, load_tokenizer, make_batches, render  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    from transformers import AutoConfig

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args(argv)
    exp = load_experiment()
    models = load_models()["models"]
    max_new = exp["generation"]["max_new_tokens"]
    report = {}
    for key, spec in models.items():
        tok = load_tokenizer(spec, exp["generation"]["padding_side"])  # raises if the template hash differs
        cfg = AutoConfig.from_pretrained(spec["hf_id"], revision=spec["revision"], trust_remote_code=False)
        ctx = cfg.get_text_config().max_position_embeddings  # multimodal configs keep it in text_config
        entry = {"chat_template_sha256_matches": True, "context_window": ctx}
        for phase in ("pilot", "main"):
            groups = dedup_prompts(read_jsonl(ROOT / exp["phases"][phase]["prompts_file"]))
            by_family = defaultdict(list)
            for g in groups:
                _, ids = render(tok, g, spec)  # raises unless system and user appear exactly once (and no thinking marker)
                g["n_input_tokens"] = len(ids)
                by_family[g["family"]].append(len(ids))
            lengths = [g["n_input_tokens"] for g in groups]
            entry[phase] = {
                "unique_prompts": len(groups),
                "system_and_user_once": True,
                "input_tokens": {"min": min(lengths), "median": statistics.median(lengths), "max": max(lengths)},
                "input_tokens_by_family_max": {f: max(v) for f, v in sorted(by_family.items())},
                "over_context_with_max_new_tokens": sum(n + max_new > ctx for n in lengths),
                "n_batches": len(make_batches(groups, exp["generation"]["batch_size"])),
            }
        report[key] = entry
        m = entry["main"]
        print(f"{key:9s} template OK | main: {m['unique_prompts']} prompts, input tokens min/median/max = "
              f"{m['input_tokens']['min']}/{m['input_tokens']['median']}/{m['input_tokens']['max']}, "
              f"{m['n_batches']} batches, over context: {m['over_context_with_max_new_tokens']} | "
              f"pilot: {entry['pilot']['unique_prompts']} prompts, {entry['pilot']['n_batches']} batches")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

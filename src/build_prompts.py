"""Build prompts_main.jsonl (2,000 ids), prompts_pilot.jsonl (200 ids) and prompts_smoke.jsonl (5 ids).

Per task: the order arm P01-P10 (canonical format, Williams orders) and the format arm V01-V10 (order fixed
at P01). P01 and V01 are byte-identical; ``shared_with`` lists the other ids in the same file with the same
text, and generation deduplicates by ``prompt_sha256``.

Usage: python -m src.build_prompts [--bench-dir DIR]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from src.common import (
    BENCH_DIR,
    active_instruction_keys,
    all_instruction_strings,
    load_experiment,
    load_prompt_strings,
    prompt_text_sha256,
    read_jsonl,
    sha256_file,
    write_jsonl,
)
from src.orders import CANONICAL_ORDER_ID, ORDER_IDS, ORDERS, order_slots
from src.prompt_builder import FORMAT_VARIANTS, VARIANT_IDS, render_user_prompt


def prompts_for_task(task: dict, system_prompt: str, slot_keys: dict[str, str], strings: dict[str, str]) -> list[dict]:
    records = []

    def make(arm: str, condition_id: str, order_id: str, variant_id: str) -> dict:
        keys = [slot_keys[slot] for slot in order_slots(order_id)]
        user_prompt = render_user_prompt(
            [strings[k] for k in keys], task["task_directive"], task["input_text"], FORMAT_VARIANTS[variant_id]
        )
        return {
            "prompt_id": f"{task['task_id']}__{condition_id}",
            "task_id": task["task_id"],
            "family": task["family"],
            "split": task["split"],
            "arm": arm,
            "condition_id": condition_id,
            "order_id": order_id,
            "order_code": ORDERS[order_id],
            "format_variant": variant_id,
            "instruction_order": keys,
            "instruction_positions": {k: i for i, k in enumerate(keys, 1)},
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "prompt_sha256": prompt_text_sha256(system_prompt, user_prompt),
            "shared_with": [],
        }

    for order_id in ORDER_IDS:
        records.append(make("order", order_id, order_id, "V01"))
    for variant_id in VARIANT_IDS:
        records.append(make("format", variant_id, CANONICAL_ORDER_ID, variant_id))
    return records


def fill_shared_with(records: list[dict]) -> list[dict]:
    by_hash: dict[str, list[str]] = defaultdict(list)
    for r in records:
        by_hash[r["prompt_sha256"]].append(r["prompt_id"])
    out = []
    for r in records:
        r = dict(r)
        r["shared_with"] = sorted(pid for pid in by_hash[r["prompt_sha256"]] if pid != r["prompt_id"])
        out.append(r)
    return out


def build(bench_dir: Path = BENCH_DIR) -> dict:
    exp = load_experiment()
    ps = load_prompt_strings()
    slot_keys = active_instruction_keys(exp)
    strings = all_instruction_strings(ps)
    system_prompt = ps["system"]

    summary = {}
    pilot_records: list[dict] = []
    for split in ("main", "pilot"):
        tasks = read_jsonl(bench_dir / f"tasks_{split}.jsonl")
        records = [r for t in tasks for r in prompts_for_task(t, system_prompt, slot_keys, strings)]
        records = fill_shared_with(records)
        write_jsonl(bench_dir / f"prompts_{split}.jsonl", records)
        summary[split] = {"ids": len(records), "unique_texts": len({r["prompt_sha256"] for r in records})}
        if split == "pilot":
            pilot_records = records

    # Smoke test: the first pilot task of each family, order P01.
    first_pilot = {}
    for r in pilot_records:
        first_pilot.setdefault(r["family"], r["task_id"])
    smoke = [r for r in pilot_records if r["task_id"] in first_pilot.values() and r["condition_id"] == "P01"]
    smoke = fill_shared_with([{**r, "shared_with": []} for r in smoke])
    write_jsonl(bench_dir / "prompts_smoke.jsonl", smoke)
    summary["smoke"] = {"ids": len(smoke), "unique_texts": len({r["prompt_sha256"] for r in smoke})}
    summary["files"] = {f"prompts_{s}.jsonl": sha256_file(bench_dir / f"prompts_{s}.jsonl")
                        for s in ("main", "pilot", "smoke")}
    summary["active_instructions"] = slot_keys
    return summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench-dir", type=Path, default=BENCH_DIR)
    args = ap.parse_args(argv)
    print(json.dumps(build(args.bench_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Token-level edit distance of every prompt to its task's P01 prompt (decision R1 §3.10; post-hoc, descriptive).

Per model tokenizer (pinned revision, read from the local Hugging Face cache only), the Levenshtein distance between
the token-id sequences of the user prompt and the task's P01 (= V01) user prompt; reported as the median over the
nine formatting variants (V02-V10) and over the nine reorderings (P02-P10), all 100 main tasks. Skipped with a status
key when a tokenizer is not in the cache.
"""

from __future__ import annotations

import os

import numpy as np

from src.common import BENCH_DIR, load_models, read_jsonl


def levenshtein(a: list[int], b: list[int]) -> int:
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    a, b = a[i:], b[i:]
    j = 0
    while j < min(len(a), len(b)) and a[-1 - j] == b[-1 - j]:
        j += 1
    a, b = (a[: len(a) - j], b[: len(b) - j])
    if not a or not b:
        return max(len(a), len(b))
    bb = np.asarray(b)
    ar = np.arange(len(b) + 1)
    prev = ar.copy()
    for k, x in enumerate(a, start=1):
        cand = np.empty_like(prev)
        cand[0] = k
        cand[1:] = np.minimum(prev[1:] + 1, prev[:-1] + (bb != x))
        prev = np.minimum.accumulate(cand - ar) + ar  # insertions along the row
    return int(prev[-1])


def edit_distances(models: list[str], prefix: str = "main.posthoc_r1.edit_distance") -> dict:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from src.generate import load_tokenizer

    prompts = read_jsonl(BENCH_DIR / "prompts_main.jsonl")
    by_task: dict[str, dict[str, str]] = {}
    for p in prompts:
        by_task.setdefault(p["task_id"], {})[p["condition_id"]] = p["user_prompt"]
    out = {f"{prefix}.label": "post-hoc, descriptive (decision R1 §3.10)"}
    specs = load_models()["models"]
    for m in models:
        try:
            tok = load_tokenizer(specs[m], "left")
        except Exception as e:  # no network access here: a tokenizer outside the cache is reported, not fetched
            out[f"{prefix}.{m}.status"] = f"tokenizer not available ({type(e).__name__})"
            continue
        fmt, ordr = [], []
        for conds in by_task.values():
            ref = tok(conds["P01"], add_special_tokens=False)["input_ids"]
            for cid, text in conds.items():
                if cid in ("P01", "V01"):
                    continue
                d = levenshtein(ref, tok(text, add_special_tokens=False)["input_ids"])
                (fmt if cid.startswith("V") else ordr).append(d)
        out.update({f"{prefix}.{m}.status": "estimated", f"{prefix}.{m}.median_format_variants": float(np.median(fmt)),
                    f"{prefix}.{m}.median_reorderings": float(np.median(ordr)), f"{prefix}.{m}.n_pairs_each": len(fmt)})
    return out

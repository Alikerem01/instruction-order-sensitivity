"""Integrity tests for the evaluation set and prompts (implementation specification §6.3).

All tests must pass before any bundle is built. Tests 1-11 are the required ones; tests prefixed "X"
are additional safeguards.

Usage: python -m src.validate_integrity [--json-out FILE] [--skip-rebuild]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path

from src.common import (
    BENCH_DIR,
    REPO_ROOT,
    active_instruction_keys,
    all_instruction_strings,
    load_experiment,
    load_phase_prompts,
    load_prompt_strings,
    prompt_text_sha256,
    read_jsonl,
    sha256_file,
)
from src.evaluators.quality import LABEL_SYNONYMS, qa_tokens
from src.orders import ORDER_IDS, ORDERS, LETTER_TO_SLOT, verify_orders
from src.prepare_tasks import leaks
from src.prompt_builder import VARIANT_IDS, canonicalize, instruction_lines_removed, parse_user_prompt

F2_LABEL_LIST = "World, Sports, Business, Sci/Tech"
BRIEF_PATH = REPO_ROOT.parent / "orchestration" / "PROJECT_BRIEF.md"


class Results:
    def __init__(self) -> None:
        self.items: list[dict] = []

    def add(self, test_id: str, name: str, errors: list[str], detail: str = "") -> None:
        self.items.append({"id": test_id, "name": name, "passed": not errors, "detail": detail,
                           "errors": errors[:20], "n_errors": len(errors)})

    @property
    def ok(self) -> bool:
        return all(i["passed"] for i in self.items)

    def print(self) -> None:
        for i in self.items:
            status = "PASS" if i["passed"] else "FAIL"
            print(f"[{status}] {i['id']:>3} {i['name']}" + (f" -- {i['detail']}" if i["detail"] else ""))
            for e in i["errors"]:
                print(f"         ! {e}")
        n_pass = sum(i["passed"] for i in self.items)
        print(f"\n{n_pass}/{len(self.items)} integrity tests passed.")


def gold_strings(task: dict) -> list[str]:
    gold = task["gold"]
    fam = task["family"]
    if fam == "F1_QA":
        return list(gold["answers"])
    if fam == "F2_CLASSIFICATION":
        return [gold["label"], *LABEL_SYNONYMS[gold["label"]]]
    if fam == "F3_SUMMARIZATION":
        return [gold["summary"]]
    out = []
    for value in gold.values():
        out.append(value)
        if value.endswith(" USD"):
            out.append(value[: -len(" USD")])
    return out


def run(bench_dir: Path = BENCH_DIR, skip_rebuild: bool = False) -> Results:
    res = Results()
    exp = load_experiment()
    ps = load_prompt_strings()
    fam_cfg = exp["evaluation_set"]["families"]
    slot_keys = active_instruction_keys(exp)
    strings = all_instruction_strings(ps)
    active_strings = {slot_keys[s]: strings[slot_keys[s]] for s in slot_keys}
    string_to_key = {v: k for k, v in active_strings.items()}
    letter_to_key = {letter: slot_keys[slot] for letter, slot in LETTER_TO_SLOT.items()}

    tasks_main = read_jsonl(bench_dir / "tasks_main.jsonl")
    tasks_pilot = read_jsonl(bench_dir / "tasks_pilot.jsonl")
    prompts = {s: read_jsonl(bench_dir / f"prompts_{s}.jsonl") for s in ("main", "pilot", "smoke")}
    tasks_by_id = {t["task_id"]: t for t in tasks_main + tasks_pilot}

    # ---- 1. main tasks -------------------------------------------------------------------------
    errs = []
    fam_counts = Counter(t["family"] for t in tasks_main)
    if len(tasks_main) != 100:
        errs.append(f"{len(tasks_main)} main tasks")
    for fam, cfg in fam_cfg.items():
        if fam_counts[fam] != cfg["main"]:
            errs.append(f"{fam}: {fam_counts[fam]} main tasks")
    cls = Counter(t["gold"]["label"] for t in tasks_main if t["family"] == "F2_CLASSIFICATION")
    per_class = exp["evaluation_set"]["f2_main_per_class"]
    if sorted(cls.values()) != [per_class] * 4:
        errs.append(f"F2 class counts {dict(cls)}")
    res.add("1", "100 main tasks, 20 per family, 5 per class in F2", errs,
            f"families={dict(fam_counts)}; F2 classes={dict(sorted(cls.items()))}")

    # ---- 2. pilot tasks ------------------------------------------------------------------------
    errs = []
    pf = Counter(t["family"] for t in tasks_pilot)
    if len(tasks_pilot) != 10 or any(pf[f] != c["pilot"] for f, c in fam_cfg.items()):
        errs.append(f"pilot counts {dict(pf)}")
    if {t["task_id"] for t in tasks_main} & {t["task_id"] for t in tasks_pilot}:
        errs.append("task ids overlap")
    main_src = {(t["family"], t["source_id"]) for t in tasks_main}
    if any((t["family"], t["source_id"]) in main_src for t in tasks_pilot):
        errs.append("source ids overlap")
    main_ctx = {t["input_text"] for t in tasks_main if t["family"] == "F1_QA"}
    if any(t["input_text"] in main_ctx for t in tasks_pilot if t["family"] == "F1_QA"):
        errs.append("SQuAD contexts overlap")
    all_ctx = [t["input_text"] for t in tasks_main + tasks_pilot if t["family"] == "F1_QA"]
    if len(all_ctx) != len(set(all_ctx)):
        errs.append("a SQuAD context is used twice")
    pilot_classes = [t["gold"]["label"] for t in tasks_pilot if t["family"] == "F2_CLASSIFICATION"]
    if len(set(pilot_classes)) != len(pilot_classes):
        errs.append(f"F2 pilot classes not distinct: {pilot_classes}")
    res.add("2", "10 pilot tasks, 2 per family, disjoint from main (ids, sources, SQuAD contexts)", errs,
            f"pilot families={dict(pf)}; F2 pilot classes={pilot_classes}")

    # ---- per-prompt parsing used by tests 3-8 ------------------------------------------------------
    parse_errors = []
    parsed: dict[str, object] = {}
    for split, recs in prompts.items():
        for r in recs:
            try:
                parsed[(split, r["prompt_id"])] = parse_user_prompt(r["user_prompt"])
            except ValueError as e:
                parse_errors.append(f"{split}/{r['prompt_id']}: {e}")

    by_task: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for split in ("main", "pilot"):
        for r in prompts[split]:
            by_task[(split, r["task_id"])].append(r)

    # ---- 3. order arm balance (from the rendered text) -----------------------------------------
    errs = list(parse_errors)
    for (split, task_id), recs in by_task.items():
        order = [r for r in recs if r["arm"] == "order"]
        if sorted(r["condition_id"] for r in order) != list(ORDER_IDS):
            errs.append(f"{task_id}: order-arm ids {[r['condition_id'] for r in order]}")
            continue
        seqs = {}
        for r in order:
            lines = parsed[(split, r["prompt_id"])].instructions
            keys = [string_to_key.get(line, f"<unknown:{line[:30]}>") for line in lines]
            expected = [letter_to_key[ch] for ch in ORDERS[r["condition_id"]]]
            if keys != expected:
                errs.append(f"{r['prompt_id']}: rendered order {keys} != {expected}")
            if r["instruction_order"] != expected:
                errs.append(f"{r['prompt_id']}: metadata order mismatch")
            seqs[r["condition_id"]] = keys
        pos = Counter((k, p) for seq in seqs.values() for p, k in enumerate(seq, 1))
        if any(pos[(k, p)] != 2 for k in active_strings for p in range(1, 6)):
            errs.append(f"{task_id}: position balance violated")
        adj = Counter((s[i], s[i + 1]) for s in seqs.values() for i in range(len(s) - 1))
        if any(adj[(x, y)] != 2 for x, y in permutations(active_strings, 2)):
            errs.append(f"{task_id}: adjacency balance violated")
    res.add("3", "order arm: 10 prompts per task; each instruction in each position twice; each ordered adjacent "
            "pair twice", errs, f"{len(by_task)} tasks checked from rendered text")

    # ---- 4. TASK block, INPUT block, system prompt identical within a task --------------------------
    errs = []
    for (split, task_id), recs in by_task.items():
        task = tasks_by_id[task_id]
        if len(recs) != 20:
            errs.append(f"{task_id}: {len(recs)} prompts")
        blocks = {(parsed[(split, r["prompt_id"])].task, parsed[(split, r["prompt_id"])].input, r["system_prompt"])
                  for r in recs}
        if len(blocks) != 1:
            errs.append(f"{task_id}: {len(blocks)} distinct (TASK, INPUT, system) combinations")
        elif next(iter(blocks)) != (task["task_directive"], task["input_text"], ps["system"]):
            errs.append(f"{task_id}: blocks differ from the task record")
    res.add("4", "within a task, TASK block, INPUT block and system prompt are byte-identical across all 20 prompts",
            errs)

    # ---- 5. instruction multiset and verbatim strings ----------------------------------------------
    errs = []
    expected_multiset = Counter(active_strings.values())
    for split, recs in prompts.items():
        for r in recs:
            lines = parsed[(split, r["prompt_id"])].instructions
            if Counter(lines) != expected_multiset:
                errs.append(f"{split}/{r['prompt_id']}: instruction multiset differs")
            for line in lines:
                if line not in active_strings.values():
                    errs.append(f"{split}/{r['prompt_id']}: instruction not in prompt_strings.yaml: {line[:50]}")
    res.add("5", "every prompt has the same instruction multiset; every instruction matches prompt_strings.yaml",
            errs, f"active keys: {list(active_strings)}")

    # ---- 6. order arm identical once instruction lines are removed --------------------------------
    errs = []
    for (split, task_id), recs in by_task.items():
        stripped = {instruction_lines_removed(r["user_prompt"]) for r in recs if r["arm"] == "order"}
        if len(stripped) != 1:
            errs.append(f"{task_id}: {len(stripped)} distinct prompts after removing instruction lines")
    res.add("6", "order arm: prompts are identical with the instruction lines removed", errs)

    # ---- 7. format arm canonicalizes to V01; V01 == P01 ---------------------------------------------
    errs = []
    for (split, task_id), recs in by_task.items():
        fmt = {r["condition_id"]: r["user_prompt"] for r in recs if r["arm"] == "format"}
        p01 = next(r["user_prompt"] for r in recs if r["condition_id"] == "P01")
        if sorted(fmt) != list(VARIANT_IDS):
            errs.append(f"{task_id}: format ids {sorted(fmt)}")
            continue
        if fmt["V01"] != p01:
            errs.append(f"{task_id}: V01 is not byte-identical to P01")
        for vid, text in fmt.items():
            if canonicalize(text) != fmt["V01"]:
                errs.append(f"{task_id}/{vid}: canonicalize() != V01")
            if vid != "V01" and text == fmt["V01"]:
                errs.append(f"{task_id}/{vid}: variant identical to V01")
        if len(set(fmt.values())) != 10:
            errs.append(f"{task_id}: format variants not all distinct")
    res.add("7", "format arm: canonicalize(V_k) == V01 for every k; V01 byte-identical to P01", errs)

    # ---- 8. gold leakage into INSTRUCTIONS / TASK ----------------------------------------------------
    errs = []
    for split, recs in prompts.items():
        for r in recs:
            task = tasks_by_id[r["task_id"]]
            p = parsed[(split, r["prompt_id"])]
            instr_text = "\n".join(p.instructions)
            task_text = p.task
            if task["family"] == "F2_CLASSIFICATION":
                if F2_LABEL_LIST not in task_text:
                    errs.append(f"{r['prompt_id']}: F2 label list not found")
                task_text = task_text.replace(F2_LABEL_LIST, " ")
            for g in gold_strings(task):
                if leaks(g, instr_text) or leaks(g, task_text):
                    errs.append(f"{split}/{r['prompt_id']}: gold {g[:40]!r} occurs in INSTRUCTIONS or TASK")
    res.add("8", "no gold string occurs in the INSTRUCTIONS or TASK blocks (F2 label list exempt)", errs,
            "whole-token match after SQuAD normalization")

    # ---- 9. ASCII-only strings -----------------------------------------------------------------------
    errs = []
    checked = {"system": ps["system"], **strings, **{f"directive:{k}": v for k, v in ps["task_directives"].items()}}
    for key, value in checked.items():
        if not value.isascii():
            errs.append(f"{key} contains non-ASCII characters")
    res.add("9", "system, instruction and directive strings are ASCII-only", errs, f"{len(checked)} strings checked")

    # ---- 10. determinism -------------------------------------------------------------------------------
    errs = []
    files = ["tasks_main.jsonl", "tasks_pilot.jsonl", "prompts_main.jsonl", "prompts_pilot.jsonl",
             "prompts_smoke.jsonl"]
    if skip_rebuild:
        detail = "skipped (--skip-rebuild)"
    else:
        from src import build_prompts, prepare_tasks

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            prepare_tasks.build(tmp)
            build_prompts.build(tmp)
            for name in files:
                a, b = sha256_file(bench_dir / name), sha256_file(tmp / name)
                if a != b:
                    errs.append(f"{name}: committed {a[:12]} != rebuilt {b[:12]}")
        detail = "tasks and prompts rebuilt from scratch in a temporary directory; SHA-256 compared"
    res.add("10", "determinism: rebuilding yields identical SHA-256 for tasks and prompts", errs, detail)

    # ---- 11. counts -------------------------------------------------------------------------------------
    errs = []
    counts = {}
    for split, recs in prompts.items():
        ids = len(recs)
        uniq = len({r["prompt_sha256"] for r in recs})
        counts[split] = (ids, uniq)
        exp_counts = exp["prompts"]["expected"][split]
        if (ids, uniq) != (exp_counts["ids"], exp_counts["unique_texts"]):
            errs.append(f"{split}: {ids} ids / {uniq} unique, expected {exp_counts}")
    res.add("11", "counts: main 2,000 ids / 1,900 unique texts; pilot 200 / 190 (smoke 5 / 5)", errs,
            "; ".join(f"{s}={i} ids/{u} unique" for s, (i, u) in counts.items()))

    # ---- X1. Williams design ---------------------------------------------------------------------------
    try:
        verify_orders()
        res.add("X1", "verify_orders(): position, adjacency and precedence balance of P01-P10", [])
    except ValueError as e:
        res.add("X1", "verify_orders(): position, adjacency and precedence balance of P01-P10", [str(e)])

    # ---- X2. hashes, ids, shared_with ----------------------------------------------------------------
    errs = []
    for split, recs in prompts.items():
        ids = [r["prompt_id"] for r in recs]
        if len(ids) != len(set(ids)):
            errs.append(f"{split}: duplicate prompt ids")
        by_hash = defaultdict(set)
        for r in recs:
            if prompt_text_sha256(r["system_prompt"], r["user_prompt"]) != r["prompt_sha256"]:
                errs.append(f"{split}/{r['prompt_id']}: prompt_sha256 mismatch")
            by_hash[r["prompt_sha256"]].add(r["prompt_id"])
        for r in recs:
            if set(r["shared_with"]) != by_hash[r["prompt_sha256"]] - {r["prompt_id"]}:
                errs.append(f"{split}/{r['prompt_id']}: shared_with inconsistent")
        dup_groups = [g for g in by_hash.values() if len(g) > 1]
        for g in dup_groups:
            conds = sorted(pid.split("__")[1] for pid in g)
            if conds != ["P01", "V01"] or len({pid.split("__")[0] for pid in g}) != 1:
                errs.append(f"{split}: unexpected identical texts {sorted(g)}")
    res.add("X2", "prompt_sha256 recomputes; ids unique; only P01/V01 of the same task share a text", errs)

    # ---- X3. whitespace hygiene --------------------------------------------------------------------------
    errs = []
    for split, recs in prompts.items():
        for r in recs:
            u = r["user_prompt"]
            if u.endswith("\n") or "\r" in u or any(line != line.rstrip() for line in u.split("\n")):
                errs.append(f"{split}/{r['prompt_id']}: trailing whitespace, trailing newline or CR")
    for t in tasks_main + tasks_pilot:
        if not t["input_text"] or t["input_text"] != t["input_text"].strip():
            errs.append(f"{t['task_id']}: empty or unstripped input")
    res.add("X3", "no trailing whitespace on any line, no trailing newline, no CR; inputs stripped", errs)

    # ---- X4. prompt_strings.yaml equals the brief block ------------------------------------------------
    errs = []
    if BRIEF_PATH.exists():
        brief = BRIEF_PATH.read_text(encoding="utf-8")
        m = re.search(r"Verbatim strings.*?```yaml\n(.*?)```", brief, re.DOTALL)
        yaml_text = (REPO_ROOT / "configs" / "prompt_strings.yaml").read_text(encoding="utf-8")
        if not m or m.group(1) != yaml_text:
            errs.append("configs/prompt_strings.yaml differs from the brief §5.3 block")
        detail = "byte comparison with the project brief §5.3 (internal record, not released)"
    else:
        detail = "skipped: brief not found"
    res.add("X4", "configs/prompt_strings.yaml is a verbatim copy of brief §5.3", errs, detail)

    # ---- X5. smoke prompts ------------------------------------------------------------------------------
    errs = []
    pilot_by_id = {r["prompt_id"]: r for r in prompts["pilot"]}
    fams = Counter(r["family"] for r in prompts["smoke"])
    if sorted(fams) != sorted(fam_cfg) or any(v != 1 for v in fams.values()):
        errs.append(f"smoke families {dict(fams)}")
    for r in prompts["smoke"]:
        ref = pilot_by_id.get(r["prompt_id"])
        if r["condition_id"] != "P01" or ref is None or ref["prompt_sha256"] != r["prompt_sha256"]:
            errs.append(f"{r['prompt_id']}: not a pilot P01 prompt")
        elif not r["task_id"].endswith("_p01"):
            errs.append(f"{r['prompt_id']}: not the first pilot task of its family")
    res.add("X5", "smoke prompts: one pilot task per family (the first), order P01", errs)

    # ---- X6. synthetic values comma-free ---------------------------------------------------------------
    errs = []
    for t in tasks_main + tasks_pilot:
        if t["family"] in ("F4_EXTRACTION", "F5_TRANSFORMATION"):
            for k, v in t["gold"].items():
                if "," in v or v not in t["input_text"]:
                    errs.append(f"{t['task_id']}: field {k}={v!r}")
    syn_inputs = [t["input_text"] for t in tasks_main + tasks_pilot if t["family"] in ("F4_EXTRACTION", "F5_TRANSFORMATION")]
    if len(syn_inputs) != len(set(syn_inputs)):
        errs.append("synthetic records not distinct")
    res.add("X6", "F4/F5 records distinct; field values comma-free and present in INPUT", errs)

    # ---- X7. F1 gold answers usable by the primary metric (R1) -----------------------------------------
    errs = [f"{t['task_id']}: gold {g!r} has no token under the R1 normalization"
            for t in tasks_main + tasks_pilot if t["family"] == "F1_QA" for g in t["gold"]["answers"]
            if not qa_tokens(g)]
    res.add("X7", "every F1 gold answer has at least one token under the R1 normalization", errs)

    # ---- X8. phase prompt sets ---------------------------------------------------------------------------
    errs = []
    if bench_dir == BENCH_DIR:
        for phase, cfg in exp["phases"].items():
            recs = load_phase_prompts(exp, phase)
            expected = exp["prompts"]["expected"].get(phase)
            if expected and (len(recs), len({r["prompt_sha256"] for r in recs})) != (expected["ids"],
                                                                                   expected["unique_texts"]):
                errs.append(f"{phase}: {len(recs)} ids, expected {expected}")
        bs1 = load_phase_prompts(exp, "pilot_bs1")
        if {r["arm"] for r in bs1} != {"order"} or len({r["task_id"] for r in bs1}) != 10:
            errs.append("pilot_bs1 is not the order arm of the 10 pilot tasks")
        detail = "pilot_bs1 = order arm of the pilot prompts (100 ids / 100 unique texts)"
    else:
        detail = "skipped for a non-default benchmark directory"
    res.add("X8", "phase prompt sets have the expected sizes (incl. pilot_bs1)", errs, detail)
    return res


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench-dir", type=Path, default=BENCH_DIR)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--skip-rebuild", action="store_true")
    args = ap.parse_args(argv)
    res = run(args.bench_dir, args.skip_rebuild)
    res.print()
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(res.items, indent=2) + "\n", encoding="utf-8")
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())

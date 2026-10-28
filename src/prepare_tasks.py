"""Build the evaluation set: tasks_main.jsonl (100), tasks_pilot.jsonl (10) and selection_report.json.

Selection follows brief §5.2 (and the original plan §8-§12 where the brief is silent). For every family:
build the eligible pool by applying the filters in sequence (pool size recorded after each step), sort it
by source id, shuffle it with a fresh ``random.Random(20261003)``, walk the shuffled pool and take the main
items first and the pilot items next. Main and pilot are disjoint; SQuAD contexts are disjoint as well.

Operationalizations and additions that the brief does not spell out are listed in DESIGN_DEVIATIONS.md
("Pre-freeze clarifications") and in data/benchmark_v1/README.md.

Usage: python -m src.prepare_tasks [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import unicodedata
from collections import Counter, OrderedDict
from pathlib import Path

import pyarrow
import pyarrow.parquet as pq

from src.common import (
    BENCH_DIR,
    CACHE_DIR,
    all_instruction_strings,
    load_experiment,
    load_prompt_strings,
    sha256_file,
    word_count,
    write_json,
    write_jsonl,
)
from src.evaluators.quality import LABEL_SYNONYMS, squad_normalize
from src.generate_synthetic import generate_f4, generate_f5

# ---- filter thresholds (brief §5.2) ----
F1_CONTEXT_WORDS = (80, 350)
F1_ANSWER_WORDS = (1, 10)
F2_WORDS = (40, 250)
F2_FALLBACK_MIN_WORDS = 30
F2_MIN_CLASS_POOL = 100
F3_DOC_WORDS = (120, 450)
F3_SUMMARY_MAX_WORDS = 30
F3_SHORT_LINE_MAX_WORDS = 4

# ---- artifact detectors ----
# Mojibake: UTF-8 text decoded as Latin-1/CP1252 ("Ã©", "â€™", "Â£", ...).
MOJIBAKE_RE = re.compile("â€|Ã[\u0080-¿‘-›€™]|Â[\u0080-¿]")
# HTML-entity artifacts such as "#39;", "&lt;", "quot;" (brief §5.2, F2).
HTML_ENTITY_RE = re.compile(r"&#?\w+;|#\d+;|\b(?:quot|amp|lt|gt|nbsp|apos);", re.IGNORECASE)
# A line that starts like a list item: a bullet, a dash, or an enumeration such as "1." or "2)".
LIST_LINE_RE = re.compile(r"^\s*(?:[-*•▪◦·‣–—]|\(?\d{1,2}[.)])\s+")
SENTENCE_END = (".", "!", "?", '"', "'", "”", "’")


def has_invisible_chars(text: str) -> bool:
    """Control, format, private-use, surrogate or unassigned characters other than newline and tab."""
    return any(unicodedata.category(ch) in {"Cc", "Cf", "Co", "Cs", "Cn"} and ch not in "\n\t" for ch in text)


def has_encoding_artifacts(text: str) -> bool:
    return "�" in text or bool(MOJIBAKE_RE.search(text)) or has_invisible_chars(text)


def has_list_like_lines(text: str) -> bool:
    return any(LIST_LINE_RE.match(line) for line in text.split("\n"))


def has_short_unterminated_lines(text: str) -> bool:
    """Lines of 1-4 words without sentence-final punctuation: headings, labels, table cells ("Age: 24")."""
    for line in text.split("\n"):
        line = line.strip()
        if 0 < word_count(line) <= F3_SHORT_LINE_MAX_WORDS and not line.endswith(SENTENCE_END):
            return True
    return False


def clean_block_text(text: str) -> str:
    """Minimal hygiene: unify line breaks, drop trailing spaces on each line, strip the whole text."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.strip().split("\n"))


def join_xsum_lines(document: str) -> str:
    """XSum stores one sentence per line; join the non-empty lines with single spaces (brief §5.2)."""
    return " ".join(line.strip() for line in document.split("\n") if line.strip())


def leaks(gold: str, text: str) -> bool:
    """Gold leakage test used for selection and integrity test 8: whole-token match after SQuAD normalization."""
    g = squad_normalize(gold)
    return bool(g) and f" {g} " in f" {squad_normalize(text)} "


# ---------------------------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------------------------
def fetch_parquet(spec: dict, cache_dir: Path) -> tuple[pyarrow.Table, Path]:
    from huggingface_hub import hf_hub_download

    path = Path(
        hf_hub_download(
            spec["hf_id"], spec["file"], repo_type="dataset", revision=spec["revision"],
            cache_dir=str(cache_dir / "hf"),
        )
    )
    digest = sha256_file(path)
    if digest != spec["file_sha256"]:
        raise RuntimeError(f"{spec['hf_id']}:{spec['file']} has SHA-256 {digest}, expected {spec['file_sha256']}")
    return pq.read_table(path), path


class Funnel:
    """Applies filters in sequence and records the pool size after each step."""

    def __init__(self, items: list[dict], start_label: str = "all_rows", by_class: str | None = None):
        self.items = items
        self.by_class = by_class
        self.steps: list[dict] = []
        self._record(start_label, "all rows of the split")

    def _record(self, name: str, rule: str) -> None:
        entry = {"step": name, "rule": rule, "n": len(self.items)}
        if self.by_class:
            counts = Counter(it[self.by_class] for it in self.items)
            entry["n_by_class"] = {k: counts[k] for k in sorted(counts)}
        self.steps.append(entry)

    def apply(self, name: str, rule: str, keep) -> None:
        self.items = [it for it in self.items if keep(it)]
        self._record(name, rule)


def _shuffled(items: list[dict], key, seed: int) -> list[dict]:
    ordered = sorted(items, key=key)
    random.Random(seed).shuffle(ordered)
    return ordered


# ---------------------------------------------------------------------------------------------
# F1: SQuAD
# ---------------------------------------------------------------------------------------------
def select_f1(spec: dict, cache_dir: Path, seed: int, n_main: int, n_pilot: int, leakage_texts: list[str],
              directive: str):
    table, _ = fetch_parquet(spec, cache_dir)
    rows = table.to_pylist()
    items = []
    for i, r in enumerate(rows):
        golds = list(dict.fromkeys(r["answers"]["text"]))
        items.append({"row": i, "id": r["id"], "title": r["title"], "context": r["context"],
                      "question": r["question"], "answers": golds})

    def consistent(golds: list[str]) -> bool:
        norm = [squad_normalize(g) for g in golds]
        longest = max(norm, key=len)
        return all(n in longest for n in norm)

    def no_leak(it: dict) -> bool:
        task_text = directive.replace("{question}", it["question"].strip())
        return not any(leaks(g, t) for g in it["answers"] for t in [*leakage_texts, task_text])

    f = Funnel(items)
    lo, hi = F1_CONTEXT_WORDS
    f.apply("context_words", f"context has {lo}-{hi} words", lambda it: lo <= word_count(it["context"]) <= hi)
    alo, ahi = F1_ANSWER_WORDS
    f.apply("answer_words", f"every gold answer has {alo}-{ahi} words",
            lambda it: all(alo <= word_count(a) <= ahi for a in it["answers"]))
    f.apply("consistent_answers",
            "every normalized gold answer is a substring of the longest normalized gold answer",
            lambda it: consistent(it["answers"]))
    f.apply("nonempty_normalized_answers", "[clarification] no gold answer normalizes to the empty string",
            lambda it: all(squad_normalize(a) for a in it["answers"]))
    f.apply("no_encoding_artifacts",
            "context has no U+FFFD, mojibake, or [clarification] invisible control/format characters",
            lambda it: not has_encoding_artifacts(it["context"]))
    f.apply("no_pipe_or_tab", "context has no '|' or tab characters",
            lambda it: "|" not in it["context"] and "\t" not in it["context"])
    f.apply("no_list_like_lines", "no context line starts with a bullet, dash or enumeration marker",
            lambda it: not has_list_like_lines(it["context"]))
    f.apply("no_gold_leakage",
            "[clarification] no gold answer occurs (whole-token, SQuAD-normalized) in the INSTRUCTIONS or TASK text",
            no_leak)
    for it in f.items:
        if "\n" in it["question"].strip():
            raise RuntimeError(f"multi-line question {it['id']}")

    pool = _shuffled(f.items, key=lambda it: it["id"], seed=seed)
    selected, used_contexts, skipped_same_context = [], set(), 0
    for it in pool:
        if it["context"] in used_contexts:
            skipped_same_context += 1
            continue
        used_contexts.add(it["context"])
        selected.append(it)
        if len(selected) == n_main + n_pilot:
            break
    if len(selected) < n_main + n_pilot:
        raise RuntimeError("F1 pool too small")

    def to_task(it: dict) -> dict:
        question = it["question"].strip()
        context = clean_block_text(it["context"])
        return {
            "source_id": it["id"],
            "task_directive": directive.replace("{question}", question),
            "input_text": context,
            "gold": {"answers": it["answers"]},
            "metadata": {"question": question, "squad_title": it["title"], "source_row": it["row"],
                         "input_word_count": word_count(context),
                         "context_cleaned": context != it["context"]},
        }

    report = {
        "filter_steps": f.steps,
        "eligible_pool": {"n_questions": len(f.items), "n_distinct_contexts": len({it["context"] for it in f.items})},
        "selection_walk": {"one_question_per_context": True, "skipped_same_context": skipped_same_context},
    }
    return [to_task(it) for it in selected[:n_main]], [to_task(it) for it in selected[n_main:]], report


# ---------------------------------------------------------------------------------------------
# F2: AG News
# ---------------------------------------------------------------------------------------------
def select_f2(spec: dict, cache_dir: Path, seed: int, n_main: int, n_pilot: int, per_class: int,
              leakage_texts: list[str], directive: str):
    table, _ = fetch_parquet(spec, cache_dir)
    meta = json.loads(table.schema.metadata[b"huggingface"])
    names = meta["info"]["features"]["label"]["names"]
    if names != spec["label_names"]:
        raise RuntimeError(f"unexpected AG News label names {names}")
    rows = table.to_pylist()
    items = [{"row": i, "text": r["text"], "label": names[r["label"]]} for i, r in enumerate(rows)]
    for label in names:
        syns = LABEL_SYNONYMS[label]
        if any(leaks(s, t) for s in syns for t in leakage_texts):
            raise RuntimeError(f"label {label} occurs in an instruction string")

    deviations = []

    def build(min_words: int) -> Funnel:
        f = Funnel(items, by_class="label")
        hi = F2_WORDS[1]
        f.apply("text_words", f"text has {min_words}-{hi} words", lambda it: min_words <= word_count(it["text"]) <= hi)
        f.apply("no_html_entity_artifacts", "no HTML-entity artifacts such as '#39;', '&lt;', 'quot;'",
                lambda it: not HTML_ENTITY_RE.search(it["text"]))
        f.apply("no_other_encoding_artifacts",
                "[clarification] no backslash sequences, U+FFFD, mojibake or invisible control/format characters",
                lambda it: "\\" not in it["text"] and not has_encoding_artifacts(it["text"]))
        return f

    f = build(F2_WORDS[0])
    smallest = min(Counter(it["label"] for it in f.items).get(lbl, 0) for lbl in names)
    if smallest < F2_MIN_CLASS_POOL:
        deviations.append(f"a class had {smallest} < {F2_MIN_CLASS_POOL} eligible items; minimum lowered to "
                          f"{F2_FALLBACK_MIN_WORDS} words")
        f = build(F2_FALLBACK_MIN_WORDS)

    pool = _shuffled(f.items, key=lambda it: it["row"], seed=seed)
    main, counts, used_texts, idx = [], Counter(), set(), 0
    while len(main) < n_main:
        it = pool[idx]
        idx += 1
        text = clean_block_text(it["text"])
        if text in used_texts or counts[it["label"]] >= per_class:
            continue
        main.append(it)
        counts[it["label"]] += 1
        used_texts.add(text)
    pilot = []
    while len(pilot) < n_pilot:
        it = pool[idx]
        idx += 1
        text = clean_block_text(it["text"])
        if text in used_texts or any(p["label"] == it["label"] for p in pilot):
            continue
        pilot.append(it)
        used_texts.add(text)

    def to_task(it: dict) -> dict:
        text = clean_block_text(it["text"])
        return {
            "source_id": f"test/{it['row']}",
            "task_directive": directive,
            "input_text": text,
            "gold": {"label": it["label"]},
            "metadata": {"source_row": it["row"], "input_word_count": word_count(text),
                         "text_cleaned": text != it["text"]},
        }

    report = {
        "filter_steps": f.steps,
        "eligible_pool": {"n": len(f.items), "n_by_class": dict(sorted(Counter(it["label"] for it in f.items).items()))},
        "min_words_used": f.steps[1]["rule"],
        "selection_walk": {"main_quota_per_class": per_class,
                           "pilot_rule": "next items after main is complete; the two pilot items differ in class",
                           "items_walked": idx},
        "deviations": deviations,
    }
    return [to_task(it) for it in main], [to_task(it) for it in pilot], report


# ---------------------------------------------------------------------------------------------
# F3: XSum
# ---------------------------------------------------------------------------------------------
def select_f3(spec: dict, cache_dir: Path, seed: int, n_main: int, n_pilot: int, directive: str):
    table, _ = fetch_parquet(spec, cache_dir)
    rows = table.to_pylist()
    items = [{"row": i, "id": r["id"], "document": r["document"], "summary": r["summary"],
              "input_text": join_xsum_lines(r["document"])} for i, r in enumerate(rows)]
    f = Funnel(items)
    f.apply("nonempty_document", "document is not empty", lambda it: it["input_text"] != "")
    lo, hi = F3_DOC_WORDS
    f.apply("document_words", f"document has {lo}-{hi} words", lambda it: lo <= word_count(it["input_text"]) <= hi)
    f.apply("summary_words", f"reference summary is non-empty and has at most {F3_SUMMARY_MAX_WORDS} words",
            lambda it: it["summary"].strip() != "" and word_count(it["summary"]) <= F3_SUMMARY_MAX_WORDS)
    f.apply("no_encoding_artifacts",
            "[clarification] document and summary have no U+FFFD, mojibake or invisible control/format characters",
            lambda it: not has_encoding_artifacts(it["document"]) and not has_encoding_artifacts(it["summary"]))
    f.apply("no_list_or_table_artifacts",
            "no list or table artifacts: no line starting with a bullet/dash/enumeration, no '|' or tab, "
            f"[clarification] no line of 1-{F3_SHORT_LINE_MAX_WORDS} words without sentence-final punctuation",
            lambda it: not has_list_like_lines(it["document"]) and "|" not in it["document"]
            and "\t" not in it["document"] and not has_short_unterminated_lines(it["document"]))

    pool = _shuffled(f.items, key=lambda it: it["id"], seed=seed)
    selected, used = [], set()
    for it in pool:
        if it["input_text"] in used:
            continue
        used.add(it["input_text"])
        selected.append(it)
        if len(selected) == n_main + n_pilot:
            break

    def to_task(it: dict) -> dict:
        return {
            "source_id": it["id"],
            "task_directive": directive,
            "input_text": it["input_text"],
            "gold": {"summary": it["summary"].strip()},
            "metadata": {"source_row": it["row"], "input_word_count": word_count(it["input_text"]),
                         "n_source_lines": len([ln for ln in it["document"].split("\n") if ln.strip()])},
        }

    report = {"filter_steps": f.steps, "eligible_pool": {"n": len(f.items)}}
    return [to_task(it) for it in selected[:n_main]], [to_task(it) for it in selected[n_main:]], report


# ---------------------------------------------------------------------------------------------
# F4/F5: synthetic
# ---------------------------------------------------------------------------------------------
def select_synthetic(family: str, seed: int, n_records: int, n_main: int, directive: str, leakage_texts: list[str]):
    records = generate_f4(seed, n_records) if family == "F4_EXTRACTION" else generate_f5(seed, n_records)
    for rec in records:
        for key, value in rec["gold"].items():
            if any(leaks(value, t) for t in [*leakage_texts, directive]):
                raise RuntimeError(f"synthetic value {key}={value!r} leaks into INSTRUCTIONS/TASK")

    def to_task(i: int, rec: dict) -> dict:
        return {
            "source_id": f"synthetic/{family}/{i:02d}",
            "task_directive": directive,
            "input_text": rec["input_text"],
            "gold": rec["gold"],
            "metadata": {**rec["metadata"], "input_word_count": word_count(rec["input_text"])},
        }

    tasks = [to_task(i + 1, rec) for i, rec in enumerate(records)]
    report = {"generator": "src/generate_synthetic.py", "n_records": n_records,
              "all_records_distinct": len({t["input_text"] for t in tasks}) == n_records,
              "comma_free_values": all("," not in v for t in tasks for v in t["gold"].values())}
    return tasks[:n_main], tasks[n_main:], report


# ---------------------------------------------------------------------------------------------
def build(out_dir: Path, cache_dir: Path = CACHE_DIR) -> dict:
    exp = load_experiment()
    ps = load_prompt_strings()
    seed = exp["seed"]
    fam_cfg = exp["evaluation_set"]["families"]
    directives = ps["task_directives"]
    leakage_texts = list(all_instruction_strings(ps).values())
    datasets = exp["datasets"]

    results = OrderedDict()
    results["F1_QA"] = select_f1(datasets["F1_QA"], cache_dir, seed, fam_cfg["F1_QA"]["main"],
                                 fam_cfg["F1_QA"]["pilot"], leakage_texts, directives["F1_QA"])
    results["F2_CLASSIFICATION"] = select_f2(
        datasets["F2_CLASSIFICATION"], cache_dir, seed, fam_cfg["F2_CLASSIFICATION"]["main"],
        fam_cfg["F2_CLASSIFICATION"]["pilot"], exp["evaluation_set"]["f2_main_per_class"], leakage_texts,
        directives["F2_CLASSIFICATION"])
    results["F3_SUMMARIZATION"] = select_f3(datasets["F3_SUMMARIZATION"], cache_dir, seed,
                                            fam_cfg["F3_SUMMARIZATION"]["main"], fam_cfg["F3_SUMMARIZATION"]["pilot"],
                                            directives["F3_SUMMARIZATION"])
    n_syn = exp["evaluation_set"]["synthetic_records_per_family"]
    for fam in ("F4_EXTRACTION", "F5_TRANSFORMATION"):
        results[fam] = select_synthetic(fam, seed, n_syn, fam_cfg[fam]["main"], directives[fam], leakage_texts)

    main_tasks, pilot_tasks = [], []
    report_families = OrderedDict()
    for fam, (main, pilot, rep) in results.items():
        prefix = fam_cfg[fam]["prefix"]
        if len(main) != fam_cfg[fam]["main"] or len(pilot) != fam_cfg[fam]["pilot"]:
            raise RuntimeError(f"{fam}: wrong counts {len(main)}/{len(pilot)}")
        for split, tasks, fmt in (("main", main, "{p}_{i:03d}"), ("pilot", pilot, "{p}_p{i:02d}")):
            for i, t in enumerate(tasks, 1):
                record = {"task_id": fmt.format(p=prefix, i=i), "family": fam, "split": split}
                if fam in datasets:
                    ds = datasets[fam]
                    record.update({"source_dataset": ds["hf_id"], "source_config": ds["config"],
                                   "source_split": ds["split"], "source_revision": ds["revision"]})
                else:
                    record.update({"source_dataset": "generated_deterministically", "source_config": None,
                                   "source_split": None, "source_revision": None})
                record.update({"source_id": t["source_id"], "task_directive_key": fam, **{
                    k: t[k] for k in ("task_directive", "input_text", "gold", "metadata")}})
                (main_tasks if split == "main" else pilot_tasks).append(record)
        entry = OrderedDict()
        if fam in datasets:
            ds = datasets[fam]
            entry["source"] = {k: ds.get(k) for k in ("hf_id", "config", "split", "revision_ref", "revision", "file",
                                                      "file_sha256", "license") if ds.get(k) is not None}
        entry.update(rep)
        entry["selected"] = {
            "main": [{"task_id": t["task_id"], "source_id": t["source_id"]} for t in main_tasks if t["family"] == fam],
            "pilot": [{"task_id": t["task_id"], "source_id": t["source_id"]} for t in pilot_tasks if t["family"] == fam],
        }
        report_families[fam] = entry

    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "tasks_main.jsonl", main_tasks)
    write_jsonl(out_dir / "tasks_pilot.jsonl", pilot_tasks)
    import huggingface_hub

    report = OrderedDict(
        seed=seed,
        shuffle="pool sorted by source id, then random.Random(seed).shuffle (fresh generator per family)",
        software={"python": sys.version.split()[0], "pyarrow": pyarrow.__version__,
                  "huggingface_hub": huggingface_hub.__version__},
        counts={"main": len(main_tasks), "pilot": len(pilot_tasks)},
        families=report_families,
        files={name: sha256_file(out_dir / name) for name in ("tasks_main.jsonl", "tasks_pilot.jsonl")},
    )
    write_json(out_dir / "selection_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=Path, default=BENCH_DIR)
    ap.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    args = ap.parse_args(argv)
    report = build(args.out_dir, args.cache_dir)
    print(json.dumps({"counts": report["counts"], "files": report["files"]}, indent=2))
    for fam, entry in report["families"].items():
        steps = entry.get("filter_steps")
        if steps:
            print(fam, " -> ".join(f"{s['step']}={s['n']}" for s in steps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

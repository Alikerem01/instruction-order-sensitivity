# Evaluation set benchmark_v1

Built by `make tasks` (`src/prepare_tasks.py`, `src/generate_synthetic.py`) and `make prompts`
(`src/build_prompts.py`) with seed `20261003`. Rebuilding reproduces every file byte for byte
(integrity test 10). Pool sizes after every filter step, source revisions and selected source ids are in
`selection_report.json`.

| File | Content |
|---|---|
| `tasks_main.jsonl` | 100 main tasks: `qa_001`-`qa_020`, `cls_001`-`cls_020`, `sum_001`-`sum_020`, `ext_001`-`ext_020`, `trf_001`-`trf_020` |
| `tasks_pilot.jsonl` | 10 pilot tasks (`*_p01`, `*_p02`), disjoint from the main tasks |
| `prompts_main.jsonl` | 2,000 prompt ids (per task P01-P10 and V01-V10), 1,900 unique texts |
| `prompts_pilot.jsonl` | 200 prompt ids, 190 unique texts |
| `prompts_smoke.jsonl` | 5 prompt ids: P01 of the first pilot task of each family |
| `selection_report.json` | dataset ids, splits, revisions, file hashes, pool size after each filter, selected ids |

## Sources

| Family | Source | Split | Revision (Hub commit) |
|---|---|---|---|
| F1 Extractive QA | `rajpurkar/squad` (`plain_text`) | validation | `7b6d24c440a36b6815f21b70d25016731768db1f` |
| F2 Topic classification | `fancyzhx/ag_news` | test | `eb185aade064a813bc0b7f42de02595523103ca4` |
| F3 Summarization | `EdinburghNLP/xsum`, branch `refs/convert/parquet` | test | `03339c27cd655c3369346bacb533293f222a9d42` |
| F4 Controlled extraction | generated deterministically | — | `src/generate_synthetic.py` |
| F5 Controlled transformation | generated deterministically | — | `src/generate_synthetic.py` |

The SHA-256 of every parquet file read is pinned in `configs/experiment.yaml` and checked at build time.

## Selection procedure

For each family the eligible pool is built by applying the filters below in sequence, sorted by source id,
shuffled with a fresh `random.Random(20261003)`, and walked in that order: main items first, pilot items
next. Clarifications that go beyond the brief are marked [C] and logged in `DESIGN_DEVIATIONS.md` §2.

**F1 (SQuAD).** Context 80-350 words (`\S+` tokens); every gold answer 1-10 words; answers consistent (every
SQuAD-normalized gold answer is a substring of the longest one); [C] no gold answer normalizes to the empty
string; context free of U+FFFD, mojibake and [C] invisible control/format characters; no `|` or tab; no
list-like line (bullet, dash or enumeration at the start of a line); [C] no gold answer occurs in any
instruction string or in the question (whole-token match after SQuAD normalization). The walk takes at most
one question per context, so main and pilot contexts are disjoint. Gold = the distinct SQuAD answers.
Eligible: 7,547 questions over 1,774 contexts.

**F2 (AG News).** 40-250 words; no HTML-entity artifacts (`#39;`, `&lt;`, `quot;`, ...); [C] no backslash
artifacts or other encoding artifacts. Every class keeps at least 297 eligible items, so the 30-word fallback
did not trigger. The walk fills 5 main items per class; the 2 pilot items come next in the walk and belong to
different classes. Gold = the label name (World, Sports, Business, Sci/Tech). Eligible: 1,648 articles.

**F3 (XSum).** XSum stores one sentence per line; lines are joined with single spaces into `input_text`.
Non-empty document of 120-450 words; reference summary non-empty and at most 30 words; [C] document and
summary free of U+FFFD, mojibake and invisible characters; no list or table artifacts: no line starting with
a bullet, dash or enumeration, no `|` or tab, and [C] no line of 1-4 words without sentence-final punctuation
(labels and table cells such as `Age: 24`). Gold = the reference summary. Eligible: 5,311 documents.

**F4 (controlled extraction).** 22 records from fixed lists in code (24 persons, organizations and cities,
5 event types, 5 sentence templates), each with a person, organization, city, date ("14 March 2025") and
amount (an integer 32-980). Every value is unique in the family. Records 1-20 are main, 21-22 pilot.
Gold = the five values. Example input: "On 25 March 2024, Daniel Reed from Quarry Lane Engineering visited
the Salzburg facility. During the visit, 463 parcels were delivered before the team closed the report."

**F5 (controlled transformation).** 22 records in the format of the original plan §12
(`Project: Orion.` / `Owner: Henrik Dahl.` / `Current status: completed.` / `Deadline: 18 February 2027.` /
`Approved budget: 572500 USD.`). Gold = project, owner, status, deadline, budget.

No field value of F4 or F5 contains a comma, so the NO_COMMA constraint can be met without altering values.

## Task record

```json
{"task_id": "qa_001", "family": "F1_QA", "split": "main", "source_dataset": "rajpurkar/squad",
 "source_config": "plain_text", "source_split": "validation", "source_revision": "7b6d24c...",
 "source_id": "56de16ca4396321400ee25c8", "task_directive_key": "F1_QA",
 "task_directive": "Answer the question below ... in \"answer\".\nQuestion: Who was the ruling class ahead of the Normans?",
 "input_text": "...", "gold": {"answers": ["Anglo-Saxons", "the Anglo-Saxons"]},
 "metadata": {"question": "...", "squad_title": "...", "source_row": 0, "input_word_count": 96, "context_cleaned": false}}
```

## Prompt record

`prompt_id` (`<task_id>__<condition_id>`), `task_id`, `family`, `split`, `arm` (order | format),
`condition_id` (P01-P10 or V01-V10), `order_id`, `order_code` (letters A-E), `format_variant`,
`instruction_order` (instruction keys in presentation order), `instruction_positions` (key → 1-5),
`system_prompt`, `user_prompt`, `prompt_sha256` (SHA-256 of `[system, user]`), `shared_with` (other ids in
the same file with the identical text; P01 ↔ V01).

## Licenses

SQuAD v1.1: CC BY-SA 4.0. AG News and XSum: license "unknown" on the Hugging Face Hub; public releases
include task ids and the rebuild script, not the full texts. F4/F5 records are generated by the code here.

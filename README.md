# Instruction-order sensitivity in small open-weight language models — code, data and outputs

This repository contains everything needed to inspect and reproduce the study: task selection, prompt
construction, generation, rule-based evaluation, the raw model outputs, the evaluation records and every reported
number, table and figure.

**Design in brief.** Five non-conflicting, automatically verifiable instructions (FORMAT, LENGTH, CARDINALITY, a
lexical constraint on the answer (no commas), VERBATIM evidence) are attached to 100 tasks (five families × 20:
extractive QA, news classification, summarization, information extraction, structured-to-text transformation).
The instructions are presented in 10 orders that form a Williams design (order arm, O01-O10, stored as P01-P10 in
the data files); a control arm keeps the order fixed and changes only the formatting of the instruction block
(format arm, V01-V10). Four
instruction-tuned models were run with greedy decoding at batch size 1 on an NVIDIA A100: SmolLM2-1.7B-Instruct,
Qwen2.5-3B-Instruct, Phi-4-mini-instruct and Gemma 4 E4B-it (pinned revisions in `configs/models.yaml`). Every
constraint is checked by code (`src/evaluators/README.md`).

## Contents

| Path | What it holds |
|---|---|
| `ANALYSIS_PLAN.md` | the analysis plan, frozen before the main run (tag `benchmark-v1.0.0`) |
| `DESIGN_DEVIATIONS.md` | every design clarification and change, with its source and date, including the post-hoc analyses |
| `configs/` | verbatim prompt strings, pinned models, experiment settings |
| `data/benchmark_v1/` | task and prompt files (see "Data and licences"), selection report, `manifest.json` (SHA-256 of the frozen design files) |
| `src/` | task selection, prompt construction, generation, evaluators, evaluation |
| `analysis/` | the analyses of the frozen plan, tables and figures |
| `runs/` | raw generations of every phase with their run metadata and import records (`main` is the analysed data) |
| `results/` | evaluation records, `metrics/summary.json` (every reported number under a stable key), tables, figures, `report/RESULTS_SUMMARY.md` |
| `results/posthoc_norm/` | post-hoc re-analysis with normalized FORMAT scoring (one enclosing code fence removed before the FORMAT check): `summary_norm.json`, tables, figures, `SUMMARY_NORM.md` |
| `colab/` | the Colab generation notebook and its runbook (in Turkish) |
| `tests/` | the test suite, including a golden-output integration test |

## Data and licences

* **SQuAD v1.1** (CC BY-SA 4.0): passages, questions and answers of the F1 tasks are included;
  SQuAD-derived texts remain under that licence.
* **AG News and XSum**: their licence is listed as "unknown" on the Hugging Face Hub, so their texts are **not**
  redistributed. The task files keep ids, source rows, dataset revisions and (AG News) the gold label; the article
  or document text, the XSum reference summary and the prompts that contain them are removed (each changed record
  lists `removed_for_release`). `make tasks` and `make prompts` rebuild the full files byte for byte from the pinned
  dataset revisions; `make freeze-check` then confirms them against `data/benchmark_v1/manifest.json`.
* **Synthetic F4/F5 tasks**: generated deterministically by `src/generate_synthetic.py`; included.
* **Model outputs** are included. They may quote short spans of the inputs as "evidence", as the task required.
  Model outputs for the AG News and XSum tasks contain short excerpts of the source texts (evidence spans and
  summaries); rights in those excerpts remain with the original publishers. These quoted spans remain under their
  sources' terms.
* **Models** are not included. Their own licences apply: SmolLM2-1.7B-Instruct (Apache-2.0), Qwen2.5-3B-Instruct
  (Qwen Research License, non-commercial), Phi-4-mini-instruct (MIT), Gemma 4 E4B-it (Apache-2.0).

**E-mail addresses.** Every e-mail address in released text is replaced with `[email removed]`. The evaluation
flags were computed on the original outputs and are unchanged. `RELEASE_REDACTIONS.json` lists every file changed
for the release with its original SHA-256 (an empty list means that no released file contained an address).

No personal data of the authors or of other people is part of this repository.

Files listed in `data/benchmark_v1/manifest.json` are identical to their frozen versions, except for wording-only
changes to comments and messages in 13 files for this public release; `RELEASE_REDACTIONS.json` lists them with
their original SHA-256.

## Reproducing

### v3.1 numerical correction (2026-10-28)

This local revision corrects floating-point tie handling in sign, rank and order-level comparisons under both
strict and normalized scoring. It does not change the scoring policies, raw outputs or stored evaluation flags.
The earlier summaries are retained in `results/archive/pre_v3_1/`. The complete before/after audit is
`results/report/NUMERICAL_CORRECTION_V31.json`; see also `DESIGN_DEVIATIONS.md` §9.

To reproduce this correction directly from the released records, without downloading source datasets or running
any model:

```bash
python -m analysis.correct_numerics
python -m pytest -q tests/test_analysis.py tests/test_posthoc_r1.py tests/test_posthoc_norm.py tests/test_numerical_ties.py tests/test_constraints.py tests/test_format.py
```

This route rechecks strict and normalized FORMAT on the raw outputs and verifies parsed-object invariance. It
reuses the stored content flags and quality scores, so it is not a fresh end-to-end evaluation of the omitted
source texts. Input-text comma-spillover, tokenizer edit distances and prior generation checks are explicitly
carried forward. The audit verifies that all inputs are unchanged and lists the retained keys. Numerical
recomputation used Python 3.12.14 with the analysis-library versions recorded in the summaries; the original
environment files are preserved.

These six test modules cover the analyses, normalized-policy checks, numerical regressions and constraint/FORMAT
evaluators (120 tests). They are not a substitute for the full suite after the complete environment and omitted
source data have been restored.

### Full evaluation and analysis

```
make setup                 # Python 3.11 virtual environment with the pinned requirements
make tasks prompts         # rebuild the full task and prompt files (downloads the pinned datasets)
make freeze-check validate test
make evaluate PHASE=main RUN=main_20261006-1354_63a1c79   # re-evaluate the raw outputs
make analyze figures       # results/metrics/summary.json, tables, RESULTS_SUMMARY.md, figures
make posthoc-norm          # post-hoc re-analysis with normalized FORMAT scoring (results/posthoc_norm/)
```

Generation needs an A100 GPU: build a bundle with `make bundle PHASE=<phase>` and run `colab/run_generation.ipynb`
(see `colab/COLAB_RUNBOOK.md`). Decoding is greedy at batch size 1; the determinism checks are described in
`ANALYSIS_PLAN.md` §9.

## Citation

See `CITATION.cff`.

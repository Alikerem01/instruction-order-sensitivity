# Design deviations

Every departure from the original plan (`instruction_order_sensitivity_experiment_plan_TR.md`) and every
operationalization the project brief (an internal planning document, not released) leaves open is logged here. After the G3
freeze, any change requires an entry here and a recorded design decision; if it could affect results, results
are reported both ways.

## 1. Pre-freeze design revisions (brief §6, adopted before any model output existed)

| # | Revision | Source |
|---|---|---|
| R1 | The paper is written in English; the abstract is submitted in English only. | brief §6.1, D1 |
| R2 | Implementation tooling differs from the original plan's (§44-§49); no effect on tasks, prompts, evaluation or analysis. | brief §6.2 |
| R3 | Prompt strings are the English verbatim strings of brief §5.3 (`configs/prompt_strings.yaml`). Task directives map the answer explicitly to `"answer"`; the word "short" is removed; T4 is NO_COMMA with a pre-specified LOWERCASE fallback (replaces LANGUAGE); T5 is renamed VERBATIM and loses the unverifiable "do not use external knowledge" clause; every instruction is self-contained. | brief §6.3, D3, D4 |
| R4 | Williams orders P01-P10 (brief §5.4) replace the cyclic orders of the original plan §16. | brief §6.4, D5 |
| R5 | A format-perturbation control arm (V01-V10, order fixed at P01) is added. | brief §6.5, D6 |
| R6 | Scoring is decoupled: strict FORMAT plus a lenient parse for the other constraints; cascade scoring (original plan §37) becomes robustness analysis E6a. | brief §6.6, D9 |
| R7 | Evaluator rules are fully specified (brief §5.8). Integrity test 8 checks gold leakage only in the INSTRUCTIONS and TASK blocks. | brief §6.7 |
| R8 | The pilot uses a separate 10-task pool; the calibration rule is pre-specified (brief §5.6); the pilot is never used for prompt or order selection. | brief §6.8, D8 |
| R9 | Selection details: one question per SQuAD context; AG News and XSum test splits; XSum read from the `refs/convert/parquet` branch; comma-free synthetic values. | brief §6.9 |
| R10 | Inference: no sampling parameters; `max_new_tokens` 512 (plan: 256); bf16 on a Colab A100; fixed batching (16); deduplication of identical texts; full logging; no remote code. | brief §6.10 |
| R11 | The analysis plan is brief §5.10. SQuAD containment is the primary QA metric (plan: token F1). Task quality is never averaged across families; the original Table 2 column "Mean Task Quality" is dropped. | brief §6.11 |
| R12 | Terminology: "open-weight", "evaluation set", "verbatim-evidence constraint"; no "first study" claims. | brief §6.12 |

Counts follow from R5: main = 2,000 prompt ids and 1,900 unique texts per model (5,700 generations for three
models); pilot = 200 ids and 190 unique texts per model.

## 2. Pre-freeze clarifications made in C1 (2026-10-04)

Choices the brief does not spell out. Each was taken as the most conservative option and was raised
for review at G1 (internal report, not released). Pool sizes are in `data/benchmark_v1/selection_report.json`.

### 2.1 Selection (brief §5.2)

| # | Clarification | Effect on the pool |
|---|---|---|
| C1 | **F1: gold answers must not normalize to the empty string.** An empty normalized answer would make containment trivially 1. | -1 question |
| C2 | **F1: gold-leakage filter.** A question is ineligible if any gold answer occurs (whole-token match after SQuAD normalization) in any instruction string (including both calibration fallbacks) or in its filled TASK directive. Needed so that integrity test 8 holds by construction; for example a question containing its own answer "three". | -82 questions |
| C3 | **Encoding artifacts, all text families.** In addition to U+FFFD and mojibake (F1) and HTML entities (F2), texts containing invisible control or format characters (Unicode categories Cc, Cf, Co, Cs, Cn other than newline and tab; e.g. U+FEFF, U+200B, U+200E, soft hyphen) are rejected, because a model cannot reproduce them in verbatim evidence. Mojibake = `â€`, `Ã` or `Â` followed by a Latin-1/CP1252 continuation character. | F1 -17 questions (3 contexts) |
| C4 | **F2: backslash artifacts.** AG News texts containing `\` (e.g. `second\team`, line breaks lost in the source) are rejected as encoding artifacts, together with the HTML-entity pattern `&#?\w+;`, `#\d+;`, `quot;`/`amp;`/`lt;`/`gt;`/`nbsp;`/`apos;`. | -234 items |
| C5 | **F3: encoding artifacts in XSum.** The F1 rule (U+FFFD, mojibake, invisible characters) is applied to XSum documents and reference summaries (e.g. `Â£` for `£`). | -757 documents |
| C6 | **F3: "list or table artifacts"** = a line starting with a bullet, dash or enumeration marker; a `\|` or tab; or a line of 1-4 words without sentence-final punctuation (headings, labels and table cells such as `Age: 24`, `Club: Saracens`, `Macron:`). | -294 documents |
| C7 | **F1: "list-like lines"** = a line starting with a bullet, dash or enumeration marker (`-`, `*`, `•`, `–`, `1.`, `2)`). | -39 questions |
| C8 | **Minimal input hygiene.** Line breaks unified to `\n`, trailing spaces removed from each line, the text stripped. XSum lines joined with single spaces (brief). Only one selected input changed (`cls_017`: one trailing space). Internal whitespace is never altered. | none |
| C9 | **Deterministic walk.** Each eligible pool is sorted by source id and shuffled with a fresh `random.Random(20261003)` per family. F1: questions whose context is already used are skipped (main and pilot contexts disjoint). F2: main takes items until each class has 5; the pilot continues the same walk, and the second pilot item must differ in class from the first. All families: an input text identical to an already selected one is skipped. | none |
| C10 | **AG News 30-word fallback** (brief §5.2) did not trigger: the smallest class pool after all filters has 297 items (≥ 100). | none |

### 2.2 Synthetic data (original plan §11-§12, brief §5.2)

| # | Clarification |
|---|---|
| C11 | F4: 24 persons, 24 organizations, 24 cities (ASCII spellings), 5 event types, 5 sentence templates (T01-T05, used in rotation); dates "D Month YYYY" with D in 1-28 and years 2024-2025; amounts are integers 32-980 (never a day number, never 20 or 25, which occur in T2 and its fallback). Values are sampled without replacement, so every value is unique within the family. |
| C12 | F5: the record format of the original plan §12 (`Project: X.` / `Owner: ...` / `Current status: ...` / `Deadline: ...` / `Approved budget: N USD.`), 24 project code names, 24 owners, 8 statuses (`approved` excluded because every input contains "Approved budget"), deadlines in 2025-2027, budgets multiples of 500 in 15,000-950,000 written as digits plus " USD". |
| C13 | 22 records per family: records 1-20 are main tasks, records 21-22 pilot tasks. Each family uses a fresh `random.Random(20261003)`. |

### 2.3 Prompts and generation

| # | Clarification |
|---|---|
| C14 | `prompt_sha256` = SHA-256 of the UTF-8 JSON array `[system_prompt, user_prompt]` (compact separators). Identical hashes are generated once; in practice only P01 and V01 of the same task share a text. |
| C15 | Smoke prompts = P01 of the first pilot task of each family (`qa_p01`, `cls_p01`, `sum_p01`, `ext_p01`, `trf_p01`). |
| C16 | **transformers 5.17.0** (released 2026-09-09) is pinned with tokenizers 0.23.2, huggingface-hub 1.33.0, safetensors 0.8.0 and accelerate 1.15.0 in both requirement files. All three models load with native classes (`LlamaForCausalLM`, `Qwen2ForCausalLM`, `Phi3ForCausalLM`) and `trust_remote_code=False`; Phi-4-mini's Hub repository ships remote code, which is never used. Colab keeps its preinstalled torch; the notebook stops if pip would change it. |
| C17 | **Effective generation config.** transformers 5.x merges the model's Hub `generation_config` into unset fields at `generate()` time; Qwen2.5's Hub config contains `do_sample: true`, `temperature: 0.7`, `top_p: 0.8`, `top_k: 20`, `repetition_penalty: 1.05`. The from-scratch config therefore also *replaces* `model.generation_config`. transformers then fills still-unset fields with its global defaults (`temperature 1.0`, `top_p 1.0`, `top_k 50`); these appear in the logged effective config but are inert, because sampling warpers are applied only when `do_sample=True`. |
| C18 | `output_text` = the new tokens before the first end-of-turn token, decoded with `skip_special_tokens=False` and `clean_up_tokenization_spaces=False` (no change to what the model produced). `n_output_tokens` counts generated tokens including the end-of-turn token. |
| C19 | Determinism settings: `torch.manual_seed(20261003)`, TF32 disabled, `torch.use_deterministic_algorithms(True, warn_only=True)`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `attn_implementation="sdpa"`. |
| C20 | Raw storage: one atomically written file per batch (`batches/batch_NNNNN.jsonl`), concatenated into `generations.jsonl` at completion. A resumed run refuses to continue if any environment field (GPU name, CUDA, cuDNN, Python, torch, transformers, tokenizers, accelerate, safetensors, huggingface-hub) or any setting differs from the first session. |
| C21 | The Mac dry-run uses phase `dryrun`: SmolLM2-135M-Instruct, CPU, float32, batch size 2 (so that interruption and resume are exercised on 5 prompts). Its outputs live under `runs/dryrun/` and are excluded from every analysis. |

### 2.4 Evaluators (brief §5.8)

| # | Clarification |
|---|---|
| C22 | Fence rule: the tag `json` is accepted in any case (```` ```JSON ````); other tags fall through to `first_object`. |
| C23 | F2 cue rule: tokens are whitespace-separated words with edge punctuation removed; "within three tokens" = the label is the 1st, 2nd or 3rd token after the cue's last token. Labels match whole words (no letter or digit on either side). |
| C24 | *Superseded by G1-R1 (§2.5).* At G1, F1 containment followed the brief (character-level substring after SQuAD normalization) with a whole-token diagnostic. |
| C25 | Dates: the numeric forms accept one- or two-digit day and month; invalid calendar dates are ignored. Numbers: thousands separators, `$ € £ US$`, `USD` and `dollars` are dropped; a number must stand alone (no letter, digit or decimal point attached) and lie outside every accepted date mention; decimals compare numerically (`120000.00` = `120000`). |
| C26 | `duplicate_keys` covers duplicate keys at any nesting level (strict FORMAT fails); in the lenient parse the last value wins, as in `json.loads`. `evidence_duplicate` compares items after VERBATIM normalization. |

### 2.5 Changes required by design decision G1 (2026-10-04)

Source of every row: design decision G1 (internal decision record, not released; status APPROVED_WITH_CHANGES).
All were applied before any model output existed; none touches the tasks or the prompts (their SHA-256 values are
unchanged, integrity test 10). The selection clarifications C1-C10 and the synthetic-data design C11-C13 were
approved as implemented.

| # | Change | Where |
|---|---|---|
| G1-R1 | **F1 primary metric = whole-token containment.** Gold answers and the model answer go through NFC, the VERBATIM quote straightening, removal of a possessive `'s` after a word character (case-insensitive), SQuAD normalization and a whitespace split; `q_primary = 1` if the token sequence of a gold answer is a contiguous subsequence of the answer's tokens. Token F1 stays secondary. The brief's character-substring rule is kept as the diagnostic `containment_char`, reported only in the robustness appendix. Supersedes C24. | `src/evaluators/quality.py` (`qa_tokens`, `qa_containment`, `qa_containment_char`); tests in `tests/test_quality.py` |
| G1-R2 | **VERBATIM without a hidden length minimum.** Before: every item had at least 3 `\S+` tokens. After: every item contains at least one letter or digit after normalization (still rejects empty, whitespace-only and punctuation-only items); everything else unchanged. The former rule is kept as the diagnostic `verbatim_min3`. | `src/evaluators/constraints.py`, `record.py`; `tests/test_constraints.py` |
| G1-R3 | **F2 synonyms:** `technology`, `tech` and `science` (whole words) added for Sci/Tech. | `src/evaluators/quality.py`; `tests/test_quality.py` |
| G1-R4 | **Fail-fast generation check.** After the from-scratch config replaces `model.generation_config`, the effective config is compared with an allow-list (`do_sample` False, `num_beams` 1, `repetition_penalty` 1.0, `max_new_tokens` 512 or 768 as configured, end-of-turn ids and pad id as in models.yaml, every processor-, criterion- or strategy-adding field inactive; temperature, top_p and top_k only at the inert global defaults). The logits processors and stopping criteria that `generate()` actually builds are recorded for every batch; anything other than no processor plus MaxLengthCriteria and EosTokenCriteria aborts before the batch is written. The result is logged as `r4_check` in run_meta.json and verified by the importer. Additionally, generation (and the notebook) stops if Colab's torch is older than 2.5 or if pip would change it (G1 answer 3). | `src/genconfig.py`, `src/generate.py`, `scripts/import_run.py`, notebook cell 4; `tests/test_genconfig.py` |
| G1-R5 | **Test hook guarded.** `IOS_TEST_ENV_OVERRIDE` aborts every phase except `dryrun` (and the unit tests that exercise it); it is never honored in smoke, pilot, pilot_bs1 or main. The importer also rejects any experimental-phase session that used it. | `src/runs.py`, `src/generate.py`, `scripts/import_run.py`; `tests/test_runs.py` |
| G1-R6 | **Golden-output integration test.** 24 hand-written outputs with hand-written expected values (`tests/fixtures/golden/`) go through the real import → evaluate path in a temporary directory; only the bundle-commit and file-hash checks are skipped; `analysis_eligible: false`. It found one evaluator bug (next row). | `tests/fixtures/golden/`, `tests/test_golden_integration.py`, `src/phases.py` |
| G1-R6a | **Bug fix found by R6:** "May" is both a full month name and an abbreviation, so a gold date such as `12 May 2025` matched two date patterns and could not be canonicalized (evaluation of any F4/F5 task with a May date would have stopped with an error). Identical mentions (same span, same date) now count once. | `src/evaluators/quality.py:find_dates`; regression test in `tests/test_quality.py` |
| G1-A1 | **Smoke run-to-run determinism.** The smoke phase runs twice in the same Colab session; the second pass is a separate run id (`run_info.replicate_of` = the first). `--run-id auto` now reuses the run made from the same bundle (finished models are skipped), so re-running the notebook never repeats work; a second run in the same minute gets a `-2` suffix. | `configs/experiment.yaml` (`passes: 2`), `src/runs.py`, notebook cells 6-8 |
| G1-A3 | **Batch-invariance phase `pilot_bs1`.** After the batch-16 pilot, the 100 order-arm pilot texts per model are regenerated at batch size 1 (300 generations, separate run id); never part of any main analysis. Implemented now so that smoke, pilot and pilot_bs1 use the same generation code. | `configs/experiment.yaml` (`prompt_arms`, `batch_size: 1`), `src/common.py:load_phase_prompts`, `src/generate.py`, `scripts/make_bundle.py` |

Phase flags added to `configs/experiment.yaml`: `experimental` (A100 and bfloat16 required) and
`analysis_eligible` (only `main` is true). Integrity checks X7 (every F1 gold answer has a token under the R1
normalization) and X8 (phase prompt-set sizes, including pilot_bs1 = 100 ids / 100 texts) were added.

### 2.6 Change required by design decision D02 (2026-10-04)

Source: decision D02 (internal decision record, not released). Infrastructure only; no effect on tasks, prompts,
evaluation or analysis (task and prompt SHA-256 unchanged).

| # | Change | Where |
|---|---|---|
| D02-1 | **Canonical Colab Drive root** `/content/drive/MyDrive/Colab Notebooks/emel_hoca_konf_colab/` (with `bundles/` and `runs/`) replaces `MyDrive/emel_hoca_konf_colab/`. It is the notebook's first, clearly marked parameter `DRIVE_ROOT`. The Mac root stays the single source of truth; files move between Drive and the Mac only through the user. | `scripts/build_notebook.py` → `colab/run_generation.ipynb`; `colab/COLAB_RUNBOOK.md`; `README.md` |
| D02-2 | **Paths with spaces.** All paths are pathlib objects and every command an argument list (no shell strings; an audit found none). New test `tests/test_paths_with_spaces.py` runs the bundle build and verification, `src.runs` resolve/env, the replicate pass, the zip and a real dry-run generation in directories whose names contain spaces, and executes the notebook's own cells against such a Drive tree. The golden-output test now also runs in a directory with a space. | `tests/test_paths_with_spaces.py`, `tests/test_golden_integration.py`, `scripts/make_bundle.py` (`out_dir`), `src/phases.py` (`runs_root`) |
| D02-3 | **Bundle selection made unambiguous.** With `BUNDLE = "auto"` the notebook now matches the phase exactly (`pilot` no longer matches a `pilot_bs1` bundle) and stops if more than one bundle for the phase is present, so a superseded bundle (such as `colab_bundle_smoke_2c8a59c.zip`) cannot be used by accident. The work folder's parent is created if missing. | notebook cell `unzip` |
| D02-4 | **Privacy rule for web access** (D02 §3): no personal data in any web request, URL, query string or header; anonymous requests only. Recorded in the project's internal working rules (not released). The analyst's web access so far (Hugging Face Hub API and downloads, PyPI metadata) was anonymous and carried no personal data. The notebook's optional Hugging Face token is described as not needed (the three models are public). | internal working rules, `colab/COLAB_RUNBOOK.md`, notebook cell `token` |

### 2.7 Decision D03 (2026-10-04)

Source: decision D03 (internal decision record, not released). No effect on tasks, prompts or evaluation rules.

| # | Change | Where |
|---|---|---|
| D03-1 | **Exploratory analysis E2 redefined.** The brief's global "forward-reference indicator" (a dependent instruction appears before FORMAT) always equals FORMAT's position minus 1, so it cannot be separated from FORMAT's position. E2 is now defined per referring instruction (LENGTH, CARDINALITY, T4, VERBATIM): compliance when the instruction precedes FORMAT versus when it follows it, stratified by the positions where both occur (2-4 for LENGTH and CARDINALITY; 3 only for T4 and VERBATIM), equal weight per position, pooled and per model, bootstrap CIs, descriptive only. The informative positions are derived from the Williams orders by code and tested against the decision's table. Implementation of the estimate: C4. | `ANALYSIS_PLAN.md` (draft) §6, `src/orders.py:e2_informative_positions`, `tests/test_prompts_and_orders.py` |
| D03-2 | **Public release = history-free snapshot** of the release tag (code, configs, task ids, synthetic tasks, outputs, evaluation results; no git history; no full AG News or XSum texts). The private repository keeps its history. | `README.md` |
| D03-3 | **Repository-local git identity** once the user confirms the e-mail address; the global configuration is never changed. Until then commits keep the current identity. | internal working rules (not released) |
| D03-4 | **No personal data under `runs/`, `results/`, `release/`**, enforced by `src/privacy.py` and `tests/test_privacy.py` (home-directory paths, e-mail addresses, ORCID iDs; the model's output text is not scanned). Logs keep using `<repo>` and `~`. | `src/privacy.py`, `tests/test_privacy.py` |

### 2.8 Decision D04 (2026-10-04) and an open item

Source: decision D04 (internal decision record, not released). Procedural; no effect on design, tasks, prompts,
evaluation or analysis: the smoke import is followed, if every check passes, by building the `pilot` and
`pilot_bs1` bundles together (one Colab session); G4 is split into G4a (numbers) and G4b (figures, remaining
tables, release preparation); no smoke or pilot number enters the abstract; the public repository is created on
GitHub by the user; no project file contains an e-mail address. G2 tooling prepared while the
smoke ran: `scripts/compare_runs.py` (A1, A3), `scripts/smoke_report.py`, `scripts/pilot_report.py` (calibration
rule, A4, A5, audit sample); `src/privacy.py` now also scans every tracked file.

**Open item for G2 (no change made).** Two main XSum tasks contain organizational e-mail addresses in their source
text: `sum_002` (a study's contact mailbox, Dundee) and `sum_013` (a BBC newsroom footer). They are dataset text,
not the authors' data, and the full XSum texts are not part of the public release; model outputs (which are
released) might copy them as evidence. Changing the selection now would reshuffle the F3 pool and change both the
main and the pilot F3 tasks, including the smoke prompt. Proposal: keep the tasks; at release, redact e-mail
addresses that appear in released outputs and evaluation files (`[email removed]`, rule documented in the release
README). `tests/test_privacy.py` pins the two known cases.

### 2.9 Decision D05 (2026-10-04): analysis-plan details

Source: decision D05 (internal decision record, not released). Pre-freeze clarifications of `ANALYSIS_PLAN.md` (draft);
no effect on tasks, prompts, evaluation or generation. Each replaces a detail that the first draft had marked as
proposed; D05 is adopted as written (the proposals differed in all four points and are withdrawn).

| # | Clarification | Replaces |
|---|---|---|
| D05-1 | **P1 display:** observed compliance by position, pooled and per model, with task-clustered bootstrap 95% CIs (Figure 3, Table 4); the per-instruction GEE supplies the joint Wald test (4 df, BH across five) and odds ratios against position 1 with robust 95% CIs. No model-based standardized predictions. | "predicted compliance by position" (brief §5.10 P1); the draft's marginal predictions |
| D05-2 | **P3 Wilcoxon:** `scipy.stats.wilcoxon(d, zero_method="pratt", alternative="two-sided", method="asymptotic")` on d = PS_order − PS_format per task; report n, zeros, positive and negative differences, statistic, p; effect size = mean difference with paired bootstrap CI; all-zero case = "no difference; test not applicable". | the draft's SciPy default (zero differences dropped) |
| D05-3 | **S2 bootstrap p:** p = min(1, 2 · min(#{Δ* ≤ 0} + 1, #{Δ* ≥ 0} + 1) / (B + 1)), with the percentile CI; BH across the three model pairs, separately for mean PS and mean CSR. | the draft's uncorrected two-sided share |
| D05-4 | **E3:** per-model difficulty from the order arm of the final pilot round; HE(m, o) = −Spearman ρ (average ranks for ties) between positions and difficulties; per model, Spearman ρ across the 10 orders between HE and order-level mean CSR and PCR over the 100 main tasks; task-clustered bootstrap CI with HE fixed; descriptive; not estimable if all difficulties tie; caveat on HE's limited range. | the draft's pooled difficulty and Kendall-τ_b index |

### 2.10 Decision D06 (2026-10-04): a fourth model, Gemma 4 E4B

Source: decision D06 (internal decision record, not released; user approval; D7 allowed a fourth model by decision
before G3). An extension that redoes nothing: no existing output is regenerated, tasks, prompts and
`prompt_strings.yaml` keep their SHA-256, existing tests stay. Updates brief §5.7 (model set) and the counts of
§5.5/§5.10.

| # | Change | Where |
|---|---|---|
| D06-1 | **Model:** `google/gemma-4-E4B-it` (verified in the `google` organization), revision `ee0ef6023621cff504d758262d4e04895a5af4a2`, not gated, Apache 2.0 (model card), "4.5B effective (8B with embeddings)" per the model card; 7,996,156,490 parameters stored in safetensors (7,941,100,832 instantiated by the class). Pinned with `scripts/pin_models.py --add gemma4e4b`; the three existing entries are unchanged. | `configs/models.yaml`, `scripts/pin_models.py` |
| D06-2 | **Loading:** native `Gemma4ForConditionalGeneration` (transformers 5.17.0, `trust_remote_code=False`, bf16, SDPA, no quantization). The official class is multimodal (text, image, audio); it is used for text-only inputs (input_ids and attention_mask only). The existing `AutoModelForCausalLM` call resolves to this class. | `src/generate.py` (unchanged loader) |
| D06-3 | **Chat template:** official template, native system role (`<|turn>system … <turn|>`, separate from the user turn, exactly once); thinking disabled with `enable_thinking=False` (also the template default); `render()` now passes model-specific template options and rejects any rendered prompt that contains a thinking marker (`<|think|>`, `<|channel>`, `<channel|>`); the importer rejects outputs that contain one. Template SHA-256 `0a2c8073…01c5b5`. For the three original models the options are empty, so their renderings are unchanged. | `src/generate.py`, `scripts/import_run.py`, `scripts/smoke_report.py` |
| D06-4 | **Generation:** the same greedy configuration built from scratch; end-of-turn ids = the model's own list from `generation_config.json`, `[1, 106, 50]` (`<eos>`, `<turn|>`, `<|tool_response>`); the Hub sampling defaults (temperature 1.0, top_p 0.95, top_k 64) are replaced; R4 unchanged. A code-path check with a tiny randomly initialized Gemma4 configuration (no pretrained weights, nothing stored) confirmed text-only generation, left padding, R4 and the processor record. | `configs/models.yaml` |
| D06-5 | **Phases:** Gemma-only phases with separate run folders: `smoke_gemma` (5 prompts × 2 passes, now), `pilot_gemma` and `pilot_bs1_gemma` (after the G2 decision, final strings; in the same round as any three-model re-run). The main phase lists four models (7,600 generations, 8,000 evaluation records). | `configs/experiment.yaml` |
| D06-6 | **Calibration** is decided on the three original models only (`calibration_models`), declared before any pilot result; Gemma's pilot serves pipeline checks, A3 and E3 and never changes the strings. | `configs/experiment.yaml`, `scripts/pilot_report.py` |
| D06-7 | **Analysis plan:** four models everywhere (P1 `C(model)` with 4 levels; P2, P3, S1 per model; S2 six pairs; E3 per model); BH families per D06 §5.2; model differences descriptive, not attributed to size or family. | `ANALYSIS_PLAN.md` §1, §4-§7 |

## 3. Post-pilot changes (design decision G2, 2026-10-05)

Source: decision G2 (internal decision record, not released; status APPROVED_WITH_CHANGES). Nothing here changes the tasks, the
prompts, the prompt strings, the evaluation rules or `max_new_tokens`; their SHA-256 values are unchanged.

**Calibration record (G2 §1).** Pilot round 0 (run `pilot_20261004-2020_d9e9fc2`): the rule of brief §5.6, decided
on the three original models (D06 §4), did not trigger: LENGTH 79.3% (rule: > 95%), T4 NO_COMMA 49.3% (rule: < 5%
or > 95%), outputs at the length limit 0.0% (rule: > 2%). The strings are final and the pilot round is closed.
Both pass rates are far from the thresholds, and the largest batch-size difference in mean CSR between the
batch-16 pilot and `pilot_bs1` is 0.014, so the batch size could not have changed this decision.

| # | Change | Where |
|---|---|---|
| G2-1 | **Main-run batch size 1** for all four models and both arms (option B). A3 found constraint-vector agreement of 90.0% (Phi-4-mini), 95.0% (Qwen2.5-3B) and 93.0% (SmolLM2-1.7B) against the 98% rule; batch composition alone changed 20-30% of the texts. **Budget statement:** the user confirmed in chat on 2026-10-05 that the Colab compute budget covers option B (estimate then: about 8-10 A100 hours). After Gemma's batch-1 pilot (10.3 s per text) the estimate rose to about 11-12 A100 hours of generation (smollm2 0.9, phi4mini 1.9, qwen25 2.9, gemma4e4b 5.5); the user re-confirmed in chat on 2026-10-05 that the budget covers it. The pre-authorized fallback C is therefore not used. Both arms always share the batch size (P01 and V01 share one generation). The batch-16 phases already run (smoke, pilot) keep their configuration. | `configs/experiment.yaml` (`main.batch_size: 1`), bundle manifest, `ANALYSIS_PLAN.md` §8-§9 |
| G2-2 | **Gemma pilot:** one run at batch size 1 with all 190 texts (both arms); `pilot_bs1_gemma` is dropped (phase, expected counts, Makefile target and empty run folder removed; no output existed). | `configs/experiment.yaml`, `Makefile`, runbook |
| G2-3 | **E3 difficulty** from the batch-1 order-arm pilot outputs, which match the main run: `pilot_bs1` for the three original models and the order arm of `pilot_gemma`. | `ANALYSIS_PLAN.md` E3 |
| G2-4 | **Constant compliance:** a model whose compliance with instruction i is constant in all its main order-arm outputs (1,000 of 1,000 pass or fail) is left out of the P1 GEE and the S2 interaction GEE for i, named with its observed rate; its observed profile stays in Figure 3 and Table 4. One model left: no `C(model)`; none varies: "no variation; test not applicable"; near-constant cases fall under §8 of the plan. A P2 test without variation is reported as "no variation; test not applicable". | `ANALYSIS_PLAN.md` §4, §5, §8 |
| G2-5 | **E-mail addresses in `sum_002` and `sum_013`:** both tasks kept. At release, every e-mail address in a released text field becomes `[email removed]`; evaluation flags stay as computed on the original outputs; the rule is stated in the release README; the privacy test that pins both cases stays. | `README.md` (release section), `tests/test_privacy.py` |
| G2-6 | **A6 determinism check at batch size 1.** At the start of each model's main run the 5 smoke prompts (order-arm pilot texts) are generated at batch size 1 and compared with the model's batch-1 pilot outputs: output text (SHA-256), token count, finish reason and rendered prompt. Reference: `results/qc/a6_reference.json`, built by `scripts/make_a6_reference.py` from the imported `pilot_bs1` and `pilot_gemma` runs. Replicate records go to `a6_replicate.jsonl` and are never analysed. A difference in an identical environment stops the run (exit code 5, notebook `STOP (A6)`); in another environment it is recorded. The main bundle is refused unless the reference covers every model; the importer verifies the records. | `src/generate.py`, `scripts/make_a6_reference.py`, `scripts/make_bundle.py`, `scripts/import_run.py`, notebook; `tests/test_determinism_and_restart.py` |
| G2-7 | **Environment change during a long run.** `--restart-if-environment-changed` (notebook parameter `RESTART_MODELS`) moves a partial model run that cannot resume because the environment changed (settings unchanged) to `superseded/<model>__<UTC stamp>/` with `SUPERSEDED.json`, never deleted and never analysed, and regenerates the model from the start. A complete model is skipped in any environment and never regenerated: the completion check now comes before the environment comparison. The importer checks that superseded runs are kept, listed in `run_meta.json` and from another environment, and makes them read-only. | `src/generate.py`, notebook, `scripts/import_run.py`, runbook §4; `tests/test_determinism_and_restart.py` |
| G2-8 | **Runbook for the long run:** separate sessions with `MODELS` (smollm2 + phi4mini, then qwen25, then gemma4e4b), a compute-unit check before each session, the tab kept open and the Mac kept awake (`caffeinate -di`), and the A6 and restart messages. | `colab/COLAB_RUNBOOK.md` |
| G2-9 | **Tooling:** `scripts/compare_runs.py` reports descriptive A3 details (first divergence, direction of the constraint flips, CSR change, generation time per text). | `scripts/compare_runs.py`, `tests/test_reports.py` |

## 4. Post-hoc analyses and presentation additions (design decision G4a, 2026-10-07)

Source: decision G4a (internal decision record, not released; status APPROVED_WITH_CHANGES). Decided after the main-run results were
seen, **after** the pre-specified P1 GEE proved not estimable for four instructions, and **before** any alternative
estimator had been computed (G4a_REPORT §1.1). The pre-specified results stay the primary results; nothing here
changes a frozen file, a prompt, a task or an evaluation rule.

| # | Change | Where |
|---|---|---|
| G4a-1 | **Post-hoc robustness analysis (option B)** for P1, all five instructions: the same mean model `pass ~ C(position) + C(model) + C(family)`, groups = task, independence working correlation with robust (sandwich) SEs. Excluded mechanically before fitting and reported: models with constant compliance for the instruction (G2 §2.4; Gemma 4 E4B for FORMAT) and family levels with constant compliance across all included models (F5 for LENGTH). Joint Wald χ²(4), p, BH q across the five instructions (its own family), ORs against position 1. A fit that still showed separation or failed to converge would be reported as not estimable (none did); no third estimator. Labelled post-hoc everywhere; never a confirmatory finding. Option C (clustering by model × task) is not used. | `analysis/stats.py` (`working`, `exclude_constant_families`), `analysis/compute.py` (`p1_independence`), Table 4b, keys `main.robustness.p1_independence.*` |
| G4a-2 | **S2 interaction GEE** stays "not estimable" for all five instructions; option B is not applied there. | none |
| G4a-3 | **Constraint-level instability** (post-hoc, descriptive): per model × constraint × arm, the share of tasks whose flag is not constant across the arm's 10 prompts, with the same bootstrap. It interprets RQ3: a (near-)constant constraint cannot contribute to PS. | `analysis/compute.py` (`constraint_instability`), Table A3, keys `main.robustness.constraint_instability.*` |
| G4a-4 | **Table notes** (presentation only): zero-width intervals where an outcome is constant within every family; each model's evaluable rate (non-evaluable outputs score 0 on constraints 2-5, brief §5.8); for FORMAT, a pooled row over the GEE sample (Gemma excluded) next to the existing pooled row. | `analysis/report.py`, keys `main.<arm>.<model>.evaluable_rate*`, `main.order.pooled_excl_gemma4e4b.position.format.*` |
| G4a-5 | **No standalone ABSTRACT_v3**: the congress abstract (v2) was submitted; the full-text abstract is written at W3. | none |

Follow-ups of decision G4b (2026-10-07; source decision G4b §2, internal decision record, not released; no new gate):

| # | Change | Where |
|---|---|---|
| G4b-1 | **Comma spill-over** (exploratory, descriptive; question Q-C2): per model and arm, the share of non-verbatim evidence items, and of outputs tagged `evidence_not_verbatim`, whose non-verbatim item contains no comma and is a contiguous span of the INPUT once its commas (',' and '，') are removed (VERBATIM normalization, whitespace re-collapsed). Main run only; no test. | `analysis/spillover.py`, keys `main.exploratory.e5.<arm>.<model>.evidence_comma_only.*` |
| G4b-2 | **Non-JSON outputs by family** (Q-C3), order arm. | `analysis/compute.py` (E5), keys `main.exploratory.e5.order.<model>.by_family.invalid_json.<family>` |
| G4b-3 | **RQ3 wording**: Gemma 4 E4B's lower PS has two sources, stated descriptively (comparison not tested): three (near-)constant constraints bound its PS mechanically, and on CARDINALITY and VERBATIM its instability is also lower. | `analysis/report.py` (RESULTS_SUMMARY RQ3) |
| G4b-4 | **Citation**: `CITATION.cff` with the paper title, the three authors in D07 order (third author "Emel ARSLAN", D07 §3) and the congress, 2026. Release README: citation and the excerpt line (G4b §2.4). | `CITATION.cff`, `README_RELEASE.md` |
| G4b-5 | **Release tag** `release-v1.0.0` only after the G7 decision, on the commit G7 approves. | none yet |


## 5. Post-hoc analyses and presentation changes (design decision R1, 2026-10-09)

Source: decision R1 §3 (internal decision record, not released; status APPROVED), the triage of review round 1. Decided after all
main-run results had been seen. Every analysis here is re-analysis of the existing main-run outputs; no output was
regenerated, and no frozen file, prompt, task or evaluation rule changed (`make freeze-check`; `git diff
benchmark-v1.0.0 HEAD` touches none of the 34 frozen files). The pre-specified results stay the primary results, and
every value reported before R1 is unchanged. Rows R1-2 to R1-8 are **post-hoc (decision R1)**; R1-9 reports
pre-specified outcomes.

| # | Change | Where |
|---|---|---|
| R1-1 | **Cascade check (Q1, m16); no bug found.** The E6a P3 contrast already uses cascade PS in both arms. The values coincide with the primary PS_format because cascade scoring changes no format-arm output of Qwen2.5-3B and Phi-4-mini (all their format-arm FORMAT failures are non-JSON and score 0 under both policies), and for SmolLM2-1.7B the 113 changed outputs (TRF, parsed JSON with a FORMAT failure) raise three tasks' PS and lower three by 0.2 each (mean 0.310 under both). Gemma 4 E4B: 0.028 primary, 0.000 cascade. The analysis code is unchanged; a regression test was added. | `analysis/posthoc_r1.py` (`cascade_check`), keys `main.posthoc_r1.cascade_check.*`; `tests/test_posthoc_r1.py` |
| R1-2 | **Order-level results (M1, M2):** per model and order (O01-O10) and per variant (V01-V10), mean CSR, PCR and FORMAT with task-clustered CIs; the span (max − min over the ten conditions) of CSR and PCR with a bootstrap CI (the span recomputed in every replicate); for every model pair, the number of orders in which one model's mean CSR (PCR) exceeds the other's. | `analysis/posthoc_r1.py` (`order_level`), Table R1a, Figure R1, keys `main.posthoc_r1.order_level.*` |
| R1-3 | **Fence-tolerant FORMAT (M4):** FORMAT_ft = strict FORMAT after removing exactly one enclosing ```` ``` ```` or ```` ```json ```` fence and surrounding whitespace; otherwise strict FORMAT. CSR_ft and PCR_ft use FORMAT_ft with the other four flags unchanged; ranking of the models; Cochran's Q of PCR_ft across orders for Gemma 4 E4B. | `analysis/posthoc_r1.py` (`format_fence_tolerant`, `fence_tolerant`), Table R1b, keys `main.posthoc_r1.fence_tolerant.*` |
| R1-4 | **Parsed-only TQS (M7):** per task and model, the range of Q over the orders whose answer was parsed, at least two such orders; cells that differ from the pre-specified TQS by more than 0.05 are flagged. | `tqs_parsed`, Table R1e, keys `main.posthoc_r1.tqs_parsed.*` |
| R1-5 | **Kendall's W companion (m1; descriptive):** the number of tasks with constant CSR across the ten orders, and tie-corrected W among the non-constant tasks. | `kendall_companion`, Table R1f, keys `main.posthoc_r1.kendall_w.*` |
| R1-6 | **Evidence length (m4; descriptive):** median `\S+` tokens per evidence item and the shares of 1- and 2-token items, over the string items of list-valued evidence in each model's 1,900 unique generations. | `evidence_length`, Table R1f, keys `main.posthoc_r1.evidence_length.*` |
| R1-7 | **FORMAT failure types by position (Q7; descriptive):** SmolLM2-1.7B and Qwen2.5-3B, order arm, strict FORMAT failures by FORMAT position as fenced, invalid_json (no JSON object), missing_or_extra_key, other (surrounding text, duplicate keys); Qwen also by family. | `failure_type`, `format_failures`, Table R1d, keys `main.posthoc_r1.format_failures.*` |
| R1-8 | **Edit distance (M3; descriptive):** per model tokenizer, the token-level Levenshtein distance of each prompt to P01 (O01) of the same task; medians over the nine formatting variants and over the nine reorderings. Uses the cached tokenizers of the pinned revisions only. | `analysis/edit_distance.py`, Table R1f, keys `main.posthoc_r1.edit_distance.*` |
| R1-9 | **Pre-specified outcomes reported (M6):** S1 format-arm VSR and flip rate (existing keys), and the secondary outcomes of ANALYSIS_PLAN §3 per arm: QA max token F1, CLS unresolved-label and no-label rates (among outputs with a parsed answer), EXT/TRF exact-all-fields, VERBATIM case-insensitive (existing E6c key). Not post-hoc; first reported after review round 1 (exception: the no-label rate is post-hoc, see R2-3). | `secondary`, Table R1c, keys `main.secondary.*` |
| R1-10 | **Display labels (m7, m8; presentation only):** orders shown as O01-O10 (= P01-P10), the fourth constraint as NO_COMMA (key `t4`), families as QA, CLS, SUM, EXT, TRF. Data ids and keys are unchanged; figure values are unchanged. | `analysis/report.py`, `analysis/figures.py` |
| R1-11 | **Analysis software versions** recorded as keys (m15). | `analysis/run.py`, keys `checks.software.analysis.*` |
| R1-12 | **Source-text attribution (m5):** quoted spans of AG News and XSum texts inside model outputs remain under their sources' terms. | `README_RELEASE.md` |

## 6. Review round 2 (design decision R2, 2026-10-10)

Source: decision R2 §3 (internal decision record, not released; status APPROVED). Re-analysis of the existing main-run outputs
only; no frozen file, prompt, task or evaluation rule changed, and every earlier value is unchanged (one label text,
`main.secondary.label`, was extended for R2-3).

| # | Change | Where |
|---|---|---|
| R2-1 | **Paired difference under the fence-tolerant reading (M9 d; post-hoc):** Gemma 4 E4B − Phi-4-mini of the per-task mean CSR_ft and PCR_ft over the ten orders, order arm, with the S2 bootstrap (5,000 task-clustered replicates, seed 20261003; percentile 95% CI; two-sided bootstrap p). A test checks that the same code reproduces S2 exactly. | `analysis/posthoc_r1.py` (`paired_difference`), Table R1b note, keys `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.{csr,pcr}.{mean,ci_low,ci_high,p}` |
| R2-2 | **Parsed orders per parsed-only TQS cell (m19; descriptive):** median and minimum number of parsed orders per qualifying task; cells with few parsed orders are lower bounds. | `tqs_parsed`, Table R1e, keys `main.posthoc_r1.tqs_parsed.<family>.<model>.n_orders_{median,min}` |
| R2-3 | **CLS no-label rate relabelled post-hoc (Q10):** the frozen `ANALYSIS_PLAN.md` (§3) and `src/evaluators/README.md` (F2) name only the unresolved-label rate as reported; the no-label rate (`label_status` = `none`) is not named. Values unchanged. | Table R1c header and caption, keys `main.secondary.label`, `main.secondary.no_label_rate.label` |
| R2-4 | **Pooled VSR and flip rate, both arms (m20):** existing keys, now listed explicitly in the key index. | `analysis/report.py` (key index), keys `main.<arm>.pooled.{vsr,flip_rate}.*` |
| R2-5 | **Release tag:** `release-v1.0.0` on the R2 commit (decision R2 §3.7, replacing G4b-5 "after G7"). If G7 requires a code change, the next tag is `release-v1.0.1`. | git tag |

## 7. Gemma visibility (design decision GV, 2026-10-20)

Source: decision GV §3.1 (internal decision record, not released; status APPROVED). Presentation only: no new
analysis, no new key, no changed value; no frozen file changed.

| # | Change | Where |
|---|---|---|
| R3-1 | **Fig. 7, strict versus fence-tolerant scoring (post-hoc):** FORMAT, CSR and PCR per model, order arm, 95% CIs; strict values (primary keys `main.order.<model>.{compliance.format,csr,pcr}`) as filled markers, fence-tolerant values (post-hoc keys `main.posthoc_r1.fence_tolerant.order.<model>.{format,csr,pcr}`, R1-3) as open markers. It shows the fence-tolerant reading that the text already reports. The decision also records that a fence-tolerant secondary metric should have been pre-specified before the freeze, as Gemma's fencing was visible at its smoke test; the numbers therefore keep the post-hoc label. Release tag `release-v1.0.1` on this commit (R2 §3.7). | `analysis/figures.py` (`fence_tolerant_values`, `fig7_fence_tolerant`), `results/figures/fig7_fence_tolerant.{png,pdf}`, `tests/test_posthoc_r1.py` |

## 8. Post-hoc re-analysis with normalized FORMAT scoring (2026-10-26)

The authors specified a re-analysis of the main-run outputs in which FORMAT is scored after one enclosing code
fence is removed. The rule was defined after the outputs had been seen, so every result of this section is
post-hoc. No output was regenerated, and no frozen file, prompt, task or evaluation rule changed
(`make freeze-check`). The pre-specified strict results are unchanged in `results/metrics/summary.json`; the
re-analysis writes only to `results/posthoc_norm/` (keys `main.posthoc_norm.*`).

| # | Item | Where |
|---|---|---|
| N-1 | **Normalized FORMAT.** If the whole response (surrounding whitespace ignored) is exactly one code fence opened by ```` ``` ```` or ```` ```json ```` (any letter case) and closed at the end, the unchanged strict FORMAT check is applied to the fence content; otherwise to the response itself. Nothing is repaired. Rejected: text outside the fence, several blocks, an unclosed fence, other language tags, other fence styles, and fence content that fails the strict check. The rule is the one already used for the fence-tolerant reading (R1-3) and applies to all four models and both arms. In the main run it changes 2,014 of 8,000 FORMAT decisions, all from fail to pass: every Gemma 4 E4B record (2,000) and 14 Qwen2.5-3B CLS records in the order arm. | `analysis/posthoc_norm.py` (`normalize_output`, `format_normalized`); `tests/test_posthoc_norm.py` |
| N-2 | **Reproduction of the strict results.** The raw outputs are evaluated again with the frozen evaluator; the 8,000 records equal the stored records, and the strict results recomputed from them equal `summary.json` (977 keys). | `analysis/posthoc_norm.py` (`inventory_and_reproduction`) |
| N-3 | **Invariance of the other measures.** Each output is evaluated as generated and after the fence is removed: LENGTH, CARDINALITY, NO_COMMA, VERBATIM (and its diagnostics), task quality and evaluability are identical in all 8,000 records. | `analysis/posthoc_norm.py` (`normalized_frame`) |
| N-4 | **Analyses under the normalized policy**, with the same bootstrap (5,000 task-clustered replicates, stratified by family, seed 20261003) and the same tests as the strict analysis: S1 metrics in both arms; Friedman and Cochran's Q tests with Benjamini-Hochberg adjustment per test family (Cochran's Q now estimable for all four models); constant-CSR task counts and Kendall's W among the variable tasks; order-level profiles, spans and rankings; PS_order − PS_format (Wilcoxon, Pratt, normal approximation); position rates, the exchangeable FORMAT GEE under the constant-compliance rule (Gemma 4 E4B, constant at 100%, is left out) and the independence-correlation sensitivity GEE; model pairs for CSR and PS_order; constraint-level instability; cascade scoring and the subset that passes FORMAT, both with normalized FORMAT; the hard-to-easy index with normalized pilot difficulties. | `analysis/posthoc_norm.py`; tables `results/posthoc_norm/tables/` |
| N-5 | **Additional post-hoc test family:** the six model pairs for mean PCR (order arm), paired over tasks, Benjamini-Hochberg across the six, set before these tests were computed. | `pcr_pairs` |
| N-6 | **Figures** from the normalized keys only (order level, PS by arm, position profiles, constraint profiles) and one labelled comparison of strict and normalized scoring. The strict figures are kept unchanged. An automatic audit checks that no table or figure reads keys of the other policy, except the labelled comparison. | `results/posthoc_norm/figures/`, `results/posthoc_norm/policy_audit.json` |
| N-7 | **Code changes without effect on earlier values:** optional key prefixes for the order-level analysis and the Kendall companion, an option to compute the model pairs without the interaction GEE, and file-name and note options for the figure functions. Every earlier figure and key is unchanged. | `analysis/compute.py`, `analysis/posthoc_r1.py`, `analysis/figures.py` |

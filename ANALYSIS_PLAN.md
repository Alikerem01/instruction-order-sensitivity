# Analysis plan — frozen at G3 (`benchmark-v1.0.0`)

Status: **frozen on 2026-10-05** (C3, after the G2 decision), before the main run: committed, hashed in
`data/benchmark_v1/manifest.json` and tagged `benchmark-v1.0.0`. It changes only through a `DESIGN_DEVIATIONS.md`
entry and a recorded design decision; if a change could affect results, results are reported both ways.

Sources: brief §5.1, §5.6, §5.9-§5.10 (internal record, not released); design decisions G1 (R1-R3, A1,
A3), D03 §3, D05, D06 and G2 (§2.1-§2.4, §3.1-§3.3) (internal records, not released); rules of `src/evaluators/README.md`.
The four implementation details proposed in the first draft (P1 display, P3 zero handling, S2 bootstrap p-values,
E3) were decided by D05, and the constant-compliance rule proposed at G2 was approved with clarifications (G2
§2.4); no proposed item remains.

## 1. Data

* **Analysed data:** the main phase only (`analysis_eligible: true`): 100 tasks (5 families × 20) × 4 models
  (SmolLM2-1.7B, Qwen2.5-3B, Phi-4-mini and, by decision D06, Gemma 4 E4B) × 20 prompt ids (order arm P01-P10,
  format arm V01-V10) = 8,000 evaluation records. P01 and V01 are the same text and share one generation
  (1,900 generations per model, 7,600 in total).
* **Pilot:** used only for the calibration rule (brief §5.6), which is decided on the three original models only
  (decision D06 §4, declared before any pilot result; it did not trigger, so the strings are final), and to
  estimate constraint difficulty for E3 from batch-1 order-arm pilot outputs (decision G2 §2.3, see E3). Gemma's
  pilot never changes the prompt strings. Never used to choose prompts or orders. Smoke, the dry-run, the A6
  replicate records, superseded partial runs and the golden-output fixture never enter any analysis.
* **Generation:** greedy decoding at batch size 1 for all main outputs, both arms and all four models (decision
  G2 §2.1; see §8 and §9).
* **Input files:** the evaluation records written by `make evaluate` (one per prompt id and model); every reported
  number is reproducible from the raw outputs with one command.
* **Units:** an output is one (prompt id, model) pair; the task is the cluster; arms are analysed separately
  unless stated otherwise.

## 2. Hypotheses (brief §5.1; all two-sided)

* **H1** Mean CSR and PCR differ across the 10 orders (per model).
* **H2** At least one instruction shows a position effect (BH-adjusted).
* **H3** Models differ in mean permutation sensitivity.
* **H4** Order-arm PS differs from format-arm PS.

## 3. Outcomes

* **Constraint flags** per output: c1 FORMAT (strict), c2 LENGTH, c3 CARDINALITY, c4 T4 (NO_COMMA, or LOWERCASE if
  the calibration rule replaced it), c5 VERBATIM (decision G1-R2: every evidence item must contain a letter or
  digit; no length minimum). c2-c5 come from the lenient parse; a non-evaluable output scores 0 on c2-c5.
* **CSR** = mean of c1-c5 for one output. **PCR** = share of outputs with all five flags equal to 1.
* **PS** (permutation sensitivity) for one task × model × arm = max CSR − min CSR over the arm's 10 prompts
  (PS_order: P01-P10; PS_format: V01-V10; always exactly 10 prompts).
* **VSR** = share of task × model pairs whose 5-bit constraint vector is identical across the 10 prompts of an arm.
* **Pairwise flip rate** = share of the 45 prompt pairs within a task × model × arm whose vectors differ, averaged
  over task × model.
* **Position compliance** = P(c_i = 1 | position = k) in the order arm, for each instruction i and position k.
* **Task quality Q** per family, reported per family only and never averaged across families:
  F1 primary = whole-token containment (decision G1-R1), secondary = token F1; F2 = label accuracy with the fixed
  synonym and cue rules (Sci/Tech synonyms include `technology`, `tech`, `science`, decision G1-R3; unresolved
  = 0); F3 = ROUGE-L F1; F4/F5 primary = field accuracy, secondary = exact-all-fields.
  **TQS** = max Q − min Q over the 10 orders for one task × model, per family.
* **Diagnostics** (robustness section only): `containment_char` (the brief's character-level F1 rule) and
  `verbatim_min3` (the VERBATIM rule before G1-R2).

## 4. Primary analyses

* **P1 (RQ2, H2).** For each instruction separately, a GEE logistic regression on the order-arm outputs:
  `pass_c ~ C(position) + C(model) + C(family)` (`C(model)` with 4 levels), groups = `task_id`, exchangeable
  working correlation, robust
  (sandwich) standard errors. The GEE supplies (a) the joint Wald test of the four position terms (4 df),
  BH-adjusted across the five instructions (q), and (b) odds ratios against position 1 with robust 95% CIs, in a
  table. The primary display (Figure 3, Table 4) is the **observed** compliance by position, pooled over models and
  per model, with task-clustered bootstrap 95% CIs: the Williams design balances position against model, family
  and the positions of the other instructions, so the observed marginal compliance by position is not confounded
  (decision D05 §1; replaces "predicted compliance by position" in brief §5.10). Model-based standardized
  predictions are not computed.
  * **Constant compliance (decision G2 §2.4).** A model whose compliance with instruction i is constant across
    all its main order-arm outputs (all 1,000 pass, or all 1,000 fail) is left out of the P1 GEE for i and of the
    S2 interaction GEE for i, because `C(model)` would separate. The table names the excluded model and its
    observed rate; its observed position profile is still shown in Figure 3 and Table 4. If only one model
    remains, the GEE drops `C(model)`; if no model varies, the result is "no variation; test not applicable".
    Near-constant cases and any other convergence or separation problem fall under §8 (not estimable; bootstrap
    descriptives).
* **P2 (RQ1, H1; systematic effect).** Per model: Cochran's Q test of PCR across the 10 orders (100 tasks × 10
  binary matrix) and a Friedman test of CSR across the 10 orders (100 × 10), with Kendall's
  W = χ² / (n (k − 1)) as the effect size. BH across the four models, separately for the Friedman tests and for the
  Cochran's Q tests (decision D06 §5). A test whose input has no variation is reported as "no variation; test not
  applicable" (decision G2 §2.4).
* **P3 (RQ4, H4).** Per model, d = PS_order − PS_format per task (100 tasks). Wilcoxon signed-rank test
  `scipy.stats.wilcoxon(d, zero_method="pratt", alternative="two-sided", method="asymptotic")` (normal
  approximation; `method="asymptotic"` is the argument name in the pinned SciPy 1.17.1; `correction=False`, the
  default). Reported: n, the number of zero differences, the numbers of positive and negative differences, the
  statistic and p; BH-adjusted across the four models. Effect size: the mean difference with its paired,
  task-clustered bootstrap 95% CI. If all differences are zero for a model: "no difference; test not applicable"
  (decision D05 §2).

## 5. Secondary analyses

* **S1 (RQ1, task level).** PS, VSR and pairwise flip rate per model, both arms, with bootstrap CIs.
* **S2 (RQ3, H3).** Paired, task-clustered bootstrap of the model differences in mean PS and in mean CSR (six
  model pairs). For a bootstrap distribution Δ*₁ … Δ*_B (B = 5,000): p = min(1, 2 · min(#{Δ*_b ≤ 0} + 1,
  #{Δ*_b ≥ 0} + 1) / (B + 1)), reported with the percentile CI; BH across the six pairs, separately for mean PS
  and for mean CSR (decisions D05 §3, D06 §5). Per-instruction GEE of P1 extended with `C(position):C(model)` and
  a Wald test of the interaction terms, BH across the five instructions; a model with constant compliance with
  the instruction is left out as in P1 (decision G2 §2.4). Model differences are descriptive of these
  four models; they are not attributed to size or family, because the models differ in both (D06 §5).
* **S3.** Task quality and TQS per family and model, descriptive, with bootstrap CIs.

Analyses by family are descriptive (20 tasks per family).

## 6. Exploratory analyses (labelled exploratory in file names, tables and text; no confirmatory claims)

* **E1 Instruction-type grouping.** Position-compliance curves pooled within the groups structural (FORMAT,
  CARDINALITY), lexical (LENGTH, T4) and content (VERBATIM), per model and pooled, with bootstrap CIs.
* **E2 Instructions placed before FORMAT (decision D03 §3).** Every non-FORMAT instruction refers to the JSON keys
  that FORMAT introduces, so a global count of such forward references always equals FORMAT's position minus 1
  and cannot be separated from FORMAT's position. E2 is therefore defined per referring instruction
  i ∈ {LENGTH, CARDINALITY, T4, VERBATIM}:
  * `before_format_i` = 1 if instruction i precedes FORMAT in the order, else 0 (1 in exactly 5 of the 10 Williams
    orders for every i).
  * Contrast: compliance with i when `before_format_i` = 1 versus 0, estimated within the positions of i at which
    both values occur (computed from the design by `src/orders.py:e2_informative_positions`):

    | Instruction | Positions where both values occur |
    |---|---|
    | LENGTH | 2, 3, 4 |
    | CARDINALITY | 2, 3, 4 |
    | T4 | 3 only |
    | VERBATIM | 3 only |

  * Estimate: the position-stratified difference in compliance, with equal weight per informative position,
    pooled over models and also per model, with task-clustered bootstrap 95% CIs (5,000 replicates, seed
    20261003).
  * Descriptive and exploratory only: no hypothesis test and no BH adjustment. `RESULTS_SUMMARY.md` states that
    for T4 and VERBATIM only one position informs the contrast.
  * Implemented in C4, with a unit test on a synthetic table whose stratified difference is known.
* **E3 Hard-to-easy order index (after Zeng et al., 2025; decision D05 §4).**
  * Difficulty: d(m, c) = 1 − compliance of constraint c for model m in the batch-1 order-arm outputs of the
    final pilot round (10 pilot tasks × 10 orders), which match the main run's batch size (decision G2 §2.3):
    `pilot_bs1` for the three original models and the order arm of Gemma's batch-1 `pilot_gemma` run. Main tasks
    are never used.
  * Index: HE(m, o) = −Spearman ρ between the positions (1-5) of the five constraints in order o and their
    difficulties d(m, c), ties given average ranks; HE = +1 means hardest first, −1 easiest first.
  * Analysis: per model, the Spearman ρ across the 10 orders between HE(m, o) and the order-level mean CSR, and
    between HE(m, o) and the order-level PCR, both over the 100 main tasks; 95% CI from a task-clustered bootstrap
    in which HE stays fixed and tasks are resampled. Descriptive only: no test, no BH.
  * If all five difficulties of a model are tied, HE is reported as not estimable for that model.
  * `RESULTS_SUMMARY.md` states that the Williams design was not built to vary HE and that 10 orders give it a
    limited range.
* **E4 Task-quality impact.** TQS per family and model (as S3), and its relation to PS, descriptive.
* **E5 Error taxonomy.** Error-tag rates per model and arm, and for the format-related tags (code fence,
  leading/trailing text, invalid JSON, extra keys) also by FORMAT position, descriptive.
* **E6 Robustness.** Key results of P1-P3 and S1 under (a) cascade scoring (no strict FORMAT pass → all five
  constraints score 0) and (b) the subset of outputs that pass FORMAT strictly; plus the diagnostics
  `containment_char` and `verbatim_min3`.

## 7. Multiple comparisons (decision D06 §5; closes a gap in brief §5.10)

| Analysis | BH adjustment across |
|---|---|
| P1 position Wald tests | the five instructions |
| P2 Friedman tests | the four models |
| P2 Cochran's Q tests | the four models (a separate family) |
| P3 Wilcoxon tests | the four models |
| S2 bootstrap model comparisons | the six model pairs, separately for mean PS and for mean CSR |
| S2 interaction Wald tests | the five instructions |

q-values are reported for each family. Exploratory analyses get no adjustment.

## 8. Conventions

* Bootstrap: 5,000 replicates; tasks resampled with replacement within each family (20 per family); all prompts,
  arms and models of a task move together; seed 20261003; percentile intervals; paired analyses resample the same
  tasks for both quantities.
* Reporting: estimates with 95% CIs; percentages with one decimal; exact p-values to three decimals or "p < .001";
  BH-adjusted values labelled q; "statistically significant" only for the pre-specified tests (P1-P3, S2).
* GEE: `statsmodels` GEE, Binomial family, exchangeable structure, groups = `task_id`. A model with constant
  compliance is left out first (P1, decision G2 §2.4). Convergence failures, separation and warnings are captured
  and reported; a GEE that fails to converge or shows separation is reported as not estimable, and the bootstrap
  descriptives are relied on instead.
* **Batch size (decision G2 §2.1).** All main outputs (both arms, all four models) are generated at batch size 1,
  so each output depends only on its own prompt. The pre-specified A3 check (§9) showed that at batch size 16
  batch composition alone changed 20-30% of the order-arm pilot texts and 5-10% of the constraint vectors
  (vector agreement 90.0%, 95.0% and 93.0% for Phi-4-mini, Qwen2.5-3B and SmolLM2-1.7B, against the 98% rule),
  with no consistent direction. Both arms always use the same batch size, because P01 and V01 share one
  generation.
* No model specification changes after seeing results without a recorded design decision.

## 9. Technical quality-control checks (method validation; not analyses)

* **A1 run-to-run determinism:** the 15 smoke outputs generated twice in one Colab session; byte identity per model
  (passed for all three models; for Gemma 4 E4B in `smoke_gemma`, decision D06, passed as well).
* **A3 batch invariance:** the 100 order-arm pilot texts per model regenerated at batch size 1 (`pilot_bs1`);
  exact output agreement and 5-bit vector agreement with the batch-16 pilot, per model. Rule: if vector agreement
  is at least 98% for every model, the main run keeps batch size 16; otherwise the study team decides at G2.
  Outcome: 90.0%, 95.0% and 93.0% (below the rule); the study team chose batch size 1 for the main run (§8).
  Gemma's pilot therefore runs once at batch size 1 with both arms (`pilot_gemma`); `pilot_bs1_gemma` was
  dropped (decision G2 §2.2).
* **A6 determinism at batch size 1 (decision G2 §3.2):** at the start of each model's main run, the 5 smoke
  prompts (order-arm pilot texts, P01 of the first pilot task per family) are generated at batch size 1 and must
  be byte-identical to the model's batch-1 pilot outputs (`pilot_bs1`; Gemma: `pilot_gemma`). They are stored as
  non-analysed replicate records; a difference in an identical environment stops the run, a difference in
  another environment is reported.
* **One environment per model (decision G2 §3.3):** all main outputs of a model come from one environment. If a
  resume is refused because the environment changed, the partial run is kept under `superseded/` (never deleted,
  never analysed) and the model is regenerated from the start; a complete model is never regenerated.
* **R4 fail-fast generation check** and **R6 golden-output test** (see `DESIGN_DEVIATIONS.md` §2.5).

## 10. Outputs

`results/metrics/summary.json` (stable dotted keys, never renamed after G4), `results/tables/*.csv|md`,
`results/figures/*.png|pdf`, `results/report/RESULTS_SUMMARY.md` (RQ1 → RQ4, then E1-E6, with a key index), as
specified in the implementation specification §6.6-§6.7 (internal record, not released).

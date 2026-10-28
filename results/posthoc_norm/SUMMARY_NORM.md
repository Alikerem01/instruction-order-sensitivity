# SUMMARY_NORM — normalized FORMAT scoring (post-hoc re-analysis)

Run `main_20261006-1354_63a1c79`; bootstrap 5000 task-clustered replicates stratified by family, seed 20261003; generated 2026-10-26T15:15:18Z. Every value is a key of `results/posthoc_norm/summary_norm.json`. These results are a post-hoc re-analysis. The pre-specified strict results are unchanged in `results/metrics/summary.json`.

## Rule

Normalized FORMAT: whitespace around the response is ignored. If the response is exactly one code fence, opened by ``` or ```json (any letter case; optional spaces or tabs and an optional line break after the opening) and closed by ``` at the very end, with no further ``` inside, the strict FORMAT check is applied to the content of the fence. Otherwise the strict FORMAT check is applied to the response itself. Strict FORMAT: the text parses as JSON without duplicate keys into an object whose keys are exactly answer and evidence. Nothing is repaired.

Rejected (strict value kept): text before or after the fence; more than one fenced block, or a fence inside the fenced content; a fence that is not closed; a language tag other than json (for example ```python or ```jsonc); other fence styles (~~~ or a four-backtick opening); fence content that fails the strict check (broken JSON, duplicate keys, missing or extra keys).

## Inventory

- SmolLM2-1.7B: 1900 unique generations, 2000 evaluation records (100 generations shared by O01 and V01); no fence: 1900.
- Qwen2.5-3B: 1900 unique generations, 2000 evaluation records (100 generations shared by O01 and V01); no fence: 1886; one enclosing fence, tag 'json': 14.
- Phi-4-mini: 1900 unique generations, 2000 evaluation records (100 generations shared by O01 and V01); no fence: 1900.
- Gemma 4 E4B: 1900 unique generations, 2000 evaluation records (100 generations shared by O01 and V01); one enclosing fence, tag 'json': 1900.

## Checks

- Fresh evaluation of the raw outputs against the stored evaluation records: 8000 records, 0 differences.
- Strict results recomputed from the fresh records against `summary.json`: 977 keys, 0 differences (S1 (both arms), position rates, P1 GEE, P2, P3, S2 pairs and task quality recomputed from the fresh records and compared with summary.json).
- Other four flags and task quality after normalization (each output evaluated as generated and after the fence is removed): 8000 records, 0 differences in the flags and quality scores, 0 in the quality details.
- FORMAT changed from pass to fail: 0 records.
- Constraint rates, position rates and GEE status of LENGTH, CARDINALITY, NO_COMMA and VERBATIM equal the strict values: 424 keys, 0 differences.
- Task quality (Q and TQS) equals the strict values: 120 keys, 0 differences.
- FORMAT, CSR and PCR equal the earlier fence-tolerant values: 90 keys, 0 differences.
- Gemma 4 E4B: FORMAT changed in 2000 of 2000 records; PS, VSR and flip rate equal the strict values up to floating-point rounding (|difference| < 1e-12; 0 differences of 18); largest deviation of the CSR shift from 0.2: 5.6e-17.
- Policy audit (`policy_audit.json`): passed.
- All checks passed: True.

## Table N7

Table N7. FORMAT decisions that differ between the pre-specified strict rule and the normalized rule, by model, arm and family (changed / evaluation records).

| Model | Arm | QA | CLS | SUM | EXT | TRF | Total changed |
|---|---:|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | order | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 |
| SmolLM2-1.7B | format | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 |
| Qwen2.5-3B | order | 0 / 200 | 14 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 14 |
| Qwen2.5-3B | format | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 |
| Phi-4-mini | order | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 |
| Phi-4-mini | format | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 / 200 | 0 |
| Gemma 4 E4B | order | 200 / 200 | 200 / 200 | 200 / 200 | 200 / 200 | 200 / 200 | 1000 |
| Gemma 4 E4B | format | 200 / 200 | 200 / 200 | 200 / 200 | 200 / 200 | 200 / 200 | 1000 |

Every change is from fail to pass. Records whose FORMAT changed from pass to fail: 0.


## Table N1

Table N1. Normalized scoring (post-hoc): FORMAT, CSR and PCR (order arm) and PS in both arms (mean [95% CI], task-clustered bootstrap).

| Model | FORMAT | CSR | PCR | PS_order | PS_format |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 39.9% [36.6%, 43.1%] | 34.1% [32.0%, 36.1%] | 5.8% [3.7%, 8.0%] | 0.296 [0.260, 0.336] | 0.310 [0.280, 0.344] |
| Qwen2.5-3B | 82.3% [81.5%, 83.0%] | 63.6% [62.4%, 64.7%] | 8.1% [5.6%, 10.8%] | 0.308 [0.284, 0.334] | 0.068 [0.052, 0.086] |
| Phi-4-mini | 99.7% [99.2%, 100.0%] | 85.2% [83.6%, 86.8%] | 45.7% [40.2%, 50.9%] | 0.264 [0.238, 0.292] | 0.148 [0.118, 0.180] |
| Gemma 4 E4B | 100.0% [100.0%, 100.0%] | 89.6% [88.0%, 91.1%] | 53.7% [47.1%, 60.3%] | 0.112 [0.090, 0.136] | 0.028 [0.016, 0.042] |
| Pooled | 80.5% [79.7%, 81.3%] | 68.1% [67.2%, 69.0%] | 28.3% [25.7%, 30.9%] | 0.245 [0.230, 0.260] | 0.138 [0.126, 0.151] |

PS is a range of CSR (0-1). CSR, PCR and FORMAT are shown as percentages.


## Table N1b

Table N1b. Normalized scoring (post-hoc): vector stability rate (VSR) and pairwise flip rate by arm (mean [95% CI]).

| Model | VSR, order arm | Flip rate, order arm | VSR, format arm | Flip rate, format arm |
|---|---:|---:|---:|---:|
| SmolLM2-1.7B | 40.0% [36.0%, 44.0%] | 36.0% [33.0%, 39.1%] | 47.0% [42.0%, 52.0%] | 26.8% [23.5%, 30.4%] |
| Qwen2.5-3B | 20.0% [16.0%, 24.0%] | 32.6% [29.4%, 35.7%] | 70.0% [63.0%, 77.0%] | 12.3% [9.0%, 15.8%] |
| Phi-4-mini | 18.0% [12.0%, 24.0%] | 47.6% [44.1%, 51.1%] | 47.0% [39.0%, 55.0%] | 23.1% [18.8%, 27.4%] |
| Gemma 4 E4B | 56.0% [48.0%, 64.0%] | 19.1% [15.1%, 23.1%] | 87.0% [81.0%, 93.0%] | 4.7% [2.3%, 7.5%] |
| Pooled | 33.5% [30.5%, 36.5%] | 33.8% [31.9%, 35.6%] | 62.7% [59.0%, 66.2%] | 16.7% [15.0%, 18.6%] |


## Table N1c

Table N1c. Normalized scoring (post-hoc): FORMAT, CSR and PCR in the format arm (mean [95% CI]).

| Model | FORMAT | CSR | PCR |
|---|---:|---:|---:|
| SmolLM2-1.7B | 46.0% [43.4%, 48.8%] | 37.5% [35.3%, 40.0%] | 12.5% [8.0%, 17.3%] |
| Qwen2.5-3B | 80.0% [80.0%, 80.0%] | 65.4% [63.9%, 66.8%] | 13.5% [9.0%, 18.2%] |
| Phi-4-mini | 99.9% [99.7%, 100.0%] | 90.2% [88.3%, 91.9%] | 62.4% [55.5%, 68.9%] |
| Gemma 4 E4B | 100.0% [100.0%, 100.0%] | 90.3% [88.3%, 92.2%] | 56.2% [48.2%, 64.2%] |
| Pooled | 81.5% [80.8%, 82.2%] | 70.8% [69.8%, 71.9%] | 36.1% [32.8%, 39.2%] |


## Table N2

Table N2. Normalized scoring (post-hoc): tests of systematic order effects across the ten orders (100 tasks per model). Friedman test on CSR; Cochran's Q on PCR.

| Model | Friedman χ² (df) | p | q | Kendall's W | Cochran's Q (df) | p | q | Constant-CSR tasks | W, variable-CSR tasks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 110.47 (9) | < .001 | < .001 | 0.123 | 22.40 (9) | .008 | .008 | 40 | 0.205 |
| Qwen2.5-3B | 151.37 (9) | < .001 | < .001 | 0.168 | 54.27 (9) | < .001 | < .001 | 20 | 0.210 |
| Phi-4-mini | 61.09 (9) | < .001 | < .001 | 0.068 | 63.28 (9) | < .001 | < .001 | 19 | 0.084 |
| Gemma 4 E4B | 101.21 (9) | < .001 | < .001 | 0.112 | 89.89 (9) | < .001 | < .001 | 56 | 0.256 |

q: Benjamini-Hochberg across the four Friedman tests, and separately across the 4 estimable Cochran's Q tests.


## Table N3

Table N3. Normalized scoring (post-hoc): FORMAT compliance by instruction position (order arm; mean [95% CI]). Each position is realized by two orders.

| Model | Position 1 | Position 2 | Position 3 | Position 4 | Position 5 |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 43.0% [39.0%, 47.5%] | 41.5% [36.5%, 46.5%] | 21.5% [16.0%, 27.5%] | 35.0% [30.5%, 40.0%] | 58.5% [55.5%, 61.5%] |
| Qwen2.5-3B | 79.5% [78.5%, 80.0%] | 80.0% [78.5%, 81.5%] | 80.0% [78.5%, 81.5%] | 80.0% [80.0%, 80.0%] | 92.0% [90.5%, 94.0%] |
| Phi-4-mini | 100.0% [100.0%, 100.0%] | 99.5% [98.5%, 100.0%] | 99.5% [98.5%, 100.0%] | 99.5% [98.5%, 100.0%] | 100.0% [100.0%, 100.0%] |
| Gemma 4 E4B | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] |
| Pooled | 80.6% [79.6%, 81.8%] | 80.2% [79.0%, 81.5%] | 75.2% [73.8%, 76.8%] | 78.6% [77.4%, 79.9%] | 87.6% [86.8%, 88.5%] |
| GEE sample (SmolLM2-1.7B, Qwen2.5-3B, Phi-4-mini) | 74.2% [72.8%, 75.7%] | 73.7% [72.0%, 75.3%] | 67.0% [65.0%, 69.0%] | 71.5% [69.8%, 73.2%] | 83.5% [82.3%, 84.7%] |

The pooled row includes every model; the GEE-sample row includes only the models in the FORMAT GEE.

- Exchangeable GEE, FORMAT: Wald χ²(4) = 105.20, p < .001, q < .001, n = 3000; excluded (constant): Gemma 4 E4B 100.0%. Odds ratios against position 1: position 2: 0.90 [0.49, 1.66], position 3: 0.25 [0.13, 0.46], position 4: 0.59 [0.32, 1.08], position 5: 11.50 [4.93, 26.87].
- Exchangeable GEE, LENGTH: not estimable (separation: family=F5_TRANSFORMATION: all pass).
- Exchangeable GEE, CARDINALITY: not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
- Exchangeable GEE, NO_COMMA: not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
- Exchangeable GEE, VERBATIM: not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
- Independence GEE (sensitivity), FORMAT: Wald χ²(4) = 105.59, p < .001, q < .001, n = 3000; excluded (constant): Gemma 4 E4B 100.0%. Odds ratios against position 1: position 2: 0.90 [0.49, 1.66], position 3: 0.25 [0.14, 0.46], position 4: 0.59 [0.32, 1.08], position 5: 11.58 [4.94, 27.15].
- Independence GEE (sensitivity), LENGTH: Wald χ²(4) = 56.98, p < .001, q < .001, n = 3200; constant families left out: TRF. Odds ratios against position 1: position 2: 0.75 [0.42, 1.31], position 3: 2.49 [1.29, 4.80], position 4: 0.37 [0.20, 0.69], position 5: 0.40 [0.20, 0.80].
- Independence GEE (sensitivity), CARDINALITY: Wald χ²(4) = 93.26, p < .001, q < .001, n = 4000. Odds ratios against position 1: position 2: 1.23 [1.01, 1.49], position 3: 1.58 [1.30, 1.92], position 4: 1.34 [1.08, 1.65], position 5: 0.63 [0.50, 0.80].
- Independence GEE (sensitivity), NO_COMMA: Wald χ²(4) = 20.61, p < .001, q < .001, n = 4000. Odds ratios against position 1: position 2: 1.29 [1.05, 1.59], position 3: 1.19 [0.94, 1.50], position 4: 1.19 [0.93, 1.52], position 5: 0.63 [0.47, 0.84].
- Independence GEE (sensitivity), VERBATIM: Wald χ²(4) = 14.58, p = .006, q = .006, n = 4000. Odds ratios against position 1: position 2: 1.19 [1.01, 1.41], position 3: 0.97 [0.82, 1.14], position 4: 1.07 [0.90, 1.29], position 5: 1.20 [1.00, 1.44].


## Table N4

Table N4. Normalized scoring (post-hoc): PS_order − PS_format per model (100 tasks; paired task-clustered bootstrap CI; Wilcoxon signed-rank test, Pratt zero handling, normal approximation; q: Benjamini-Hochberg across the four models).

| Model | Mean difference [95% CI] | Tasks + / − / 0 | Wilcoxon statistic | p | q |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | -0.014 [-0.048, 0.018] | 28 / 32 / 40 | 2000.0 | .682 | .682 |
| Qwen2.5-3B | 0.240 [0.212, 0.270] | 69 / 3 / 28 | 132.5 | < .001 | < .001 |
| Phi-4-mini | 0.116 [0.084, 0.148] | 55 / 7 / 38 | 480.5 | < .001 | < .001 |
| Gemma 4 E4B | 0.084 [0.060, 0.110] | 35 / 2 / 63 | 150.0 | < .001 | < .001 |


## Table N5

Table N5. Normalized scoring (post-hoc): paired differences between models, order arm (difference a − b, mean [95% CI], bootstrap q).

| Pair | Mean CSR | Mean PS_order | Mean PCR |
|---|---:|---:|---:|
| SmolLM2-1.7B − Qwen2.5-3B | -29.6% [-32.2%, -27.0%], q < .001 | -0.012 [-0.058, 0.034], q = .565 | -2.3% [-6.5%, 1.8%], q = .280 |
| SmolLM2-1.7B − Phi-4-mini | -51.1% [-53.7%, -48.7%], q < .001 | 0.032 [-0.014, 0.078], q = .192 | -39.9% [-45.5%, -34.3%], q < .001 |
| SmolLM2-1.7B − Gemma 4 E4B | -55.5% [-58.0%, -53.1%], q < .001 | 0.184 [0.144, 0.226], q < .001 | -47.9% [-54.8%, -41.0%], q < .001 |
| Qwen2.5-3B − Phi-4-mini | -21.6% [-23.4%, -19.8%], q < .001 | 0.044 [0.006, 0.084], q = .029 | -37.6% [-43.5%, -31.2%], q < .001 |
| Qwen2.5-3B − Gemma 4 E4B | -25.9% [-27.7%, -24.2%], q < .001 | 0.196 [0.162, 0.230], q < .001 | -45.6% [-52.6%, -38.5%], q < .001 |
| Phi-4-mini − Gemma 4 E4B | -4.4% [-6.3%, -2.3%], q < .001 | 0.152 [0.116, 0.186], q < .001 | -8.0% [-14.9%, -1.0%], q = .033 |

Each column is its own Benjamini-Hochberg family of six pairs. The PCR family is an additional post-hoc family.


## Table N6

Table N6. Normalized scoring (post-hoc): mean CSR across the ten orders, with the span (max − min over the ten conditions; bootstrap 95% CI) of CSR and PCR, and the span of CSR across the ten formatting variants. Per-order values with CIs are in the CSV file.

| Model | Lowest CSR (order) | Highest CSR (order) | CSR span, order arm | PCR span, order arm | CSR span, format arm |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 24.2% (O02) | 43.4% (O03) | 0.192 [0.152, 0.234] | 0.100 [0.060, 0.170] | 0.266 [0.238, 0.300] |
| Qwen2.5-3B | 56.6% (O07) | 77.6% (O03) | 0.210 [0.186, 0.240] | 0.150 [0.110, 0.190] | 0.026 [0.018, 0.044] |
| Phi-4-mini | 80.2% (O05) | 90.8% (O01) | 0.106 [0.080, 0.136] | 0.310 [0.240, 0.400] | 0.050 [0.038, 0.078] |
| Gemma 4 E4B | 84.8% (O10) | 93.0% (O04) | 0.082 [0.062, 0.108] | 0.280 [0.210, 0.370] | 0.018 [0.010, 0.032] |

Rankings:

- CSR, order arm: Gemma 4 E4B > Phi-4-mini > Qwen2.5-3B > SmolLM2-1.7B (mean over the ten conditions) in 9 of 10 conditions.
- PCR, order arm: Gemma 4 E4B > Phi-4-mini > Qwen2.5-3B > SmolLM2-1.7B (mean over the ten conditions) in 6 of 10 conditions.
- CSR, format arm: Gemma 4 E4B > Phi-4-mini > Qwen2.5-3B > SmolLM2-1.7B (mean over the ten conditions) in 4 of 10 conditions.
- PCR, format arm: Phi-4-mini > Gemma 4 E4B > Qwen2.5-3B > SmolLM2-1.7B (mean over the ten conditions) in 2 of 10 conditions.
- SmolLM2-1.7B vs Qwen2.5-3B, order arm: CSR 0 / 10 / 0; PCR 3 / 6 / 1 (higher / lower / tied).
- SmolLM2-1.7B vs Phi-4-mini, order arm: CSR 0 / 10 / 0; PCR 0 / 10 / 0 (higher / lower / tied).
- SmolLM2-1.7B vs Gemma 4 E4B, order arm: CSR 0 / 10 / 0; PCR 0 / 10 / 0 (higher / lower / tied).
- Qwen2.5-3B vs Phi-4-mini, order arm: CSR 0 / 10 / 0; PCR 0 / 10 / 0 (higher / lower / tied).
- Qwen2.5-3B vs Gemma 4 E4B, order arm: CSR 0 / 10 / 0; PCR 0 / 10 / 0 (higher / lower / tied).
- Phi-4-mini vs Gemma 4 E4B, order arm: CSR 1 / 9 / 0; PCR 2 / 8 / 0 (higher / lower / tied).

Ties: the counts compare the per-condition means. A ranking holds in a condition only if every adjacent pair is strictly ordered, and `n_ties` counts equal means. Because the means are compared as floating-point numbers, an exact tie can be counted as higher or lower. Phi-4-mini and Gemma 4 E4B have exactly equal mean CSR in V07 and V09 (format arm). Rounding error decides these ties, so the stored counts are 6 / 4 / 0 (higher / lower / tied) and the CSR ranking holds in 4 of 10 conditions. Counting exact ties as ties gives 6 / 2 / 2 and 2 of 10. No other count is affected; the stored values are unchanged.


## Table N8

Table N8. Normalized scoring (post-hoc): compliance with each constraint and PCR, order arm (mean [95% CI]). Only FORMAT differs from the strict scoring.

| Model | FORMAT | LENGTH | CARDINALITY | NO_COMMA | VERBATIM | PCR |
|---|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 39.9% [36.6%, 43.1%] | 60.6% [59.6%, 61.9%] | 9.7% [6.7%, 12.8%] | 33.4% [29.5%, 37.2%] | 26.8% [23.3%, 30.2%] | 5.8% [3.7%, 8.0%] |
| Qwen2.5-3B | 82.3% [81.5%, 83.0%] | 82.2% [81.3%, 82.9%] | 46.6% [43.6%, 49.6%] | 35.0% [31.1%, 38.3%] | 72.1% [68.7%, 74.9%] | 8.1% [5.6%, 10.8%] |
| Phi-4-mini | 99.7% [99.2%, 100.0%] | 95.2% [93.1%, 97.1%] | 80.0% [75.5%, 84.2%] | 73.5% [70.0%, 76.5%] | 77.7% [72.5%, 82.9%] | 45.7% [40.2%, 50.9%] |
| Gemma 4 E4B | 100.0% [100.0%, 100.0%] | 99.7% [99.2%, 100.0%] | 83.2% [77.9%, 88.3%] | 99.6% [98.8%, 100.0%] | 65.4% [58.5%, 72.2%] | 53.7% [47.1%, 60.3%] |
| Pooled | 80.5% [79.7%, 81.3%] | 84.4% [83.8%, 85.1%] | 54.9% [52.2%, 57.5%] | 60.4% [58.4%, 62.2%] | 60.5% [57.9%, 63.1%] | 28.3% [25.7%, 30.9%] |


## Table N9

Table N9. Normalized scoring (post-hoc): exploratory and robustness analyses.

**Cascade scoring with normalized FORMAT and the subset passing normalized FORMAT** (order arm):

- SmolLM2-1.7B: cascade CSR 27.9% [25.1%, 30.7%]; cascade PS_order − PS_format 0.130 [0.084, 0.174], p = .003; subset passing normalized FORMAT: n = 399, CSR 70.0% [66.8%, 73.1%].
- Qwen2.5-3B: cascade CSR 63.6% [62.4%, 64.7%]; cascade PS_order − PS_format 0.240 [0.212, 0.270], p < .001; subset passing normalized FORMAT: n = 823, CSR 77.3% [76.0%, 78.5%].
- Phi-4-mini: cascade CSR 85.2% [83.6%, 86.8%]; cascade PS_order − PS_format 0.118 [0.086, 0.150], p < .001; subset passing normalized FORMAT: n = 997, CSR 85.5% [83.8%, 87.0%].
- Gemma 4 E4B: cascade CSR 89.6% [88.0%, 91.1%]; cascade PS_order − PS_format 0.084 [0.060, 0.110], p < .001; subset passing normalized FORMAT: n = 1000, CSR 89.6% [88.0%, 91.1%].

**Hard-to-easy index with normalized pilot difficulties** (ten fixed orders, not a test):

- SmolLM2-1.7B: difficulties FORMAT 0.62, LENGTH 0.41, CARDINALITY 0.88, NO_COMMA 0.70, VERBATIM 0.73; ρ(HE, order-level CSR) = -0.08 [-0.15, 0.03]; ρ(HE, order-level PCR) = -0.23 [-0.61, 0.26].
- Qwen2.5-3B: difficulties FORMAT 0.18, LENGTH 0.17, CARDINALITY 0.46, NO_COMMA 0.61, VERBATIM 0.34; ρ(HE, order-level CSR) = -0.12 [-0.42, 0.01]; ρ(HE, order-level PCR) = -0.20 [-0.30, 0.28].
- Phi-4-mini: difficulties FORMAT 0.00, LENGTH 0.00, CARDINALITY 0.09, NO_COMMA 0.31, VERBATIM 0.22; ρ(HE, order-level CSR) = -0.62 [-0.67, -0.21]; ρ(HE, order-level PCR) = -0.41 [-0.72, -0.17].
- Gemma 4 E4B: difficulties FORMAT 0.00, LENGTH 0.00, CARDINALITY 0.16, NO_COMMA 0.00, VERBATIM 0.52; ρ(HE, order-level CSR) = 0.67 [0.39, 0.78]; ρ(HE, order-level PCR) = 0.62 [0.37, 0.78].

**Normalized FORMAT failures by type, with the raw-output code_fence tag** (order arm):

- SmolLM2-1.7B: normalized FORMAT failures 60.1% of 1000 order-arm records (invalid JSON 392, missing or extra key 209, fenced with failing content 0, other 0); raw-output code_fence tag 0.0%.
- Qwen2.5-3B: normalized FORMAT failures 17.7% of 1000 order-arm records (invalid JSON 177, missing or extra key 0, fenced with failing content 0, other 0); raw-output code_fence tag 1.4%.
- Phi-4-mini: normalized FORMAT failures 0.3% of 1000 order-arm records (invalid JSON 2, missing or extra key 0, fenced with failing content 0, other 1); raw-output code_fence tag 0.0%.
- Gemma 4 E4B: normalized FORMAT failures 0.0% of 1000 order-arm records (invalid JSON 0, missing or extra key 0, fenced with failing content 0, other 0); raw-output code_fence tag 100.0%.

**Share of tasks whose flag varies across the ten orders**:

- SmolLM2-1.7B: FORMAT 54.0%, LENGTH 3.0%, CARDINALITY 33.0%, NO_COMMA 13.0%, VERBATIM 51.0%.
- Qwen2.5-3B: FORMAT 21.0%, LENGTH 22.0%, CARDINALITY 51.0%, NO_COMMA 27.0%, VERBATIM 51.0%.
- Phi-4-mini: FORMAT 2.0%, LENGTH 16.0%, CARDINALITY 54.0%, NO_COMMA 35.0%, VERBATIM 52.0%.
- Gemma 4 E4B: FORMAT 0.0%, LENGTH 2.0%, CARDINALITY 23.0%, NO_COMMA 1.0%, VERBATIM 34.0%.


## Figures

In `results/posthoc_norm/figures/` (300 dpi PNG and PDF, 16 cm wide):

- `fig_overall_strict_vs_norm`: Fig. 2 of the v2.9 numbering; FORMAT, CSR and PCR per model, pre-specified strict versus normalized
- `fig_order_level_norm`: Fig. 3 of the v2.9 numbering; mean CSR and FORMAT compliance in O01-O10, normalized
- `fig_noise_floor_norm`: Fig. 4 of the v2.9 numbering; PS by arm and PS_order - PS_format, normalized
- `fig_position_norm`: Fig. 5 of the v2.9 numbering; compliance by instruction position, normalized
- `fig_constraints_norm`: Fig. 7 of the v2.9 numbering; constraint profiles and PCR, normalized

## Key index

- `main.posthoc_norm.<arm>.<model>.{csr,pcr,ps,vsr,flip_rate}.<stat>` and `main.posthoc_norm.<arm>.<model>.compliance.<c>.<stat>`: S1 metrics and constraint rates (both arms; `<model>` includes `pooled`)
- `main.posthoc_norm.order.<model>.position.<c>.<k>.<stat>`; `main.posthoc_norm.order.gee_sample.position.format.<k>.<stat>`: position rates
- `main.posthoc_norm.p1.<c>.{status,wald_chi2,df,p,q,n,excluded_models,reason,or.<k>.*}`, `main.posthoc_norm.p1.format.sample_models`: exchangeable GEE
- `main.posthoc_norm.robustness.p1_independence.<c>.*`: independence GEE (sensitivity)
- `main.posthoc_norm.tests.friedman.<model>.{chi2,df,p,q_bh,kendall_w,status}`, `main.posthoc_norm.tests.cochran_q.<model>.{q,df,p,q_bh,status}`: order tests
- `main.posthoc_norm.kendall_w.<model>.{n_constant_tasks,n_nonconstant_tasks,kendall_w_nonconstant}`: constant-CSR tasks and W among the variable tasks
- `main.posthoc_norm.p3.<model>.{mean_diff,ci_low,ci_high,wilcoxon_stat,p,q,n,n_pos,n_neg,n_zero,status}`: PS_order − PS_format
- `main.posthoc_norm.s2.<a>_vs_<b>.{csr,ps,pcr}_diff.{mean,ci_low,ci_high,p,q}`: model pairs
- `main.posthoc_norm.order_level.<arm>.<model>.<condition>.{csr,pcr,format}.<stat>`, `.span.{csr,pcr}.<stat>`, `main.posthoc_norm.order_level.<arm>.rank.*`: order-level profiles
- `main.posthoc_norm.order_level.<arm>.rank.<a>_vs_<b>.<metric>.{n_a_higher,n_b_higher,n_ties}` and `main.posthoc_norm.order_level.<arm>.rank.overall.<metric>.n_conditions_reproducing`: counts over the ten conditions; the per-condition means are compared as floating-point numbers, so an exact tie can be counted as higher or lower (listed in the note to Table N6: normalized format arm, CSR, Phi-4-mini and Gemma 4 E4B in V07 and V09)
- `main.posthoc_norm.robustness.constraint_instability.<arm>.<model>.<c>.<stat>`: constraint-level instability
- `main.posthoc_norm.robustness.cascade.*`, `main.posthoc_norm.robustness.norm_format_subset.*`: cascade and subset analyses
- `main.posthoc_norm.exploratory.e3.<model>.*`: hard-to-easy index with normalized pilot difficulties
- `main.posthoc_norm.e5.<arm>.<model>.{format_failure_rate,format_failure.<type>,code_fence_raw,n_records}`: failure types
- `main.posthoc_norm.records.<model>.<family>.<arm>.{n_records,format_strict_pass,format_norm_pass,n_changed}`: record level
- `main.posthoc_norm.inventory.*`, `main.posthoc_norm.checks.*`: inventory and checks

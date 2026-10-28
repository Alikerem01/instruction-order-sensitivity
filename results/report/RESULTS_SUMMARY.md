# RESULTS_SUMMARY — main run

Run `main_20261006-1354_63a1c79`; analysis plan frozen at tag `benchmark-v1.0.0`; bootstrap 5000 replicates, seed 20261003; generated 2026-10-28T13:56:30Z. Every number below is a key of `results/metrics/summary.json` (key index at the end). Proportions are shown as percentages with one decimal, 95% CIs in brackets (task-clustered bootstrap, percentile), p to three decimals or "< .001"; q = Benjamini-Hochberg within the families of ANALYSIS_PLAN §7. Model differences are descriptive of these four models and are not attributed to size or family (D06 §5).

**Reading note (decision G3 §4).** Gemma 4 E4B's strict FORMAT score is driven by fenced JSON: it wrapped 100.0% of its order-arm outputs and 100.0% of its format-arm outputs in a ```json fence (E5, descriptive), so its strict FORMAT compliance and PCR are 0 and its CSR is at most 0.8.

## Data

8000 evaluation records: 100 tasks × 4 models × 20 prompt ids (order arm O01-O10 = data ids P01-P10, format arm V01-V10; O01 and V01 share one generation). All outputs were generated at batch size 1 (decision G2). Outputs at the length limit: SmolLM2-1.7B 0.0%, Qwen2.5-3B 0.1%, Phi-4-mini 0.0%, Gemma 4 E4B 0.0%. Evaluable outputs (a JSON object could be parsed), order arm: SmolLM2-1.7B 60.8% [60.0%, 62.0%], Qwen2.5-3B 82.3% [81.5%, 83.0%], Phi-4-mini 99.8% [99.4%, 100.0%], Gemma 4 E4B 100.0% [100.0%, 100.0%]. Non-evaluable outputs score 0 on constraints 2-5 (brief §5.8); SmolLM2-1.7B's non-JSON outputs in F1 and F3 (evaluable 4.0% and 0.0%) explain much of its low CSR.

## RQ1 — Do orders change compliance systematically? (P2, S1)

| Model | Friedman χ² (df) | p | q | Kendall's W | Cochran's Q (df) | p | q |
|---|---:|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 110.5 (9) | < .001 | < .001 | 0.123 | 22.4 (9) | .008 | .008 |
| Qwen2.5-3B | 155.8 (9) | < .001 | < .001 | 0.173 | 54.3 (9) | < .001 | < .001 |
| Phi-4-mini | 61.1 (9) | < .001 | < .001 | 0.068 | 63.3 (9) | < .001 | < .001 |
| Gemma 4 E4B | 101.2 (9) | < .001 | < .001 | 0.112 | no variation; test not applicable |  |  |

- SmolLM2-1.7B: Friedman χ²(9) = 110.47, p < .001, q < .001, Kendall's W = 0.123 (CSR across the 10 orders).
- SmolLM2-1.7B: Cochran's Q(9) = 22.40, p = .008, q = .008 (PCR across the 10 orders).
- Qwen2.5-3B: Friedman χ²(9) = 155.80, p < .001, q < .001, Kendall's W = 0.173 (CSR across the 10 orders).
- Qwen2.5-3B: Cochran's Q(9) = 54.27, p < .001, q < .001 (PCR across the 10 orders).
- Phi-4-mini: Friedman χ²(9) = 61.09, p < .001, q < .001, Kendall's W = 0.068 (CSR across the 10 orders).
- Phi-4-mini: Cochran's Q(9) = 63.28, p < .001, q < .001 (PCR across the 10 orders).
- Gemma 4 E4B: Friedman χ²(9) = 101.21, p < .001, q < .001, Kendall's W = 0.112 (CSR across the 10 orders).
- Gemma 4 E4B: Cochran's Q test of PCR: no variation; test not applicable (PCR 0.0% in every order).

Task-level sensitivity (S1):

| Model | CSR | PCR | PS_order | PS_format | VSR | Flip rate |
|---|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 34.1% [32.0%, 36.1%] | 5.8% [3.7%, 8.0%] | 0.296 [0.260, 0.336] | 0.310 [0.280, 0.344] | 40.0% [36.0%, 44.0%] | 36.0% [33.0%, 39.1%] |
| Qwen2.5-3B | 63.4% [62.1%, 64.5%] | 8.1% [5.6%, 10.8%] | 0.316 [0.292, 0.342] | 0.068 [0.052, 0.086] | 20.0% [16.0%, 24.0%] | 33.2% [30.1%, 36.4%] |
| Phi-4-mini | 85.2% [83.6%, 86.8%] | 45.7% [40.2%, 50.9%] | 0.264 [0.238, 0.292] | 0.148 [0.118, 0.180] | 18.0% [12.0%, 24.0%] | 47.6% [44.1%, 51.1%] |
| Gemma 4 E4B | 69.6% [68.0%, 71.1%] | 0.0% [0.0%, 0.0%] | 0.112 [0.090, 0.136] | 0.028 [0.016, 0.042] | 56.0% [48.0%, 64.0%] | 19.1% [15.1%, 23.1%] |
| Pooled | 63.1% [62.2%, 63.9%] | 14.9% [13.4%, 16.4%] | 0.247 [0.232, 0.262] | 0.138 [0.127, 0.151] | 33.5% [30.5%, 36.5%] | 34.0% [32.1%, 35.8%] |

- SmolLM2-1.7B: PS_order 0.296 [0.260, 0.336], PS_format 0.310 [0.280, 0.344]; VSR order 40.0% [36.0%, 44.0%], format 47.0% [42.0%, 52.0%]; flip rate order 36.0% [33.0%, 39.1%], format 26.8% [23.5%, 30.4%].
- Qwen2.5-3B: PS_order 0.316 [0.292, 0.342], PS_format 0.068 [0.052, 0.086]; VSR order 20.0% [16.0%, 24.0%], format 70.0% [63.0%, 77.0%]; flip rate order 33.2% [30.1%, 36.4%], format 12.3% [9.0%, 15.8%].
- Phi-4-mini: PS_order 0.264 [0.238, 0.292], PS_format 0.148 [0.118, 0.180]; VSR order 18.0% [12.0%, 24.0%], format 47.0% [39.0%, 55.0%]; flip rate order 47.6% [44.1%, 51.1%], format 23.1% [18.8%, 27.4%].
- Gemma 4 E4B: PS_order 0.112 [0.090, 0.136], PS_format 0.028 [0.016, 0.042]; VSR order 56.0% [48.0%, 64.0%], format 87.0% [81.0%, 93.0%]; flip rate order 19.1% [15.1%, 23.1%], format 4.7% [2.3%, 7.5%].
- Pooled: PS_order 0.247 [0.232, 0.262], PS_format 0.138 [0.127, 0.151]; VSR order 33.5% [30.5%, 36.5%], format 62.7% [59.0%, 66.2%]; flip rate order 34.0% [32.1%, 35.8%], format 16.7% [15.0%, 18.6%].

## RQ2 — Does an instruction's position change its compliance? (P1)

The primary display is the observed compliance by position (Table 4, decision D05 §1); the GEE supplies the Wald test and odds ratios when it is estimable. A GEE that fails to converge or shows separation is reported as not estimable, and the bootstrap descriptives are relied on (ANALYSIS_PLAN §8).

- FORMAT: GEE Wald χ²(4) = 89.15, p < .001, q < .001; Gemma 4 E4B excluded for constant compliance (0.0%). Odds ratios against position 1: position 2: OR 0.77 [0.44, 1.33]; position 3: OR 0.28 [0.16, 0.47]; position 4: OR 0.58 [0.34, 0.99]; position 5: OR 6.05 [3.06, 11.99].
  Observed pooled compliance ranged from 49.9% [48.4%, 51.4%] at position 3 to 62.4% [61.5%, 63.2%] at position 5.
- LENGTH: GEE not estimable (separation: family=F5_TRANSFORMATION: all pass).
  Observed pooled compliance ranged from 83.1% [82.0%, 84.2%] at position 4 to 86.5% [85.4%, 87.6%] at position 3.
- CARDINALITY: GEE not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
  Observed pooled compliance ranged from 46.5% [42.8%, 50.1%] at position 5 to 60.1% [57.1%, 63.0%] at position 3.
- NO_COMMA: GEE not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
  Observed pooled compliance ranged from 56.1% [53.4%, 58.8%] at position 5 to 62.4% [60.6%, 64.1%] at position 2.
- VERBATIM: GEE not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
  Observed pooled compliance ranged from 58.8% [56.0%, 61.5%] at position 3 to 62.1% [59.0%, 65.2%] at position 5.

A post-hoc robustness analysis with an independence working correlation (decision G4a §2.1) is reported separately under "Post-hoc analyses" (Table 4b); it is not a pre-specified test.

**FORMAT**

| Model | Position 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 43.0% [39.0%, 47.5%] | 41.5% [36.5%, 46.5%] | 21.5% [16.0%, 27.5%] | 35.0% [30.5%, 40.0%] | 58.5% [55.5%, 61.5%] |
| Qwen2.5-3B | 79.5% [78.5%, 80.0%] | 77.0% [74.5%, 79.5%] | 78.5% [76.5%, 80.5%] | 78.5% [77.0%, 80.0%] | 91.0% [89.0%, 93.0%] |
| Phi-4-mini | 100.0% [100.0%, 100.0%] | 99.5% [98.5%, 100.0%] | 99.5% [98.5%, 100.0%] | 99.5% [98.5%, 100.0%] | 100.0% [100.0%, 100.0%] |
| Gemma 4 E4B | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] |
| Pooled | 55.6% [54.6%, 56.8%] | 54.5% [53.1%, 55.9%] | 49.9% [48.4%, 51.4%] | 53.2% [52.0%, 54.5%] | 62.4% [61.5%, 63.2%] |
| Pooled, GEE sample (Gemma 4 E4B excluded) | 74.2% [72.8%, 75.7%] | 72.7% [70.8%, 74.5%] | 66.5% [64.5%, 68.5%] | 71.0% [69.3%, 72.7%] | 83.2% [82.0%, 84.3%] |

GEE (P1): Wald χ²(4) = 89.15, p < .001, q < .001; excluded for constant compliance: Gemma 4 E4B (0.0%).

**LENGTH**

| Model | Position 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 60.0% [60.0%, 60.0%] | 61.5% [60.0%, 64.0%] | 61.5% [59.0%, 64.5%] | 60.0% [58.5%, 61.5%] | 60.0% [60.0%, 60.0%] |
| Qwen2.5-3B | 81.0% [80.0%, 83.0%] | 79.5% [78.5%, 80.0%] | 89.5% [88.5%, 90.0%] | 81.5% [79.5%, 83.5%] | 79.5% [78.5%, 80.0%] |
| Phi-4-mini | 98.5% [96.0%, 100.0%] | 96.5% [94.5%, 98.5%] | 96.0% [93.0%, 98.5%] | 91.5% [87.5%, 95.0%] | 93.5% [90.0%, 96.5%] |
| Gemma 4 E4B | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 99.0% [97.5%, 100.0%] | 99.5% [98.5%, 100.0%] | 100.0% [100.0%, 100.0%] |
| Pooled | 84.9% [84.1%, 85.6%] | 84.4% [83.6%, 85.1%] | 86.5% [85.4%, 87.6%] | 83.1% [82.0%, 84.2%] | 83.2% [82.4%, 84.0%] |

GEE (P1): not estimable (separation: family=F5_TRANSFORMATION: all pass).

**CARDINALITY**

| Model | Position 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 11.5% [7.0%, 16.5%] | 7.0% [4.0%, 10.5%] | 15.5% [10.5%, 20.5%] | 10.0% [6.0%, 14.5%] | 4.5% [1.5%, 8.0%] |
| Qwen2.5-3B | 28.5% [25.0%, 32.5%] | 48.5% [44.0%, 52.5%] | 53.0% [48.5%, 57.5%] | 55.0% [50.5%, 59.5%] | 48.0% [43.0%, 53.0%] |
| Phi-4-mini | 85.5% [80.0%, 90.5%] | 85.0% [79.5%, 90.5%] | 86.0% [81.0%, 90.5%] | 83.0% [78.5%, 87.5%] | 60.5% [53.0%, 67.5%] |
| Gemma 4 E4B | 88.5% [84.0%, 92.5%] | 85.5% [79.5%, 91.5%] | 86.0% [80.5%, 91.5%] | 83.0% [77.0%, 89.0%] | 73.0% [66.5%, 80.0%] |
| Pooled | 53.5% [50.7%, 56.2%] | 56.5% [53.5%, 59.2%] | 60.1% [57.1%, 63.0%] | 57.8% [54.8%, 60.6%] | 46.5% [42.8%, 50.1%] |

GEE (P1): not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).

**NO_COMMA**

| Model | Position 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 38.0% [33.0%, 43.0%] | 34.0% [30.0%, 38.0%] | 32.5% [28.5%, 36.5%] | 31.0% [27.0%, 35.0%] | 31.5% [27.0%, 36.0%] |
| Qwen2.5-3B | 35.5% [30.0%, 40.5%] | 35.0% [30.5%, 39.0%] | 34.5% [30.5%, 37.5%] | 37.0% [32.5%, 41.0%] | 33.0% [28.0%, 37.0%] |
| Phi-4-mini | 67.0% [61.5%, 72.0%] | 80.5% [77.0%, 83.5%] | 79.5% [75.5%, 83.0%] | 79.5% [75.5%, 83.5%] | 61.0% [55.0%, 66.5%] |
| Gemma 4 E4B | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 100.0% [100.0%, 100.0%] | 99.0% [97.0%, 100.0%] | 99.0% [97.0%, 100.0%] |
| Pooled | 60.1% [57.8%, 62.4%] | 62.4% [60.6%, 64.1%] | 61.6% [59.8%, 63.4%] | 61.6% [59.2%, 63.6%] | 56.1% [53.4%, 58.8%] |

GEE (P1): not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).

**VERBATIM**

| Model | Position 1 | 2 | 3 | 4 | 5 |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 28.5% [23.5%, 33.5%] | 31.0% [25.5%, 36.5%] | 23.0% [18.5%, 27.5%] | 19.0% [15.5%, 22.5%] | 32.5% [27.5%, 37.0%] |
| Qwen2.5-3B | 62.0% [57.0%, 66.5%] | 78.0% [73.5%, 82.0%] | 73.0% [69.5%, 76.0%] | 74.5% [70.5%, 78.0%] | 73.0% [68.5%, 77.0%] |
| Phi-4-mini | 74.0% [66.0%, 81.5%] | 74.0% [68.0%, 80.0%] | 78.5% [73.0%, 84.0%] | 84.5% [79.0%, 89.5%] | 77.5% [70.5%, 84.5%] |
| Gemma 4 E4B | 72.5% [65.0%, 79.0%] | 65.0% [57.5%, 72.0%] | 60.5% [53.0%, 68.0%] | 63.5% [56.0%, 71.0%] | 65.5% [57.5%, 73.0%] |
| Pooled | 59.2% [55.9%, 62.4%] | 62.0% [58.9%, 65.1%] | 58.8% [56.0%, 61.5%] | 60.4% [57.8%, 63.0%] | 62.1% [59.0%, 65.2%] |

GEE (P1): not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).

## RQ3 — Do the models differ? (S2; descriptive of these four models)

- mean PS_order, SmolLM2-1.7B − Qwen2.5-3B: -0.020 [-0.064, 0.028], bootstrap p = .418, q = .418.
- mean PS_order, SmolLM2-1.7B − Phi-4-mini: 0.032 [-0.014, 0.078], bootstrap p = .185, q = .222.
- mean PS_order, SmolLM2-1.7B − Gemma 4 E4B: 0.184 [0.144, 0.226], bootstrap p < .001, q < .001.
- mean PS_order, Qwen2.5-3B − Phi-4-mini: 0.052 [0.014, 0.094], bootstrap p = .011, q = .017.
- mean PS_order, Qwen2.5-3B − Gemma 4 E4B: 0.204 [0.170, 0.238], bootstrap p < .001, q < .001.
- mean PS_order, Phi-4-mini − Gemma 4 E4B: 0.152 [0.116, 0.186], bootstrap p < .001, q < .001.
- mean CSR (order arm), SmolLM2-1.7B − Qwen2.5-3B: -29.3% [-31.9%, -26.7%], bootstrap p < .001, q < .001.
- mean CSR (order arm), SmolLM2-1.7B − Phi-4-mini: -51.1% [-53.7%, -48.7%], bootstrap p < .001, q < .001.
- mean CSR (order arm), SmolLM2-1.7B − Gemma 4 E4B: -35.5% [-38.0%, -33.1%], bootstrap p < .001, q < .001.
- mean CSR (order arm), Qwen2.5-3B − Phi-4-mini: -21.9% [-23.7%, -20.0%], bootstrap p < .001, q < .001.
- mean CSR (order arm), Qwen2.5-3B − Gemma 4 E4B: -6.2% [-8.0%, -4.4%], bootstrap p < .001, q < .001.
- mean CSR (order arm), Phi-4-mini − Gemma 4 E4B: 15.6% [13.7%, 17.7%], bootstrap p < .001, q < .001.

- Position × model interaction, FORMAT: not estimable (separation: position×model=1/phi4mini: all pass; position×model=5/phi4mini: all pass).
- Position × model interaction, LENGTH: not estimable (separation: family=F5_TRANSFORMATION: all pass; position×model=1/gemma4e4b: all pass; position×model=2/gemma4e4b: all pass; position×model=5/gemma4e4b: all pass).
- Position × model interaction, CARDINALITY: not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
- Position × model interaction, NO_COMMA: not estimable (separation: position×model=1/gemma4e4b: all pass; position×model=2/gemma4e4b: all pass; position×model=3/gemma4e4b: all pass).
- Position × model interaction, VERBATIM: not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).

Gemma 4 E4B's lower PS_order has two sources (Table A3; post-hoc and descriptive, the comparison is not tested, decision G4b §2.2): (i) three of its constraints are (near-)constant: its FORMAT, LENGTH and NO_COMMA flags vary across the 10 orders in 0.0%, 2.0%, 1.0% of its tasks, which bounds its PS mechanically; (ii) on the two constraints that vary for every model, its instability is also lower: CARDINALITY 23.0% against 33.0%-54.0% for the other models, VERBATIM 34.0% against 51.0%-52.0%; for CARDINALITY this holds at a base rate similar to Phi-4-mini's (compliance 83.2% against 80.0%).

## RQ4 — Is reordering more disruptive than reformatting? (P3)

- SmolLM2-1.7B: mean PS_order − PS_format = -0.014 [-0.048, 0.018] over 100 tasks (24 positive, 27 negative, 49 zero); Wilcoxon signed-rank statistic 1822.00, p = .740, q = .740.
- Qwen2.5-3B: mean PS_order − PS_format = 0.248 [0.220, 0.280] over 100 tasks (61 positive, 2 negative, 37 zero); Wilcoxon signed-rank statistic 109.00, p < .001, q < .001.
- Phi-4-mini: mean PS_order − PS_format = 0.116 [0.084, 0.148] over 100 tasks (55 positive, 7 negative, 38 zero); Wilcoxon signed-rank statistic 481.50, p < .001, q < .001.
- Gemma 4 E4B: mean PS_order − PS_format = 0.084 [0.060, 0.110] over 100 tasks (35 positive, 2 negative, 63 zero); Wilcoxon signed-rank statistic 155.00, p < .001, q < .001.

## Task quality (S3)

Mean Q

| Family | SmolLM2-1.7B | Qwen2.5-3B | Phi-4-mini | Gemma 4 E4B |
|---|---:|---:|---:|---:|
| QA | 0.025 [0.000, 0.075] | 0.775 [0.590, 0.935] | 0.875 [0.725, 1.000] | 0.865 [0.720, 0.980] |
| CLS | 0.515 [0.315, 0.710] | 0.795 [0.620, 0.945] | 0.715 [0.530, 0.885] | 0.900 [0.750, 1.000] |
| SUM | 0.000 [0.000, 0.000] | 0.027 [0.019, 0.036] | 0.207 [0.178, 0.238] | 0.180 [0.152, 0.208] |
| EXT | 0.926 [0.888, 0.962] | 0.965 [0.937, 0.989] | 0.985 [0.964, 1.000] | 0.992 [0.978, 1.000] |
| TRF | 0.968 [0.938, 0.992] | 0.987 [0.974, 0.997] | 0.996 [0.990, 1.000] | 1.000 [1.000, 1.000] |

TQS (max Q − min Q over the 10 orders, per task)

| Family | SmolLM2-1.7B | Qwen2.5-3B | Phi-4-mini | Gemma 4 E4B |
|---|---:|---:|---:|---:|
| QA | 0.050 [0.000, 0.150] | 0.100 [0.000, 0.250] | 0.100 [0.000, 0.250] | 0.150 [0.000, 0.300] |
| CLS | 0.200 [0.050, 0.400] | 0.150 [0.000, 0.300] | 0.200 [0.050, 0.400] | 0.000 [0.000, 0.000] |
| SUM | 0.000 [0.000, 0.000] | 0.202 [0.164, 0.244] | 0.102 [0.075, 0.131] | 0.074 [0.046, 0.105] |
| EXT | 0.120 [0.060, 0.180] | 0.060 [0.020, 0.100] | 0.030 [0.000, 0.060] | 0.020 [0.000, 0.050] |
| TRF | 0.050 [0.020, 0.090] | 0.040 [0.010, 0.080] | 0.020 [0.000, 0.050] | 0.000 [0.000, 0.000] |

## Exploratory analyses (E1-E6; no confirmatory claims, no adjustment)

**E1 — instruction-type groups** (structural: FORMAT, CARDINALITY; answer-level: LENGTH, NO_COMMA; content: VERBATIM; key name `lexical`), pooled over models:

- structural: position 1 54.6% [53.1%, 56.1%]; position 2 55.5% [53.9%, 57.1%]; position 3 55.0% [53.5%, 56.4%]; position 4 55.5% [53.9%, 57.1%]; position 5 54.4% [52.6%, 56.2%].
- lexical: position 1 72.5% [71.2%, 73.8%]; position 2 73.4% [72.3%, 74.4%]; position 3 74.1% [73.0%, 75.1%]; position 4 72.4% [71.1%, 73.6%]; position 5 69.7% [68.2%, 71.1%].
- content: position 1 59.2% [55.9%, 62.4%]; position 2 62.0% [58.9%, 65.1%]; position 3 58.8% [56.0%, 61.5%]; position 4 60.4% [57.8%, 63.0%]; position 5 62.1% [59.0%, 65.2%].

**E2 — instructions placed before FORMAT** (compliance when the instruction precedes FORMAT minus when it follows, within the positions where both occur; for NO_COMMA and VERBATIM only position 3 informs the contrast):

- LENGTH (positions [2, 3, 4]): pooled 1.3% [0.3%, 2.4%]; SmolLM2-1.7B 0.7% [-0.7%, 2.3%]; Qwen2.5-3B 8.3% [6.7%, 10.3%]; Phi-4-mini -2.7% [-5.7%, 0.3%]; Gemma 4 E4B -1.0% [-2.7%, 0.0%].
- CARDINALITY (positions [2, 3, 4]): pooled -4.4% [-6.7%, -2.2%]; SmolLM2-1.7B -1.7% [-5.3%, 2.3%]; Qwen2.5-3B 0.3% [-4.3%, 5.0%]; Phi-4-mini -16.0% [-21.0%, -11.3%]; Gemma 4 E4B -0.3% [-4.0%, 3.3%].
- NO_COMMA (positions [3]): pooled -0.2% [-2.0%, 1.5%]; SmolLM2-1.7B 1.0% [-2.0%, 4.0%]; Qwen2.5-3B 3.0% [-1.0%, 7.0%]; Phi-4-mini -5.0% [-9.0%, -1.0%]; Gemma 4 E4B 0.0% [0.0%, 0.0%].
- VERBATIM (positions [3]): pooled 6.0% [2.5%, 9.5%]; SmolLM2-1.7B 12.0% [3.0%, 21.0%]; Qwen2.5-3B 4.0% [-2.0%, 9.0%]; Phi-4-mini 21.0% [13.0%, 30.0%]; Gemma 4 E4B -13.0% [-20.0%, -7.0%].

**E3 — hard-to-easy order index** (difficulty from the batch-1 order-arm pilot outputs, decision G2 §2.3). The Williams design was not built to vary HE, and 10 orders give it a limited range.

- SmolLM2-1.7B: difficulties FORMAT 0.62, LENGTH 0.41, CARDINALITY 0.88, NO_COMMA 0.70, VERBATIM 0.73; ρ(HE, order-level CSR) = -0.09 [-0.15, 0.04]; ρ(HE, order-level PCR) = -0.23 [-0.61, 0.26].
- Qwen2.5-3B: difficulties FORMAT 0.18, LENGTH 0.17, CARDINALITY 0.46, NO_COMMA 0.61, VERBATIM 0.34; ρ(HE, order-level CSR) = -0.06 [-0.41, 0.02]; ρ(HE, order-level PCR) = -0.20 [-0.30, 0.28].
- Phi-4-mini: difficulties FORMAT 0.00, LENGTH 0.00, CARDINALITY 0.09, NO_COMMA 0.31, VERBATIM 0.22; ρ(HE, order-level CSR) = -0.62 [-0.68, -0.22]; ρ(HE, order-level PCR) = -0.41 [-0.72, -0.17].
- Gemma 4 E4B: difficulties FORMAT 1.00, LENGTH 0.00, CARDINALITY 0.16, NO_COMMA 0.00, VERBATIM 0.52; ρ(HE, order-level CSR) = 0.68 [0.54, 0.88]; ρ(HE, order-level PCR): no variation; test not applicable.

**E4 — task-quality impact**: Spearman ρ between TQS and PS_order across the 20 tasks of each family:

| Family | SmolLM2-1.7B | Qwen2.5-3B | Phi-4-mini | Gemma 4 E4B |
|---|---:|---:|---:|---:|
| QA | 0.69 | 0.35 | -0.35 | 0.34 |
| CLS | -0.20 | -0.03 | 0.00 | n/a |
| SUM | n/a | 0.04 | 0.43 | 0.16 |
| EXT | 0.21 | -0.27 | 0.61 | -0.19 |
| TRF | 0.41 | -0.17 | 0.13 | n/a |

**E5 — error taxonomy** (share of outputs with each tag; order arm):

| Tag | SmolLM2-1.7B | Qwen2.5-3B | Phi-4-mini | Gemma 4 E4B |
|---|---:|---:|---:|---:|
| code_fence | 0.0% | 1.4% | 0.0% | 100.0% |
| invalid_json | 39.2% | 17.7% | 0.2% | 0.0% |
| leading_text | 0.0% | 0.0% | 0.1% | 0.0% |
| trailing_text | 0.0% | 0.0% | 0.0% | 0.0% |
| extra_keys | 0.0% | 0.0% | 0.0% | 0.0% |
| missing_evidence | 20.9% | 0.0% | 0.0% | 0.0% |
| evidence_count_1 | 0.0% | 31.6% | 16.4% | 16.8% |
| evidence_count_3plus | 30.2% | 0.3% | 3.4% | 0.0% |
| evidence_not_verbatim | 13.1% | 6.4% | 22.1% | 34.6% |
| evidence_duplicate | 1.1% | 1.9% | 5.2% | 0.5% |
| truncated | 0.0% | 0.2% | 0.0% | 0.0% |

Comma spill-over into the evidence spans (exploratory, descriptive; decision G4b §2.1, Q-C2): share of non-verbatim evidence items that are comma-only, order arm: SmolLM2-1.7B 0.0% [0.0%, 0.0%] (0 of 406); Qwen2.5-3B 0.0% [0.0%, 0.0%] (0 of 71); Phi-4-mini 1.7% [0.0%, 4.2%] (5 of 295); Gemma 4 E4B 96.2% [90.7%, 99.4%] (430 of 447). An evidence item that fails VERBATIM counts as comma-only if it contains no comma and, after the VERBATIM normalization (NFC, straightened quotes, collapsed whitespace), is a contiguous substring of the INPUT from which every comma (',' and '，') has been removed and whitespace re-collapsed.

Non-JSON outputs (`invalid_json`) by family, order arm (Q-C3):

| Family | SmolLM2-1.7B | Qwen2.5-3B | Phi-4-mini | Gemma 4 E4B |
|---|---:|---:|---:|---:|
| QA | 96.0% | 1.5% | 0.0% | 0.0% |
| CLS | 0.0% | 0.0% | 0.0% | 0.0% |
| SUM | 100.0% | 87.0% | 1.0% | 0.0% |
| EXT | 0.0% | 0.0% | 0.0% | 0.0% |
| TRF | 0.0% | 0.0% | 0.0% | 0.0% |

**E6 — robustness** (cascade scoring: no strict FORMAT pass → all five constraints score 0; strict-FORMAT subset: only outputs that pass FORMAT strictly):

- SmolLM2-1.7B: cascade CSR 27.9% [25.1%, 30.7%], cascade PS_order 0.440 [0.396, 0.486]; strict-FORMAT subset CSR 70.0% [66.8%, 73.1%] over 399 outputs.
- Qwen2.5-3B: cascade CSR 62.6% [61.1%, 64.1%], cascade PS_order 0.346 [0.312, 0.384]; strict-FORMAT subset CSR 77.4% [76.1%, 78.6%] over 809 outputs.
- Phi-4-mini: cascade CSR 85.2% [83.6%, 86.8%], cascade PS_order 0.266 [0.238, 0.294]; strict-FORMAT subset CSR 85.5% [83.8%, 87.0%] over 997 outputs.
- Gemma 4 E4B: cascade CSR 0.0% [0.0%, 0.0%], cascade PS_order 0.000 [0.000, 0.000]; strict-FORMAT subset: no output passes FORMAT strictly.
- Cascade P3, SmolLM2-1.7B: mean PS_order − PS_format = 0.130 [0.084, 0.174]; p = .003.
- Cascade P3, Qwen2.5-3B: mean PS_order − PS_format = 0.278 [0.238, 0.320]; p < .001.
- Cascade P3, Phi-4-mini: mean PS_order − PS_format = 0.118 [0.086, 0.150]; p < .001.
- Cascade P3, Gemma 4 E4B: mean PS_order − PS_format = 0.000 [0.000, 0.000]; no difference; test not applicable.
- Cascade P1, FORMAT: estimated, Wald χ²(4) = 89.15, p < .001.
- Cascade P1, LENGTH: estimated, Wald χ²(4) = 53.07, p < .001.
- Cascade P1, CARDINALITY: not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
- Cascade P1, NO_COMMA: not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
- Cascade P1, VERBATIM: not estimable (did not converge: the iterations diverged to non-finite estimates (working correlation nan); no factor level has a constant outcome).
- Diagnostics: VERBATIM under the former 3-token rule (`verbatim_min3`), order arm: SmolLM2-1.7B 2.3% [0.7%, 4.2%]; Qwen2.5-3B 50.9% [47.0%, 54.2%]; Phi-4-mini 59.8% [54.5%, 64.8%]; Gemma 4 E4B 45.4% [38.5%, 52.2%]. F1 character-level containment (`containment_char`): SmolLM2-1.7B 2.5% [0.0%, 7.5%]; Qwen2.5-3B 77.5% [59.0%, 93.5%]; Phi-4-mini 87.5% [72.5%, 100.0%]; Gemma 4 E4B 86.5% [72.0%, 98.0%].

## Post-hoc analyses (decision G4a; labelled post-hoc, not pre-specified)

**Option B — P1 with an independence working correlation** (robustness analysis; same mean model and clusters as P1, robust SEs; constant models and constant family levels left out mechanically before fitting; q across the five instructions as its own family):

- FORMAT: Wald χ²(4) = 89.40, p < .001, q < .001 (n = 3000; Gemma 4 E4B left out (constant, 0.0%)). Odds ratios against position 1: position 2: 0.77 [0.45, 1.33]; position 3: 0.28 [0.16, 0.47]; position 4: 0.58 [0.34, 0.99]; position 5: 5.99 [3.05, 11.77].
- LENGTH: Wald χ²(4) = 56.98, p < .001, q < .001 (n = 3200; TRF left out (constant across the included models, 100.0%)). Odds ratios against position 1: position 2: 0.75 [0.42, 1.31]; position 3: 2.49 [1.29, 4.80]; position 4: 0.37 [0.20, 0.69]; position 5: 0.40 [0.20, 0.80].
- CARDINALITY: Wald χ²(4) = 93.26, p < .001, q < .001 (n = 4000). Odds ratios against position 1: position 2: 1.23 [1.01, 1.49]; position 3: 1.58 [1.30, 1.92]; position 4: 1.34 [1.08, 1.65]; position 5: 0.63 [0.50, 0.80].
- NO_COMMA: Wald χ²(4) = 20.61, p < .001, q < .001 (n = 4000). Odds ratios against position 1: position 2: 1.29 [1.05, 1.59]; position 3: 1.19 [0.94, 1.50]; position 4: 1.19 [0.93, 1.52]; position 5: 0.63 [0.47, 0.84].
- VERBATIM: Wald χ²(4) = 14.58, p = .006, q = .006 (n = 4000). Odds ratios against position 1: position 2: 1.19 [1.01, 1.41]; position 3: 0.97 [0.82, 1.14]; position 4: 1.07 [0.90, 1.29]; position 5: 1.20 [1.00, 1.44].

**Constraint-level instability** (descriptive): share of tasks whose flag is not constant across the arm's 10 prompts, order arm:

| Model | FORMAT | LENGTH | CARDINALITY | NO_COMMA | VERBATIM |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 54.0% [49.0%, 59.0%] | 3.0% [0.0%, 7.0%] | 33.0% [25.0%, 41.0%] | 13.0% [7.0%, 19.0%] | 51.0% [44.0%, 57.0%] |
| Qwen2.5-3B | 27.0% [23.0%, 32.0%] | 22.0% [20.0%, 25.0%] | 51.0% [45.0%, 57.0%] | 27.0% [19.0%, 35.0%] | 51.0% [44.0%, 59.0%] |
| Phi-4-mini | 2.0% [0.0%, 5.0%] | 16.0% [12.0%, 19.0%] | 54.0% [47.0%, 62.0%] | 35.0% [29.0%, 41.0%] | 52.0% [43.0%, 60.0%] |
| Gemma 4 E4B | 0.0% [0.0%, 0.0%] | 2.0% [0.0%, 5.0%] | 23.0% [16.0%, 30.0%] | 1.0% [0.0%, 3.0%] | 34.0% [26.0%, 42.0%] |
| Pooled | 20.8% [19.0%, 22.5%] | 10.8% [9.2%, 12.2%] | 40.2% [36.2%, 44.2%] | 19.0% [16.0%, 22.0%] | 47.0% [43.0%, 50.7%] |

## Post-hoc analyses and checks of review round 1 (decision R1)

**Cascade PS_format check (Q1, m16).** The E6a P3 contrast uses PS_format under cascade scoring; there is no analysis error. In the format arm, cascade scoring changes SmolLM2-1.7B 113 outputs and the PS of 3 tasks upwards and 3 downwards; Qwen2.5-3B 0 outputs and the PS of 0 tasks upwards and 0 downwards; Phi-4-mini 0 outputs and the PS of 0 tasks upwards and 0 downwards; Gemma 4 E4B 1000 outputs and the PS of 0 tasks upwards and 13 downwards. Qwen2.5-3B's and Phi-4-mini's format-arm FORMAT failures are all non-JSON outputs, which already score 0 on all five constraints; for SmolLM2-1.7B the upward and downward changes (all in TRF tasks) cancel in the mean (0.310 under both policies). For Gemma 4 E4B cascade PS_format is 0.000 (primary 0.028). SmolLM2-1.7B's cascade P3 result stands: 0.130 [0.084, 0.174], p = .003.

**Order-level results (post-hoc).** Span (max − min over the ten orders) of mean CSR, order arm versus format arm: SmolLM2-1.7B 0.192 [0.152, 0.234] versus 0.266; Qwen2.5-3B 0.212 [0.186, 0.240] versus 0.026; Phi-4-mini 0.106 [0.080, 0.136] versus 0.050; Gemma 4 E4B 0.082 [0.062, 0.108] versus 0.018. Span of PCR, order arm: SmolLM2-1.7B 0.100 [0.060, 0.170]; Qwen2.5-3B 0.150 [0.110, 0.190]; Phi-4-mini 0.310 [0.240, 0.400]; Gemma 4 E4B 0.000 [0.000, 0.000]. Model ranking: CSR, order arm, Phi-4-mini > Gemma 4 E4B > Qwen2.5-3B > SmolLM2-1.7B (mean over the ten conditions) in 9 of 10 conditions; CSR, format arm, Phi-4-mini > Gemma 4 E4B > Qwen2.5-3B > SmolLM2-1.7B (mean over the ten conditions) in 10 of 10 conditions; PCR, order arm, Phi-4-mini > Qwen2.5-3B > SmolLM2-1.7B > Gemma 4 E4B (mean over the ten conditions) in 6 of 10 conditions; PCR, format arm, Phi-4-mini > Qwen2.5-3B > SmolLM2-1.7B > Gemma 4 E4B (mean over the ten conditions) in 3 of 10 conditions; pairwise counts are in Table R1a.

**Fence-tolerant FORMAT (post-hoc).** Order arm: SmolLM2-1.7B FORMAT_ft 39.9%, CSR_ft 34.1% [32.0%, 36.1%], PCR_ft 5.8% [3.7%, 8.0%]; Qwen2.5-3B FORMAT_ft 82.3%, CSR_ft 63.6% [62.4%, 64.7%], PCR_ft 8.1% [5.6%, 10.8%]; Phi-4-mini FORMAT_ft 99.7%, CSR_ft 85.2% [83.6%, 86.8%], PCR_ft 45.7% [40.2%, 50.9%]; Gemma 4 E4B FORMAT_ft 100.0%, CSR_ft 89.6% [88.0%, 91.1%], PCR_ft 53.7% [47.1%, 60.3%]. Under strict scoring Phi-4-mini has the highest CSR; under the fence-tolerant reading Gemma 4 E4B has. Cochran's Q of PCR_ft across orders for Gemma 4 E4B: Q(9) = 89.89, p < .001. Paired difference Gemma 4 E4B − Phi-4-mini under the fence-tolerant reading (post-hoc, decision R2; task-clustered bootstrap as in S2): CSR 4.4% [2.3%, 6.3%], bootstrap p < .001; PCR 8.0% [1.0%, 14.9%], bootstrap p = .028.

**Kendall's W companion (descriptive).** SmolLM2-1.7B: 40 of 100 tasks with constant CSR, W among the others 0.205; Qwen2.5-3B: 20 of 100 tasks with constant CSR, W among the others 0.216; Phi-4-mini: 19 of 100 tasks with constant CSR, W among the others 0.084; Gemma 4 E4B: 56 of 100 tasks with constant CSR, W among the others 0.256.

**Token edit distance to O01 (post-hoc, descriptive).** Median over the formatting variants versus the reorderings: SmolLM2-1.7B 5.00 versus 66.00 tokens; Qwen2.5-3B 4.00 versus 67.00 tokens; Phi-4-mini 4.00 versus 66.00 tokens; Gemma 4 E4B 4.00 versus 66.00 tokens.

Further R1 tables: secondary outcomes (Table R1c, pre-specified), FORMAT failure types (R1d), parsed-only TQS (R1e), evidence lengths and the descriptives (R1f).

## Method validation (technical checks; not results)

- A1 run-to-run determinism (smoke, two passes): byte-identical for SmolLM2-1.7B yes, Qwen2.5-3B yes, Phi-4-mini yes, Gemma 4 E4B yes.
- A3 batch invariance (pilot, three original models): below the pre-specified 98% rule, so all main outputs were generated at batch size 1 (decision G2).
- A6 determinism at batch size 1 (start of each model's main run): byte-identical to the batch-1 pilot for SmolLM2-1.7B yes, Qwen2.5-3B yes, Phi-4-mini yes, Gemma 4 E4B yes; one environment per model (NVIDIA A100-SXM4-80GB).
- Analysis software: Python 3.12.14, NumPy 2.4.6, SciPy 1.17.1, statsmodels 0.15.0, pandas 3.0.6, pyarrow 25.0.1, Matplotlib 3.11.2.

## Anomalies and caveats

- qwen25: 0.1% of outputs ended at the length limit (512 new tokens); they are scored as generated.
- Gemma 4 E4B fenced its JSON in every output, so its strict FORMAT compliance and PCR are 0: Gemma is left out of the FORMAT position GEE (constant compliance, decision G2 §2.4), its Cochran's Q test is not applicable, and E3 for its PCR is not applicable.
- P1 GEE not estimable for length, cardinality, t4, verbatim (separation or non-convergence of the pre-specified exchangeable GEE; ANALYSIS_PLAN §8): the observed compliance by position with bootstrap CIs (Table 4) is relied on for these instructions. No other estimator was substituted (no model specification changes after seeing results without a recorded design decision).
- S2 position × model interaction GEE not estimable for format, length, cardinality, t4, verbatim.
- E2: for NO_COMMA and VERBATIM only position 3 informs the contrast.
- E3: the Williams design was not built to vary HE, and 10 orders give it a limited range.
- Task quality is computed from the parsed answer; Q = 0 when no answer can be parsed, so a model's Q in a family partly reflects its FORMAT failures there. Q is never averaged across families.
- Model differences are descriptive of these four models; they are not attributed to size or family.

## Key index

Tables: Table 2 `main.<arm>.<model>.{csr,pcr,ps,vsr,flip_rate}.{mean,ci_low,ci_high}`; Table 3 `main.tests.friedman.<model>.{chi2,df,p,q_bh,kendall_w}` and `main.tests.cochran_q.<model>.{q,df,p,q_bh}` (here `.q` is Cochran's statistic and `.q_bh` the Benjamini-Hochberg value); Table 4 `main.order.<model>.position.<c>.<k>.{mean,ci_low,ci_high}` and `main.p1.<c>.{status,wald_chi2,df,p,q,excluded_models,reason,or.<k>.*}` (FORMAT GEE-sample row: `main.order.pooled_excl_gemma4e4b.position.format.<k>.*`); Table 4b (post-hoc) `main.robustness.p1_independence.<c>.{status,wald_chi2,df,p,q,n,excluded_models,excluded_families,or.<k>.*}`; Table 5 `main.quality.<family>.<model>.{q,tqs}.{mean,ci_low,ci_high}`; Table A3 (post-hoc) `main.robustness.constraint_instability.<arm>.<model>.<c>.{mean,ci_low,ci_high}`; evaluable rates `main.<arm>.<model>.evaluable_rate.*`, `main.<arm>.<model>.evaluable_rate_by_family.<family>` and `main.counts.<model>.evaluable_rate` (both arms); comma spill-over (exploratory, Q-C2) `main.exploratory.e5.<arm>.<model>.evidence_comma_only.{items,outputs_all,outputs_any}.{mean,ci_low,ci_high}`, `.n_items_not_verbatim`, `.n_items_comma_only`, `.n_outputs_not_verbatim`, procedure `main.exploratory.e5.evidence_comma_only.procedure`; non-JSON outputs by family (Q-C3) `main.exploratory.e5.order.<model>.by_family.invalid_json.<family>`; generation hours `checks.compute.main.<model>.generation_hours`; review round 1 (decision R1; post-hoc unless stated): order level `main.posthoc_r1.order_level.<arm>.<model>.<condition>.{csr,pcr,format}.*` (condition = data id P01-P10 shown as O01-O10, or V01-V10), `.span.{csr,pcr}.*`, `main.posthoc_r1.order_level.<arm>.rank.<a>_vs_<b>.{csr,pcr}.{n_a_higher,n_b_higher,n_ties}`, `main.posthoc_r1.order_level.<arm>.rank.overall.{csr,pcr}.{ranking,n_conditions_reproducing}`; fence-tolerant `main.posthoc_r1.fence_tolerant.<arm>.<model>.{format,csr,pcr}.*`, `main.posthoc_r1.fence_tolerant.<arm>.ranking.{csr,pcr}`, `main.posthoc_r1.fence_tolerant.cochran_q.gemma4e4b.{q,df,p,status}`, paired difference (post-hoc, decision R2) `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.{csr,pcr}.{mean,ci_low,ci_high,p}`; pooled VSR and flip rate, both arms `main.<arm>.pooled.{vsr,flip_rate}.{mean,ci_low,ci_high}`; pre-specified outcomes first reported in round 1: S1 format arm `main.format.<model>.{vsr,flip_rate}.*`, VERBATIM case-insensitive `main.robustness.diagnostics.<arm>.<model>.verbatim_case_insensitive.*`, secondary outcomes `main.secondary.<arm>.F1_QA.<model>.max_token_f1.*`, `main.secondary.<arm>.F2_CLASSIFICATION.<model>.{unresolved_rate,no_label_rate}.*` (no-label rate post-hoc, decision R2) and `.{n_with_answer,n_unresolved}`, `main.secondary.<arm>.{F4_EXTRACTION,F5_TRANSFORMATION}.<model>.exact_all_fields.*`; parsed-only TQS `main.posthoc_r1.tqs_parsed.<family>.<model>.{status,mean,ci_low,ci_high,n_task_model_pairs,differs_from_prespecified,n_orders_median,n_orders_min}`; Kendall's W companion `main.posthoc_r1.kendall_w.<model>.{n_constant_tasks,n_nonconstant_tasks,kendall_w_nonconstant}`; evidence length `main.posthoc_r1.evidence_length.<model>.{median_tokens,share_1_token,share_2_tokens,n_items}`; FORMAT failure types `main.posthoc_r1.format_failures.<model>.<position>.{n_outputs,invalid_json,missing_or_extra_key,fenced,other}` (smollm2, qwen25) and `main.posthoc_r1.format_failures.qwen25.by_family.<family>.*`; edit distance `main.posthoc_r1.edit_distance.<model>.{median_format_variants,median_reorderings,n_pairs_each,status}`; cascade check `main.posthoc_r1.cascade_check.format.<model>.{ps_primary,ps_cascade,n_outputs_changed,n_tasks_ps_up,n_tasks_ps_down,families_changed}`; analysis software `checks.software.analysis.<package>`; Table A1 `main.exploratory.e5.<arm>.<model>.<tag>`; Table A2 `main.robustness.{cascade,strict_format}.*`. `<model>` is one of `smollm2`, `qwen25`, `phi4mini`, `gemma4e4b` or `pooled` (equal weight over the four models).

Numbers in the text, in order of appearance:

- 8000 → `main.counts.evaluation_records`
- 100 → `main.counts.tasks`
- 4 → `main.counts.models`
- 0.0% → `main.counts.smollm2.truncated_rate`
- 0.1% → `main.counts.qwen25.truncated_rate`
- 0.0% → `main.counts.phi4mini.truncated_rate`
- 0.0% → `main.counts.gemma4e4b.truncated_rate`
- 60.8% → `main.order.smollm2.evaluable_rate.mean`
- 60.0% → `main.order.smollm2.evaluable_rate.ci_low`
- 62.0% → `main.order.smollm2.evaluable_rate.ci_high`
- 82.3% → `main.order.qwen25.evaluable_rate.mean`
- 81.5% → `main.order.qwen25.evaluable_rate.ci_low`
- 83.0% → `main.order.qwen25.evaluable_rate.ci_high`
- 99.8% → `main.order.phi4mini.evaluable_rate.mean`
- 99.4% → `main.order.phi4mini.evaluable_rate.ci_low`
- 100.0% → `main.order.phi4mini.evaluable_rate.ci_high`
- 100.0% → `main.order.gemma4e4b.evaluable_rate.mean`
- 100.0% → `main.order.gemma4e4b.evaluable_rate.ci_low`
- 100.0% → `main.order.gemma4e4b.evaluable_rate.ci_high`
- 4.0% → `main.order.smollm2.evaluable_rate_by_family.F1_QA`
- 0.0% → `main.order.smollm2.evaluable_rate_by_family.F3_SUMMARIZATION`
- 9 → `main.tests.friedman.smollm2.df`
- 110.47 → `main.tests.friedman.smollm2.chi2`
- < .001 → `main.tests.friedman.smollm2.p`
- < .001 → `main.tests.friedman.smollm2.q_bh`
- 0.123 → `main.tests.friedman.smollm2.kendall_w`
- 9 → `main.tests.cochran_q.smollm2.df`
- 22.40 → `main.tests.cochran_q.smollm2.q`
- .008 → `main.tests.cochran_q.smollm2.p`
- .008 → `main.tests.cochran_q.smollm2.q_bh`
- 9 → `main.tests.friedman.qwen25.df`
- 155.80 → `main.tests.friedman.qwen25.chi2`
- < .001 → `main.tests.friedman.qwen25.p`
- < .001 → `main.tests.friedman.qwen25.q_bh`
- 0.173 → `main.tests.friedman.qwen25.kendall_w`
- 9 → `main.tests.cochran_q.qwen25.df`
- 54.27 → `main.tests.cochran_q.qwen25.q`
- < .001 → `main.tests.cochran_q.qwen25.p`
- < .001 → `main.tests.cochran_q.qwen25.q_bh`
- 9 → `main.tests.friedman.phi4mini.df`
- 61.09 → `main.tests.friedman.phi4mini.chi2`
- < .001 → `main.tests.friedman.phi4mini.p`
- < .001 → `main.tests.friedman.phi4mini.q_bh`
- 0.068 → `main.tests.friedman.phi4mini.kendall_w`
- 9 → `main.tests.cochran_q.phi4mini.df`
- 63.28 → `main.tests.cochran_q.phi4mini.q`
- < .001 → `main.tests.cochran_q.phi4mini.p`
- < .001 → `main.tests.cochran_q.phi4mini.q_bh`
- 9 → `main.tests.friedman.gemma4e4b.df`
- 101.21 → `main.tests.friedman.gemma4e4b.chi2`
- < .001 → `main.tests.friedman.gemma4e4b.p`
- < .001 → `main.tests.friedman.gemma4e4b.q_bh`
- 0.112 → `main.tests.friedman.gemma4e4b.kendall_w`
- 0.0% → `main.order.gemma4e4b.pcr.mean`
- 0.296 → `main.order.smollm2.ps.mean`
- 0.260 → `main.order.smollm2.ps.ci_low`
- 0.336 → `main.order.smollm2.ps.ci_high`
- 0.310 → `main.format.smollm2.ps.mean`
- 0.280 → `main.format.smollm2.ps.ci_low`
- 0.344 → `main.format.smollm2.ps.ci_high`
- 40.0% → `main.order.smollm2.vsr.mean`
- 36.0% → `main.order.smollm2.vsr.ci_low`
- 44.0% → `main.order.smollm2.vsr.ci_high`
- 47.0% → `main.format.smollm2.vsr.mean`
- 42.0% → `main.format.smollm2.vsr.ci_low`
- 52.0% → `main.format.smollm2.vsr.ci_high`
- 36.0% → `main.order.smollm2.flip_rate.mean`
- 33.0% → `main.order.smollm2.flip_rate.ci_low`
- 39.1% → `main.order.smollm2.flip_rate.ci_high`
- 26.8% → `main.format.smollm2.flip_rate.mean`
- 23.5% → `main.format.smollm2.flip_rate.ci_low`
- 30.4% → `main.format.smollm2.flip_rate.ci_high`
- 0.316 → `main.order.qwen25.ps.mean`
- 0.292 → `main.order.qwen25.ps.ci_low`
- 0.342 → `main.order.qwen25.ps.ci_high`
- 0.068 → `main.format.qwen25.ps.mean`
- 0.052 → `main.format.qwen25.ps.ci_low`
- 0.086 → `main.format.qwen25.ps.ci_high`
- 20.0% → `main.order.qwen25.vsr.mean`
- 16.0% → `main.order.qwen25.vsr.ci_low`
- 24.0% → `main.order.qwen25.vsr.ci_high`
- 70.0% → `main.format.qwen25.vsr.mean`
- 63.0% → `main.format.qwen25.vsr.ci_low`
- 77.0% → `main.format.qwen25.vsr.ci_high`
- 33.2% → `main.order.qwen25.flip_rate.mean`
- 30.1% → `main.order.qwen25.flip_rate.ci_low`
- 36.4% → `main.order.qwen25.flip_rate.ci_high`
- 12.3% → `main.format.qwen25.flip_rate.mean`
- 9.0% → `main.format.qwen25.flip_rate.ci_low`
- 15.8% → `main.format.qwen25.flip_rate.ci_high`
- 0.264 → `main.order.phi4mini.ps.mean`
- 0.238 → `main.order.phi4mini.ps.ci_low`
- 0.292 → `main.order.phi4mini.ps.ci_high`
- 0.148 → `main.format.phi4mini.ps.mean`
- 0.118 → `main.format.phi4mini.ps.ci_low`
- 0.180 → `main.format.phi4mini.ps.ci_high`
- 18.0% → `main.order.phi4mini.vsr.mean`
- 12.0% → `main.order.phi4mini.vsr.ci_low`
- 24.0% → `main.order.phi4mini.vsr.ci_high`
- 47.0% → `main.format.phi4mini.vsr.mean`
- 39.0% → `main.format.phi4mini.vsr.ci_low`
- 55.0% → `main.format.phi4mini.vsr.ci_high`
- 47.6% → `main.order.phi4mini.flip_rate.mean`
- 44.1% → `main.order.phi4mini.flip_rate.ci_low`
- 51.1% → `main.order.phi4mini.flip_rate.ci_high`
- 23.1% → `main.format.phi4mini.flip_rate.mean`
- 18.8% → `main.format.phi4mini.flip_rate.ci_low`
- 27.4% → `main.format.phi4mini.flip_rate.ci_high`
- 0.112 → `main.order.gemma4e4b.ps.mean`
- 0.090 → `main.order.gemma4e4b.ps.ci_low`
- 0.136 → `main.order.gemma4e4b.ps.ci_high`
- 0.028 → `main.format.gemma4e4b.ps.mean`
- 0.016 → `main.format.gemma4e4b.ps.ci_low`
- 0.042 → `main.format.gemma4e4b.ps.ci_high`
- 56.0% → `main.order.gemma4e4b.vsr.mean`
- 48.0% → `main.order.gemma4e4b.vsr.ci_low`
- 64.0% → `main.order.gemma4e4b.vsr.ci_high`
- 87.0% → `main.format.gemma4e4b.vsr.mean`
- 81.0% → `main.format.gemma4e4b.vsr.ci_low`
- 93.0% → `main.format.gemma4e4b.vsr.ci_high`
- 19.1% → `main.order.gemma4e4b.flip_rate.mean`
- 15.1% → `main.order.gemma4e4b.flip_rate.ci_low`
- 23.1% → `main.order.gemma4e4b.flip_rate.ci_high`
- 4.7% → `main.format.gemma4e4b.flip_rate.mean`
- 2.3% → `main.format.gemma4e4b.flip_rate.ci_low`
- 7.5% → `main.format.gemma4e4b.flip_rate.ci_high`
- 0.247 → `main.order.pooled.ps.mean`
- 0.232 → `main.order.pooled.ps.ci_low`
- 0.262 → `main.order.pooled.ps.ci_high`
- 0.138 → `main.format.pooled.ps.mean`
- 0.127 → `main.format.pooled.ps.ci_low`
- 0.151 → `main.format.pooled.ps.ci_high`
- 33.5% → `main.order.pooled.vsr.mean`
- 30.5% → `main.order.pooled.vsr.ci_low`
- 36.5% → `main.order.pooled.vsr.ci_high`
- 62.7% → `main.format.pooled.vsr.mean`
- 59.0% → `main.format.pooled.vsr.ci_low`
- 66.2% → `main.format.pooled.vsr.ci_high`
- 34.0% → `main.order.pooled.flip_rate.mean`
- 32.1% → `main.order.pooled.flip_rate.ci_low`
- 35.8% → `main.order.pooled.flip_rate.ci_high`
- 16.7% → `main.format.pooled.flip_rate.mean`
- 15.0% → `main.format.pooled.flip_rate.ci_low`
- 18.6% → `main.format.pooled.flip_rate.ci_high`
- 0.0% → `main.order.gemma4e4b.compliance.format.mean`
- 0.77 → `main.p1.format.or.2.estimate`
- 0.44 → `main.p1.format.or.2.ci_low`
- 1.33 → `main.p1.format.or.2.ci_high`
- 0.28 → `main.p1.format.or.3.estimate`
- 0.16 → `main.p1.format.or.3.ci_low`
- 0.47 → `main.p1.format.or.3.ci_high`
- 0.58 → `main.p1.format.or.4.estimate`
- 0.34 → `main.p1.format.or.4.ci_low`
- 0.99 → `main.p1.format.or.4.ci_high`
- 6.05 → `main.p1.format.or.5.estimate`
- 3.06 → `main.p1.format.or.5.ci_low`
- 11.99 → `main.p1.format.or.5.ci_high`
- 4 → `main.p1.format.df`
- 89.15 → `main.p1.format.wald_chi2`
- < .001 → `main.p1.format.p`
- < .001 → `main.p1.format.q`
- 49.9% → `main.order.pooled.position.format.3.mean`
- 48.4% → `main.order.pooled.position.format.3.ci_low`
- 51.4% → `main.order.pooled.position.format.3.ci_high`
- 62.4% → `main.order.pooled.position.format.5.mean`
- 61.5% → `main.order.pooled.position.format.5.ci_low`
- 63.2% → `main.order.pooled.position.format.5.ci_high`
- 83.1% → `main.order.pooled.position.length.4.mean`
- 82.0% → `main.order.pooled.position.length.4.ci_low`
- 84.2% → `main.order.pooled.position.length.4.ci_high`
- 86.5% → `main.order.pooled.position.length.3.mean`
- 85.4% → `main.order.pooled.position.length.3.ci_low`
- 87.6% → `main.order.pooled.position.length.3.ci_high`
- 46.5% → `main.order.pooled.position.cardinality.5.mean`
- 42.8% → `main.order.pooled.position.cardinality.5.ci_low`
- 50.1% → `main.order.pooled.position.cardinality.5.ci_high`
- 60.1% → `main.order.pooled.position.cardinality.3.mean`
- 57.1% → `main.order.pooled.position.cardinality.3.ci_low`
- 63.0% → `main.order.pooled.position.cardinality.3.ci_high`
- 56.1% → `main.order.pooled.position.t4.5.mean`
- 53.4% → `main.order.pooled.position.t4.5.ci_low`
- 58.8% → `main.order.pooled.position.t4.5.ci_high`
- 62.4% → `main.order.pooled.position.t4.2.mean`
- 60.6% → `main.order.pooled.position.t4.2.ci_low`
- 64.1% → `main.order.pooled.position.t4.2.ci_high`
- 58.8% → `main.order.pooled.position.verbatim.3.mean`
- 56.0% → `main.order.pooled.position.verbatim.3.ci_low`
- 61.5% → `main.order.pooled.position.verbatim.3.ci_high`
- 62.1% → `main.order.pooled.position.verbatim.5.mean`
- 59.0% → `main.order.pooled.position.verbatim.5.ci_low`
- 65.2% → `main.order.pooled.position.verbatim.5.ci_high`
- -0.020 → `main.s2.smollm2_vs_qwen25.ps_diff.mean`
- -0.064 → `main.s2.smollm2_vs_qwen25.ps_diff.ci_low`
- 0.028 → `main.s2.smollm2_vs_qwen25.ps_diff.ci_high`
- .418 → `main.s2.smollm2_vs_qwen25.ps_diff.p`
- .418 → `main.s2.smollm2_vs_qwen25.ps_diff.q`
- 0.032 → `main.s2.smollm2_vs_phi4mini.ps_diff.mean`
- -0.014 → `main.s2.smollm2_vs_phi4mini.ps_diff.ci_low`
- 0.078 → `main.s2.smollm2_vs_phi4mini.ps_diff.ci_high`
- .185 → `main.s2.smollm2_vs_phi4mini.ps_diff.p`
- .222 → `main.s2.smollm2_vs_phi4mini.ps_diff.q`
- 0.184 → `main.s2.smollm2_vs_gemma4e4b.ps_diff.mean`
- 0.144 → `main.s2.smollm2_vs_gemma4e4b.ps_diff.ci_low`
- 0.226 → `main.s2.smollm2_vs_gemma4e4b.ps_diff.ci_high`
- < .001 → `main.s2.smollm2_vs_gemma4e4b.ps_diff.p`
- < .001 → `main.s2.smollm2_vs_gemma4e4b.ps_diff.q`
- 0.052 → `main.s2.qwen25_vs_phi4mini.ps_diff.mean`
- 0.014 → `main.s2.qwen25_vs_phi4mini.ps_diff.ci_low`
- 0.094 → `main.s2.qwen25_vs_phi4mini.ps_diff.ci_high`
- .011 → `main.s2.qwen25_vs_phi4mini.ps_diff.p`
- .017 → `main.s2.qwen25_vs_phi4mini.ps_diff.q`
- 0.204 → `main.s2.qwen25_vs_gemma4e4b.ps_diff.mean`
- 0.170 → `main.s2.qwen25_vs_gemma4e4b.ps_diff.ci_low`
- 0.238 → `main.s2.qwen25_vs_gemma4e4b.ps_diff.ci_high`
- < .001 → `main.s2.qwen25_vs_gemma4e4b.ps_diff.p`
- < .001 → `main.s2.qwen25_vs_gemma4e4b.ps_diff.q`
- 0.152 → `main.s2.phi4mini_vs_gemma4e4b.ps_diff.mean`
- 0.116 → `main.s2.phi4mini_vs_gemma4e4b.ps_diff.ci_low`
- 0.186 → `main.s2.phi4mini_vs_gemma4e4b.ps_diff.ci_high`
- < .001 → `main.s2.phi4mini_vs_gemma4e4b.ps_diff.p`
- < .001 → `main.s2.phi4mini_vs_gemma4e4b.ps_diff.q`
- -29.3% → `main.s2.smollm2_vs_qwen25.csr_diff.mean`
- -31.9% → `main.s2.smollm2_vs_qwen25.csr_diff.ci_low`
- -26.7% → `main.s2.smollm2_vs_qwen25.csr_diff.ci_high`
- < .001 → `main.s2.smollm2_vs_qwen25.csr_diff.p`
- < .001 → `main.s2.smollm2_vs_qwen25.csr_diff.q`
- -51.1% → `main.s2.smollm2_vs_phi4mini.csr_diff.mean`
- -53.7% → `main.s2.smollm2_vs_phi4mini.csr_diff.ci_low`
- -48.7% → `main.s2.smollm2_vs_phi4mini.csr_diff.ci_high`
- < .001 → `main.s2.smollm2_vs_phi4mini.csr_diff.p`
- < .001 → `main.s2.smollm2_vs_phi4mini.csr_diff.q`
- -35.5% → `main.s2.smollm2_vs_gemma4e4b.csr_diff.mean`
- -38.0% → `main.s2.smollm2_vs_gemma4e4b.csr_diff.ci_low`
- -33.1% → `main.s2.smollm2_vs_gemma4e4b.csr_diff.ci_high`
- < .001 → `main.s2.smollm2_vs_gemma4e4b.csr_diff.p`
- < .001 → `main.s2.smollm2_vs_gemma4e4b.csr_diff.q`
- -21.9% → `main.s2.qwen25_vs_phi4mini.csr_diff.mean`
- -23.7% → `main.s2.qwen25_vs_phi4mini.csr_diff.ci_low`
- -20.0% → `main.s2.qwen25_vs_phi4mini.csr_diff.ci_high`
- < .001 → `main.s2.qwen25_vs_phi4mini.csr_diff.p`
- < .001 → `main.s2.qwen25_vs_phi4mini.csr_diff.q`
- -6.2% → `main.s2.qwen25_vs_gemma4e4b.csr_diff.mean`
- -8.0% → `main.s2.qwen25_vs_gemma4e4b.csr_diff.ci_low`
- -4.4% → `main.s2.qwen25_vs_gemma4e4b.csr_diff.ci_high`
- < .001 → `main.s2.qwen25_vs_gemma4e4b.csr_diff.p`
- < .001 → `main.s2.qwen25_vs_gemma4e4b.csr_diff.q`
- 15.6% → `main.s2.phi4mini_vs_gemma4e4b.csr_diff.mean`
- 13.7% → `main.s2.phi4mini_vs_gemma4e4b.csr_diff.ci_low`
- 17.7% → `main.s2.phi4mini_vs_gemma4e4b.csr_diff.ci_high`
- < .001 → `main.s2.phi4mini_vs_gemma4e4b.csr_diff.p`
- < .001 → `main.s2.phi4mini_vs_gemma4e4b.csr_diff.q`
- 0.0% → `main.robustness.constraint_instability.order.gemma4e4b.format.mean`
- 2.0% → `main.robustness.constraint_instability.order.gemma4e4b.length.mean`
- 1.0% → `main.robustness.constraint_instability.order.gemma4e4b.t4.mean`
- 23.0% → `main.robustness.constraint_instability.order.gemma4e4b.cardinality.mean`
- 33.0% → `main.robustness.constraint_instability.order.smollm2.cardinality.mean`
- 54.0% → `main.robustness.constraint_instability.order.phi4mini.cardinality.mean`
- 34.0% → `main.robustness.constraint_instability.order.gemma4e4b.verbatim.mean`
- 51.0% → `main.robustness.constraint_instability.order.smollm2.verbatim.mean`
- 52.0% → `main.robustness.constraint_instability.order.phi4mini.verbatim.mean`
- 83.2% → `main.order.gemma4e4b.compliance.cardinality.mean`
- 80.0% → `main.order.phi4mini.compliance.cardinality.mean`
- 1822.00 → `main.p3.smollm2.wilcoxon_stat`
- .740 → `main.p3.smollm2.p`
- .740 → `main.p3.smollm2.q`
- -0.014 → `main.p3.smollm2.mean_diff`
- -0.048 → `main.p3.smollm2.ci_low`
- 0.018 → `main.p3.smollm2.ci_high`
- 100 → `main.p3.smollm2.n`
- 24 → `main.p3.smollm2.n_pos`
- 27 → `main.p3.smollm2.n_neg`
- 49 → `main.p3.smollm2.n_zero`
- 109.00 → `main.p3.qwen25.wilcoxon_stat`
- < .001 → `main.p3.qwen25.p`
- < .001 → `main.p3.qwen25.q`
- 0.248 → `main.p3.qwen25.mean_diff`
- 0.220 → `main.p3.qwen25.ci_low`
- 0.280 → `main.p3.qwen25.ci_high`
- 100 → `main.p3.qwen25.n`
- 61 → `main.p3.qwen25.n_pos`
- 2 → `main.p3.qwen25.n_neg`
- 37 → `main.p3.qwen25.n_zero`
- 481.50 → `main.p3.phi4mini.wilcoxon_stat`
- < .001 → `main.p3.phi4mini.p`
- < .001 → `main.p3.phi4mini.q`
- 0.116 → `main.p3.phi4mini.mean_diff`
- 0.084 → `main.p3.phi4mini.ci_low`
- 0.148 → `main.p3.phi4mini.ci_high`
- 100 → `main.p3.phi4mini.n`
- 55 → `main.p3.phi4mini.n_pos`
- 7 → `main.p3.phi4mini.n_neg`
- 38 → `main.p3.phi4mini.n_zero`
- 155.00 → `main.p3.gemma4e4b.wilcoxon_stat`
- < .001 → `main.p3.gemma4e4b.p`
- < .001 → `main.p3.gemma4e4b.q`
- 0.084 → `main.p3.gemma4e4b.mean_diff`
- 0.060 → `main.p3.gemma4e4b.ci_low`
- 0.110 → `main.p3.gemma4e4b.ci_high`
- 100 → `main.p3.gemma4e4b.n`
- 35 → `main.p3.gemma4e4b.n_pos`
- 2 → `main.p3.gemma4e4b.n_neg`
- 63 → `main.p3.gemma4e4b.n_zero`
- 54.6% → `main.exploratory.e1.structural.pooled.1.mean`
- 53.1% → `main.exploratory.e1.structural.pooled.1.ci_low`
- 56.1% → `main.exploratory.e1.structural.pooled.1.ci_high`
- 55.5% → `main.exploratory.e1.structural.pooled.2.mean`
- 53.9% → `main.exploratory.e1.structural.pooled.2.ci_low`
- 57.1% → `main.exploratory.e1.structural.pooled.2.ci_high`
- 55.0% → `main.exploratory.e1.structural.pooled.3.mean`
- 53.5% → `main.exploratory.e1.structural.pooled.3.ci_low`
- 56.4% → `main.exploratory.e1.structural.pooled.3.ci_high`
- 55.5% → `main.exploratory.e1.structural.pooled.4.mean`
- 53.9% → `main.exploratory.e1.structural.pooled.4.ci_low`
- 57.1% → `main.exploratory.e1.structural.pooled.4.ci_high`
- 54.4% → `main.exploratory.e1.structural.pooled.5.mean`
- 52.6% → `main.exploratory.e1.structural.pooled.5.ci_low`
- 56.2% → `main.exploratory.e1.structural.pooled.5.ci_high`
- 72.5% → `main.exploratory.e1.lexical.pooled.1.mean`
- 71.2% → `main.exploratory.e1.lexical.pooled.1.ci_low`
- 73.8% → `main.exploratory.e1.lexical.pooled.1.ci_high`
- 73.4% → `main.exploratory.e1.lexical.pooled.2.mean`
- 72.3% → `main.exploratory.e1.lexical.pooled.2.ci_low`
- 74.4% → `main.exploratory.e1.lexical.pooled.2.ci_high`
- 74.1% → `main.exploratory.e1.lexical.pooled.3.mean`
- 73.0% → `main.exploratory.e1.lexical.pooled.3.ci_low`
- 75.1% → `main.exploratory.e1.lexical.pooled.3.ci_high`
- 72.4% → `main.exploratory.e1.lexical.pooled.4.mean`
- 71.1% → `main.exploratory.e1.lexical.pooled.4.ci_low`
- 73.6% → `main.exploratory.e1.lexical.pooled.4.ci_high`
- 69.7% → `main.exploratory.e1.lexical.pooled.5.mean`
- 68.2% → `main.exploratory.e1.lexical.pooled.5.ci_low`
- 71.1% → `main.exploratory.e1.lexical.pooled.5.ci_high`
- 59.2% → `main.exploratory.e1.content.pooled.1.mean`
- 55.9% → `main.exploratory.e1.content.pooled.1.ci_low`
- 62.4% → `main.exploratory.e1.content.pooled.1.ci_high`
- 62.0% → `main.exploratory.e1.content.pooled.2.mean`
- 58.9% → `main.exploratory.e1.content.pooled.2.ci_low`
- 65.1% → `main.exploratory.e1.content.pooled.2.ci_high`
- 58.8% → `main.exploratory.e1.content.pooled.3.mean`
- 56.0% → `main.exploratory.e1.content.pooled.3.ci_low`
- 61.5% → `main.exploratory.e1.content.pooled.3.ci_high`
- 60.4% → `main.exploratory.e1.content.pooled.4.mean`
- 57.8% → `main.exploratory.e1.content.pooled.4.ci_low`
- 63.0% → `main.exploratory.e1.content.pooled.4.ci_high`
- 62.1% → `main.exploratory.e1.content.pooled.5.mean`
- 59.0% → `main.exploratory.e1.content.pooled.5.ci_low`
- 65.2% → `main.exploratory.e1.content.pooled.5.ci_high`
- 1.3% → `main.exploratory.e2.length.pooled.diff.mean`
- 0.3% → `main.exploratory.e2.length.pooled.diff.ci_low`
- 2.4% → `main.exploratory.e2.length.pooled.diff.ci_high`
- 0.7% → `main.exploratory.e2.length.smollm2.diff.mean`
- -0.7% → `main.exploratory.e2.length.smollm2.diff.ci_low`
- 2.3% → `main.exploratory.e2.length.smollm2.diff.ci_high`
- 8.3% → `main.exploratory.e2.length.qwen25.diff.mean`
- 6.7% → `main.exploratory.e2.length.qwen25.diff.ci_low`
- 10.3% → `main.exploratory.e2.length.qwen25.diff.ci_high`
- -2.7% → `main.exploratory.e2.length.phi4mini.diff.mean`
- -5.7% → `main.exploratory.e2.length.phi4mini.diff.ci_low`
- 0.3% → `main.exploratory.e2.length.phi4mini.diff.ci_high`
- -1.0% → `main.exploratory.e2.length.gemma4e4b.diff.mean`
- -2.7% → `main.exploratory.e2.length.gemma4e4b.diff.ci_low`
- 0.0% → `main.exploratory.e2.length.gemma4e4b.diff.ci_high`
- -4.4% → `main.exploratory.e2.cardinality.pooled.diff.mean`
- -6.7% → `main.exploratory.e2.cardinality.pooled.diff.ci_low`
- -2.2% → `main.exploratory.e2.cardinality.pooled.diff.ci_high`
- -1.7% → `main.exploratory.e2.cardinality.smollm2.diff.mean`
- -5.3% → `main.exploratory.e2.cardinality.smollm2.diff.ci_low`
- 2.3% → `main.exploratory.e2.cardinality.smollm2.diff.ci_high`
- 0.3% → `main.exploratory.e2.cardinality.qwen25.diff.mean`
- -4.3% → `main.exploratory.e2.cardinality.qwen25.diff.ci_low`
- 5.0% → `main.exploratory.e2.cardinality.qwen25.diff.ci_high`
- -16.0% → `main.exploratory.e2.cardinality.phi4mini.diff.mean`
- -21.0% → `main.exploratory.e2.cardinality.phi4mini.diff.ci_low`
- -11.3% → `main.exploratory.e2.cardinality.phi4mini.diff.ci_high`
- -0.3% → `main.exploratory.e2.cardinality.gemma4e4b.diff.mean`
- -4.0% → `main.exploratory.e2.cardinality.gemma4e4b.diff.ci_low`
- 3.3% → `main.exploratory.e2.cardinality.gemma4e4b.diff.ci_high`
- -0.2% → `main.exploratory.e2.t4.pooled.diff.mean`
- -2.0% → `main.exploratory.e2.t4.pooled.diff.ci_low`
- 1.5% → `main.exploratory.e2.t4.pooled.diff.ci_high`
- 1.0% → `main.exploratory.e2.t4.smollm2.diff.mean`
- -2.0% → `main.exploratory.e2.t4.smollm2.diff.ci_low`
- 4.0% → `main.exploratory.e2.t4.smollm2.diff.ci_high`
- 3.0% → `main.exploratory.e2.t4.qwen25.diff.mean`
- -1.0% → `main.exploratory.e2.t4.qwen25.diff.ci_low`
- 7.0% → `main.exploratory.e2.t4.qwen25.diff.ci_high`
- -5.0% → `main.exploratory.e2.t4.phi4mini.diff.mean`
- -9.0% → `main.exploratory.e2.t4.phi4mini.diff.ci_low`
- -1.0% → `main.exploratory.e2.t4.phi4mini.diff.ci_high`
- 0.0% → `main.exploratory.e2.t4.gemma4e4b.diff.mean`
- 0.0% → `main.exploratory.e2.t4.gemma4e4b.diff.ci_low`
- 0.0% → `main.exploratory.e2.t4.gemma4e4b.diff.ci_high`
- 6.0% → `main.exploratory.e2.verbatim.pooled.diff.mean`
- 2.5% → `main.exploratory.e2.verbatim.pooled.diff.ci_low`
- 9.5% → `main.exploratory.e2.verbatim.pooled.diff.ci_high`
- 12.0% → `main.exploratory.e2.verbatim.smollm2.diff.mean`
- 3.0% → `main.exploratory.e2.verbatim.smollm2.diff.ci_low`
- 21.0% → `main.exploratory.e2.verbatim.smollm2.diff.ci_high`
- 4.0% → `main.exploratory.e2.verbatim.qwen25.diff.mean`
- -2.0% → `main.exploratory.e2.verbatim.qwen25.diff.ci_low`
- 9.0% → `main.exploratory.e2.verbatim.qwen25.diff.ci_high`
- 21.0% → `main.exploratory.e2.verbatim.phi4mini.diff.mean`
- 13.0% → `main.exploratory.e2.verbatim.phi4mini.diff.ci_low`
- 30.0% → `main.exploratory.e2.verbatim.phi4mini.diff.ci_high`
- -13.0% → `main.exploratory.e2.verbatim.gemma4e4b.diff.mean`
- -20.0% → `main.exploratory.e2.verbatim.gemma4e4b.diff.ci_low`
- -7.0% → `main.exploratory.e2.verbatim.gemma4e4b.diff.ci_high`
- 0.62 → `main.exploratory.e3.smollm2.difficulty.format`
- 0.41 → `main.exploratory.e3.smollm2.difficulty.length`
- 0.88 → `main.exploratory.e3.smollm2.difficulty.cardinality`
- 0.70 → `main.exploratory.e3.smollm2.difficulty.t4`
- 0.73 → `main.exploratory.e3.smollm2.difficulty.verbatim`
- -0.09 → `main.exploratory.e3.smollm2.he_vs_csr.rho`
- -0.15 → `main.exploratory.e3.smollm2.he_vs_csr.ci_low`
- 0.04 → `main.exploratory.e3.smollm2.he_vs_csr.ci_high`
- -0.23 → `main.exploratory.e3.smollm2.he_vs_pcr.rho`
- -0.61 → `main.exploratory.e3.smollm2.he_vs_pcr.ci_low`
- 0.26 → `main.exploratory.e3.smollm2.he_vs_pcr.ci_high`
- 0.18 → `main.exploratory.e3.qwen25.difficulty.format`
- 0.17 → `main.exploratory.e3.qwen25.difficulty.length`
- 0.46 → `main.exploratory.e3.qwen25.difficulty.cardinality`
- 0.61 → `main.exploratory.e3.qwen25.difficulty.t4`
- 0.34 → `main.exploratory.e3.qwen25.difficulty.verbatim`
- -0.06 → `main.exploratory.e3.qwen25.he_vs_csr.rho`
- -0.41 → `main.exploratory.e3.qwen25.he_vs_csr.ci_low`
- 0.02 → `main.exploratory.e3.qwen25.he_vs_csr.ci_high`
- -0.20 → `main.exploratory.e3.qwen25.he_vs_pcr.rho`
- -0.30 → `main.exploratory.e3.qwen25.he_vs_pcr.ci_low`
- 0.28 → `main.exploratory.e3.qwen25.he_vs_pcr.ci_high`
- 0.00 → `main.exploratory.e3.phi4mini.difficulty.format`
- 0.00 → `main.exploratory.e3.phi4mini.difficulty.length`
- 0.09 → `main.exploratory.e3.phi4mini.difficulty.cardinality`
- 0.31 → `main.exploratory.e3.phi4mini.difficulty.t4`
- 0.22 → `main.exploratory.e3.phi4mini.difficulty.verbatim`
- -0.62 → `main.exploratory.e3.phi4mini.he_vs_csr.rho`
- -0.68 → `main.exploratory.e3.phi4mini.he_vs_csr.ci_low`
- -0.22 → `main.exploratory.e3.phi4mini.he_vs_csr.ci_high`
- -0.41 → `main.exploratory.e3.phi4mini.he_vs_pcr.rho`
- -0.72 → `main.exploratory.e3.phi4mini.he_vs_pcr.ci_low`
- -0.17 → `main.exploratory.e3.phi4mini.he_vs_pcr.ci_high`
- 1.00 → `main.exploratory.e3.gemma4e4b.difficulty.format`
- 0.00 → `main.exploratory.e3.gemma4e4b.difficulty.length`
- 0.16 → `main.exploratory.e3.gemma4e4b.difficulty.cardinality`
- 0.00 → `main.exploratory.e3.gemma4e4b.difficulty.t4`
- 0.52 → `main.exploratory.e3.gemma4e4b.difficulty.verbatim`
- 0.68 → `main.exploratory.e3.gemma4e4b.he_vs_csr.rho`
- 0.54 → `main.exploratory.e3.gemma4e4b.he_vs_csr.ci_low`
- 0.88 → `main.exploratory.e3.gemma4e4b.he_vs_csr.ci_high`
- 0.69 → `main.exploratory.e4.F1_QA.smollm2.rho_tqs_ps`
- 0.35 → `main.exploratory.e4.F1_QA.qwen25.rho_tqs_ps`
- -0.35 → `main.exploratory.e4.F1_QA.phi4mini.rho_tqs_ps`
- 0.34 → `main.exploratory.e4.F1_QA.gemma4e4b.rho_tqs_ps`
- -0.20 → `main.exploratory.e4.F2_CLASSIFICATION.smollm2.rho_tqs_ps`
- -0.03 → `main.exploratory.e4.F2_CLASSIFICATION.qwen25.rho_tqs_ps`
- 0.00 → `main.exploratory.e4.F2_CLASSIFICATION.phi4mini.rho_tqs_ps`
- 0.04 → `main.exploratory.e4.F3_SUMMARIZATION.qwen25.rho_tqs_ps`
- 0.43 → `main.exploratory.e4.F3_SUMMARIZATION.phi4mini.rho_tqs_ps`
- 0.16 → `main.exploratory.e4.F3_SUMMARIZATION.gemma4e4b.rho_tqs_ps`
- 0.21 → `main.exploratory.e4.F4_EXTRACTION.smollm2.rho_tqs_ps`
- -0.27 → `main.exploratory.e4.F4_EXTRACTION.qwen25.rho_tqs_ps`
- 0.61 → `main.exploratory.e4.F4_EXTRACTION.phi4mini.rho_tqs_ps`
- -0.19 → `main.exploratory.e4.F4_EXTRACTION.gemma4e4b.rho_tqs_ps`
- 0.41 → `main.exploratory.e4.F5_TRANSFORMATION.smollm2.rho_tqs_ps`
- -0.17 → `main.exploratory.e4.F5_TRANSFORMATION.qwen25.rho_tqs_ps`
- 0.13 → `main.exploratory.e4.F5_TRANSFORMATION.phi4mini.rho_tqs_ps`
- 0.0% → `main.exploratory.e5.order.smollm2.code_fence`
- 1.4% → `main.exploratory.e5.order.qwen25.code_fence`
- 0.0% → `main.exploratory.e5.order.phi4mini.code_fence`
- 100.0% → `main.exploratory.e5.order.gemma4e4b.code_fence`
- 39.2% → `main.exploratory.e5.order.smollm2.invalid_json`
- 17.7% → `main.exploratory.e5.order.qwen25.invalid_json`
- 0.2% → `main.exploratory.e5.order.phi4mini.invalid_json`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.invalid_json`
- 0.0% → `main.exploratory.e5.order.smollm2.leading_text`
- 0.0% → `main.exploratory.e5.order.qwen25.leading_text`
- 0.1% → `main.exploratory.e5.order.phi4mini.leading_text`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.leading_text`
- 0.0% → `main.exploratory.e5.order.smollm2.trailing_text`
- 0.0% → `main.exploratory.e5.order.qwen25.trailing_text`
- 0.0% → `main.exploratory.e5.order.phi4mini.trailing_text`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.trailing_text`
- 0.0% → `main.exploratory.e5.order.smollm2.extra_keys`
- 0.0% → `main.exploratory.e5.order.qwen25.extra_keys`
- 0.0% → `main.exploratory.e5.order.phi4mini.extra_keys`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.extra_keys`
- 20.9% → `main.exploratory.e5.order.smollm2.missing_evidence`
- 0.0% → `main.exploratory.e5.order.qwen25.missing_evidence`
- 0.0% → `main.exploratory.e5.order.phi4mini.missing_evidence`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.missing_evidence`
- 0.0% → `main.exploratory.e5.order.smollm2.evidence_count_1`
- 31.6% → `main.exploratory.e5.order.qwen25.evidence_count_1`
- 16.4% → `main.exploratory.e5.order.phi4mini.evidence_count_1`
- 16.8% → `main.exploratory.e5.order.gemma4e4b.evidence_count_1`
- 30.2% → `main.exploratory.e5.order.smollm2.evidence_count_3plus`
- 0.3% → `main.exploratory.e5.order.qwen25.evidence_count_3plus`
- 3.4% → `main.exploratory.e5.order.phi4mini.evidence_count_3plus`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.evidence_count_3plus`
- 13.1% → `main.exploratory.e5.order.smollm2.evidence_not_verbatim`
- 6.4% → `main.exploratory.e5.order.qwen25.evidence_not_verbatim`
- 22.1% → `main.exploratory.e5.order.phi4mini.evidence_not_verbatim`
- 34.6% → `main.exploratory.e5.order.gemma4e4b.evidence_not_verbatim`
- 1.1% → `main.exploratory.e5.order.smollm2.evidence_duplicate`
- 1.9% → `main.exploratory.e5.order.qwen25.evidence_duplicate`
- 5.2% → `main.exploratory.e5.order.phi4mini.evidence_duplicate`
- 0.5% → `main.exploratory.e5.order.gemma4e4b.evidence_duplicate`
- 0.0% → `main.exploratory.e5.order.smollm2.truncated`
- 0.2% → `main.exploratory.e5.order.qwen25.truncated`
- 0.0% → `main.exploratory.e5.order.phi4mini.truncated`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.truncated`
- 0.0% → `main.exploratory.e5.order.smollm2.evidence_comma_only.items.mean`
- 0.0% → `main.exploratory.e5.order.smollm2.evidence_comma_only.items.ci_low`
- 0.0% → `main.exploratory.e5.order.smollm2.evidence_comma_only.items.ci_high`
- 0 → `main.exploratory.e5.order.smollm2.evidence_comma_only.n_items_comma_only`
- 406 → `main.exploratory.e5.order.smollm2.evidence_comma_only.n_items_not_verbatim`
- 0.0% → `main.exploratory.e5.order.qwen25.evidence_comma_only.items.mean`
- 0.0% → `main.exploratory.e5.order.qwen25.evidence_comma_only.items.ci_low`
- 0.0% → `main.exploratory.e5.order.qwen25.evidence_comma_only.items.ci_high`
- 0 → `main.exploratory.e5.order.qwen25.evidence_comma_only.n_items_comma_only`
- 71 → `main.exploratory.e5.order.qwen25.evidence_comma_only.n_items_not_verbatim`
- 1.7% → `main.exploratory.e5.order.phi4mini.evidence_comma_only.items.mean`
- 0.0% → `main.exploratory.e5.order.phi4mini.evidence_comma_only.items.ci_low`
- 4.2% → `main.exploratory.e5.order.phi4mini.evidence_comma_only.items.ci_high`
- 5 → `main.exploratory.e5.order.phi4mini.evidence_comma_only.n_items_comma_only`
- 295 → `main.exploratory.e5.order.phi4mini.evidence_comma_only.n_items_not_verbatim`
- 96.2% → `main.exploratory.e5.order.gemma4e4b.evidence_comma_only.items.mean`
- 90.7% → `main.exploratory.e5.order.gemma4e4b.evidence_comma_only.items.ci_low`
- 99.4% → `main.exploratory.e5.order.gemma4e4b.evidence_comma_only.items.ci_high`
- 430 → `main.exploratory.e5.order.gemma4e4b.evidence_comma_only.n_items_comma_only`
- 447 → `main.exploratory.e5.order.gemma4e4b.evidence_comma_only.n_items_not_verbatim`
- 96.0% → `main.exploratory.e5.order.smollm2.by_family.invalid_json.F1_QA`
- 1.5% → `main.exploratory.e5.order.qwen25.by_family.invalid_json.F1_QA`
- 0.0% → `main.exploratory.e5.order.phi4mini.by_family.invalid_json.F1_QA`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.by_family.invalid_json.F1_QA`
- 0.0% → `main.exploratory.e5.order.smollm2.by_family.invalid_json.F2_CLASSIFICATION`
- 0.0% → `main.exploratory.e5.order.qwen25.by_family.invalid_json.F2_CLASSIFICATION`
- 0.0% → `main.exploratory.e5.order.phi4mini.by_family.invalid_json.F2_CLASSIFICATION`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.by_family.invalid_json.F2_CLASSIFICATION`
- 100.0% → `main.exploratory.e5.order.smollm2.by_family.invalid_json.F3_SUMMARIZATION`
- 87.0% → `main.exploratory.e5.order.qwen25.by_family.invalid_json.F3_SUMMARIZATION`
- 1.0% → `main.exploratory.e5.order.phi4mini.by_family.invalid_json.F3_SUMMARIZATION`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.by_family.invalid_json.F3_SUMMARIZATION`
- 0.0% → `main.exploratory.e5.order.smollm2.by_family.invalid_json.F4_EXTRACTION`
- 0.0% → `main.exploratory.e5.order.qwen25.by_family.invalid_json.F4_EXTRACTION`
- 0.0% → `main.exploratory.e5.order.phi4mini.by_family.invalid_json.F4_EXTRACTION`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.by_family.invalid_json.F4_EXTRACTION`
- 0.0% → `main.exploratory.e5.order.smollm2.by_family.invalid_json.F5_TRANSFORMATION`
- 0.0% → `main.exploratory.e5.order.qwen25.by_family.invalid_json.F5_TRANSFORMATION`
- 0.0% → `main.exploratory.e5.order.phi4mini.by_family.invalid_json.F5_TRANSFORMATION`
- 0.0% → `main.exploratory.e5.order.gemma4e4b.by_family.invalid_json.F5_TRANSFORMATION`
- 70.0% → `main.robustness.strict_format.order.smollm2.csr.mean`
- 66.8% → `main.robustness.strict_format.order.smollm2.csr.ci_low`
- 73.1% → `main.robustness.strict_format.order.smollm2.csr.ci_high`
- 399 → `main.robustness.strict_format.order.smollm2.n_outputs`
- 27.9% → `main.robustness.cascade.order.smollm2.csr.mean`
- 25.1% → `main.robustness.cascade.order.smollm2.csr.ci_low`
- 30.7% → `main.robustness.cascade.order.smollm2.csr.ci_high`
- 0.440 → `main.robustness.cascade.order.smollm2.ps.mean`
- 0.396 → `main.robustness.cascade.order.smollm2.ps.ci_low`
- 0.486 → `main.robustness.cascade.order.smollm2.ps.ci_high`
- 77.4% → `main.robustness.strict_format.order.qwen25.csr.mean`
- 76.1% → `main.robustness.strict_format.order.qwen25.csr.ci_low`
- 78.6% → `main.robustness.strict_format.order.qwen25.csr.ci_high`
- 809 → `main.robustness.strict_format.order.qwen25.n_outputs`
- 62.6% → `main.robustness.cascade.order.qwen25.csr.mean`
- 61.1% → `main.robustness.cascade.order.qwen25.csr.ci_low`
- 64.1% → `main.robustness.cascade.order.qwen25.csr.ci_high`
- 0.346 → `main.robustness.cascade.order.qwen25.ps.mean`
- 0.312 → `main.robustness.cascade.order.qwen25.ps.ci_low`
- 0.384 → `main.robustness.cascade.order.qwen25.ps.ci_high`
- 85.5% → `main.robustness.strict_format.order.phi4mini.csr.mean`
- 83.8% → `main.robustness.strict_format.order.phi4mini.csr.ci_low`
- 87.0% → `main.robustness.strict_format.order.phi4mini.csr.ci_high`
- 997 → `main.robustness.strict_format.order.phi4mini.n_outputs`
- 85.2% → `main.robustness.cascade.order.phi4mini.csr.mean`
- 83.6% → `main.robustness.cascade.order.phi4mini.csr.ci_low`
- 86.8% → `main.robustness.cascade.order.phi4mini.csr.ci_high`
- 0.266 → `main.robustness.cascade.order.phi4mini.ps.mean`
- 0.238 → `main.robustness.cascade.order.phi4mini.ps.ci_low`
- 0.294 → `main.robustness.cascade.order.phi4mini.ps.ci_high`
- 0.0% → `main.robustness.cascade.order.gemma4e4b.csr.mean`
- 0.0% → `main.robustness.cascade.order.gemma4e4b.csr.ci_low`
- 0.0% → `main.robustness.cascade.order.gemma4e4b.csr.ci_high`
- 0.000 → `main.robustness.cascade.order.gemma4e4b.ps.mean`
- 0.000 → `main.robustness.cascade.order.gemma4e4b.ps.ci_low`
- 0.000 → `main.robustness.cascade.order.gemma4e4b.ps.ci_high`
- .003 → `main.robustness.cascade.p3.smollm2.p`
- 0.130 → `main.robustness.cascade.p3.smollm2.mean_diff`
- 0.084 → `main.robustness.cascade.p3.smollm2.ci_low`
- 0.174 → `main.robustness.cascade.p3.smollm2.ci_high`
- < .001 → `main.robustness.cascade.p3.qwen25.p`
- 0.278 → `main.robustness.cascade.p3.qwen25.mean_diff`
- 0.238 → `main.robustness.cascade.p3.qwen25.ci_low`
- 0.320 → `main.robustness.cascade.p3.qwen25.ci_high`
- < .001 → `main.robustness.cascade.p3.phi4mini.p`
- 0.118 → `main.robustness.cascade.p3.phi4mini.mean_diff`
- 0.086 → `main.robustness.cascade.p3.phi4mini.ci_low`
- 0.150 → `main.robustness.cascade.p3.phi4mini.ci_high`
- 0.000 → `main.robustness.cascade.p3.gemma4e4b.mean_diff`
- 0.000 → `main.robustness.cascade.p3.gemma4e4b.ci_low`
- 0.000 → `main.robustness.cascade.p3.gemma4e4b.ci_high`
- 4 → `main.robustness.cascade.p1.format.df`
- 89.15 → `main.robustness.cascade.p1.format.wald_chi2`
- < .001 → `main.robustness.cascade.p1.format.p`
- 4 → `main.robustness.cascade.p1.length.df`
- 53.07 → `main.robustness.cascade.p1.length.wald_chi2`
- < .001 → `main.robustness.cascade.p1.length.p`
- 2.3% → `main.robustness.diagnostics.order.smollm2.verbatim_min3.mean`
- 0.7% → `main.robustness.diagnostics.order.smollm2.verbatim_min3.ci_low`
- 4.2% → `main.robustness.diagnostics.order.smollm2.verbatim_min3.ci_high`
- 50.9% → `main.robustness.diagnostics.order.qwen25.verbatim_min3.mean`
- 47.0% → `main.robustness.diagnostics.order.qwen25.verbatim_min3.ci_low`
- 54.2% → `main.robustness.diagnostics.order.qwen25.verbatim_min3.ci_high`
- 59.8% → `main.robustness.diagnostics.order.phi4mini.verbatim_min3.mean`
- 54.5% → `main.robustness.diagnostics.order.phi4mini.verbatim_min3.ci_low`
- 64.8% → `main.robustness.diagnostics.order.phi4mini.verbatim_min3.ci_high`
- 45.4% → `main.robustness.diagnostics.order.gemma4e4b.verbatim_min3.mean`
- 38.5% → `main.robustness.diagnostics.order.gemma4e4b.verbatim_min3.ci_low`
- 52.2% → `main.robustness.diagnostics.order.gemma4e4b.verbatim_min3.ci_high`
- 2.5% → `main.robustness.diagnostics.order.smollm2.f1_containment_char.mean`
- 0.0% → `main.robustness.diagnostics.order.smollm2.f1_containment_char.ci_low`
- 7.5% → `main.robustness.diagnostics.order.smollm2.f1_containment_char.ci_high`
- 77.5% → `main.robustness.diagnostics.order.qwen25.f1_containment_char.mean`
- 59.0% → `main.robustness.diagnostics.order.qwen25.f1_containment_char.ci_low`
- 93.5% → `main.robustness.diagnostics.order.qwen25.f1_containment_char.ci_high`
- 87.5% → `main.robustness.diagnostics.order.phi4mini.f1_containment_char.mean`
- 72.5% → `main.robustness.diagnostics.order.phi4mini.f1_containment_char.ci_low`
- 100.0% → `main.robustness.diagnostics.order.phi4mini.f1_containment_char.ci_high`
- 86.5% → `main.robustness.diagnostics.order.gemma4e4b.f1_containment_char.mean`
- 72.0% → `main.robustness.diagnostics.order.gemma4e4b.f1_containment_char.ci_low`
- 98.0% → `main.robustness.diagnostics.order.gemma4e4b.f1_containment_char.ci_high`
- 0.0% → `main.robustness.p1_independence.format.excluded_models`
- 0.77 → `main.robustness.p1_independence.format.or.2.estimate`
- 0.45 → `main.robustness.p1_independence.format.or.2.ci_low`
- 1.33 → `main.robustness.p1_independence.format.or.2.ci_high`
- 0.28 → `main.robustness.p1_independence.format.or.3.estimate`
- 0.16 → `main.robustness.p1_independence.format.or.3.ci_low`
- 0.47 → `main.robustness.p1_independence.format.or.3.ci_high`
- 0.58 → `main.robustness.p1_independence.format.or.4.estimate`
- 0.34 → `main.robustness.p1_independence.format.or.4.ci_low`
- 0.99 → `main.robustness.p1_independence.format.or.4.ci_high`
- 5.99 → `main.robustness.p1_independence.format.or.5.estimate`
- 3.05 → `main.robustness.p1_independence.format.or.5.ci_low`
- 11.77 → `main.robustness.p1_independence.format.or.5.ci_high`
- 4 → `main.robustness.p1_independence.format.df`
- 89.40 → `main.robustness.p1_independence.format.wald_chi2`
- < .001 → `main.robustness.p1_independence.format.p`
- < .001 → `main.robustness.p1_independence.format.q`
- 3000 → `main.robustness.p1_independence.format.n`
- 0.75 → `main.robustness.p1_independence.length.or.2.estimate`
- 0.42 → `main.robustness.p1_independence.length.or.2.ci_low`
- 1.31 → `main.robustness.p1_independence.length.or.2.ci_high`
- 2.49 → `main.robustness.p1_independence.length.or.3.estimate`
- 1.29 → `main.robustness.p1_independence.length.or.3.ci_low`
- 4.80 → `main.robustness.p1_independence.length.or.3.ci_high`
- 0.37 → `main.robustness.p1_independence.length.or.4.estimate`
- 0.20 → `main.robustness.p1_independence.length.or.4.ci_low`
- 0.69 → `main.robustness.p1_independence.length.or.4.ci_high`
- 0.40 → `main.robustness.p1_independence.length.or.5.estimate`
- 0.20 → `main.robustness.p1_independence.length.or.5.ci_low`
- 0.80 → `main.robustness.p1_independence.length.or.5.ci_high`
- 4 → `main.robustness.p1_independence.length.df`
- 56.98 → `main.robustness.p1_independence.length.wald_chi2`
- < .001 → `main.robustness.p1_independence.length.p`
- < .001 → `main.robustness.p1_independence.length.q`
- 3200 → `main.robustness.p1_independence.length.n`
- 1.23 → `main.robustness.p1_independence.cardinality.or.2.estimate`
- 1.01 → `main.robustness.p1_independence.cardinality.or.2.ci_low`
- 1.49 → `main.robustness.p1_independence.cardinality.or.2.ci_high`
- 1.58 → `main.robustness.p1_independence.cardinality.or.3.estimate`
- 1.30 → `main.robustness.p1_independence.cardinality.or.3.ci_low`
- 1.92 → `main.robustness.p1_independence.cardinality.or.3.ci_high`
- 1.34 → `main.robustness.p1_independence.cardinality.or.4.estimate`
- 1.08 → `main.robustness.p1_independence.cardinality.or.4.ci_low`
- 1.65 → `main.robustness.p1_independence.cardinality.or.4.ci_high`
- 0.63 → `main.robustness.p1_independence.cardinality.or.5.estimate`
- 0.50 → `main.robustness.p1_independence.cardinality.or.5.ci_low`
- 0.80 → `main.robustness.p1_independence.cardinality.or.5.ci_high`
- 4 → `main.robustness.p1_independence.cardinality.df`
- 93.26 → `main.robustness.p1_independence.cardinality.wald_chi2`
- < .001 → `main.robustness.p1_independence.cardinality.p`
- < .001 → `main.robustness.p1_independence.cardinality.q`
- 4000 → `main.robustness.p1_independence.cardinality.n`
- 1.29 → `main.robustness.p1_independence.t4.or.2.estimate`
- 1.05 → `main.robustness.p1_independence.t4.or.2.ci_low`
- 1.59 → `main.robustness.p1_independence.t4.or.2.ci_high`
- 1.19 → `main.robustness.p1_independence.t4.or.3.estimate`
- 0.94 → `main.robustness.p1_independence.t4.or.3.ci_low`
- 1.50 → `main.robustness.p1_independence.t4.or.3.ci_high`
- 1.19 → `main.robustness.p1_independence.t4.or.4.estimate`
- 0.93 → `main.robustness.p1_independence.t4.or.4.ci_low`
- 1.52 → `main.robustness.p1_independence.t4.or.4.ci_high`
- 0.63 → `main.robustness.p1_independence.t4.or.5.estimate`
- 0.47 → `main.robustness.p1_independence.t4.or.5.ci_low`
- 0.84 → `main.robustness.p1_independence.t4.or.5.ci_high`
- 4 → `main.robustness.p1_independence.t4.df`
- 20.61 → `main.robustness.p1_independence.t4.wald_chi2`
- < .001 → `main.robustness.p1_independence.t4.p`
- < .001 → `main.robustness.p1_independence.t4.q`
- 4000 → `main.robustness.p1_independence.t4.n`
- 1.19 → `main.robustness.p1_independence.verbatim.or.2.estimate`
- 1.01 → `main.robustness.p1_independence.verbatim.or.2.ci_low`
- 1.41 → `main.robustness.p1_independence.verbatim.or.2.ci_high`
- 0.97 → `main.robustness.p1_independence.verbatim.or.3.estimate`
- 0.82 → `main.robustness.p1_independence.verbatim.or.3.ci_low`
- 1.14 → `main.robustness.p1_independence.verbatim.or.3.ci_high`
- 1.07 → `main.robustness.p1_independence.verbatim.or.4.estimate`
- 0.90 → `main.robustness.p1_independence.verbatim.or.4.ci_low`
- 1.29 → `main.robustness.p1_independence.verbatim.or.4.ci_high`
- 1.20 → `main.robustness.p1_independence.verbatim.or.5.estimate`
- 1.00 → `main.robustness.p1_independence.verbatim.or.5.ci_low`
- 1.44 → `main.robustness.p1_independence.verbatim.or.5.ci_high`
- 4 → `main.robustness.p1_independence.verbatim.df`
- 14.58 → `main.robustness.p1_independence.verbatim.wald_chi2`
- .006 → `main.robustness.p1_independence.verbatim.p`
- .006 → `main.robustness.p1_independence.verbatim.q`
- 4000 → `main.robustness.p1_independence.verbatim.n`
- 54.0% → `main.robustness.constraint_instability.order.smollm2.format.mean`
- 49.0% → `main.robustness.constraint_instability.order.smollm2.format.ci_low`
- 59.0% → `main.robustness.constraint_instability.order.smollm2.format.ci_high`
- 3.0% → `main.robustness.constraint_instability.order.smollm2.length.mean`
- 0.0% → `main.robustness.constraint_instability.order.smollm2.length.ci_low`
- 7.0% → `main.robustness.constraint_instability.order.smollm2.length.ci_high`
- 25.0% → `main.robustness.constraint_instability.order.smollm2.cardinality.ci_low`
- 41.0% → `main.robustness.constraint_instability.order.smollm2.cardinality.ci_high`
- 13.0% → `main.robustness.constraint_instability.order.smollm2.t4.mean`
- 7.0% → `main.robustness.constraint_instability.order.smollm2.t4.ci_low`
- 19.0% → `main.robustness.constraint_instability.order.smollm2.t4.ci_high`
- 44.0% → `main.robustness.constraint_instability.order.smollm2.verbatim.ci_low`
- 57.0% → `main.robustness.constraint_instability.order.smollm2.verbatim.ci_high`
- 27.0% → `main.robustness.constraint_instability.order.qwen25.format.mean`
- 23.0% → `main.robustness.constraint_instability.order.qwen25.format.ci_low`
- 32.0% → `main.robustness.constraint_instability.order.qwen25.format.ci_high`
- 22.0% → `main.robustness.constraint_instability.order.qwen25.length.mean`
- 20.0% → `main.robustness.constraint_instability.order.qwen25.length.ci_low`
- 25.0% → `main.robustness.constraint_instability.order.qwen25.length.ci_high`
- 51.0% → `main.robustness.constraint_instability.order.qwen25.cardinality.mean`
- 45.0% → `main.robustness.constraint_instability.order.qwen25.cardinality.ci_low`
- 57.0% → `main.robustness.constraint_instability.order.qwen25.cardinality.ci_high`
- 27.0% → `main.robustness.constraint_instability.order.qwen25.t4.mean`
- 19.0% → `main.robustness.constraint_instability.order.qwen25.t4.ci_low`
- 35.0% → `main.robustness.constraint_instability.order.qwen25.t4.ci_high`
- 51.0% → `main.robustness.constraint_instability.order.qwen25.verbatim.mean`
- 44.0% → `main.robustness.constraint_instability.order.qwen25.verbatim.ci_low`
- 59.0% → `main.robustness.constraint_instability.order.qwen25.verbatim.ci_high`
- 2.0% → `main.robustness.constraint_instability.order.phi4mini.format.mean`
- 0.0% → `main.robustness.constraint_instability.order.phi4mini.format.ci_low`
- 5.0% → `main.robustness.constraint_instability.order.phi4mini.format.ci_high`
- 16.0% → `main.robustness.constraint_instability.order.phi4mini.length.mean`
- 12.0% → `main.robustness.constraint_instability.order.phi4mini.length.ci_low`
- 19.0% → `main.robustness.constraint_instability.order.phi4mini.length.ci_high`
- 47.0% → `main.robustness.constraint_instability.order.phi4mini.cardinality.ci_low`
- 62.0% → `main.robustness.constraint_instability.order.phi4mini.cardinality.ci_high`
- 35.0% → `main.robustness.constraint_instability.order.phi4mini.t4.mean`
- 29.0% → `main.robustness.constraint_instability.order.phi4mini.t4.ci_low`
- 41.0% → `main.robustness.constraint_instability.order.phi4mini.t4.ci_high`
- 43.0% → `main.robustness.constraint_instability.order.phi4mini.verbatim.ci_low`
- 60.0% → `main.robustness.constraint_instability.order.phi4mini.verbatim.ci_high`
- 0.0% → `main.robustness.constraint_instability.order.gemma4e4b.format.ci_low`
- 0.0% → `main.robustness.constraint_instability.order.gemma4e4b.format.ci_high`
- 0.0% → `main.robustness.constraint_instability.order.gemma4e4b.length.ci_low`
- 5.0% → `main.robustness.constraint_instability.order.gemma4e4b.length.ci_high`
- 16.0% → `main.robustness.constraint_instability.order.gemma4e4b.cardinality.ci_low`
- 30.0% → `main.robustness.constraint_instability.order.gemma4e4b.cardinality.ci_high`
- 0.0% → `main.robustness.constraint_instability.order.gemma4e4b.t4.ci_low`
- 3.0% → `main.robustness.constraint_instability.order.gemma4e4b.t4.ci_high`
- 26.0% → `main.robustness.constraint_instability.order.gemma4e4b.verbatim.ci_low`
- 42.0% → `main.robustness.constraint_instability.order.gemma4e4b.verbatim.ci_high`
- 20.8% → `main.robustness.constraint_instability.order.pooled.format.mean`
- 19.0% → `main.robustness.constraint_instability.order.pooled.format.ci_low`
- 22.5% → `main.robustness.constraint_instability.order.pooled.format.ci_high`
- 10.8% → `main.robustness.constraint_instability.order.pooled.length.mean`
- 9.2% → `main.robustness.constraint_instability.order.pooled.length.ci_low`
- 12.2% → `main.robustness.constraint_instability.order.pooled.length.ci_high`
- 40.2% → `main.robustness.constraint_instability.order.pooled.cardinality.mean`
- 36.2% → `main.robustness.constraint_instability.order.pooled.cardinality.ci_low`
- 44.2% → `main.robustness.constraint_instability.order.pooled.cardinality.ci_high`
- 19.0% → `main.robustness.constraint_instability.order.pooled.t4.mean`
- 16.0% → `main.robustness.constraint_instability.order.pooled.t4.ci_low`
- 22.0% → `main.robustness.constraint_instability.order.pooled.t4.ci_high`
- 47.0% → `main.robustness.constraint_instability.order.pooled.verbatim.mean`
- 43.0% → `main.robustness.constraint_instability.order.pooled.verbatim.ci_low`
- 50.7% → `main.robustness.constraint_instability.order.pooled.verbatim.ci_high`
- 113 → `main.posthoc_r1.cascade_check.format.smollm2.n_outputs_changed`
- 3 → `main.posthoc_r1.cascade_check.format.smollm2.n_tasks_ps_up`
- 3 → `main.posthoc_r1.cascade_check.format.smollm2.n_tasks_ps_down`
- 0 → `main.posthoc_r1.cascade_check.format.qwen25.n_outputs_changed`
- 0 → `main.posthoc_r1.cascade_check.format.qwen25.n_tasks_ps_up`
- 0 → `main.posthoc_r1.cascade_check.format.qwen25.n_tasks_ps_down`
- 0 → `main.posthoc_r1.cascade_check.format.phi4mini.n_outputs_changed`
- 0 → `main.posthoc_r1.cascade_check.format.phi4mini.n_tasks_ps_up`
- 0 → `main.posthoc_r1.cascade_check.format.phi4mini.n_tasks_ps_down`
- 1000 → `main.posthoc_r1.cascade_check.format.gemma4e4b.n_outputs_changed`
- 0 → `main.posthoc_r1.cascade_check.format.gemma4e4b.n_tasks_ps_up`
- 13 → `main.posthoc_r1.cascade_check.format.gemma4e4b.n_tasks_ps_down`
- 0.310 → `main.posthoc_r1.cascade_check.format.smollm2.ps_primary`
- 0.000 → `main.robustness.cascade.format.gemma4e4b.ps.mean`
- 0.192 → `main.posthoc_r1.order_level.order.smollm2.span.csr.mean`
- 0.152 → `main.posthoc_r1.order_level.order.smollm2.span.csr.ci_low`
- 0.234 → `main.posthoc_r1.order_level.order.smollm2.span.csr.ci_high`
- 0.266 → `main.posthoc_r1.order_level.format.smollm2.span.csr.mean`
- 0.212 → `main.posthoc_r1.order_level.order.qwen25.span.csr.mean`
- 0.186 → `main.posthoc_r1.order_level.order.qwen25.span.csr.ci_low`
- 0.240 → `main.posthoc_r1.order_level.order.qwen25.span.csr.ci_high`
- 0.026 → `main.posthoc_r1.order_level.format.qwen25.span.csr.mean`
- 0.106 → `main.posthoc_r1.order_level.order.phi4mini.span.csr.mean`
- 0.080 → `main.posthoc_r1.order_level.order.phi4mini.span.csr.ci_low`
- 0.136 → `main.posthoc_r1.order_level.order.phi4mini.span.csr.ci_high`
- 0.050 → `main.posthoc_r1.order_level.format.phi4mini.span.csr.mean`
- 0.082 → `main.posthoc_r1.order_level.order.gemma4e4b.span.csr.mean`
- 0.062 → `main.posthoc_r1.order_level.order.gemma4e4b.span.csr.ci_low`
- 0.108 → `main.posthoc_r1.order_level.order.gemma4e4b.span.csr.ci_high`
- 0.018 → `main.posthoc_r1.order_level.format.gemma4e4b.span.csr.mean`
- 0.100 → `main.posthoc_r1.order_level.order.smollm2.span.pcr.mean`
- 0.060 → `main.posthoc_r1.order_level.order.smollm2.span.pcr.ci_low`
- 0.170 → `main.posthoc_r1.order_level.order.smollm2.span.pcr.ci_high`
- 0.150 → `main.posthoc_r1.order_level.order.qwen25.span.pcr.mean`
- 0.110 → `main.posthoc_r1.order_level.order.qwen25.span.pcr.ci_low`
- 0.190 → `main.posthoc_r1.order_level.order.qwen25.span.pcr.ci_high`
- 0.310 → `main.posthoc_r1.order_level.order.phi4mini.span.pcr.mean`
- 0.240 → `main.posthoc_r1.order_level.order.phi4mini.span.pcr.ci_low`
- 0.400 → `main.posthoc_r1.order_level.order.phi4mini.span.pcr.ci_high`
- 0.000 → `main.posthoc_r1.order_level.order.gemma4e4b.span.pcr.mean`
- 0.000 → `main.posthoc_r1.order_level.order.gemma4e4b.span.pcr.ci_low`
- 0.000 → `main.posthoc_r1.order_level.order.gemma4e4b.span.pcr.ci_high`
- 9 → `main.posthoc_r1.order_level.order.rank.overall.csr.n_conditions_reproducing`
- 10 → `main.posthoc_r1.order_level.format.rank.overall.csr.n_conditions_reproducing`
- 6 → `main.posthoc_r1.order_level.order.rank.overall.pcr.n_conditions_reproducing`
- 3 → `main.posthoc_r1.order_level.format.rank.overall.pcr.n_conditions_reproducing`
- 39.9% → `main.posthoc_r1.fence_tolerant.order.smollm2.format.mean`
- 34.1% → `main.posthoc_r1.fence_tolerant.order.smollm2.csr.mean`
- 32.0% → `main.posthoc_r1.fence_tolerant.order.smollm2.csr.ci_low`
- 36.1% → `main.posthoc_r1.fence_tolerant.order.smollm2.csr.ci_high`
- 5.8% → `main.posthoc_r1.fence_tolerant.order.smollm2.pcr.mean`
- 3.7% → `main.posthoc_r1.fence_tolerant.order.smollm2.pcr.ci_low`
- 8.0% → `main.posthoc_r1.fence_tolerant.order.smollm2.pcr.ci_high`
- 82.3% → `main.posthoc_r1.fence_tolerant.order.qwen25.format.mean`
- 63.6% → `main.posthoc_r1.fence_tolerant.order.qwen25.csr.mean`
- 62.4% → `main.posthoc_r1.fence_tolerant.order.qwen25.csr.ci_low`
- 64.7% → `main.posthoc_r1.fence_tolerant.order.qwen25.csr.ci_high`
- 8.1% → `main.posthoc_r1.fence_tolerant.order.qwen25.pcr.mean`
- 5.6% → `main.posthoc_r1.fence_tolerant.order.qwen25.pcr.ci_low`
- 10.8% → `main.posthoc_r1.fence_tolerant.order.qwen25.pcr.ci_high`
- 99.7% → `main.posthoc_r1.fence_tolerant.order.phi4mini.format.mean`
- 85.2% → `main.posthoc_r1.fence_tolerant.order.phi4mini.csr.mean`
- 83.6% → `main.posthoc_r1.fence_tolerant.order.phi4mini.csr.ci_low`
- 86.8% → `main.posthoc_r1.fence_tolerant.order.phi4mini.csr.ci_high`
- 45.7% → `main.posthoc_r1.fence_tolerant.order.phi4mini.pcr.mean`
- 40.2% → `main.posthoc_r1.fence_tolerant.order.phi4mini.pcr.ci_low`
- 50.9% → `main.posthoc_r1.fence_tolerant.order.phi4mini.pcr.ci_high`
- 100.0% → `main.posthoc_r1.fence_tolerant.order.gemma4e4b.format.mean`
- 89.6% → `main.posthoc_r1.fence_tolerant.order.gemma4e4b.csr.mean`
- 88.0% → `main.posthoc_r1.fence_tolerant.order.gemma4e4b.csr.ci_low`
- 91.1% → `main.posthoc_r1.fence_tolerant.order.gemma4e4b.csr.ci_high`
- 53.7% → `main.posthoc_r1.fence_tolerant.order.gemma4e4b.pcr.mean`
- 47.1% → `main.posthoc_r1.fence_tolerant.order.gemma4e4b.pcr.ci_low`
- 60.3% → `main.posthoc_r1.fence_tolerant.order.gemma4e4b.pcr.ci_high`
- 9 → `main.posthoc_r1.fence_tolerant.cochran_q.gemma4e4b.df`
- 89.89 → `main.posthoc_r1.fence_tolerant.cochran_q.gemma4e4b.q`
- < .001 → `main.posthoc_r1.fence_tolerant.cochran_q.gemma4e4b.p`
- 4.4% → `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.csr.mean`
- 2.3% → `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.csr.ci_low`
- 6.3% → `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.csr.ci_high`
- < .001 → `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.csr.p`
- 8.0% → `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.pcr.mean`
- 1.0% → `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.pcr.ci_low`
- 14.9% → `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.pcr.ci_high`
- .028 → `main.posthoc_r1.fence_tolerant.paired.gemma4e4b_vs_phi4mini.pcr.p`
- 40 → `main.posthoc_r1.kendall_w.smollm2.n_constant_tasks`
- 0.205 → `main.posthoc_r1.kendall_w.smollm2.kendall_w_nonconstant`
- 20 → `main.posthoc_r1.kendall_w.qwen25.n_constant_tasks`
- 0.216 → `main.posthoc_r1.kendall_w.qwen25.kendall_w_nonconstant`
- 19 → `main.posthoc_r1.kendall_w.phi4mini.n_constant_tasks`
- 0.084 → `main.posthoc_r1.kendall_w.phi4mini.kendall_w_nonconstant`
- 56 → `main.posthoc_r1.kendall_w.gemma4e4b.n_constant_tasks`
- 0.256 → `main.posthoc_r1.kendall_w.gemma4e4b.kendall_w_nonconstant`
- 5.00 → `main.posthoc_r1.edit_distance.smollm2.median_format_variants`
- 66.00 → `main.posthoc_r1.edit_distance.smollm2.median_reorderings`
- 4.00 → `main.posthoc_r1.edit_distance.qwen25.median_format_variants`
- 67.00 → `main.posthoc_r1.edit_distance.qwen25.median_reorderings`
- 4.00 → `main.posthoc_r1.edit_distance.phi4mini.median_format_variants`
- 66.00 → `main.posthoc_r1.edit_distance.phi4mini.median_reorderings`
- 4.00 → `main.posthoc_r1.edit_distance.gemma4e4b.median_format_variants`
- 66.00 → `main.posthoc_r1.edit_distance.gemma4e4b.median_reorderings`

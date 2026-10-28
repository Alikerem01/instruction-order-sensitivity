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

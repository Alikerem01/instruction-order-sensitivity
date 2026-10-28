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
- CSR, format arm: Gemma 4 E4B > Phi-4-mini > Qwen2.5-3B > SmolLM2-1.7B (mean over the ten conditions) in 2 of 10 conditions.
- PCR, format arm: Phi-4-mini > Gemma 4 E4B > Qwen2.5-3B > SmolLM2-1.7B (mean over the ten conditions) in 2 of 10 conditions.
- SmolLM2-1.7B vs Qwen2.5-3B, order arm: CSR 0 / 10 / 0; PCR 3 / 6 / 1 (higher / lower / tied).
- SmolLM2-1.7B vs Phi-4-mini, order arm: CSR 0 / 10 / 0; PCR 0 / 10 / 0 (higher / lower / tied).
- SmolLM2-1.7B vs Gemma 4 E4B, order arm: CSR 0 / 10 / 0; PCR 0 / 10 / 0 (higher / lower / tied).
- Qwen2.5-3B vs Phi-4-mini, order arm: CSR 0 / 10 / 0; PCR 0 / 10 / 0 (higher / lower / tied).
- Qwen2.5-3B vs Gemma 4 E4B, order arm: CSR 0 / 10 / 0; PCR 0 / 10 / 0 (higher / lower / tied).
- Phi-4-mini vs Gemma 4 E4B, order arm: CSR 1 / 9 / 0; PCR 2 / 8 / 0 (higher / lower / tied).

Ties: the counts compare the per-condition means. A ranking holds in a condition only if every adjacent pair is strictly ordered, and `n_ties` counts equal means. Means are canonicalized to 12 decimal places before comparisons to remove machine-precision artifacts (v3.1 numerical correction). SmolLM2-1.7B and Qwen2.5-3B have exactly equal mean PCR in O01 (order arm). Counts are 3 / 6 / 1 (higher / lower / tied). Phi-4-mini and Gemma 4 E4B have exactly equal mean CSR in V07 and V09 (format arm). Counts are 6 / 2 / 2 (higher / lower / tied). SmolLM2-1.7B and Qwen2.5-3B have exactly equal mean PCR in V01 and V09 (format arm). Counts are 5 / 3 / 2 (higher / lower / tied).

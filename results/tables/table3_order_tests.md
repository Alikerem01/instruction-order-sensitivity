Table 3. Tests of systematic order effects across the 10 orders (P2; 100 tasks per model). q = Benjamini-Hochberg across the four models, separately for each test.

| Model | Friedman χ² (df) | p | q | Kendall's W | Cochran's Q (df) | p | q |
|---|---:|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 110.5 (9) | < .001 | < .001 | 0.123 | 22.4 (9) | .008 | .008 |
| Qwen2.5-3B | 155.8 (9) | < .001 | < .001 | 0.173 | 54.3 (9) | < .001 | < .001 |
| Phi-4-mini | 61.1 (9) | < .001 | < .001 | 0.068 | 63.3 (9) | < .001 | < .001 |
| Gemma 4 E4B | 101.2 (9) | < .001 | < .001 | 0.112 | no variation; test not applicable |  |  |

Gemma 4 E4B's strict FORMAT score is driven by fenced JSON: it wrapped 100.0% of its order-arm outputs and 100.0% of its format-arm outputs in a ```json fence (E5, descriptive), so its strict FORMAT compliance and PCR are 0 and its CSR is at most 0.8.

Table A3. **Post-hoc, descriptive** (decision G4a §3.2): constraint-level instability, the share of tasks whose flag for a constraint is not constant across the arm's 10 prompts (mean [95% CI], task-clustered bootstrap). A constraint that never varies cannot contribute to PS, so a model with several (near-)constant constraints has a mechanically bounded PS.

| Model, arm | FORMAT | LENGTH | CARDINALITY | NO_COMMA | VERBATIM |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B, order arm | 54.0% [49.0%, 59.0%] | 3.0% [0.0%, 7.0%] | 33.0% [25.0%, 41.0%] | 13.0% [7.0%, 19.0%] | 51.0% [44.0%, 57.0%] |
| Qwen2.5-3B, order arm | 27.0% [23.0%, 32.0%] | 22.0% [20.0%, 25.0%] | 51.0% [45.0%, 57.0%] | 27.0% [19.0%, 35.0%] | 51.0% [44.0%, 59.0%] |
| Phi-4-mini, order arm | 2.0% [0.0%, 5.0%] | 16.0% [12.0%, 19.0%] | 54.0% [47.0%, 62.0%] | 35.0% [29.0%, 41.0%] | 52.0% [43.0%, 60.0%] |
| Gemma 4 E4B, order arm | 0.0% [0.0%, 0.0%] | 2.0% [0.0%, 5.0%] | 23.0% [16.0%, 30.0%] | 1.0% [0.0%, 3.0%] | 34.0% [26.0%, 42.0%] |
| Pooled, order arm | 20.8% [19.0%, 22.5%] | 10.8% [9.2%, 12.2%] | 40.2% [36.2%, 44.2%] | 19.0% [16.0%, 22.0%] | 47.0% [43.0%, 50.7%] |
| SmolLM2-1.7B, format arm | 39.0% [35.0%, 43.0%] | 41.0% [38.0%, 44.0%] | 27.0% [20.0%, 34.0%] | 18.0% [13.0%, 24.0%] | 40.0% [33.0%, 47.0%] |
| Qwen2.5-3B, format arm | 0.0% [0.0%, 0.0%] | 1.0% [0.0%, 3.0%] | 15.0% [9.0%, 21.0%] | 14.0% [9.0%, 20.0%] | 8.0% [3.0%, 13.0%] |
| Phi-4-mini, format arm | 1.0% [0.0%, 3.0%] | 7.0% [3.0%, 11.0%] | 17.0% [10.0%, 25.0%] | 31.0% [26.0%, 37.0%] | 30.0% [22.0%, 38.0%] |
| Gemma 4 E4B, format arm | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] | 3.0% [0.0%, 7.0%] | 1.0% [0.0%, 3.0%] | 11.0% [6.0%, 17.0%] |
| Pooled, format arm | 10.0% [9.0%, 11.2%] | 12.2% [10.8%, 13.8%] | 15.5% [12.8%, 18.5%] | 16.0% [13.8%, 18.5%] | 22.2% [19.0%, 25.8%] |

Gemma 4 E4B's strict FORMAT score is driven by fenced JSON: it wrapped 100.0% of its order-arm outputs and 100.0% of its format-arm outputs in a ```json fence (E5, descriptive), so its strict FORMAT compliance and PCR are 0 and its CSR is at most 0.8.

Table 2. Main results by model (order arm unless stated; mean [95% CI], task-clustered bootstrap).

| Model | CSR | PCR | PS_order | PS_format | VSR | Flip rate |
|---|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 34.1% [32.0%, 36.1%] | 5.8% [3.7%, 8.0%] | 0.296 [0.260, 0.336] | 0.310 [0.280, 0.344] | 40.0% [36.0%, 44.0%] | 36.0% [33.0%, 39.1%] |
| Qwen2.5-3B | 63.4% [62.1%, 64.5%] | 8.1% [5.6%, 10.8%] | 0.316 [0.292, 0.342] | 0.068 [0.052, 0.086] | 20.0% [16.0%, 24.0%] | 33.2% [30.1%, 36.4%] |
| Phi-4-mini | 85.2% [83.6%, 86.8%] | 45.7% [40.2%, 50.9%] | 0.264 [0.238, 0.292] | 0.148 [0.118, 0.180] | 18.0% [12.0%, 24.0%] | 47.6% [44.1%, 51.1%] |
| Gemma 4 E4B | 69.6% [68.0%, 71.1%] | 0.0% [0.0%, 0.0%] | 0.112 [0.090, 0.136] | 0.028 [0.016, 0.042] | 56.0% [48.0%, 64.0%] | 19.1% [15.1%, 23.1%] |
| Pooled | 63.1% [62.2%, 63.9%] | 14.9% [13.4%, 16.4%] | 0.247 [0.232, 0.262] | 0.138 [0.127, 0.152] | 33.5% [30.5%, 36.5%] | 34.0% [32.1%, 35.8%] |

CSR, PCR, VSR and flip rate are proportions shown as percentages; PS is a difference of CSR (0-1). Gemma 4 E4B's strict FORMAT score is driven by fenced JSON: it wrapped 100.0% of its order-arm outputs and 100.0% of its format-arm outputs in a ```json fence (E5, descriptive), so its strict FORMAT compliance and PCR are 0 and its CSR is at most 0.8. Evaluable outputs (a JSON object could be parsed), order arm: SmolLM2-1.7B 60.8%, Qwen2.5-3B 82.3%, Phi-4-mini 99.8%, Gemma 4 E4B 100.0%. Non-evaluable outputs score 0 on constraints 2-5 (brief §5.8); SmolLM2-1.7B's non-JSON outputs in F1 and F3 (evaluable 4.0% and 0.0%) explain much of its low CSR. Zero-width intervals occur where the outcome is constant within every family, so the family-stratified bootstrap cannot vary it (e.g., Gemma 4 E4B PCR: 0.0% [0.0%, 0.0%]).

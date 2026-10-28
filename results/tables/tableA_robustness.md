Table A2. Robustness (E6, exploratory; order arm): cascade scoring (no strict FORMAT pass → all five constraints score 0) and the subset of outputs that pass FORMAT strictly.

| Model | Cascade CSR | Cascade PCR | Cascade PS_order | Cascade PS_order − PS_format | Strict-FORMAT CSR | Strict-FORMAT PCR |
|---|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 27.9% [25.1%, 30.7%] | 5.8% [3.7%, 8.0%] | 0.440 [0.396, 0.486] | 0.130 [0.084, 0.174], p .003 | 70.0% [66.8%, 73.1%] (n = 399) | 14.5% [9.3%, 19.9%] |
| Qwen2.5-3B | 62.6% [61.1%, 64.1%] | 8.1% [5.6%, 10.8%] | 0.346 [0.312, 0.384] | 0.278 [0.238, 0.320], p < .001 | 77.4% [76.1%, 78.6%] (n = 809) | 10.0% [6.9%, 13.3%] |
| Phi-4-mini | 85.2% [83.6%, 86.8%] | 45.7% [40.2%, 50.9%] | 0.266 [0.238, 0.294] | 0.118 [0.086, 0.150], p < .001 | 85.5% [83.8%, 87.0%] (n = 997) | 45.8% [40.3%, 51.1%] |
| Gemma 4 E4B | 0.0% [0.0%, 0.0%] | 0.0% [0.0%, 0.0%] | 0.000 [0.000, 0.000] | no difference; test not applicable | no output passes FORMAT strictly | n/a |

Cascade P1 GEE (pre-specified estimator): FORMAT: χ²(4) = 89.15, p < .001; LENGTH: χ²(4) = 53.07, p < .001; CARDINALITY: not estimable; NO_COMMA: not estimable; VERBATIM: not estimable.

Gemma 4 E4B's strict FORMAT score is driven by fenced JSON: it wrapped 100.0% of its order-arm outputs and 100.0% of its format-arm outputs in a ```json fence (E5, descriptive), so its strict FORMAT compliance and PCR are 0 and its CSR is at most 0.8.

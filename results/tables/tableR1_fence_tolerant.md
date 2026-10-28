Table R1b. **Post-hoc (decision R1)**: fence-tolerant FORMAT and the CSR and PCR that follow from it, next to strict CSR and PCR (mean [95% CI]). FORMAT_ft = strict FORMAT after removing exactly one enclosing ``` or ```json fence and surrounding whitespace (valid JSON, no duplicate keys, key set exactly {answer, evidence}); otherwise strict FORMAT. The other four constraints are unchanged.

| Model, arm | FORMAT_ft | CSR_ft | PCR_ft | CSR (strict) | PCR (strict) |
|---|---:|---:|---:|---:|---:|
| SmolLM2-1.7B, order | 39.9% [36.6%, 43.1%] | 34.1% [32.0%, 36.1%] | 5.8% [3.7%, 8.0%] | 34.1% [32.0%, 36.1%] | 5.8% [3.7%, 8.0%] |
| Qwen2.5-3B, order | 82.3% [81.5%, 83.0%] | 63.6% [62.4%, 64.7%] | 8.1% [5.6%, 10.8%] | 63.4% [62.1%, 64.5%] | 8.1% [5.6%, 10.8%] |
| Phi-4-mini, order | 99.7% [99.2%, 100.0%] | 85.2% [83.6%, 86.8%] | 45.7% [40.2%, 50.9%] | 85.2% [83.6%, 86.8%] | 45.7% [40.2%, 50.9%] |
| Gemma 4 E4B, order | 100.0% [100.0%, 100.0%] | 89.6% [88.0%, 91.1%] | 53.7% [47.1%, 60.3%] | 69.6% [68.0%, 71.1%] | 0.0% [0.0%, 0.0%] |
| Pooled, order | 80.5% [79.7%, 81.3%] | 68.1% [67.2%, 69.0%] | 28.3% [25.7%, 30.9%] | 63.1% [62.2%, 63.9%] | 14.9% [13.4%, 16.4%] |
| SmolLM2-1.7B, format | 46.0% [43.4%, 48.8%] | 37.5% [35.3%, 40.0%] | 12.5% [8.0%, 17.3%] | 37.5% [35.3%, 40.0%] | 12.5% [8.0%, 17.3%] |
| Qwen2.5-3B, format | 80.0% [80.0%, 80.0%] | 65.4% [63.9%, 66.8%] | 13.5% [9.0%, 18.2%] | 65.4% [63.9%, 66.8%] | 13.5% [9.0%, 18.2%] |
| Phi-4-mini, format | 99.9% [99.7%, 100.0%] | 90.2% [88.3%, 91.9%] | 62.4% [55.5%, 68.9%] | 90.2% [88.3%, 91.9%] | 62.4% [55.5%, 68.9%] |
| Gemma 4 E4B, format | 100.0% [100.0%, 100.0%] | 90.3% [88.3%, 92.2%] | 56.2% [48.2%, 64.2%] | 70.3% [68.3%, 72.2%] | 0.0% [0.0%, 0.0%] |
| Pooled, format | 81.5% [80.8%, 82.2%] | 70.8% [69.8%, 71.9%] | 36.1% [32.8%, 39.2%] | 65.8% [64.8%, 66.9%] | 22.1% [19.8%, 24.4%] |

Ranking by CSR_ft, order arm: Gemma 4 E4B > Phi-4-mini > Qwen2.5-3B > SmolLM2-1.7B; by PCR_ft: Gemma 4 E4B > Phi-4-mini > Qwen2.5-3B > SmolLM2-1.7B. Cochran's Q of PCR_ft across the ten orders for Gemma 4 E4B (post-hoc): Q(9) = 89.89, p < .001. Paired difference Gemma 4 E4B − Phi-4-mini under the fence-tolerant reading, order arm (post-hoc, decision R2; task-clustered bootstrap as in S2): CSR_ft 4.4% [2.3%, 6.3%] (percentage points), bootstrap p < .001; PCR_ft 8.0% [1.0%, 14.9%] (percentage points), bootstrap p = .028.

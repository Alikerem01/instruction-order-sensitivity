Table R1f. Descriptive companions (decision R1 §3.6, §3.7, §3.10): Kendall's W of P2 and the tie-corrected W among the tasks whose CSR is not constant across the ten orders; evidence-item length (\S+ tokens, string items of list evidence, 1,900 unique generations per model); median token-level edit distance of a prompt to its task's O01 prompt under the model's tokenizer (post-hoc).

| Model | W (P2) | Tasks with constant CSR | W, non-constant tasks | Median evidence tokens | 1-token items | 2-token items | Evidence items | Edit distance, formatting variants | Edit distance, reorderings |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SmolLM2-1.7B | 0.123 | 40 | 0.205 | 2 | 39.5% | 26.5% | 3763 | 5 | 66 |
| Qwen2.5-3B | 0.173 | 20 | 0.216 | 12 | 0.4% | 16.4% | 2472 | 4 | 67 |
| Phi-4-mini | 0.068 | 19 | 0.084 | 13 | 0.7% | 11.9% | 3671 | 4 | 66 |
| Gemma 4 E4B | 0.112 | 56 | 0.256 | 14 | 0.0% | 10.9% | 3501 | 4 | 66 |

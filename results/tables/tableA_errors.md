Table A1. Error-tag rates by model and arm (share of the 1,000 outputs per model and arm; E5, exploratory).

| Tag | SmolLM2-1.7B order | SmolLM2-1.7B format | Qwen2.5-3B order | Qwen2.5-3B format | Phi-4-mini order | Phi-4-mini format | Gemma 4 E4B order | Gemma 4 E4B format |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| empty_output | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| code_fence | 0.0% | 0.0% | 1.4% | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% |
| leading_text | 0.0% | 0.2% | 0.0% | 0.0% | 0.1% | 0.0% | 0.0% | 0.0% |
| trailing_text | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| invalid_json | 39.2% | 42.7% | 17.7% | 20.0% | 0.2% | 0.1% | 0.0% | 0.0% |
| duplicate_keys | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| extra_keys | 0.0% | 0.2% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| missing_answer | 0.0% | 0.2% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| missing_evidence | 20.9% | 11.1% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| answer_not_string | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| evidence_not_list | 0.0% | 0.0% | 3.8% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| evidence_count_0 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| evidence_count_1 | 0.0% | 0.0% | 31.6% | 25.4% | 16.4% | 6.7% | 16.8% | 14.5% |
| evidence_count_3plus | 30.2% | 27.9% | 0.3% | 0.0% | 3.4% | 0.0% | 0.0% | 0.0% |
| evidence_not_verbatim | 13.1% | 11.6% | 6.4% | 9.3% | 22.1% | 19.1% | 34.6% | 32.9% |
| evidence_duplicate | 1.1% | 2.4% | 1.9% | 1.3% | 5.2% | 6.1% | 0.5% | 0.7% |
| truncated | 0.0% | 0.0% | 0.2% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |

Gemma 4 E4B's strict FORMAT score is driven by fenced JSON: it wrapped 100.0% of its order-arm outputs and 100.0% of its format-arm outputs in a ```json fence (E5, descriptive), so its strict FORMAT compliance and PCR are 0 and its CSR is at most 0.8.

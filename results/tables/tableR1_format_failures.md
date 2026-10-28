Table R1d. **Descriptive, post-hoc (decision R1)**: strict FORMAT failures in the order arm by type and FORMAT position (count and share of the outputs in the row): fenced; invalid_json = no JSON object; missing_or_extra_key = valid JSON with a missing or extra key; other = surrounding text or duplicate keys.

**SmolLM2-1.7B, by FORMAT position**

| Position | Outputs | Failures | invalid_json | missing_or_extra_key | fenced | other |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 200 | 114 | 76 (38.0%) | 38 (19.0%) | 0 (0.0%) | 0 (0.0%) |
| 2 | 200 | 117 | 80 (40.0%) | 37 (18.5%) | 0 (0.0%) | 0 (0.0%) |
| 3 | 200 | 157 | 80 (40.0%) | 77 (38.5%) | 0 (0.0%) | 0 (0.0%) |
| 4 | 200 | 130 | 79 (39.5%) | 51 (25.5%) | 0 (0.0%) | 0 (0.0%) |
| 5 | 200 | 83 | 77 (38.5%) | 6 (3.0%) | 0 (0.0%) | 0 (0.0%) |

**Qwen2.5-3B, by FORMAT position**

| Position | Outputs | Failures | invalid_json | missing_or_extra_key | fenced | other |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 200 | 41 | 41 (20.5%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| 2 | 200 | 46 | 40 (20.0%) | 0 (0.0%) | 6 (3.0%) | 0 (0.0%) |
| 3 | 200 | 43 | 40 (20.0%) | 0 (0.0%) | 3 (1.5%) | 0 (0.0%) |
| 4 | 200 | 43 | 40 (20.0%) | 0 (0.0%) | 3 (1.5%) | 0 (0.0%) |
| 5 | 200 | 18 | 16 (8.0%) | 0 (0.0%) | 2 (1.0%) | 0 (0.0%) |

**Qwen2.5-3B, by family**

| Family | Outputs | Failures | invalid_json | missing_or_extra_key | fenced | other |
|---|---:|---:|---:|---:|---:|---:|
| QA | 200 | 3 | 3 (1.5%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| CLS | 200 | 14 | 0 (0.0%) | 0 (0.0%) | 14 (7.0%) | 0 (0.0%) |
| SUM | 200 | 174 | 174 (87.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| EXT | 200 | 0 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |
| TRF | 200 | 0 | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) |

Table R1e. **Post-hoc (decision R1)**: parsed-only TQS, per task and model, the range of Q over the orders whose answer could be parsed (q_answer_available = 1), at least 2 such orders; flagged where it differs from the pre-specified TQS by more than 0.05 (mean [95% CI]; n = task-model pairs that qualify; † = differs from the pre-specified TQS of Table 5 by more than 0.05; not computable = no task with at least 2 parsed orders).

| Family | SmolLM2-1.7B | Qwen2.5-3B | Phi-4-mini | Gemma 4 E4B |
|---|---:|---:|---:|---:|
| QA | 0.000 [0.000, 0.000] (n = 2) | 0.050 [0.000, 0.150] (n = 20) | 0.100 [0.000, 0.250] (n = 20) | 0.150 [0.000, 0.300] (n = 20) |
| CLS | 0.200 [0.050, 0.400] (n = 20) | 0.150 [0.000, 0.300] (n = 20) | 0.200 [0.050, 0.400] (n = 20) | 0.000 [0.000, 0.000] (n = 20) |
| SUM | not computable (n = 0) | 0.042 [0.012, 0.074] (n = 5) † | 0.096 [0.074, 0.119] (n = 20) | 0.074 [0.046, 0.105] (n = 20) |
| EXT | 0.120 [0.060, 0.180] (n = 20) | 0.060 [0.020, 0.100] (n = 20) | 0.030 [0.000, 0.060] (n = 20) | 0.020 [0.000, 0.050] (n = 20) |
| TRF | 0.050 [0.020, 0.090] (n = 20) | 0.040 [0.010, 0.080] (n = 20) | 0.020 [0.000, 0.050] (n = 20) | 0.000 [0.000, 0.000] (n = 20) |

Parsed orders per qualifying task, median (minimum), of 10 (decision R2, m19). A range taken over a subset of the orders cannot exceed the range over all ten orders had all of them been parsed, so the cells with few parsed orders (SmolLM2-1.7B QA, Qwen2.5-3B SUM) are lower bounds.

| Family | SmolLM2-1.7B | Qwen2.5-3B | Phi-4-mini | Gemma 4 E4B |
|---|---:|---:|---:|---:|
| QA | 4.0 (3) | 10.0 (7) | 10.0 (10) | 10.0 (10) |
| CLS | 10.0 (10) | 10.0 (10) | 10.0 (10) | 10.0 (10) |
| SUM | – | 2.0 (2) | 10.0 (8) | 10.0 (10) |
| EXT | 10.0 (10) | 10.0 (10) | 10.0 (10) | 10.0 (10) |
| TRF | 10.0 (10) | 10.0 (10) | 10.0 (10) | 10.0 (10) |

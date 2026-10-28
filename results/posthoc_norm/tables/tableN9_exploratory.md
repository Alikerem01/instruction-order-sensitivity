Table N9. Normalized scoring (post-hoc): exploratory and robustness analyses.

**Cascade scoring with normalized FORMAT and the subset passing normalized FORMAT** (order arm):

- SmolLM2-1.7B: cascade CSR 27.9% [25.1%, 30.7%]; cascade PS_order − PS_format 0.130 [0.084, 0.174], p = .003; subset passing normalized FORMAT: n = 399, CSR 70.0% [66.8%, 73.1%].
- Qwen2.5-3B: cascade CSR 63.6% [62.4%, 64.7%]; cascade PS_order − PS_format 0.240 [0.212, 0.270], p < .001; subset passing normalized FORMAT: n = 823, CSR 77.3% [76.0%, 78.5%].
- Phi-4-mini: cascade CSR 85.2% [83.6%, 86.8%]; cascade PS_order − PS_format 0.118 [0.086, 0.150], p < .001; subset passing normalized FORMAT: n = 997, CSR 85.5% [83.8%, 87.0%].
- Gemma 4 E4B: cascade CSR 89.6% [88.0%, 91.1%]; cascade PS_order − PS_format 0.084 [0.060, 0.110], p < .001; subset passing normalized FORMAT: n = 1000, CSR 89.6% [88.0%, 91.1%].

**Hard-to-easy index with normalized pilot difficulties** (ten fixed orders, not a test):

- SmolLM2-1.7B: difficulties FORMAT 0.62, LENGTH 0.41, CARDINALITY 0.88, NO_COMMA 0.70, VERBATIM 0.73; ρ(HE, order-level CSR) = -0.08 [-0.15, 0.03]; ρ(HE, order-level PCR) = -0.23 [-0.61, 0.26].
- Qwen2.5-3B: difficulties FORMAT 0.18, LENGTH 0.17, CARDINALITY 0.46, NO_COMMA 0.61, VERBATIM 0.34; ρ(HE, order-level CSR) = -0.12 [-0.42, 0.01]; ρ(HE, order-level PCR) = -0.20 [-0.30, 0.28].
- Phi-4-mini: difficulties FORMAT 0.00, LENGTH 0.00, CARDINALITY 0.09, NO_COMMA 0.31, VERBATIM 0.22; ρ(HE, order-level CSR) = -0.62 [-0.67, -0.21]; ρ(HE, order-level PCR) = -0.41 [-0.72, -0.17].
- Gemma 4 E4B: difficulties FORMAT 0.00, LENGTH 0.00, CARDINALITY 0.16, NO_COMMA 0.00, VERBATIM 0.52; ρ(HE, order-level CSR) = 0.67 [0.39, 0.78]; ρ(HE, order-level PCR) = 0.62 [0.37, 0.78].

**Normalized FORMAT failures by type, with the raw-output code_fence tag** (order arm):

- SmolLM2-1.7B: normalized FORMAT failures 60.1% of 1000 order-arm records (invalid JSON 392, missing or extra key 209, fenced with failing content 0, other 0); raw-output code_fence tag 0.0%.
- Qwen2.5-3B: normalized FORMAT failures 17.7% of 1000 order-arm records (invalid JSON 177, missing or extra key 0, fenced with failing content 0, other 0); raw-output code_fence tag 1.4%.
- Phi-4-mini: normalized FORMAT failures 0.3% of 1000 order-arm records (invalid JSON 2, missing or extra key 0, fenced with failing content 0, other 1); raw-output code_fence tag 0.0%.
- Gemma 4 E4B: normalized FORMAT failures 0.0% of 1000 order-arm records (invalid JSON 0, missing or extra key 0, fenced with failing content 0, other 0); raw-output code_fence tag 100.0%.

**Share of tasks whose flag varies across the ten orders**:

- SmolLM2-1.7B: FORMAT 54.0%, LENGTH 3.0%, CARDINALITY 33.0%, NO_COMMA 13.0%, VERBATIM 51.0%.
- Qwen2.5-3B: FORMAT 21.0%, LENGTH 22.0%, CARDINALITY 51.0%, NO_COMMA 27.0%, VERBATIM 51.0%.
- Phi-4-mini: FORMAT 2.0%, LENGTH 16.0%, CARDINALITY 54.0%, NO_COMMA 35.0%, VERBATIM 52.0%.
- Gemma 4 E4B: FORMAT 0.0%, LENGTH 2.0%, CARDINALITY 23.0%, NO_COMMA 1.0%, VERBATIM 34.0%.

# Pilot report — run `pilot_gemma_20261005-1529_ccc7919`

Pooled descriptive checks only. Orders and format variants are never compared here (brief §5.6), pilot outputs never enter any analysis, and no pilot number enters the abstract (D04).

Calibration round 0; active instructions: T1=T1_FORMAT, T2=T2_LENGTH, T3=T3_CARDINALITY, T4=T4_NO_COMMA, T5=T5_VERBATIM.

## 1. Compliance per model × constraint (unique texts, pooled over orders and variants)

| Model | n | FORMAT | LENGTH | CARDINALITY | T4 | VERBATIM | PCR | evaluable | truncated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma4e4b | 190 | 0.0% | 100.0% | 86.8% | 100.0% | 43.2% | 0.0% | 100.0% | 0.0% |

## 2. Parsing and error tags

| Model | strict | fence | first_object | none | code-fence rate |
|---|---:|---:|---:|---:|---:|
| gemma4e4b | 0 | 190 | 0 | 0 | 100.0% |

| Tag | gemma4e4b |
|---|---:|
| code_fence | 190 |
| evidence_count_1 | 25 |
| evidence_not_verbatim | 108 |

## 3. Calibration rule (brief §5.6), applied mechanically

Not applicable: no calibration model in this run (D06 §4): this pilot never changes the prompt strings.

## 4. Task-quality sanity checks

| Family | gemma4e4b |
|---|---:|
| F1_QA | 1.000 (answered 38/38) |
| F2_CLASSIFICATION | 1.000 (answered 38/38) |
| F3_SUMMARIZATION | 0.181 (answered 38/38) |
| F4_EXTRACTION | 0.979 (answered 38/38) |
| F5_TRANSFORMATION | 1.000 (answered 38/38) |

### F2 label status (A4)

Distribution: single 38.

### F1 character-level versus token-level containment (A4)

0 disagreement(s) among 38 answered F1 outputs.

## 5. Compute so far (A5)

Generation time of the imported smoke and pilot runs (all models): 0.92 A100 hours (sum of batch times; model loading excluded).

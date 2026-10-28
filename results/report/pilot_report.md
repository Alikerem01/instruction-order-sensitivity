# Pilot report — run `pilot_20261004-2020_d9e9fc2`

Pooled descriptive checks only. Orders and format variants are never compared here (brief §5.6), pilot outputs never enter any analysis, and no pilot number enters the abstract (D04).

Calibration round 0; active instructions: T1=T1_FORMAT, T2=T2_LENGTH, T3=T3_CARDINALITY, T4=T4_NO_COMMA, T5=T5_VERBATIM.

## 1. Compliance per model × constraint (unique texts, pooled over orders and variants)

| Model | n | FORMAT | LENGTH | CARDINALITY | T4 | VERBATIM | PCR | evaluable | truncated |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| phi4mini | 190 | 100.0% | 99.5% | 94.7% | 76.8% | 80.0% | 64.7% | 100.0% | 0.0% |
| qwen25 | 190 | 81.1% | 81.1% | 55.8% | 41.6% | 63.7% | 8.9% | 82.1% | 0.0% |
| smollm2 | 190 | 42.6% | 57.4% | 14.2% | 29.5% | 30.0% | 10.5% | 57.9% | 0.0% |

## 2. Parsing and error tags

| Model | strict | fence | first_object | none | code-fence rate |
|---|---:|---:|---:|---:|---:|
| phi4mini | 190 | 0 | 0 | 0 | 0.0% |
| qwen25 | 154 | 0 | 2 | 34 | 0.0% |
| smollm2 | 110 | 0 | 0 | 80 | 0.0% |

| Tag | phi4mini | qwen25 | smollm2 |
|---|---:|---:|---:|
| leading_text | 0 | 2 | 0 |
| trailing_text | 0 | 2 | 0 |
| invalid_json | 0 | 34 | 80 |
| extra_keys | 0 | 2 | 0 |
| missing_answer | 0 | 2 | 0 |
| missing_evidence | 0 | 2 | 29 |
| evidence_not_list | 0 | 3 | 0 |
| evidence_count_1 | 7 | 45 | 0 |
| evidence_count_3plus | 3 | 0 | 54 |
| evidence_not_verbatim | 38 | 30 | 24 |
| evidence_duplicate | 5 | 0 | 7 |

## 3. Calibration rule (brief §5.6), applied mechanically

Pooled over 570 outputs (all unique pilot texts of the calibration models phi4mini, qwen25, smollm2; decision D06 §4).

| Quantity | Value | Threshold | Decision |
|---|---:|---|---|
| LENGTH pass rate | 79.3% | > 95% | keep T2_LENGTH |
| T4 (T4_NO_COMMA) pass rate | 49.3% | < 5% or > 95% | keep the current T4 |
| Outputs at the length limit | 0.0% | > 2% | keep max_new_tokens 512 |

No string replacement is triggered.

## 4. Task-quality sanity checks

| Family | phi4mini | qwen25 | smollm2 |
|---|---:|---:|---:|
| F1_QA | 1.000 (answered 38/38) | 1.000 (answered 38/38) | 0.000 (answered 0/38) |
| F2_CLASSIFICATION | 1.000 (answered 38/38) | 0.868 (answered 38/38) | 0.579 (answered 38/38) |
| F3_SUMMARIZATION | 0.156 (answered 38/38) | 0.007 (answered 2/38) | 0.000 (answered 0/38) |
| F4_EXTRACTION | 1.000 (answered 38/38) | 1.000 (answered 38/38) | 0.947 (answered 36/38) |
| F5_TRANSFORMATION | 0.937 (answered 38/38) | 1.000 (answered 38/38) | 0.926 (answered 36/38) |

### F2 label status (A4)

Distribution: none 5, single 109.
- qwen25 `cls_p01__V02` (none, gold World): 'This news article is about a hostage situation in Iraq involving a Japanese citizen.'
- qwen25 `cls_p01__V03` (none, gold World): 'This news article is about a hostage situation in Iraq involving a Japanese citizen.'
- qwen25 `cls_p01__V06` (none, gold World): 'This news article is about a hostage situation in Iraq involving a Japanese citizen.'
- qwen25 `cls_p01__V09` (none, gold World): 'This news article is about a hostage situation in Iraq involving a Japanese citizen.'
- qwen25 `cls_p01__V10` (none, gold World): 'This news article is about a hostage situation in Iraq involving a Japanese citizen.'

### F1 character-level versus token-level containment (A4)

0 disagreement(s) among 76 answered F1 outputs.

## 5. Compute so far (A5)

Generation time of the imported smoke and pilot runs (all models): 0.38 A100 hours (sum of batch times; model loading excluded).

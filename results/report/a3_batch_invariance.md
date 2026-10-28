# A3 batch invariance

Pilot run `pilot_20261004-2020_d9e9fc2` (batch 16) versus `pilot_bs1_20261004-2033_d9e9fc2` (batch 1), order-arm pilot texts.

| Model | Texts | Exact output agreement | Vector agreement | Mean CSR batch 16 | Mean CSR batch 1 |
|---|---:|---:|---:|---:|---:|
| phi4mini | 100 | 70.0% (70) | 90.0% (90) | 0.884 | 0.876 |
| qwen25 | 100 | 80.0% (80) | 95.0% (95) | 0.634 | 0.648 |
| smollm2 | 100 | 77.0% (77) | 93.0% (93) | 0.334 | 0.332 |

Rule: keep batch size 16 for the main run if vector agreement >= 98% for every model; otherwise the study team decides at G2.
Mechanical outcome: keep batch size 16 = **no (the study team decides)**.

Details (descriptive): where differing outputs first diverge, the direction of the constraint flips, the CSR change and the generation time per text (sum of batch times / texts; loading excluded).

| Model | Differing texts | First difference (character): median [min, max] | Differ at the first character | Flips: batch 16 pass, batch 1 fail | Flips: batch 1 pass, batch 16 fail | Mean CSR change (batch 1 - batch 16) | s/text batch 16 | s/text batch 1 |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| phi4mini | 30 | 49.0 [22, 206] | 0 | 7 | 3 | -0.008 (3 up, 7 down) | 0.326 | 3.695 |
| qwen25 | 20 | 74.5 [4, 476] | 0 | 1 | 8 | +0.014 (4 up, 1 down) | 0.544 | 5.535 |
| smollm2 | 23 | 69 [0, 208] | 1 | 6 | 5 | -0.002 (3 up, 4 down) | 0.18 | 1.71 |

phi4mini: differing texts by family {'F1_QA': 3, 'F2_CLASSIFICATION': 1, 'F3_SUMMARIZATION': 14, 'F4_EXTRACTION': 6, 'F5_TRANSFORMATION': 6}; flips per constraint (batch 16 pass, batch 1 fail / the reverse): length 0/1, cardinality 1/2, t4 4/0, verbatim 2/0

qwen25: differing texts by family {'F1_QA': 1, 'F2_CLASSIFICATION': 8, 'F3_SUMMARIZATION': 7, 'F4_EXTRACTION': 2, 'F5_TRANSFORMATION': 2}; flips per constraint (batch 16 pass, batch 1 fail / the reverse): length 0/1, cardinality 1/1, t4 0/2, verbatim 0/4

smollm2: differing texts by family {'F1_QA': 1, 'F2_CLASSIFICATION': 3, 'F3_SUMMARIZATION': 10, 'F4_EXTRACTION': 5, 'F5_TRANSFORMATION': 4}; flips per constraint (batch 16 pass, batch 1 fail / the reverse): format_strict 2/1, cardinality 2/2, verbatim 2/2

phi4mini: vector disagreements: ext_p02__P03, ext_p02__P09, sum_p01__P04, sum_p01__P06, sum_p01__P10, sum_p02__P01, sum_p02__P09, sum_p02__P10, trf_p02__P07, trf_p02__P10

qwen25: vector disagreements: cls_p01__P09, cls_p02__P07, cls_p02__P09, cls_p02__P10, sum_p02__P02

smollm2: vector disagreements: cls_p02__P07, cls_p02__P09, ext_p02__P02, trf_p01__P09, trf_p02__P01, trf_p02__P03, trf_p02__P08

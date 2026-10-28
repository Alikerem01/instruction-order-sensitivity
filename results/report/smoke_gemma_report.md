# Smoke-test report

Check only: smoke outputs never enter any analysis, and no smoke number enters the abstract (D04).

## Summary

| Run | Checks passed | Models native + R4 | Generation time (min) |
|---|---|---|---:|
| `smoke_gemma_20261004-2123_38dc8cd` | True | True | 0.20 |
| `smoke_gemma_20261004-2125_38dc8cd` | True | True | 0.20 |

A1 run-to-run determinism (byte-identical outputs per model): gemma4e4b yes (5/5)

## Run `smoke_gemma_20261004-2123_38dc8cd` (pass 1)

Bundle commit `38dc8cd`; GPU `NVIDIA A100-SXM4-80GB` (81920 MiB), driver 580.82.07, CUDA 13.0, cuDNN 92700, Python 3.13.15, torch 2.11.0+cu130, transformers 5.17.0, accelerate 1.15.0, tokenizers 0.23.2.

| Check | Result |
|---|---|
| torch >= 2.5 | yes |
| transformers == 5.17.0 | yes |
| GPU is an A100 | yes |
| import passed | yes |

| Model | Class | Native | R4 | Logits processors | Stopping criteria | Batches | Sessions | Generation s | Finish reasons |
|---|---|---|---|---|---|---:|---:|---:|---|
| gemma4e4b | `Gemma4ForConditionalGeneration` | yes | passed | [] | ['MaxLengthCriteria', 'EosTokenCriteria'] | 1/1 | 1 | 12.22 | {'eos': 5} |

### gemma4e4b

**ext_p01__P01** — 92 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.6); Q 1.000; tags ['code_fence', 'evidence_not_verbatim']

~~~~
```json
{
  "answer": "Priya Nair visited Rotterdam on January 4 2025 with Willow Creek Pharma testing 299 samples.",
  "evidence": [
    "On 4 January 2025 Priya Nair from Willow Creek Pharma visited the Rotterdam facility.",
    "During the visit 299 samples were tested before the team closed the report."
  ]
}
```
~~~~

**trf_p01__P01** — 82 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 1 (CSR 0.8); Q 1.000; tags ['code_fence']

~~~~
```json
{
  "answer": "The Meridian project owned by Marcus Hale is on track with a deadline of 12 May 2025 and a budget of 733000 USD.",
  "evidence": [
    "Project: Meridian.",
    "Approved budget: 733000 USD."
  ]
}
```
~~~~

**cls_p01__P01** — 96 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.6); Q 1.000; tags ['code_fence', 'evidence_not_verbatim']

~~~~
```json
{
  "answer": "The news article belongs to the World category.",
  "evidence": [
    "Japan has confirmed that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda 24 within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
```
~~~~

**qa_p01__P01** — 83 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.6); Q 1.000; tags ['code_fence', 'evidence_not_verbatim']

~~~~
```json
{
  "answer": "Oil companies sought to boost oil supplies even in harsh areas like the Arctic.",
  "evidence": [
    "The embargo left oil companies searching for new ways to increase oil supplies even in rugged terrain such as the Arctic.",
    "Finding oil and developing new fields usually required five to ten years before significant production."
  ]
}
```
~~~~

**sum_p01__P01** — 91 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.6); Q 0.146; tags ['code_fence', 'evidence_not_verbatim']

~~~~
```json
{
  "answer": "Despite a win over Solihull Moors Nicholson was concerned about the team's attitude and need for improvement.",
  "evidence": [
    "Nicholson was unhappy with the attitude afterwards.",
    "But then that comes from a will to improve you've got to put the work in every day at training so that those kind of mistakes stop happening."
  ]
}
```
~~~~

## Run `smoke_gemma_20261004-2125_38dc8cd` (pass 2, replicate of `smoke_gemma_20261004-2123_38dc8cd`)

Bundle commit `38dc8cd`; GPU `NVIDIA A100-SXM4-80GB` (81920 MiB), driver 580.82.07, CUDA 13.0, cuDNN 92700, Python 3.13.15, torch 2.11.0+cu130, transformers 5.17.0, accelerate 1.15.0, tokenizers 0.23.2.

| Check | Result |
|---|---|
| torch >= 2.5 | yes |
| transformers == 5.17.0 | yes |
| GPU is an A100 | yes |
| import passed | yes |

| Model | Class | Native | R4 | Logits processors | Stopping criteria | Batches | Sessions | Generation s | Finish reasons |
|---|---|---|---|---|---|---:|---:|---:|---|
| gemma4e4b | `Gemma4ForConditionalGeneration` | yes | passed | [] | ['MaxLengthCriteria', 'EosTokenCriteria'] | 1/1 | 1 | 11.92 | {'eos': 5} |

### gemma4e4b

**ext_p01__P01** — 92 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.6); Q 1.000; tags ['code_fence', 'evidence_not_verbatim']

~~~~
```json
{
  "answer": "Priya Nair visited Rotterdam on January 4 2025 with Willow Creek Pharma testing 299 samples.",
  "evidence": [
    "On 4 January 2025 Priya Nair from Willow Creek Pharma visited the Rotterdam facility.",
    "During the visit 299 samples were tested before the team closed the report."
  ]
}
```
~~~~

**trf_p01__P01** — 82 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 1 (CSR 0.8); Q 1.000; tags ['code_fence']

~~~~
```json
{
  "answer": "The Meridian project owned by Marcus Hale is on track with a deadline of 12 May 2025 and a budget of 733000 USD.",
  "evidence": [
    "Project: Meridian.",
    "Approved budget: 733000 USD."
  ]
}
```
~~~~

**cls_p01__P01** — 96 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.6); Q 1.000; tags ['code_fence', 'evidence_not_verbatim']

~~~~
```json
{
  "answer": "The news article belongs to the World category.",
  "evidence": [
    "Japan has confirmed that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda 24 within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
```
~~~~

**qa_p01__P01** — 83 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.6); Q 1.000; tags ['code_fence', 'evidence_not_verbatim']

~~~~
```json
{
  "answer": "Oil companies sought to boost oil supplies even in harsh areas like the Arctic.",
  "evidence": [
    "The embargo left oil companies searching for new ways to increase oil supplies even in rugged terrain such as the Arctic.",
    "Finding oil and developing new fields usually required five to ten years before significant production."
  ]
}
```
~~~~

**sum_p01__P01** — 91 tokens, finish `eos`, parse `fence`; FORMAT 0 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.6); Q 0.146; tags ['code_fence', 'evidence_not_verbatim']

~~~~
```json
{
  "answer": "Despite a win over Solihull Moors Nicholson was concerned about the team's attitude and need for improvement.",
  "evidence": [
    "Nicholson was unhappy with the attitude afterwards.",
    "But then that comes from a will to improve you've got to put the work in every day at training so that those kind of mistakes stop happening."
  ]
}
```
~~~~


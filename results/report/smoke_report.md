# Smoke-test report

Check only: smoke outputs never enter any analysis, and no smoke number enters the abstract (D04).

## Summary

| Run | Checks passed | Models native + R4 | Generation time (min) |
|---|---|---|---:|
| `smoke_20261004-1558_51d293c` | True | True | 0.30 |
| `smoke_20261004-1601_51d293c` | True | True | 0.30 |

A1 run-to-run determinism (byte-identical outputs per model): phi4mini yes (5/5), qwen25 yes (5/5), smollm2 yes (5/5)

## Run `smoke_20261004-1558_51d293c` (pass 1)

Bundle commit `51d293c`; GPU `NVIDIA A100-SXM4-80GB` (81920 MiB), driver 580.82.07, CUDA 13.0, cuDNN 92700, Python 3.13.15, torch 2.11.0+cu130, transformers 5.17.0, accelerate 1.15.0, tokenizers 0.23.2.

| Check | Result |
|---|---|
| torch >= 2.5 | yes |
| transformers == 5.17.0 | yes |
| GPU is an A100 | yes |
| import passed | yes |

| Model | Class | Native | R4 | Logits processors | Stopping criteria | Batches | Sessions | Generation s | Finish reasons |
|---|---|---|---|---|---|---:|---:|---:|---|
| phi4mini | `Phi3ForCausalLM` | yes | passed | [] | ['MaxLengthCriteria', 'EosTokenCriteria'] | 1/1 | 1 | 6.08 | {'eos': 5} |
| qwen25 | `Qwen2ForCausalLM` | yes | passed | [] | ['MaxLengthCriteria', 'EosTokenCriteria'] | 1/1 | 1 | 7.62 | {'eos': 5} |
| smollm2 | `LlamaForCausalLM` | yes | passed | [] | ['MaxLengthCriteria', 'EosTokenCriteria'] | 1/1 | 1 | 4.43 | {'eos': 5} |

### phi4mini

**ext_p01__P01** — 71 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.8); Q 1.000; tags ['evidence_not_verbatim']

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025. 299 samples were tested.",
  "evidence": [
    "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025",
    "299 samples were tested"
  ]
}
~~~~

**trf_p01__P01** — 61 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 1 (CSR 0.8); Q 1.000; tags []

~~~~
{
  "answer": "Project Meridian is on track with Marcus Hale as the owner, a deadline of 12 May 2025, and an approved budget of 733000 USD.",
  "evidence": [
    "Project: Meridian.",
    "Owner: Marcus Hale."
  ]
}
~~~~

**cls_p01__P01** — 64 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 1 (CSR 1.0); Q 1.000; tags []

~~~~
{
  "answer": "World",
  "evidence": [
    "Japan confirms captive in Iraq beheaded",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda, 24, within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
~~~~

**qa_p01__P01** — 73 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 1 (CSR 1.0); Q 1.000; tags []

~~~~
{
  "answer": "The oil crisis led oil companies to increase oil supplies in the Arctic.",
  "evidence": [
    "Finding oil and developing new fields usually required five to ten years before significant production.",
    "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic."
  ]
}
~~~~

**sum_p01__P01** — 108 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 0 (CSR 0.6); Q 0.182; tags ['evidence_not_verbatim']

~~~~
{
  "answer": "Torquay Gulls beat Solihull Moors in a first win in nine, but Nicholson criticized the team's attitude and defensive errors.",
  "evidence": [
    "Torquay Gulls beat Solihull Moors for a first win in nine, but Nicholson was unhappy with the attitude afterwards.",
    "He continued: \"Overall it was an OK half and then one terrible bit of defending and a goal and you throw away all the good work that you've done.\""
  ]
}
~~~~

### qwen25

**ext_p01__P01** — 89 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 1 (CSR 0.8); Q 1.000; tags []

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited Rotterdam facility on 4 January 2025, testing 299 samples.",
  "evidence": [
    "On 4 January 2025, Priya Nair from Willow Creek Pharma visited the Rotterdam facility.",
    "During the visit, 299 samples were tested before the team closed the report."
  ]
}
~~~~

**trf_p01__P01** — 76 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 1 (CSR 0.8); Q 1.000; tags []

~~~~
{
  "answer": "Meridian project, on track with Marcus Hale as owner, has an approved budget of 733000 USD and is due by 12 May 2025.",
  "evidence": [
    "Project: Meridian.",
    "Approved budget: 733000 USD."
  ]
}
~~~~

**cls_p01__P01** — 97 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 1 (CSR 0.8); Q 1.000; tags []

~~~~
{
  "answer": "This news article is about a hostage situation and beheading threat, classified under World category.",
  "evidence": [
    "Japan has confirmed that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda, 24, within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
~~~~

**qa_p01__P01** — 44 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 0 T4 1 VERBATIM 1 (CSR 0.8); Q 1.000; tags ['evidence_count_1']

~~~~
{
  "answer": "The Arctic",
  "evidence": [
    "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic."
  ]
}
~~~~

**sum_p01__P01** — 67 tokens, finish `eos`, parse `none`; FORMAT 0 LENGTH 0 CARDINALITY 0 T4 0 VERBATIM 0 (CSR 0.0); Q 0.000; tags ['invalid_json']

~~~~
answer: Torquay lost to Tranmere despite a strong start, with Nicholson criticizing team attitude.
evidence: ["Torquay have not beaten Tranmere since 1998, having lost the last three matches the two sides have played since Rovers were relegated to the National League in 2015."]
~~~~

### smollm2

**ext_p01__P01** — 89 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 0 T4 0 VERBATIM 1 (CSR 0.6); Q 1.000; tags ['evidence_count_3plus']

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025, and 299 samples were tested before the team closed the report.",
  "evidence": ["Priya Nair", "Willow Creek Pharma", "Rotterdam facility", "4 January 2025", "299 samples"]
}
~~~~

**trf_p01__P01** — 46 tokens, finish `eos`, parse `strict`; FORMAT 0 LENGTH 1 CARDINALITY 0 T4 0 VERBATIM 0 (CSR 0.2); Q 1.000; tags ['missing_evidence']

~~~~
{"answer": "Project: Meridian, owned by Marcus Hale, is on track with a deadline of 12 May 2025 and an approved budget of 733000 USD."}
~~~~

**cls_p01__P01** — 61 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 0 T4 1 VERBATIM 0 (CSR 0.6); Q 1.000; tags ['evidence_count_3plus', 'evidence_not_verbatim', 'evidence_duplicate']

~~~~
{
  "answer": "World",
  "evidence": ["Japan", "captive", "Iraq", "beheaded", "Japanese", "held captive", "Iraq", "armed group", "Iraq", "threatened", "pulls troops out of Iraq"]
}
~~~~

**qa_p01__P01** — 16 tokens, finish `eos`, parse `none`; FORMAT 0 LENGTH 0 CARDINALITY 0 T4 0 VERBATIM 0 (CSR 0.0); Q 0.000; tags ['invalid_json']

~~~~
The oil crisis caused oil companies to increase oil supplies in the Arctic area.
~~~~

**sum_p01__P01** — 44 tokens, finish `eos`, parse `none`; FORMAT 0 LENGTH 0 CARDINALITY 0 T4 0 VERBATIM 0 (CSR 0.0); Q 0.000; tags ['invalid_json']

~~~~
"Nicholson criticized the team's attitude after a 1-0 win over Solihull Moors, stating that they should focus on improving and not make the same mistakes they did in the previous matches."
~~~~

## Run `smoke_20261004-1601_51d293c` (pass 2, replicate of `smoke_20261004-1558_51d293c`)

Bundle commit `51d293c`; GPU `NVIDIA A100-SXM4-80GB` (81920 MiB), driver 580.82.07, CUDA 13.0, cuDNN 92700, Python 3.13.15, torch 2.11.0+cu130, transformers 5.17.0, accelerate 1.15.0, tokenizers 0.23.2.

| Check | Result |
|---|---|
| torch >= 2.5 | yes |
| transformers == 5.17.0 | yes |
| GPU is an A100 | yes |
| import passed | yes |

| Model | Class | Native | R4 | Logits processors | Stopping criteria | Batches | Sessions | Generation s | Finish reasons |
|---|---|---|---|---|---|---:|---:|---:|---|
| phi4mini | `Phi3ForCausalLM` | yes | passed | [] | ['MaxLengthCriteria', 'EosTokenCriteria'] | 1/1 | 1 | 6.03 | {'eos': 5} |
| qwen25 | `Qwen2ForCausalLM` | yes | passed | [] | ['MaxLengthCriteria', 'EosTokenCriteria'] | 1/1 | 1 | 7.74 | {'eos': 5} |
| smollm2 | `LlamaForCausalLM` | yes | passed | [] | ['MaxLengthCriteria', 'EosTokenCriteria'] | 1/1 | 1 | 4.14 | {'eos': 5} |

### phi4mini

**ext_p01__P01** — 71 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 0 (CSR 0.8); Q 1.000; tags ['evidence_not_verbatim']

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025. 299 samples were tested.",
  "evidence": [
    "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025",
    "299 samples were tested"
  ]
}
~~~~

**trf_p01__P01** — 61 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 1 (CSR 0.8); Q 1.000; tags []

~~~~
{
  "answer": "Project Meridian is on track with Marcus Hale as the owner, a deadline of 12 May 2025, and an approved budget of 733000 USD.",
  "evidence": [
    "Project: Meridian.",
    "Owner: Marcus Hale."
  ]
}
~~~~

**cls_p01__P01** — 64 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 1 (CSR 1.0); Q 1.000; tags []

~~~~
{
  "answer": "World",
  "evidence": [
    "Japan confirms captive in Iraq beheaded",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda, 24, within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
~~~~

**qa_p01__P01** — 73 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 1 VERBATIM 1 (CSR 1.0); Q 1.000; tags []

~~~~
{
  "answer": "The oil crisis led oil companies to increase oil supplies in the Arctic.",
  "evidence": [
    "Finding oil and developing new fields usually required five to ten years before significant production.",
    "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic."
  ]
}
~~~~

**sum_p01__P01** — 108 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 0 (CSR 0.6); Q 0.182; tags ['evidence_not_verbatim']

~~~~
{
  "answer": "Torquay Gulls beat Solihull Moors in a first win in nine, but Nicholson criticized the team's attitude and defensive errors.",
  "evidence": [
    "Torquay Gulls beat Solihull Moors for a first win in nine, but Nicholson was unhappy with the attitude afterwards.",
    "He continued: \"Overall it was an OK half and then one terrible bit of defending and a goal and you throw away all the good work that you've done.\""
  ]
}
~~~~

### qwen25

**ext_p01__P01** — 89 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 1 (CSR 0.8); Q 1.000; tags []

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited Rotterdam facility on 4 January 2025, testing 299 samples.",
  "evidence": [
    "On 4 January 2025, Priya Nair from Willow Creek Pharma visited the Rotterdam facility.",
    "During the visit, 299 samples were tested before the team closed the report."
  ]
}
~~~~

**trf_p01__P01** — 76 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 1 (CSR 0.8); Q 1.000; tags []

~~~~
{
  "answer": "Meridian project, on track with Marcus Hale as owner, has an approved budget of 733000 USD and is due by 12 May 2025.",
  "evidence": [
    "Project: Meridian.",
    "Approved budget: 733000 USD."
  ]
}
~~~~

**cls_p01__P01** — 97 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 1 T4 0 VERBATIM 1 (CSR 0.8); Q 1.000; tags []

~~~~
{
  "answer": "This news article is about a hostage situation and beheading threat, classified under World category.",
  "evidence": [
    "Japan has confirmed that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda, 24, within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
~~~~

**qa_p01__P01** — 44 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 0 T4 1 VERBATIM 1 (CSR 0.8); Q 1.000; tags ['evidence_count_1']

~~~~
{
  "answer": "The Arctic",
  "evidence": [
    "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic."
  ]
}
~~~~

**sum_p01__P01** — 67 tokens, finish `eos`, parse `none`; FORMAT 0 LENGTH 0 CARDINALITY 0 T4 0 VERBATIM 0 (CSR 0.0); Q 0.000; tags ['invalid_json']

~~~~
answer: Torquay lost to Tranmere despite a strong start, with Nicholson criticizing team attitude.
evidence: ["Torquay have not beaten Tranmere since 1998, having lost the last three matches the two sides have played since Rovers were relegated to the National League in 2015."]
~~~~

### smollm2

**ext_p01__P01** — 89 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 0 T4 0 VERBATIM 1 (CSR 0.6); Q 1.000; tags ['evidence_count_3plus']

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025, and 299 samples were tested before the team closed the report.",
  "evidence": ["Priya Nair", "Willow Creek Pharma", "Rotterdam facility", "4 January 2025", "299 samples"]
}
~~~~

**trf_p01__P01** — 46 tokens, finish `eos`, parse `strict`; FORMAT 0 LENGTH 1 CARDINALITY 0 T4 0 VERBATIM 0 (CSR 0.2); Q 1.000; tags ['missing_evidence']

~~~~
{"answer": "Project: Meridian, owned by Marcus Hale, is on track with a deadline of 12 May 2025 and an approved budget of 733000 USD."}
~~~~

**cls_p01__P01** — 61 tokens, finish `eos`, parse `strict`; FORMAT 1 LENGTH 1 CARDINALITY 0 T4 1 VERBATIM 0 (CSR 0.6); Q 1.000; tags ['evidence_count_3plus', 'evidence_not_verbatim', 'evidence_duplicate']

~~~~
{
  "answer": "World",
  "evidence": ["Japan", "captive", "Iraq", "beheaded", "Japanese", "held captive", "Iraq", "armed group", "Iraq", "threatened", "pulls troops out of Iraq"]
}
~~~~

**qa_p01__P01** — 16 tokens, finish `eos`, parse `none`; FORMAT 0 LENGTH 0 CARDINALITY 0 T4 0 VERBATIM 0 (CSR 0.0); Q 0.000; tags ['invalid_json']

~~~~
The oil crisis caused oil companies to increase oil supplies in the Arctic area.
~~~~

**sum_p01__P01** — 44 tokens, finish `eos`, parse `none`; FORMAT 0 LENGTH 0 CARDINALITY 0 T4 0 VERBATIM 0 (CSR 0.0); Q 0.000; tags ['invalid_json']

~~~~
"Nicholson criticized the team's attitude after a 1-0 win over Solihull Moors, stating that they should focus on improving and not make the same mistakes they did in the previous matches."
~~~~


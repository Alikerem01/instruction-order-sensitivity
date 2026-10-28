# Audit sample — pilot run `pilot_gemma_20261005-1529_ccc7919`

2 outputs per model × family stratum, drawn with random.Random(20261003) from the unique pilot texts (strata in sorted order). For each: the raw output, the parsed object and every evaluator decision.

## 1. gemma4e4b · `qa_p01__P02` (F1_QA)

Raw output:

~~~~
```json
{
  "answer": "Oil companies sought new methods to boost oil supplies even in harsh areas like the Arctic",
  "evidence": [
    "The embargo left oil companies searching for new ways to increase oil supplies even in rugged terrain such as the Arctic"
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "Oil companies sought new methods to boost oil supplies even in harsh areas like the Arctic",
 "evidence": [
  "The embargo left oil companies searching for new ways to increase oil supplies even in rugged terrain such as the Arctic"
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P02",
 "positions": {
  "format": 3,
  "length": 1,
  "cardinality": 5,
  "t4": 2,
  "verbatim": 4
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.4,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": 0.125,
 "q_answer_available": 1,
 "quality_detail": {
  "containment_char": 1
 },
 "error_tags": [
  "code_fence",
  "evidence_count_1",
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 2. gemma4e4b · `qa_p01__P01` (F1_QA)

Raw output:

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

Parsed object (rule `fence`):

~~~~
{
 "answer": "Oil companies sought to boost oil supplies even in harsh areas like the Arctic.",
 "evidence": [
  "The embargo left oil companies searching for new ways to increase oil supplies even in rugged terrain such as the Arctic.",
  "Finding oil and developing new fields usually required five to ten years before significant production."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P01",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.6,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": 0.14285714285714288,
 "q_answer_available": 1,
 "quality_detail": {
  "containment_char": 1
 },
 "error_tags": [
  "code_fence",
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 3. gemma4e4b · `cls_p02__P03` (F2_CLASSIFICATION)

Raw output:

~~~~
```json
{
  "answer": "The article belongs to the Business category because it discusses corporate leadership and partnership dissolution.",
  "evidence": [
    "When Walt Disney Co. chief executive Michael D. Eisner and Disney President Michael S. Ovitz appeared on \"Larry King Live\" on Sept. 30 1996 their corporate partnership was dissolving into an acrimonious disaster."
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "The article belongs to the Business category because it discusses corporate leadership and partnership dissolution.",
 "evidence": [
  "When Walt Disney Co. chief executive Michael D. Eisner and Disney President Michael S. Ovitz appeared on \"Larry King Live\" on Sept. 30 1996 their corporate partnership was dissolving into an acrimonious disaster."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P03",
 "positions": {
  "format": 5,
  "length": 3,
  "cardinality": 4,
  "t4": 1,
  "verbatim": 2
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.4,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": null,
 "q_answer_available": 1,
 "quality_detail": {
  "label_prediction": "Business",
  "label_status": "single",
  "labels_found": [
   "Business"
  ]
 },
 "error_tags": [
  "code_fence",
  "evidence_count_1",
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 4. gemma4e4b · `cls_p01__P10` (F2_CLASSIFICATION)

Raw output:

~~~~
```json
{
  "answer": "The article belongs to the World category because it discusses an international incident involving Japan and Iraq.",
  "evidence": [
    "Japan has confirmed that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda 24 within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "The article belongs to the World category because it discusses an international incident involving Japan and Iraq.",
 "evidence": [
  "Japan has confirmed that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
  "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda 24 within 48-hours unless Japan pulled its troops out of Iraq."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P10",
 "positions": {
  "format": 4,
  "length": 2,
  "cardinality": 5,
  "t4": 1,
  "verbatim": 3
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.6,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": null,
 "q_answer_available": 1,
 "quality_detail": {
  "label_prediction": "World",
  "label_status": "single",
  "labels_found": [
   "World"
  ]
 },
 "error_tags": [
  "code_fence",
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 5. gemma4e4b · `sum_p02__V04` (F3_SUMMARIZATION)

Raw output:

~~~~
```json
{
  "answer": "A detailed fossil reconstruction of Calvapilosa shows an ancient slug-like mollusc ancestor from Morocco",
  "evidence": [
    "Researchers discovered it after looking back at some fossils found in the late 2000s in Morocco North Africa.",
    "Jakob Vinther who was the lead researcher on the project said \"This discovery brings a neat solution to how the ancestor of all molluscs may have looked.\""
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "A detailed fossil reconstruction of Calvapilosa shows an ancient slug-like mollusc ancestor from Morocco",
 "evidence": [
  "Researchers discovered it after looking back at some fossils found in the late 2000s in Morocco North Africa.",
  "Jakob Vinther who was the lead researcher on the project said \"This discovery brings a neat solution to how the ancestor of all molluscs may have looked.\""
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V04",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.6,
 "pcr": 0,
 "q_primary": 0.24,
 "q_secondary": null,
 "q_answer_available": 1,
 "quality_detail": {},
 "error_tags": [
  "code_fence",
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 6. gemma4e4b · `sum_p01__V10` (F3_SUMMARIZATION)

Raw output:

~~~~
```json
{
  "answer": "Despite a win over Solihull Moors Nicholson was concerned about the team's attitude and defensive errors.",
  "evidence": [
    "Nicholson was unhappy with the attitude afterwards.",
    "Overall it was an OK half and then one terrible bit of defending and a goal and you throw away all the good work that you've done."
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "Despite a win over Solihull Moors Nicholson was concerned about the team's attitude and defensive errors.",
 "evidence": [
  "Nicholson was unhappy with the attitude afterwards.",
  "Overall it was an OK half and then one terrible bit of defending and a goal and you throw away all the good work that you've done."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V10",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 0.8,
 "pcr": 0,
 "q_primary": 0.15,
 "q_secondary": null,
 "q_answer_available": 1,
 "quality_detail": {},
 "error_tags": [
  "code_fence"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 7. gemma4e4b · `ext_p02__V06` (F4_EXTRACTION)

Raw output:

~~~~
```json
{
  "answer": "Tomas Novak of Cedar Grove Health signed 48 contracts in Tampere on October 15 2025.",
  "evidence": [
    "Tomas Novak of Cedar Grove Health reported that 48 contracts were signed at the Tampere site on 15 October 2025."
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "Tomas Novak of Cedar Grove Health signed 48 contracts in Tampere on October 15 2025.",
 "evidence": [
  "Tomas Novak of Cedar Grove Health reported that 48 contracts were signed at the Tampere site on 15 October 2025."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V06",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 0.6,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": 1.0,
 "q_answer_available": 1,
 "quality_detail": {
  "fields_matched": {
   "person": true,
   "organization": true,
   "city": true,
   "date": true,
   "amount": true
  }
 },
 "error_tags": [
  "code_fence",
  "evidence_count_1"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 8. gemma4e4b · `ext_p01__P07` (F4_EXTRACTION)

Raw output:

~~~~
```json
{
  "answer": "Priya Nair from Willow Creek Pharma visited Rotterdam on January 4 2025 and 299 samples were tested.",
  "evidence": [
    "On 4 January 2025 Priya Nair from Willow Creek Pharma visited the Rotterdam facility.",
    "During the visit 299 samples were tested before the team closed the report."
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "Priya Nair from Willow Creek Pharma visited Rotterdam on January 4 2025 and 299 samples were tested.",
 "evidence": [
  "On 4 January 2025 Priya Nair from Willow Creek Pharma visited the Rotterdam facility.",
  "During the visit 299 samples were tested before the team closed the report."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P07",
 "positions": {
  "format": 3,
  "length": 5,
  "cardinality": 1,
  "t4": 4,
  "verbatim": 2
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.6,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": 1.0,
 "q_answer_available": 1,
 "quality_detail": {
  "fields_matched": {
   "person": true,
   "organization": true,
   "city": true,
   "date": true,
   "amount": true
  }
 },
 "error_tags": [
  "code_fence",
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 9. gemma4e4b · `trf_p02__P06` (F5_TRANSFORMATION)

Raw output:

~~~~
```json
{
  "answer": "The Nimbus project owned by Diego Alvarez is on track with an approved budget of 840500 USD and a deadline of 21 July 2027.",
  "evidence": [
    "Project: Nimbus.",
    "Owner: Diego Alvarez."
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "The Nimbus project owned by Diego Alvarez is on track with an approved budget of 840500 USD and a deadline of 21 July 2027.",
 "evidence": [
  "Project: Nimbus.",
  "Owner: Diego Alvarez."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P06",
 "positions": {
  "format": 5,
  "length": 4,
  "cardinality": 3,
  "t4": 2,
  "verbatim": 1
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 0,
 "csr": 0.8,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": 1.0,
 "q_answer_available": 1,
 "quality_detail": {
  "fields_matched": {
   "project": true,
   "owner": true,
   "status": true,
   "deadline": true,
   "budget": true
  }
 },
 "error_tags": [
  "code_fence"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 10. gemma4e4b · `trf_p02__V06` (F5_TRANSFORMATION)

Raw output:

~~~~
```json
{
  "answer": "The Nimbus project owned by Diego Alvarez is on track with a deadline of 21 July 2027 and an approved budget of 840500 USD.",
  "evidence": [
    "Project: Nimbus.",
    "Approved budget: 840500 USD."
  ]
}
```
~~~~

Parsed object (rule `fence`):

~~~~
{
 "answer": "The Nimbus project owned by Diego Alvarez is on track with a deadline of 21 July 2027 and an approved budget of 840500 USD.",
 "evidence": [
  "Project: Nimbus.",
  "Approved budget: 840500 USD."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V06",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 0,
 "parse_rule": "fence",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 0,
 "csr": 0.8,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": 1.0,
 "q_answer_available": 1,
 "quality_detail": {
  "fields_matched": {
   "project": true,
   "owner": true,
   "status": true,
   "deadline": true,
   "budget": true
  }
 },
 "error_tags": [
  "code_fence"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 0,
 "cascade_length": 0,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.0,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~


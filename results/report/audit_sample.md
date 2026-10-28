# Audit sample — pilot run `pilot_20261004-2020_d9e9fc2`

2 outputs per model × family stratum, drawn with random.Random(20261003) from the unique pilot texts (strata in sorted order). For each: the raw output, the parsed object and every evaluator decision.

## 1. phi4mini · `qa_p01__P02` (F1_QA)

Raw output:

~~~~
{
  "answer": "The oil crisis led oil companies to increase oil supplies in the Arctic.",
  "evidence": [
    "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic.",
    "Finding oil and developing new fields usually required five to ten years before significant production."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "The oil crisis led oil companies to increase oil supplies in the Arctic.",
 "evidence": [
  "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic.",
  "Finding oil and developing new fields usually required five to ten years before significant production."
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 1.0,
 "pcr": 1,
 "q_primary": 1.0,
 "q_secondary": 0.16666666666666669,
 "q_answer_available": 1,
 "quality_detail": {
  "containment_char": 1
 },
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 1.0,
 "cascade_pcr": 1,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 2. phi4mini · `qa_p01__P01` (F1_QA)

Raw output:

~~~~
{
  "answer": "The oil crisis led oil companies to increase oil supplies in the Arctic.",
  "evidence": [
    "Finding oil and developing new fields usually required five to ten years before significant production.",
    "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "The oil crisis led oil companies to increase oil supplies in the Arctic.",
 "evidence": [
  "Finding oil and developing new fields usually required five to ten years before significant production.",
  "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic."
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 1.0,
 "pcr": 1,
 "q_primary": 1.0,
 "q_secondary": 0.16666666666666669,
 "q_answer_available": 1,
 "quality_detail": {
  "containment_char": 1
 },
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 1.0,
 "cascade_pcr": 1,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 3. phi4mini · `cls_p02__P03` (F2_CLASSIFICATION)

Raw output:

~~~~
{
  "answer": "Business",
  "evidence": [
    "Eisner Continues Defense of Hiring, Firing GEORGETOWN, Del. Nov. 18 --",
    "When Walt Disney Co. chief executive Michael D. Eisner and Disney President Michael S. Ovitz appeared on \"Larry King Live\" on Sept. 30, 1996, their corporate partnership was dissolving into an acrimonious disaster."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Business",
 "evidence": [
  "Eisner Continues Defense of Hiring, Firing GEORGETOWN, Del. Nov. 18 --",
  "When Walt Disney Co. chief executive Michael D. Eisner and Disney President Michael S. Ovitz appeared on \"Larry King Live\" on Sept. 30, 1996, their corporate partnership was dissolving into an acrimonious disaster."
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.8,
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
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 0,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 4. phi4mini · `cls_p01__P10` (F2_CLASSIFICATION)

Raw output:

~~~~
{
  "answer": "World",
  "evidence": [
    "Japan has confirmed that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda, 24, within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "World",
 "evidence": [
  "Japan has confirmed that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
  "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda, 24, within 48-hours unless Japan pulled its troops out of Iraq."
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 1.0,
 "pcr": 1,
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
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 1.0,
 "cascade_pcr": 1,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 5. phi4mini · `sum_p02__V04` (F3_SUMMARIZATION)

Raw output:

~~~~
{
  "answer": "Researchers discovered a four-inch ancient mollusc relative, Calvapilosa, with a detailed reconstruction from fossils found in Morocco.",
  "evidence": [
    "Researchers discovered it after looking back at some fossils found in the late 2000s in Morocco, North Africa.",
    "Two of the fossils were in such good condition that the team were able to make this amazingly detailed reconstruction."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Researchers discovered a four-inch ancient mollusc relative, Calvapilosa, with a detailed reconstruction from fossils found in Morocco.",
 "evidence": [
  "Researchers discovered it after looking back at some fossils found in the late 2000s in Morocco, North Africa.",
  "Two of the fossils were in such good condition that the team were able to make this amazingly detailed reconstruction."
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 0,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 0.8,
 "pcr": 0,
 "q_primary": 0.14285714285714285,
 "q_secondary": null,
 "q_answer_available": 1,
 "quality_detail": {},
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 0,
 "cascade_verbatim": 1,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 6. phi4mini · `sum_p01__V10` (F3_SUMMARIZATION)

Raw output:

~~~~
{
  "answer": "Torquay Gulls beat Solihull Moors in a first win in nine, but Nicholson criticized the team's attitude and defensive errors.",
  "evidence": [
    "Torquay Gulls beat Solihull Moors for a first win in nine, but Nicholson was unhappy with the attitude afterwards.",
    "He continued: \"Overall it was an OK half and then one terrible bit of defending and a goal and you throw away all the good work that you've done.\""
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Torquay Gulls beat Solihull Moors in a first win in nine, but Nicholson criticized the team's attitude and defensive errors.",
 "evidence": [
  "Torquay Gulls beat Solihull Moors for a first win in nine, but Nicholson was unhappy with the attitude afterwards.",
  "He continued: \"Overall it was an OK half and then one terrible bit of defending and a goal and you throw away all the good work that you've done.\""
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.6,
 "pcr": 0,
 "q_primary": 0.1818181818181818,
 "q_secondary": null,
 "q_answer_available": 1,
 "quality_detail": {},
 "error_tags": [
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 0,
 "cascade_verbatim": 0,
 "cascade_csr": 0.6,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 7. phi4mini · `ext_p02__V06` (F4_EXTRACTION)

Raw output:

~~~~
{
  "answer": "Tomas Novak of Cedar Grove Health signed 48 contracts in Tampere on 15 October 2025.",
  "evidence": [
    "Tomas Novak of Cedar Grove Health",
    "48 contracts were signed at the Tampere site on 15 October 2025"
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Tomas Novak of Cedar Grove Health signed 48 contracts in Tampere on 15 October 2025.",
 "evidence": [
  "Tomas Novak of Cedar Grove Health",
  "48 contracts were signed at the Tampere site on 15 October 2025"
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 1.0,
 "pcr": 1,
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
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 1.0,
 "cascade_pcr": 1,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 8. phi4mini · `ext_p01__P07` (F4_EXTRACTION)

Raw output:

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025. 299 samples were tested.",
  "evidence": [
    "Priya Nair from Willow Creek Pharma visited the Rotterdam facility",
    "299 samples were tested"
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025. 299 samples were tested.",
 "evidence": [
  "Priya Nair from Willow Creek Pharma visited the Rotterdam facility",
  "299 samples were tested"
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 1.0,
 "pcr": 1,
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
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 1.0,
 "cascade_pcr": 1,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 9. phi4mini · `trf_p02__P06` (F5_TRANSFORMATION)

Raw output:

~~~~
{
  "answer": "Project Nimbus owned by Diego Alvarez is on track with a deadline of 21 July 2027 and an approved budget of 840500 USD",
  "evidence": [
    "Project: Nimbus",
    "Owner: Diego Alvarez"
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Project Nimbus owned by Diego Alvarez is on track with a deadline of 21 July 2027 and an approved budget of 840500 USD",
 "evidence": [
  "Project: Nimbus",
  "Owner: Diego Alvarez"
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 0,
 "csr": 1.0,
 "pcr": 1,
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
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 1.0,
 "cascade_pcr": 1,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 10. phi4mini · `trf_p02__V06` (F5_TRANSFORMATION)

Raw output:

~~~~
{
  "answer": "Project Nimbus is on track with a deadline of 21 July 2027 and an approved budget of 840500 USD.",
  "evidence": [
    "Project: Nimbus",
    "Owner: Diego Alvarez"
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Project Nimbus is on track with a deadline of 21 July 2027 and an approved budget of 840500 USD.",
 "evidence": [
  "Project: Nimbus",
  "Owner: Diego Alvarez"
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 0,
 "csr": 1.0,
 "pcr": 1,
 "q_primary": 0.8,
 "q_secondary": 0.0,
 "q_answer_available": 1,
 "quality_detail": {
  "fields_matched": {
   "project": true,
   "owner": false,
   "status": true,
   "deadline": true,
   "budget": true
  }
 },
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 1.0,
 "cascade_pcr": 1,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 11. qwen25 · `qa_p02__P01` (F1_QA)

Raw output:

~~~~
{
  "answer": "Robert Boyle proved that air is necessary for combustion.",
  "evidence": [
    "In the late 17th century, Robert Boyle proved that air is necessary for combustion."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Robert Boyle proved that air is necessary for combustion.",
 "evidence": [
  "In the late 17th century, Robert Boyle proved that air is necessary for combustion."
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 0.8,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": 0.3636363636363636,
 "q_answer_available": 1,
 "quality_detail": {
  "containment_char": 1
 },
 "error_tags": [
  "evidence_count_1"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 0,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 12. qwen25 · `qa_p01__P04` (F1_QA)

Raw output:

~~~~
{
  "answer": "oil companies increased supplies in the Arctic",
  "evidence": "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic."
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "oil companies increased supplies in the Arctic",
 "evidence": "The embargo left oil companies searching for new ways to increase oil supplies, even in rugged terrain such as the Arctic."
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P04",
 "positions": {
  "format": 4,
  "length": 5,
  "cardinality": 2,
  "t4": 3,
  "verbatim": 1
 },
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.6,
 "pcr": 0,
 "q_primary": 1.0,
 "q_secondary": 0.2857142857142857,
 "q_answer_available": 1,
 "quality_detail": {
  "containment_char": 1
 },
 "error_tags": [
  "evidence_not_list"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 0,
 "cascade_t4": 1,
 "cascade_verbatim": 0,
 "cascade_csr": 0.6,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 13. qwen25 · `cls_p01__P02` (F2_CLASSIFICATION)

Raw output:

~~~~
{
  "answer": "This news article is about World events involving a hostage situation.",
  "evidence": [
    "Japan confirms that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
    "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda, 24, within 48-hours unless Japan pulled its troops out of Iraq."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "This news article is about World events involving a hostage situation.",
 "evidence": [
  "Japan confirms that the headless body found in Baghdad on Saturday is of the Japanese being held captive in Iraq.",
  "An armed group in Iraq had on Tuesday threatened to behead Shosei Koda, 24, within 48-hours unless Japan pulled its troops out of Iraq."
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.8,
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
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 0,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 14. qwen25 · `cls_p02__V03` (F2_CLASSIFICATION)

Raw output:

~~~~
{
  "answer": "This news article is about business as it discusses corporate partnerships and executive firings at Walt Disney Company.",
  "evidence": [
    "Eisner Continues Defense of Hiring, Firing",
    "Walt Disney Co. chief executive Michael D. Eisner and Disney President Michael S. Ovitz appeared on 'Larry King Live' on Sept. 30, 1996"
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "This news article is about business as it discusses corporate partnerships and executive firings at Walt Disney Company.",
 "evidence": [
  "Eisner Continues Defense of Hiring, Firing",
  "Walt Disney Co. chief executive Michael D. Eisner and Disney President Michael S. Ovitz appeared on 'Larry King Live' on Sept. 30, 1996"
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V03",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.8,
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
  "evidence_not_verbatim"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 0,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 15. qwen25 · `sum_p02__P06` (F3_SUMMARIZATION)

Raw output:

~~~~
answer: Ancient mollusc-like creature, about 4 inches long, with a protective shell, was discovered in Morocco.
evidence: [{"text": "Researchers discovered it after looking back at some fossils found in the late 2000s in Morocco, North Africa. Two of the fossils were in such good condition that the team were able to make this amazingly detailed reconstruction. You can clearly see its small mouth filled with hundreds of teeth and the prickly spines which cover its body. This slug like creature also had a built in, helmet like, shell to keep it safe from predators."}, {"text": "Molluscs first appeared on earth around 520 million years ago, Calvapilosa is an ancient relative of modern molluscs. A mollusc is a type of animal that doesn't have a spine, there are lots of different kinds including slugs, snails, oysters and squid. Jakob Vinther who was the lead researcher on the project said \"This discovery brings a neat solution to how the ancestor of all molluscs may have looked.\""}}]
~~~~

Parsed object (rule `first_object`):

~~~~
{
 "text": "Researchers discovered it after looking back at some fossils found in the late 2000s in Morocco, North Africa. Two of the fossils were in such good condition that the team were able to make this amazingly detailed reconstruction. You can clearly see its small mouth filled with hundreds of teeth and the prickly spines which cover its body. This slug like creature also had a built in, helmet like, shell to keep it safe from predators."
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
 "parse_rule": "first_object",
 "evaluable": 1,
 "length": 0,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.0,
 "pcr": 0,
 "q_primary": 0.0,
 "q_secondary": null,
 "q_answer_available": 0,
 "quality_detail": {},
 "error_tags": [
  "leading_text",
  "trailing_text",
  "extra_keys",
  "missing_answer",
  "missing_evidence"
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

## 16. qwen25 · `sum_p01__P08` (F3_SUMMARIZATION)

Raw output:

~~~~
answer: Torquay lost to Tranmere despite a strong start, with Nicholson criticizing team attitude.
evidence: "Torquay have not beaten Tranmere since 1998, having lost the last three matches the two sides have played since Rovers were relegated to the National League in 2015."
~~~~

Parsed object (rule `none`):

~~~~
(none)
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P08",
 "positions": {
  "format": 1,
  "length": 3,
  "cardinality": 2,
  "t4": 5,
  "verbatim": 4
 },
 "format_strict": 0,
 "parse_rule": "none",
 "evaluable": 0,
 "length": 0,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.0,
 "pcr": 0,
 "q_primary": 0.0,
 "q_secondary": null,
 "q_answer_available": 0,
 "quality_detail": {},
 "error_tags": [
  "invalid_json"
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

## 17. qwen25 · `ext_p01__P09` (F4_EXTRACTION)

Raw output:

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited Rotterdam facility on 4 January 2025, 299 samples were tested.",
  "evidence": [
    "On 4 January 2025, Priya Nair from Willow Creek Pharma visited the Rotterdam facility.",
    "During the visit, 299 samples were tested"
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Priya Nair from Willow Creek Pharma visited Rotterdam facility on 4 January 2025, 299 samples were tested.",
 "evidence": [
  "On 4 January 2025, Priya Nair from Willow Creek Pharma visited the Rotterdam facility.",
  "During the visit, 299 samples were tested"
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P09",
 "positions": {
  "format": 2,
  "length": 1,
  "cardinality": 4,
  "t4": 3,
  "verbatim": 5
 },
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 0,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 0.8,
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
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 0,
 "cascade_verbatim": 1,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 18. qwen25 · `ext_p02__V05` (F4_EXTRACTION)

Raw output:

~~~~
{
  "answer": "Tomas Novak from Cedar Grove Health signed 48 contracts in Tampere on 15 October 2025",
  "evidence": [
    "Tomas Novak of Cedar Grove Health",
    "15 October 2025"
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Tomas Novak from Cedar Grove Health signed 48 contracts in Tampere on 15 October 2025",
 "evidence": [
  "Tomas Novak of Cedar Grove Health",
  "15 October 2025"
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V05",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 1,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
 "verbatim_min3": 1,
 "csr": 1.0,
 "pcr": 1,
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
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 1.0,
 "cascade_pcr": 1,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 19. qwen25 · `trf_p01__P04` (F5_TRANSFORMATION)

Raw output:

~~~~
{
  "answer": "Meridian project, on track with Marcus Hale as owner, has an approved budget of 733000 USD and is due by 12 May 2025.",
  "evidence": [
    "Project: Meridian.",
    "Approved budget: 733000 USD."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Meridian project, on track with Marcus Hale as owner, has an approved budget of 733000 USD and is due by 12 May 2025.",
 "evidence": [
  "Project: Meridian.",
  "Approved budget: 733000 USD."
 ]
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "order",
 "condition_id": "P04",
 "positions": {
  "format": 4,
  "length": 5,
  "cardinality": 2,
  "t4": 3,
  "verbatim": 1
 },
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 0,
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
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 0,
 "cascade_verbatim": 1,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 20. qwen25 · `trf_p01__V06` (F5_TRANSFORMATION)

Raw output:

~~~~
{
  "answer": "Meridian project, on track with Marcus Hale as owner, has an approved budget of 733000 USD and is due by 12 May 2025.",
  "evidence": [
    "Project: Meridian.",
    "Owner: Marcus Hale."
  ]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Meridian project, on track with Marcus Hale as owner, has an approved budget of 733000 USD and is due by 12 May 2025.",
 "evidence": [
  "Project: Meridian.",
  "Owner: Marcus Hale."
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 1,
 "t4": 0,
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
 "error_tags": [],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 1,
 "cascade_t4": 0,
 "cascade_verbatim": 1,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 21. smollm2 · `qa_p02__V08` (F1_QA)

Raw output:

~~~~
Answer: Robert Boyle proved that air is necessary for combustion.
~~~~

Parsed object (rule `none`):

~~~~
(none)
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V08",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 0,
 "parse_rule": "none",
 "evaluable": 0,
 "length": 0,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.0,
 "pcr": 0,
 "q_primary": 0.0,
 "q_secondary": 0.0,
 "q_answer_available": 0,
 "quality_detail": {},
 "error_tags": [
  "invalid_json"
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

## 22. smollm2 · `qa_p02__V04` (F1_QA)

Raw output:

~~~~
Answer: Robert Boyle proved that air is necessary for combustion.
~~~~

Parsed object (rule `none`):

~~~~
(none)
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
 "parse_rule": "none",
 "evaluable": 0,
 "length": 0,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.0,
 "pcr": 0,
 "q_primary": 0.0,
 "q_secondary": 0.0,
 "q_answer_available": 0,
 "quality_detail": {},
 "error_tags": [
  "invalid_json"
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

## 23. smollm2 · `cls_p01__P10` (F2_CLASSIFICATION)

Raw output:

~~~~
{
  "answer": "World"
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "World"
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
 "parse_rule": "strict",
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
  "label_prediction": "World",
  "label_status": "single",
  "labels_found": [
   "World"
  ]
 },
 "error_tags": [
  "missing_evidence"
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

## 24. smollm2 · `cls_p01__V06` (F2_CLASSIFICATION)

Raw output:

~~~~
{
  "answer": "World",
  "evidence": ["Japan", "captive", "Iraq", "beheaded", "Japanese", "held captive", "Iraq", "armed group", "Iraq", "threatened", "pulls troops out of Iraq"]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "World",
 "evidence": [
  "Japan",
  "captive",
  "Iraq",
  "beheaded",
  "Japanese",
  "held captive",
  "Iraq",
  "armed group",
  "Iraq",
  "threatened",
  "pulls troops out of Iraq"
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
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
  "evidence_count_3plus",
  "evidence_not_verbatim",
  "evidence_duplicate"
 ],
 "evidence_duplicate": 1,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 0,
 "cascade_t4": 1,
 "cascade_verbatim": 0,
 "cascade_csr": 0.6,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 25. smollm2 · `sum_p02__P01` (F3_SUMMARIZATION)

Raw output:

~~~~
"Researchers discovered a detailed reconstruction of a four-inch-long, ancient mollusc-like creature with a helmet-like shell and spines, found in Morocco in the late 2000s, and believe it survived by eating algae off rocks."
~~~~

Parsed object (rule `none`):

~~~~
(none)
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
 "parse_rule": "none",
 "evaluable": 0,
 "length": 0,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.0,
 "pcr": 0,
 "q_primary": 0.0,
 "q_secondary": null,
 "q_answer_available": 0,
 "quality_detail": {},
 "error_tags": [
  "invalid_json"
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

## 26. smollm2 · `sum_p02__P03` (F3_SUMMARIZATION)

Raw output:

~~~~
Researchers discovered a detailed reconstruction of a four-inch-long, ancient mollusc-like creature with a helmet-like shell and hundreds of teeth, found in Morocco in the late 2000s, and named Calvapilosa.
~~~~

Parsed object (rule `none`):

~~~~
(none)
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
 "parse_rule": "none",
 "evaluable": 0,
 "length": 0,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.0,
 "pcr": 0,
 "q_primary": 0.0,
 "q_secondary": null,
 "q_answer_available": 0,
 "quality_detail": {},
 "error_tags": [
  "invalid_json"
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

## 27. smollm2 · `ext_p02__P03` (F4_EXTRACTION)

Raw output:

~~~~
{
  "answer": "48 contracts were signed at the Tampere site on 15 October 2025 by Tomas Novak of Cedar Grove Health.",
  "evidence": ["Tomas Novak of Cedar Grove Health", "15 October 2025", "Tampere site", "48 contracts"]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "48 contracts were signed at the Tampere site on 15 October 2025 by Tomas Novak of Cedar Grove Health.",
 "evidence": [
  "Tomas Novak of Cedar Grove Health",
  "15 October 2025",
  "Tampere site",
  "48 contracts"
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
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
   "person": true,
   "organization": true,
   "city": true,
   "date": true,
   "amount": true
  }
 },
 "error_tags": [
  "evidence_count_3plus"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 0,
 "cascade_t4": 1,
 "cascade_verbatim": 1,
 "cascade_csr": 0.8,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 28. smollm2 · `ext_p01__P03` (F4_EXTRACTION)

Raw output:

~~~~
{
  "answer": "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025, testing 299 samples before closing the report.",
  "evidence": ["Priya Nair", "Willow Creek Pharma", "Rotterdam facility", "4 January 2025", "299 samples"]
}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Priya Nair from Willow Creek Pharma visited the Rotterdam facility on 4 January 2025, testing 299 samples before closing the report.",
 "evidence": [
  "Priya Nair",
  "Willow Creek Pharma",
  "Rotterdam facility",
  "4 January 2025",
  "299 samples"
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
 "format_strict": 1,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 1,
 "verbatim_case_insensitive": 1,
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
  "evidence_count_3plus"
 ],
 "evidence_duplicate": 0,
 "finish_reason": "eos",
 "cascade_format": 1,
 "cascade_length": 1,
 "cascade_cardinality": 0,
 "cascade_t4": 0,
 "cascade_verbatim": 1,
 "cascade_csr": 0.6,
 "cascade_pcr": 0,
 "t4_rule": "T4_NO_COMMA",
 "length_limit": 25
}
~~~~

## 29. smollm2 · `trf_p01__V08` (F5_TRANSFORMATION)

Raw output:

~~~~
{"answer": "Project: Meridian, owned by Marcus Hale, is on track with a deadline of 12 May 2025 and an approved budget of 733000 USD."}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Project: Meridian, owned by Marcus Hale, is on track with a deadline of 12 May 2025 and an approved budget of 733000 USD."
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V08",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 0,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.2,
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
  "missing_evidence"
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

## 30. smollm2 · `trf_p01__V03` (F5_TRANSFORMATION)

Raw output:

~~~~
{"answer": "Project: Meridian, owned by Marcus Hale, is on track with a deadline of 12 May 2025 and an approved budget of 733000 USD."}
~~~~

Parsed object (rule `strict`):

~~~~
{
 "answer": "Project: Meridian, owned by Marcus Hale, is on track with a deadline of 12 May 2025 and an approved budget of 733000 USD."
}
~~~~

Evaluator decisions:

~~~~
{
 "arm": "format",
 "condition_id": "V03",
 "positions": {
  "format": 1,
  "length": 2,
  "cardinality": 3,
  "t4": 4,
  "verbatim": 5
 },
 "format_strict": 0,
 "parse_rule": "strict",
 "evaluable": 1,
 "length": 1,
 "cardinality": 0,
 "t4": 0,
 "verbatim": 0,
 "verbatim_case_insensitive": 0,
 "verbatim_min3": 0,
 "csr": 0.2,
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
  "missing_evidence"
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


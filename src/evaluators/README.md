# Evaluators

Rule-based checks for the five constraints, task quality and error tags, exactly as in brief §5.8.
Every rule below is covered by unit tests in `tests/test_format.py`, `tests/test_constraints.py`,
`tests/test_quality.py` and `tests/test_tags.py`. All checks run on the raw output string `o`; nothing in
an output is ever repaired, rewritten or retried.

| File | Contents |
|---|---|
| `format.py` | strict FORMAT (T1) and the lenient parse |
| `constraints.py` | LENGTH (T2), CARDINALITY (T3), T4 (NO_COMMA; LOWERCASE fallback), VERBATIM (T5) |
| `quality.py` | task quality per family |
| `tags.py` | error tags |
| `record.py` | assembles one evaluation record per prompt id (implementation specification §6.2) |

## 1. FORMAT (T1), scored strictly

Let `s = o.strip()`. FORMAT passes if `json.loads(s)` succeeds, no object anywhere in it has duplicate keys
(detected with `object_pairs_hook`), the result is a dict, and its key set is exactly `{"answer", "evidence"}`.

| Output | FORMAT |
|---|---|
| `{"answer": "...", "evidence": ["...", "..."]}` | pass |
| the same with leading/trailing spaces or newlines | pass |
| ```` ```json\n{...}\n``` ```` (code fence) | fail |
| `Here is the JSON: {...}` or `{...} Hope this helps` | fail |
| `{"answer": "a", "answer": "b", "evidence": [...]}` (duplicate key) | fail |
| `{"answer": "...", "evidence": [...], "note": "..."}` (extra key) | fail |
| `{"answer": "..."}` (missing key), `[...]`, `"text"` | fail |

Notes. Python's `json.loads` is used as specified: raw control characters (for example a literal newline)
inside a string make the JSON invalid. `json.loads` also accepts the non-standard constants `NaN` and
`Infinity`; the rule is applied as written, and any such output would be reported at G2.

## 2. Lenient parse (never used for the FORMAT score)

Used only to obtain an object for LENGTH, CARDINALITY, T4, VERBATIM and task quality. Rules, in order:

1. `strict`: `json.loads(s)` returns a dict (this also covers dicts with extra keys or duplicate keys; for
   duplicate keys the last value wins, as in `json.loads`).
2. `fence`: all of `s` is one fenced block, ```` ``` ```` or ```` ```json ```` (the tag `json` in any case),
   and its content parses to a dict.
3. `first_object`: for each `{` in `s` from left to right, `json.JSONDecoder().raw_decode(s, i)`; the first
   result that is a dict is used. Braces inside string values are handled by the JSON decoder; with two
   objects, the first is used.
4. `none`: no object; `evaluable = 0`. LENGTH, CARDINALITY, T4 and VERBATIM score 0 and the output is flagged.

`parse_rule ∈ {strict, fence, first_object, none}` is recorded for every output. Single-quoted pseudo-JSON
(`{'answer': 'x'}`) is not repaired and gives `none`.

## 3. LENGTH (T2)

`answer` is a string and `len(re.findall(r"\S+", answer)) <= L`, with L = 25 (`T2_LENGTH`) or 20
(`T2_LENGTH_20`, calibration fallback). The limit is read from the instruction keys of each prompt.
25 tokens pass, 26 fail. A list or number in `answer` fails.

## 4. CARDINALITY (T3)

`evidence` is a list of exactly 2 items, each a string that is non-empty after stripping.
Fails: `[]`, one item, three items, a non-string item, `""` or `"   "`, a string instead of a list.

## 5. T4

* `T4_NO_COMMA` (default): `answer` is a string containing neither `,` nor the fullwidth comma `，` (U+FF0C).
* `T4_LOWERCASE` (calibration fallback only): `answer` is a string with at least one letter and
  `answer == answer.lower()`. Digits are allowed; any uppercase letter fails; a string without letters fails.

## 6. VERBATIM (T5)

`evidence` is a non-empty list and every item is a string that, after normalization, contains at least one
letter or digit and is a substring of the normalized INPUT text (the INPUT block only; never the question,
the instructions or the task text). Normalization: Unicode NFC; typographic single quotes `‘ ’ ‚ ‛` → `'`;
typographic double quotes `“ ” „ ‟` → `"`; every whitespace run → one space; strip.
Matching is case-sensitive; `verbatim_case_insensitive` is the secondary metric (both sides lowercased).
The number of items is CARDINALITY's job: one verbatim item passes VERBATIM. Identical items are allowed and
flagged (`evidence_duplicate`, comparison after normalization).

T5 states no length requirement, so there is no length minimum (design decision G1, R2; before R2 every
item needed at least 3 `\S+` tokens). The letter-or-digit rule still rejects `""`, whitespace-only and
punctuation-only items. The former rule is kept as the diagnostic `verbatim_min3` (case-sensitive, every item
also needs at least 3 tokens); it is reported only as a robustness check.

| Evidence (INPUT contains `... such as the Arctic. Engineers called it “the hardest frontier” in 1974.`) | VERBATIM |
|---|---|
| `["such as the Arctic.", "called it \"the hardest frontier\" in"]` | pass (quotes normalized) |
| `["SUCH AS THE Arctic."]` | fail; case-insensitive variant passes |
| `["the Arctic"]` | pass; `verbatim_min3` fails (2 tokens) |
| `["Project: Orion."]` (F5 input line) | pass; `verbatim_min3` fails |
| `["."]`, `[""]`, `["   "]` | fail (no letter or digit) |
| an item copied from the F1 question but absent from the passage | fail |

## 7. Task quality

Computed from the lenient-parsed `answer` when it is a string. Otherwise Q = 0 and `q_answer_available = 0`.
Quality is reported per family and never averaged across families.

**F1 QA.** Primary (`q_primary`, design decision G1, R1): whole-token containment. Both the gold answers
and the model answer go through (1) Unicode NFC, (2) the VERBATIM quote straightening, (3) removal of a
possessive `'s` after a word character (case-insensitive: `Beyoncé's` → `Beyoncé`), (4) SQuAD normalization
(lowercase, remove ASCII punctuation, remove the articles a/an/the, collapse whitespace) and (5) a split on
whitespace. `q_primary = 1` if the token sequence of some gold answer occurs as a contiguous subsequence of
the answer's tokens. Secondary (`q_secondary`): maximum token F1 over the gold answers (official SQuAD
normalization, unchanged). Diagnostic (`quality_detail.containment_char`, robustness appendix only): the
brief's original rule, a SQuAD-normalized gold answer is a character substring of the normalized answer.

| Gold | Answer | `q_primary` | `containment_char` |
|---|---|---|---|
| `Arctic` | `Antarctic` | 0 | 1 |
| `4` | `1994` | 0 | 1 |
| `1,000` | `1000` (and the reverse) | 1 | 1 |
| `Beyoncé` | `Beyoncé's`, `Beyoncé’s` | 1 | 1 |
| `Normans` | `The Normans` | 1 | 1 |
| `Battle of Hastings` | `… at the Battle of Hastings in 1066` | 1 | 1 |
| `Hastings` | `Hastingsville` | 0 | 1 |

**F2 classification.** Case-insensitive whole-word matching (no letter or digit on either side) of the
synonyms: World: `world`. Sports: `sports`, `sport`. Business: `business`. Sci/Tech: `sci/tech`, `sci-tech`,
`scitech`, `sci tech`, `science/technology`, `science and technology`, `science & technology`, and (design
decision G1, R3) `technology`, `tech`, `science`. Matches never cross labels (for example `sci tech` also
contains `tech`, both Sci/Tech); `high-tech` contains the whole word `tech`, while `biotechnology`,
`technical` and `neuroscience` do not match.
Exactly one distinct label → prediction. Several distinct labels → the label that directly follows a cue
within three tokens, if exactly one label does; tokens are whitespace-separated words with edge punctuation
removed, and "within three tokens" means the label is the 1st, 2nd or 3rd token after the cue's last token.
Cues: `category is`, `category was`, `classified as`, `belongs to`, `falls under`, `falls into`, `is`, `as`,
`under`, `into`. Otherwise the case is unresolved and scores 0 (`quality_detail.label_status`:
`none | single | cue_resolved | unresolved`; the unresolved rate is reported).

| Answer | Prediction |
|---|---|
| `The article about the World Cup belongs to the Sports category.` | Sports (only "Sports" follows a cue) |
| `It is a sport story.` | Sports |
| `It belongs to the Technology category.` | Sci/Tech |
| `An article about a high-tech firm's profits belongs to Business.` | Business ("tech" follows no cue) |
| `The category is World and also is Sports.` | unresolved → 0 |
| `It could be Business or Technology.` | unresolved → 0 |
| `This is about computers and the internet.` | none → 0 |

**F3 summarization.** ROUGE-L F1 (`rouge-score` 0.1.2, `RougeScorer(["rougeL"], use_stemmer=True)`) of the
answer against the XSum reference summary.

**F4 extraction and F5 transformation.** Field accuracy (`q_primary`) = fraction of the 5 gold fields found
in the answer; exact-all-fields (`q_secondary`) = 1 if all 5 are found.

* Names, organizations, cities, project, owner and status: case-insensitive whole-phrase match after
  whitespace normalization (`Leeds` does not match `Leedsville`; `Daniel Reed's` matches `Daniel Reed`).
* Dates: canonicalized to a calendar date. Accepted forms (month names in any case):
  `14 March 2025`, `March 14 2025`, `March 14, 2025`, `14 Mar 2025`, `Mar 14 2025`, `2025-03-14`,
  `14/03/2025` (day first). One- or two-digit days and months are accepted in the numeric forms.
  Not accepted: `14th March 2025`, `Mar. 14 2025`, `March 2025`, `03/14/2025`. "May" is both a full month name
  and an abbreviation; a mention matched by both patterns counts once (bug found by the golden-output test).
* Numbers, amounts and budgets: thousands separators (`120,000`), currency symbols (`$ € £`, `US$`) and the
  words `USD` and `dollars` are dropped; the gold value must then appear as a standalone number (no letter,
  digit or decimal point attached; `47th` does not count) outside every accepted date mention.
  `$120,000`, `120000 USD`, `120,000 dollars`, `USD 120000`, `120000.00` all match gold `120000 USD`.

## 8. Error tags (non-exclusive)

| Tag | Condition |
|---|---|
| `empty_output` | `o.strip() == ""` |
| `code_fence` | ```` ``` ```` occurs outside the parsed object (anywhere, if nothing was parsed) |
| `leading_text`, `trailing_text` | non-whitespace text other than fence markers before / after the parsed object |
| `invalid_json` | non-empty output without any parseable JSON object (`parse_rule = none`) |
| `duplicate_keys` | the parsed object contains duplicate keys at any level |
| `extra_keys` | keys other than `answer` and `evidence` |
| `missing_answer`, `missing_evidence` | key absent from the parsed object |
| `answer_not_string`, `evidence_not_list` | key present with the wrong type |
| `evidence_count_0`, `evidence_count_1`, `evidence_count_3plus` | evidence is a list with 0, 1 or ≥ 3 items |
| `evidence_not_verbatim` | evidence is a non-empty list and VERBATIM fails |
| `evidence_duplicate` | two evidence strings are identical after normalization |
| `truncated` | generation ended at the length limit (`finish_reason = length`) |

## 9. Scoring policies

* Primary (decoupled): FORMAT from the strict rule; the other four constraints from the lenient parse.
  CSR = mean of the five flags; PCR = 1 if all five flags are 1.
* E6a robustness (cascade, original plan §37): if FORMAT fails strictly, all five flags are 0
  (`cascade_*` fields, `cascade_csr`, `cascade_pcr`).
* E6b robustness: analyses restricted to `format_strict = 1` (selected at analysis time).

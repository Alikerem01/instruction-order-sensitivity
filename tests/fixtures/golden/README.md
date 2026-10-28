# Golden-output fixture (design decision G1, R6)

Hand-written model outputs with hand-written expected evaluator decisions. They are pushed through the real
import → evaluate path by `tests/test_golden_integration.py`, which writes a run folder for the fictitious model
`fixture_model` into a temporary directory (never under `runs/`), imports it with
`scripts/import_run.py:run_import` and evaluates it with `src/evaluate.py:evaluate_run`. The fixture flag skips
only the bundle-commit and file-hash checks that need a real bundle; every other import check runs. The phase
`golden_fixture` is `analysis_eligible: false`.

| File | Content |
|---|---|
| `cases.py` | 24 cases: output text, finish reason, expected flags (derivations in comments) |
| `prompts.jsonl` | the 25 pilot prompt records the cases use (`qa_p01__P01` and `qa_p01__V01` share a text) |
| `tasks.jsonl` | the 10 pilot tasks (copied from `data/benchmark_v1/tasks_pilot.jsonl`) |
| `fixture_config.json` | phase name, model specification, batch size, `max_new_tokens`, `analysis_eligible: false` |

Coverage: one strictly valid, correct output per family; parse rules `fence`, `first_object` with leading and
with trailing text, `none`; a truncated output; an empty output; duplicate keys; an extra key; evidence with 1
and with 3 items, with typographic quotes, and not verbatim; a 2-token verbatim item (R2); a curly possessive in
an F1 answer (R1); a NO_COMMA failure; a 26-word answer; an ambiguous F2 answer; an F2 answer resolved by a cue
after the new `tech` synonym (R3); an alternative F4 date format; an F5 budget with a thousands separator; and
one output shared by two prompt ids (P01 = V01).

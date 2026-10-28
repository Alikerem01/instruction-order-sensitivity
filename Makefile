# Instruction-order study. Run `make help` for the targets.
PY := .venv/bin/python
PHASE ?=
RUN ?=
RUNS ?=
PILOT ?=
BS1 ?=

.PHONY: help setup test tasks prompts validate notebook bundle bundles-pilot a6-reference freeze freeze-check release dryrun import evaluate a1 smoke-report pilot-report a3 privacy analyze figures posthoc-norm tables report all-local pin-models

help:
	@echo "setup      create .venv (Python 3.11) and install requirements.txt"
	@echo "test       run the pytest suite"
	@echo "tasks      build tasks_main/pilot.jsonl and selection_report.json"
	@echo "prompts    build prompts_main/pilot/smoke.jsonl"
	@echo "validate   run the integrity tests (required before any bundle)"
	@echo "notebook   regenerate colab/run_generation.ipynb"
	@echo "bundle     PHASE=smoke|pilot|pilot_bs1|main|smoke_gemma|pilot_gemma"
	@echo "           -> dist/colab_bundle_<phase>_<gitsha7>.zip (Gemma phases: D06; main needs the A6 reference)"
	@echo "dryrun     local pipeline dry-run with SmolLM2-135M (interrupt, resume, import, evaluate)"
	@echo "import     PHASE=.. RUN=<run_id>|all  verify and register runs placed in runs/<phase>/ (folders or zips)"
	@echo "evaluate   PHASE=.. RUN=.. evaluation records -> results/eval/<phase>/<run_id>/"
	@echo "bundles-pilot  pilot and pilot_bs1 bundles together (decision D04)"
	@echo "a6-reference   A6 reference from the imported batch-1 pilot runs -> results/qc/ (decision G2 §3.2)"
	@echo "freeze     write data/benchmark_v1/manifest.json (G3 freeze); freeze-check compares the files with it"
	@echo "a1         RUNS=\"<pass1> <pass2>\" [PHASE=smoke_gemma] run-to-run determinism -> results/report/"
	@echo "smoke-report   RUNS=\"<pass1> <pass2>\" [PHASE=smoke_gemma] -> results/report/<phase>_report.md"
	@echo "pilot-report   RUN=<pilot run> [PHASE=pilot_gemma] -> pilot_report.md, pilot_summary.json, audit_sample.md"
	@echo "a3         PILOT=<pilot run> BS1=<pilot_bs1 run> [PHASE=pilot_gemma] batch invariance -> results/report/"
	@echo "privacy    scan runs/, results/, release/ and tracked files for personal data"
	@echo "analyze    all analyses of the frozen plan -> results/metrics/summary.json, results/tables/table2-5,"
	@echo "           results/report/RESULTS_SUMMARY.md (G4a); tables and report are aliases"
	@echo "figures    fig1-fig5 (300 dpi PNG + PDF, 16 cm) from summary.json -> results/figures/ (G4b)"
	@echo "all-local  analyze + figures"
	@echo "release    public-release tree in release/ (no AG News/XSum texts, e-mails redacted; decisions D03, G2)"

setup:
	uv venv --python 3.11 .venv
	uv pip sync requirements.txt --python $(PY)

pin-models:
	$(PY) scripts/pin_models.py

test:
	$(PY) -m pytest tests

tasks:
	$(PY) -m src.prepare_tasks

prompts:
	$(PY) -m src.build_prompts

validate:
	$(PY) -m src.validate_integrity

notebook:
	$(PY) scripts/build_notebook.py

bundle: test
	@test -n "$(PHASE)" || (echo "usage: make bundle PHASE=smoke|pilot|pilot_bs1|main|smoke_gemma|pilot_gemma" && exit 2)
	$(PY) scripts/make_bundle.py --phase $(PHASE)

bundles-pilot: test
	$(PY) scripts/make_bundle.py --phase pilot
	$(PY) scripts/make_bundle.py --phase pilot_bs1

a6-reference:
	$(PY) scripts/make_a6_reference.py

freeze: test validate
	$(PY) scripts/freeze_manifest.py

freeze-check:
	$(PY) scripts/freeze_manifest.py --check

a1:
	@test -n "$(RUNS)" || (echo 'usage: make a1 RUNS="<pass1> <pass2>"' && exit 2)
	$(PY) scripts/compare_runs.py determinism --phase $(or $(PHASE),smoke) --runs $(RUNS)

smoke-report:
	@test -n "$(RUNS)" || (echo 'usage: make smoke-report RUNS="<pass1> <pass2>"' && exit 2)
	$(PY) scripts/smoke_report.py --phase $(or $(PHASE),smoke) --runs $(RUNS)

pilot-report:
	@test -n "$(RUN)" || (echo "usage: make pilot-report RUN=<pilot run>" && exit 2)
	$(PY) scripts/pilot_report.py --phase $(or $(PHASE),pilot) --run $(RUN)

a3:
	@test -n "$(PILOT)" -a -n "$(BS1)" || (echo "usage: make a3 PILOT=<pilot run> BS1=<pilot_bs1 run>" && exit 2)
	$(PY) scripts/compare_runs.py batch-invariance --pilot-run $(PILOT) --bs1-run $(BS1) \
		--pilot-phase $(or $(PHASE),pilot) --bs1-phase $(patsubst pilot%,pilot_bs1%,$(or $(PHASE),pilot))

privacy:
	$(PY) -m src.privacy

dryrun:
	$(PY) scripts/dryrun.py

import:
	@test -n "$(PHASE)" -a -n "$(RUN)" || (echo "usage: make import PHASE=<phase> RUN=<run_id>|all" && exit 2)
	$(PY) scripts/import_run.py --phase $(PHASE) --run $(RUN)

evaluate:
	@test -n "$(PHASE)" -a -n "$(RUN)" || (echo "usage: make evaluate PHASE=<phase> RUN=<run_id>" && exit 2)
	$(PY) -m src.evaluate --phase $(PHASE) --run $(RUN)

analyze:
	$(PY) -m analysis.run

posthoc-norm:   ## post-hoc re-analysis with normalized FORMAT scoring (results/posthoc_norm/)
	$(PY) -m analysis.posthoc_norm

tables report: analyze

figures:
	$(PY) -m analysis.figures

all-local: analyze figures

release:
	$(PY) scripts/make_release.py

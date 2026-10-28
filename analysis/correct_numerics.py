"""Rebuild v3.1 statistics from released evaluation records without downloading data.

No model is run and no task, prompt, generation or evaluation record is changed.
FORMAT is independently rechecked on every released raw output. Other flags and
quality scores are reused from the original evaluation records; equality of the
lenient-parsed objects before/after normalization is verified. This is NOT a new
end-to-end evaluation of the copyrighted source texts omitted from the release.
Only input-text comma-spillover measurements, tokenizer edit distances and prior
generation checks are carried forward, explicitly recorded in the audit.

Usage: python -m analysis.correct_numerics
"""
from __future__ import annotations

import copy
import math
import platform
import shutil
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from analysis.compute import Analysis, robustness
from analysis.data import check_main_table, imported_run, load_eval, main_models, pilot_difficulties
from analysis import figures as F
from analysis.posthoc_r1 import run_all
from analysis import posthoc_norm as N
from analysis.report import tables, results_summary
from src.common import REPO_ROOT, RESULTS_DIR, RUNS_DIR, read_json, read_jsonl, write_json, atomic_write_text, sha256_file
from src.evaluators.format import format_strict, lenient_parse
from src.runs import utc_now

BASE_COMMIT = '931f44c0cec7ba10224f9fd44825f87adbab80eb'
ARCHIVE = RESULTS_DIR / 'archive' / 'pre_v3_1'


def same(a, b):
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
    return a == b


def changed(before, after):
    return {k: {'before': before.get(k), 'after': after.get(k)}
            for k in sorted(set(before) | set(after)) if k != '_meta' and not same(before.get(k), after.get(k))}


def is_carried(k):
    return (k.startswith('checks.') or k.startswith('main.posthoc_r1.edit_distance.')
            or (k.startswith('main.exploratory.e5.') and 'evidence_comma_only' in k))


def inputs():
    roots = [REPO_ROOT / 'data', REPO_ROOT / 'configs', REPO_ROOT / 'src', RUNS_DIR, RESULTS_DIR / 'eval']
    paths = [p for root in roots for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [REPO_ROOT / 'ANALYSIS_PLAN.md', REPO_ROOT / 'requirements.txt', REPO_ROOT / 'requirements-colab.txt']
    return {str(p.relative_to(REPO_ROOT)): sha256_file(p) for p in sorted(paths)}


def main():
    baseline_inputs = inputs()
    models = main_models()
    run = imported_run('main', analysis_eligible=True)
    strict_path = RESULTS_DIR / 'metrics/summary.json'
    norm_path = N.OUT / 'summary_norm.json'
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    for source, name in [(strict_path, 'summary_strict.json'), (norm_path, 'summary_norm.json')]:
        dest = ARCHIVE / name
        if not dest.exists():
            if read_json(source).get('_meta', {}).get('numerical_correction'):
                raise RuntimeError('Cannot create an original archive from already-corrected results')
            shutil.copy2(source, dest)
    before_s = read_json(ARCHIVE / 'summary_strict.json')
    before_n = read_json(ARCHIVE / 'summary_norm.json')
    n_boot, seed = before_s['_meta']['n_boot'], before_s['_meta']['seed']
    assert (n_boot, seed) == (5000, 20261003)
    df = load_eval('main', run, models)
    check_main_table(df, models)

    a = Analysis(df, models, n_boot, seed)
    for fn in [a.counts, a.s1, a.positions]: fn()
    a.gee_family('main.p1', interaction=False)
    for fn in [a.p2, a.p3, a.s2, a.s3, a.e1, a.e2]: fn()
    a.e3(pilot_difficulties(models))
    for fn in [a.e4, a.e5, a.presentation, a.p1_independence, a.constraint_instability]: fn()
    run_all(a, run)
    fresh_s = {**a.s, **robustness(df, models, n_boot, seed)}
    carried = {k: v for k, v in before_s.items() if k != '_meta' and k not in fresh_s}
    assert all(is_carried(k) for k in carried), [k for k in carried if not is_carried(k)]
    strict = {**carried, **fresh_s}
    strict['checks.software.analysis.python'] = platform.python_version()
    for pkg in ('numpy', 'scipy', 'statsmodels', 'pandas', 'matplotlib'):
        strict[f'checks.software.analysis.{pkg}'] = version(pkg)
    stamp = utc_now()
    code_hashes = {str(p.relative_to(REPO_ROOT)): sha256_file(p) for p in sorted((REPO_ROOT/'analysis').glob('*.py'))}
    correction = {'version': 'v3.1', 'date': '2026-10-28', 'base_commit': BASE_COMMIT,
                  'tie_decimals': 12, 'archive': str(ARCHIVE.relative_to(REPO_ROOT)),
                  'scope': 'numerical tie correction; no new generation or evaluation policy',
                  'recomputed_keys': len(fresh_s), 'carried_forward_keys': sorted(carried)}
    meta = {**before_s['_meta'], 'generated_utc': stamp, 'code_sha256': code_hashes,
            'numerical_correction': correction, 'original_summary_sha256': sha256_file(ARCHIVE/'summary_strict.json')}
    strict = {'_meta': meta, **dict(sorted(strict.items()))}
    write_json(strict_path, strict)
    md = tables(strict, models, RESULTS_DIR/'tables')
    atomic_write_text(RESULTS_DIR/'report/RESULTS_SUMMARY.md', results_summary(strict, models, meta, md))
    print(f'Strict statistics rebuilt: {len(fresh_s)} keys; {len(carried)} explicitly carried forward.', flush=True)

    raw, norm, gens = {}, {}, []
    mismatch = parse_mismatch = 0
    for m in models:
        stored = {r['prompt_id']: r for r in read_jsonl(RESULTS_DIR/'eval/main'/run/f'{m}.jsonl')}
        for g in read_jsonl(RUNS_DIR/'main'/run/m/'generations.jsonl'):
            text = g['output_text']
            normalized = N.normalize_output(text)
            parsed_equal = lenient_parse(text).obj == lenient_parse(normalized).obj
            gens.append({'model_key': m, 'n_prompt_ids': len(g['prompt_ids']), 'form': N.fence_form(text)})
            for pid in g['prompt_ids']:
                raw[m, pid] = stored[pid]
                mismatch += int(format_strict(text)) != stored[pid]['format_strict']
                parse_mismatch += not parsed_equal
                norm[m, pid] = {**stored[pid], 'format_strict': N.format_normalized(text)}
    assert len(raw) == 8000 and mismatch == 0 and parse_mismatch == 0
    s = {k: v for k, v in before_n.items() if k.startswith(N.P+'.inventory.')}
    assert len(gens) == s[N.P+'.inventory.unique_generations'] == 7600
    s.update({N.P+'.checks.strict_records.n': len(raw), N.P+'.checks.strict_records.n_mismatch': mismatch,
              N.P+'.checks.strict_records.scope': 'raw-output strict FORMAT only; other fields retained from stored evaluations',
              N.P+'.checks.parsed_objects.n': len(raw), N.P+'.checks.parsed_objects.n_mismatch': parse_mismatch})
    # Independent recomputation using the canonical sorted-record frame.
    check = Analysis(N.frame(raw, models), models, n_boot, seed)
    check.s1(); check.positions(); check.gee_family('main.p1', interaction=False)
    check.p2(); check.p3(); check.s2(interaction=False); check.s3()
    bad = [k for k, v in check.s.items() if k not in strict or not same(v, strict[k])]
    s.update({N.P+'.checks.strict_keys.n': len(check.s), N.P+'.checks.strict_keys.n_mismatch': len(bad),
              N.P+'.checks.strict_keys.mismatches': bad,
              N.P+'.checks.strict_keys.scope': 'S1, position rates, P1, P2, P3, S2 pairs and quality from stored records; numeric tolerance 1e-12 absolute/1e-10 relative'})
    ndf = N.normalized_frame(raw, norm, models, s)
    s[N.P+'.checks.content_unchanged.scope'] = 'stored content/quality retained; raw parsed-object invariance verified independently'
    N.write_records(ndf)
    na = N.normalized_analysis(ndf, models, n_boot, seed, s)
    N.consistency_checks(ndf, na, strict, models, s)
    assert s[N.P+'.checks.all_passed'], {k:v for k,v in s.items() if k.endswith('n_mismatch') and v}
    norm_meta = {**before_n['_meta'], 'generated_utc': stamp, 'strict_summary_sha256': sha256_file(strict_path),
                 'code_sha256': code_hashes, 'recomputation_mode': 'stored-evaluation-records',
                 'numerical_correction': correction,
                 'original_summary_sha256': sha256_file(ARCHIVE/'summary_norm.json')}
    normalized = {'_meta': norm_meta, **dict(sorted(s.items()))}
    write_json(norm_path, normalized)
    audit = N.Audit()
    nmd = N.tables(N.Tracked(normalized), models, audit)
    N.comparison_table(N.Tracked({**strict, **normalized}), models, audit)
    N.figures(normalized, strict, models, audit)
    assert audit.write()
    atomic_write_text(N.OUT/'SUMMARY_NORM.md', N.summary_md(normalized, models, nmd, True))
    F.main()
    assert baseline_inputs == inputs(), 'An immutable input changed'
    report = {'base_commit': BASE_COMMIT, 'generated_utc': stamp, 'n_boot': n_boot, 'seed': seed,
              'strict_changes': changed(before_s, strict), 'normalized_changes': changed(before_n, normalized),
              'immutable_inputs_sha256': baseline_inputs, 'immutable_inputs_unchanged': True,
              'raw_format_mismatches': mismatch, 'parsed_object_mismatches': parse_mismatch,
              'strict_recomputed_keys': len(fresh_s), 'strict_carried_forward_keys': sorted(carried),
              'normalized_checks_passed': s[N.P+'.checks.all_passed'], 'policy_audit_passed': True,
              'scope_note': __doc__}
    write_json(RESULTS_DIR/'report/NUMERICAL_CORRECTION_V31.json', report)
    print(f"Normalized statistics rebuilt. Changes: {len(report['strict_changes'])} strict / "
          f"{len(report['normalized_changes'])} normalized; all immutable inputs unchanged.", flush=True)


if __name__ == '__main__':
    main()

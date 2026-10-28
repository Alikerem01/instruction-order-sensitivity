"""Regression tests for v3.1: preserve the exact ties implied by binary flags."""
import itertools

import numpy as np
import pandas as pd
import pytest

from analysis.bootstrap import bootstrap_p
from analysis.compute import Analysis
from analysis.data import imported_run, load_eval, main_models
from analysis.posthoc_norm import FLAGS_NORM, P, pcr_pairs
from analysis.posthoc_r1 import order_level
from analysis.stats import bh, p3_test
from src.common import RESULTS_DIR
from tests.test_analysis import synthetic


def test_bootstrap_counts_machine_residuals_in_both_zero_tails():
    assert bootstrap_p(np.array([-0.2, 1e-16, -1e-16, 0.2, 0.4, 0.6])) == bootstrap_p(
        np.array([-0.2, 0, 0, 0.2, 0.4, 0.6]))
    # Real small differences remain distinct at the study's resolution.
    assert bootstrap_p(np.full(100, 0.000002)) == pytest.approx(2 / 101)


def test_wilcoxon_zeros_and_tied_ranks_survive_subtraction():
    exact = np.array([0.2, 0.2, -0.2, 0, 0.4, -0.4, 0])
    noisy = exact + np.array([1, -1, 1, 1, -1, 1, -1]) * 1e-16
    assert p3_test(noisy) == p3_test(exact)
    assert p3_test(noisy)['n_zero'] == 2


def test_identical_pass_count_ranges_have_identical_ps():
    df = synthetic(lambda c, pos, m, task, rng: True)
    for m, high, low in [('m1', 4, 3), ('m2', 2, 1)]:
        for idx, row in df[df.model_key == m].iterrows():
            n = low if row.condition_id in ('P01', 'V01') else high
            for j, c in enumerate(('format', 'length', 'cardinality', 't4', 'verbatim')):
                df.loc[idx, c] = int(j < n)
    a = Analysis(df, ['m1', 'm2'], n_boot=10)
    assert (a.task_values('order', 'm1').ps == a.task_values('order', 'm2').ps).all()


@pytest.fixture(scope='module')
def main_analysis():
    models = main_models()
    df = load_eval('main', imported_run('main'), models)
    rec = pd.read_csv(RESULTS_DIR / 'posthoc_norm/records_format.csv')
    df = df.merge(rec[['model_key', 'prompt_id', 'format_norm']], on=['model_key', 'prompt_id'], validate='one_to_one')
    return Analysis(df, models, n_boot=5000, seed=20261003, flags=FLAGS_NORM)


def test_main_wilcoxon_matches_integer_oracle(main_analysis):
    a = main_analysis
    a.p3(prefix=f'{P}.p3')
    oracle = {}
    for m in a.models:
        d = np.rint(a.task_values('order', m).ps.to_numpy() * 5).astype(int) - np.rint(
            a.task_values('format', m).ps.to_numpy() * 5).astype(int)
        oracle[m] = p3_test(d)
        assert a.s[f'{P}.p3.{m}.wilcoxon_stat'] == oracle[m]['wilcoxon_stat']
        assert a.s[f'{P}.p3.{m}.n_zero'] == oracle[m]['n_zero']
        assert a.s[f'{P}.p3.{m}.p'] == pytest.approx(oracle[m]['p'], abs=1e-15)
    assert a.s[f'{P}.p3.smollm2.q'] == pytest.approx(0.7395427426145943)


def test_main_bootstrap_pairs_match_integer_oracle(main_analysis):
    a = main_analysis
    a.s2(prefix=f'{P}.s2', interaction=False)
    pcr_pairs(a, f'{P}.s2')
    for metric, scale in [('ps', 5), ('csr', 50), ('pcr', 10)]:
        oracle = {}
        for x, y in itertools.combinations(a.models, 2):
            d = a.task_values('order', x)[metric] - a.task_values('order', y)[metric]
            counts = np.rint(d.to_numpy() * scale).astype(np.int64)
            reps = a.bs.counts.astype(np.int64) @ counts
            expected = min(1.0, 2 * min(int((reps <= 0).sum()) + 1, int((reps >= 0).sum()) + 1) / 5001)
            oracle[(x, y)] = expected
            assert a.s[f'{P}.s2.{x}_vs_{y}.{metric}_diff.p'] == expected
        for (x, y), q in bh(oracle).items():
            assert a.s[f'{P}.s2.{x}_vs_{y}.{metric}_diff.q'] == q


def test_main_format_ranking_counts_exact_ties(main_analysis):
    a = main_analysis
    order_level(a, prefix=f'{P}.order_level')
    key = f'{P}.order_level.format.rank.phi4mini_vs_gemma4e4b.csr'
    assert tuple(a.s[f'{key}.{k}'] for k in ('n_a_higher', 'n_b_higher', 'n_ties')) == (6, 2, 2)
    assert a.s[f'{P}.order_level.format.rank.overall.csr.n_conditions_reproducing'] == 2

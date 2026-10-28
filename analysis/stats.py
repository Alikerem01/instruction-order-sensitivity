"""Hypothesis tests of the frozen ANALYSIS_PLAN.md (§4 P1-P3, §5 S2) with the multiplicity rules of §7.

* P1 / S2 interaction: GEE logistic regression per instruction, groups = task, exchangeable working correlation,
  robust (sandwich) covariance; a model whose compliance with the instruction is constant across all its
  order-arm outputs is left out first (decision G2 §2.4). Warnings are captured and reported, never silenced; a
  GEE that fails to converge or shows separation is reported as not estimable (plan §8).
* P2: Friedman test of CSR and Cochran's Q test of PCR across the 10 orders, per model (100 × 10 matrices).
* P3: Wilcoxon signed-rank test of PS_order − PS_format per task (zero_method="pratt", normal approximation).
* Benjamini-Hochberg within each family of §7.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.contingency_tables import cochrans_q
from statsmodels.stats.multitest import multipletests

from analysis.numerics import canonical

NOT_APPLICABLE = "no variation; test not applicable"
NOT_ESTIMABLE = "not estimable"


def bh(pvalues: dict[str, float | None]) -> dict[str, float | None]:
    """Benjamini-Hochberg q-values within one family; tests without a p-value stay without a q-value."""
    keys = [k for k, p in pvalues.items() if p is not None and np.isfinite(p)]
    out: dict[str, float | None] = {k: None for k in pvalues}
    if keys:
        q = multipletests([pvalues[k] for k in keys], method="fdr_bh")[1]
        out.update({k: float(v) for k, v in zip(keys, q)})
    return out


def _separation(data: pd.DataFrame, factors: list[list[str]]) -> list[str]:
    """Levels (or level combinations) of the model's factors in which the outcome is constant: these produce
    quasi-complete separation in a logistic model."""
    found = []
    for cols in factors:
        for level, y in data.groupby(cols)["y"]:
            if y.nunique() == 1:
                lv = level if isinstance(level, tuple) else (level,)
                found.append(f"{'×'.join(cols)}={'/'.join(map(str, lv))}: all {'pass' if y.iloc[0] == 1 else 'fail'}")
    return found


def gee_position(order: pd.DataFrame, constraint: str, models: list[str], flag: str | None = None,
                 interaction: bool = False, working: str = "exchangeable",
                 exclude_constant_families: bool = False) -> dict:
    """P1 (interaction=False) or the S2 interaction GEE (interaction=True) for one instruction.

    ``order``: order-arm rows with columns task_id, family, model_key, pos_<c> and the flag column.
    ``working="independence"`` with ``exclude_constant_families=True`` is the post-hoc robustness analysis of
    decision G4a §2.1 (option B): independence working correlation (robust sandwich SEs); family levels whose
    outcome is constant across all included models are left out before fitting, like constant models."""
    flag = flag or constraint
    data = pd.DataFrame({"task_id": order.task_id.to_numpy(), "family": order.family.to_numpy(),
                         "model": order.model_key.to_numpy(), "position": order[f"pos_{constraint}"].to_numpy(),
                         "y": order[flag].astype(int).to_numpy()})
    rates = data.groupby("model")["y"].mean()
    excluded = {m: float(rates[m]) for m in models if m in rates.index and data[data.model == m].y.nunique() == 1}
    keep = [m for m in models if m in rates.index and m not in excluded]
    out = {"models_included": keep, "excluded_models": excluded, "n": int(data.model.isin(keep).sum()),
           "warnings": []}
    if not keep or (interaction and len(keep) < 2):
        return {**out, "status": NOT_APPLICABLE,
                "reason": "no model varies" if not keep else "fewer than two models vary (no interaction)"}
    d = data[data.model.isin(keep)].reset_index(drop=True)
    if exclude_constant_families:
        fam_rates = d.groupby("family")["y"].agg(["mean", "nunique"])
        const = fam_rates[fam_rates["nunique"] == 1]
        out["excluded_families"] = {f: float(r) for f, r in const["mean"].items()}
        d = d[~d.family.isin(const.index)].reset_index(drop=True)
        out["n"] = int(len(d))
        if d.empty:
            return {**out, "status": NOT_APPLICABLE, "reason": "every family has a constant outcome"}
    terms = ["C(position)", "C(family)"] + (["C(model)"] if len(keep) > 1 else [])
    if interaction:
        terms.append("C(position):C(model)")
    factor_cols = [["position"], ["family"]] + ([["model"]] if len(keep) > 1 else [])
    if interaction:
        factor_cols.append(["position", "model"])
    sep = _separation(d, factor_cols)
    if sep:
        return {**out, "status": NOT_ESTIMABLE, "reason": "separation: " + "; ".join(sep[:6])
                + (f" (+{len(sep) - 6} more)" if len(sep) > 6 else "")}
    formula = "y ~ " + " + ".join(terms)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            cov = sm.cov_struct.Independence() if working == "independence" else sm.cov_struct.Exchangeable()
            res = smf.gee(formula, groups="task_id", data=d, family=sm.families.Binomial(), cov_struct=cov).fit()
        except Exception as e:  # reported, never hidden
            return {**out, "status": NOT_ESTIMABLE, "reason": f"fit failed: {type(e).__name__}: {e}"}
    out["warnings"] = sorted({f"{w.category.__name__}: {w.message}" for w in caught})
    names = list(res.params.index)
    if any("IterationLimit" in w or "Convergence" in w for w in out["warnings"]):
        return {**out, "status": NOT_ESTIMABLE, "reason": "did not converge"}
    if not (np.all(np.isfinite(res.params)) and np.all(np.isfinite(res.bse))):
        dep = getattr(res.model.cov_struct, "dep_params", None)
        return {**out, "status": NOT_ESTIMABLE,
                "reason": "did not converge: the iterations diverged to non-finite estimates "
                          f"(working correlation {dep}); no factor level has a constant outcome"}
    if any("separation" in w.lower() for w in out["warnings"]):
        return {**out, "status": NOT_ESTIMABLE, "reason": "separation warning"}
    if interaction:
        tested = [n for n in names if ":" in n]
    else:
        tested = [n for n in names if n.startswith("C(position)[") and ":" not in n]
    r = np.zeros((len(tested), len(names)))
    for i, n in enumerate(tested):
        r[i, names.index(n)] = 1.0
    wald = res.wald_test(r, use_f=False, scalar=True)
    out.update({"status": "estimated", "formula": formula, "wald_chi2": float(wald.statistic), "df": len(tested),
                "p": float(wald.pvalue)})
    if not interaction:
        ci = res.conf_int(alpha=0.05)
        out["odds_ratios"] = {int(n.split("T.")[1].rstrip("]")): {
            "estimate": float(np.exp(res.params[n])), "ci_low": float(np.exp(ci.loc[n, 0])),
            "ci_high": float(np.exp(ci.loc[n, 1]))} for n in tested}
    return out


def p2_tests(csr: np.ndarray, pcr: np.ndarray) -> dict:
    """Friedman test of CSR and Cochran's Q test of PCR across the orders (columns), tasks in rows."""
    n, k = csr.shape
    out = {"n": n, "k": k}
    if np.all(csr == csr[:, :1]):
        out["friedman"] = {"status": NOT_APPLICABLE}
    else:
        chi2, p = st.friedmanchisquare(*[csr[:, j] for j in range(k)])
        out["friedman"] = {"status": "estimated", "chi2": float(chi2), "df": k - 1, "p": float(p),
                           "kendall_w": float(chi2 / (n * (k - 1)))}
    if np.all(pcr == pcr[:, :1]):
        out["cochran_q"] = {"status": NOT_APPLICABLE}
    else:
        res = cochrans_q(pcr.astype(int))
        out["cochran_q"] = {"status": "estimated", "q": float(res.statistic), "df": int(res.df),
                            "p": float(res.pvalue)}
    return out


def p3_test(d: np.ndarray) -> dict:
    """Wilcoxon signed-rank test of d = PS_order − PS_format per task (decision D05 §2)."""
    # Restore exact equalities before Pratt zero handling and absolute ranks.
    d = canonical(d)
    out = {"n": int(d.size), "n_zero": int((d == 0).sum()), "n_pos": int((d > 0).sum()), "n_neg": int((d < 0).sum())}
    if np.all(d == 0):
        return {**out, "status": "no difference; test not applicable"}
    res = st.wilcoxon(d, zero_method="pratt", alternative="two-sided", method="asymptotic")
    return {**out, "status": "estimated", "wilcoxon_stat": float(res.statistic), "p": float(res.pvalue)}

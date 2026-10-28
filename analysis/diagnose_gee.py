"""Diagnostics for P1 GEEs that are not estimable (ANALYSIS_PLAN §8), for the study team's decision at G4a.

For each instruction whose pre-specified GEE (Binomial, exchangeable, groups = task) is not estimable, this
reports why: factor levels with a constant outcome (separation), and the course of the exchangeable working
correlation and of the largest |coefficient| over the iterations. It also reports whether a GLM / independence
fit of the same mean model converges. It deliberately reports no Wald test, p-value or odds ratio of any
alternative estimator, so that the choice of a remedy cannot depend on its results.

Usage: python -m analysis.diagnose_gee   (writes results/report/p1_gee_diagnostics.md)
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from analysis.data import CONSTRAINTS, imported_run, load_eval, main_models
from analysis.report import CNAMES
from analysis.stats import _separation, gee_position
from src.common import RESULTS_DIR, atomic_write_text


def main() -> int:
    models = main_models()
    run_id = imported_run("main", analysis_eligible=True)
    order = load_eval("main", run_id, models).query("arm == 'order'")
    lines = ["# P1 GEE diagnostics (no tests of alternative estimators are computed)", "",
             f"Run `{run_id}`; order arm; mean model `y ~ C(position) + C(family) + C(model)`, groups = task "
             "(40 outputs per task: 4 models × 10 orders).", ""]
    for c in CONSTRAINTS:
        r = gee_position(order, c, models)
        lines.append(f"## {CNAMES[c]}: {r['status']}" + (f" ({r['reason']})" if r.get("reason") else ""))
        lines.append("")
        if r["status"] == "estimated":
            lines += ["The pre-specified GEE converged; nothing to diagnose.", ""]
            continue
        d = pd.DataFrame({"task_id": order.task_id.to_numpy(), "family": order.family.to_numpy(),
                          "model": order.model_key.to_numpy(), "position": order[f"pos_{c}"].to_numpy(),
                          "y": order[c].astype(int).to_numpy()})
        d = d[d.model.isin(r["models_included"])]
        sep = _separation(d, [["position"], ["family"], ["model"]])
        lines.append("- Factor levels with a constant outcome: " + ("; ".join(sep) if sep else "none") + ".")
        f = "y ~ C(position) + C(family)" + (" + C(model)" if len(r["models_included"]) > 1 else "")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            glm = smf.glm(f, data=d, family=sm.families.Binomial()).fit()
            lines.append(f"- GLM (independence) fit of the same mean model: converged = {glm.converged}, largest "
                         f"|coefficient| = {np.abs(glm.params).max():.2f}.")
            trace = []
            for it in (1, 2, 3, 4, 5, 6, 8, 10):
                cov = sm.cov_struct.Exchangeable()
                res = smf.gee(f, groups="task_id", data=d, family=sm.families.Binomial(), cov_struct=cov).fit(maxiter=it)
                rho = float(np.asarray(cov.dep_params))
                big = float(np.nanmax(np.abs(res.params))) if np.isfinite(res.params).any() else float("nan")
                trace.append(f"{it}: ρ = {rho:.3f}, max |coef| = {big:.3g}")
        lines.append("- Exchangeable GEE, iterations (maxiter → working correlation ρ, largest |coefficient|): "
                     + "; ".join(trace) + ".")
        lines.append("")
    atomic_write_text(RESULTS_DIR / "report" / "p1_gee_diagnostics.md", "\n".join(lines) + "\n")
    print("Wrote results/report/p1_gee_diagnostics.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Every reportable number of the frozen ANALYSIS_PLAN.md as a flat dict of stable dotted keys (summary.json).

Key scheme (implementation specification §6.7): proportions are fractions (0-1); `<stat>` ∈ {mean, ci_low,
ci_high}; `<model>` ∈ the four main models and `pooled` (pooled over models with equal weight; every model has the
same number of outputs per task). CIs are task-clustered bootstrap percentile intervals (analysis/bootstrap.py).
Unless a key says otherwise, an arm-specific quantity uses only that arm's 10 prompts per task.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import scipy.stats as st

from analysis.bootstrap import TaskBootstrap, bootstrap_p
from analysis.data import ARM_IDS, CONSTRAINTS, FAMILIES, ORDER_IDS, SLOT
from analysis.numerics import canonical
from analysis.stats import NOT_APPLICABLE, NOT_ESTIMABLE, bh, gee_position, p2_tests, p3_test
from src.evaluators.tags import TAG_ORDER
from src.orders import e2_informative_positions

FORMAT_TAGS = ("code_fence", "leading_text", "trailing_text", "invalid_json", "extra_keys")
E1_GROUPS = {"structural": ("format", "cardinality"), "lexical": ("length", "t4"), "content": ("verbatim",)}


def _put(s: dict, prefix: str, est: dict) -> None:
    for k, v in est.items():
        s[f"{prefix}.{k}"] = v


def _per_task(sub: pd.DataFrame, col: str, how: str, tasks: list[str]) -> pd.Series:
    return sub.groupby("task_id")[col].agg(how).reindex(tasks)


class Analysis:
    """Computes the summary from the main evaluation records (one row per prompt id and model)."""

    def __init__(self, df: pd.DataFrame, models: list[str], n_boot: int = 5000, seed: int = 20261003,
                 flags: dict[str, str] | None = None) -> None:
        self.models = list(models)
        self.flags = flags or {c: c for c in CONSTRAINTS}  # constraint -> column (cascade flags in E6a)
        self.df = df.copy()
        f = [self.flags[c] for c in CONSTRAINTS]
        self.df["_csr"] = self.df[f].mean(axis=1)
        self.df["_pcr"] = self.df[f].min(axis=1)
        tasks = self.df.drop_duplicates("task_id").sort_values("task_id")
        self.tasks = list(tasks.task_id)
        self.family_of = dict(zip(tasks.task_id, tasks.family))
        self.bs = TaskBootstrap(self.tasks, [self.family_of[t] for t in self.tasks], n_boot=n_boot, seed=seed)
        self.s: dict = {}
        self.notes: list[str] = []
        self._tv: dict[tuple[str, str], pd.DataFrame] = {}

    # ---- helpers --------------------------------------------------------------------------------------
    def arm(self, arm: str, model: str | None = None) -> pd.DataFrame:
        d = self.df[self.df.arm == arm]
        return d if model is None else d[d.model_key == model]

    def model_sets(self) -> list[tuple[str, list[str]]]:
        return [(m, [m]) for m in self.models] + [("pooled", self.models)]

    def _sum_count(self, sub: pd.DataFrame, col: str) -> tuple[np.ndarray, np.ndarray]:
        g = sub.groupby("task_id")[col]
        return self.bs.align(g.sum()), self.bs.align(g.count())

    def task_values(self, arm: str, model: str) -> pd.DataFrame:
        """Per task: PS, vector stability, pairwise flip rate, mean CSR (one model, one arm, 10 prompts)."""
        if (arm, model) in self._tv:
            return self._tv[(arm, model)]
        sub = self.arm(arm, model)
        f = [self.flags[c] for c in CONSTRAINTS]
        rows = {}
        for task, g in sub.groupby("task_id"):
            assert len(g) == 10, (model, arm, task)
            vec = [tuple(v) for v in g[f].to_numpy()]
            pairs = list(itertools.combinations(vec, 2))
            # Range the integer pass counts before division: equal ranges such
            # as 4/5 - 3/5 and 2/5 - 1/5 must have the same representation.
            counts = g[f].sum(axis=1).to_numpy(dtype=np.int64)
            rows[task] = {"ps": float(counts.max() - counts.min()) / len(f), "vsr": float(len(set(vec)) == 1),
                          "flip_rate": sum(a != b for a, b in pairs) / len(pairs), "csr": g._csr.mean(),
                          "pcr": g._pcr.mean()}
        self._tv[(arm, model)] = pd.DataFrame.from_dict(rows, orient="index").reindex(self.tasks)
        return self._tv[(arm, model)]

    # ---- S1 and descriptive compliance ----------------------------------------------------------------
    def s1(self, prefix: str = "main") -> None:
        for arm in ARM_IDS:
            tv = {m: self.task_values(arm, m) for m in self.models}
            for name, ms in self.model_sets():
                sub = self.arm(arm)[self.arm(arm).model_key.isin(ms)]
                _put(self.s, f"{prefix}.{arm}.{name}.csr", self.bs.estimate(*self._sum_count(sub, "_csr")))
                _put(self.s, f"{prefix}.{arm}.{name}.pcr", self.bs.estimate(*self._sum_count(sub, "_pcr")))
                for c in CONSTRAINTS:
                    _put(self.s, f"{prefix}.{arm}.{name}.compliance.{c}",
                         self.bs.estimate(*self._sum_count(sub, self.flags[c])))
                for metric in ("ps", "vsr", "flip_rate"):
                    num = sum(tv[m][metric].to_numpy() for m in ms)
                    _put(self.s, f"{prefix}.{arm}.{name}.{metric}", self.bs.estimate(num, np.full(len(num), len(ms))))

    def positions(self, prefix: str = "main.order", constraints=CONSTRAINTS) -> None:
        order = self.arm("order")
        for c in constraints:
            for name, ms in self.model_sets():
                sub = order[order.model_key.isin(ms)]
                for k in range(1, 6):
                    at = sub[sub[f"pos_{c}"] == k]
                    _put(self.s, f"{prefix}.{name}.position.{c}.{k}", self.bs.estimate(*self._sum_count(at, self.flags[c])))

    # ---- P1 and the S2 interaction GEE ----------------------------------------------------------------
    def gee_family(self, prefix: str, interaction: bool, constraints=CONSTRAINTS, rows: pd.DataFrame | None = None,
                   working: str = "exchangeable", exclude_constant_families: bool = False) -> dict:
        order = self.arm("order") if rows is None else rows
        results = {c: gee_position(order, c, self.models, flag=self.flags[c], interaction=interaction, working=working,
                                   exclude_constant_families=exclude_constant_families) for c in constraints}
        q = bh({c: r.get("p") for c, r in results.items()})
        for c, r in results.items():
            p = f"{prefix}.{c}"
            self.s[f"{p}.status"] = r["status"]
            self.s[f"{p}.excluded_models"] = r["excluded_models"]
            if "excluded_families" in r:
                self.s[f"{p}.excluded_families"] = r["excluded_families"]
            self.s[f"{p}.n"] = r["n"]
            if r.get("reason"):
                self.s[f"{p}.reason"] = r["reason"]
            if r["warnings"]:
                self.s[f"{p}.warnings"] = r["warnings"]
            if r["status"] == "estimated":
                self.s.update({f"{p}.wald_chi2": r["wald_chi2"], f"{p}.df": r["df"], f"{p}.p": r["p"],
                               f"{p}.q": q[c]})
                for k, orr in r.get("odds_ratios", {}).items():
                    _put(self.s, f"{p}.or.{k}", orr)
        return results

    # ---- P2 -------------------------------------------------------------------------------------------
    def p2(self, prefix: str = "main.tests") -> None:
        res = {}
        order = self.arm("order")
        for m in self.models:
            sub = order[order.model_key == m]
            csr = sub.pivot(index="task_id", columns="condition_id", values="_csr").reindex(self.tasks)[list(ORDER_IDS)]
            pcr = sub.pivot(index="task_id", columns="condition_id", values="_pcr").reindex(self.tasks)[list(ORDER_IDS)]
            res[m] = p2_tests(csr.to_numpy(dtype=float), pcr.to_numpy(dtype=float))
        for test, stat_key in (("friedman", "chi2"), ("cochran_q", "q")):
            q = bh({m: res[m][test].get("p") for m in self.models})
            for m in self.models:
                r = res[m][test]
                p = f"{prefix}.{test}.{m}"
                self.s[f"{p}.status"] = r["status"]
                if r["status"] == "estimated":
                    self.s.update({f"{p}.{stat_key}": r[stat_key], f"{p}.df": r["df"], f"{p}.p": r["p"], f"{p}.q_bh": q[m]})
                    if test == "friedman":
                        self.s[f"{p}.kendall_w"] = r["kendall_w"]

    # ---- P3 -------------------------------------------------------------------------------------------
    def p3(self, prefix: str = "main.p3") -> None:
        res, diffs = {}, {}
        for m in self.models:
            d = (self.task_values("order", m)["ps"] - self.task_values("format", m)["ps"]).to_numpy()
            diffs[m] = d
            res[m] = p3_test(d)
        q = bh({m: res[m].get("p") for m in self.models})
        for m in self.models:
            p = f"{prefix}.{m}"
            est = self.bs.estimate(diffs[m])
            self.s.update({f"{p}.mean_diff": est["mean"], f"{p}.ci_low": est["ci_low"], f"{p}.ci_high": est["ci_high"],
                           f"{p}.status": res[m]["status"], f"{p}.n": res[m]["n"], f"{p}.n_zero": res[m]["n_zero"],
                           f"{p}.n_pos": res[m]["n_pos"], f"{p}.n_neg": res[m]["n_neg"]})
            if res[m]["status"] == "estimated":
                self.s.update({f"{p}.wilcoxon_stat": res[m]["wilcoxon_stat"], f"{p}.p": res[m]["p"], f"{p}.q": q[m]})

    # ---- S2 -------------------------------------------------------------------------------------------
    def s2(self, prefix: str = "main.s2", interaction: bool = True) -> None:
        tv = {m: self.task_values("order", m) for m in self.models}
        pairs = list(itertools.combinations(self.models, 2))
        for metric in ("ps", "csr"):
            pvals, ests = {}, {}
            for a, b in pairs:
                d = (tv[a][metric] - tv[b][metric]).to_numpy()
                point, reps = self.bs.ratio(d)
                lo, hi = self.bs.percentile_ci(reps)
                ests[(a, b)] = {"mean": point, "ci_low": lo, "ci_high": hi, "p": bootstrap_p(reps)}
                pvals[(a, b)] = ests[(a, b)]["p"]
            q = bh(pvals)
            for (a, b), e in ests.items():
                _put(self.s, f"{prefix}.{a}_vs_{b}.{metric}_diff", {**e, "q": q[(a, b)]})
        if interaction:
            self.gee_family(f"{prefix}.interaction", interaction=True)

    # ---- S3 -------------------------------------------------------------------------------------------
    def s3(self, prefix: str = "main.quality") -> None:
        order = self.arm("order")
        for fam in FAMILIES:
            for m in self.models:
                sub = order[(order.model_key == m) & (order.family == fam)]
                num, den = self._sum_count(sub, "q_primary")
                _put(self.s, f"{prefix}.{fam}.{m}.q", self.bs.estimate(num, den))
                g = sub.groupby("task_id").q_primary
                tqs = (g.max() - g.min()).reindex(self.tasks)
                has = tqs.notna().to_numpy()
                _put(self.s, f"{prefix}.{fam}.{m}.tqs", self.bs.estimate(np.nan_to_num(tqs.to_numpy()), has.astype(float)))

    # ---- Exploratory ----------------------------------------------------------------------------------
    def e1(self, prefix: str = "main.exploratory.e1") -> None:
        order = self.arm("order")
        for group, cs in E1_GROUPS.items():
            for name, ms in self.model_sets():
                sub = order[order.model_key.isin(ms)]
                for k in range(1, 6):
                    num = np.zeros(len(self.tasks))
                    den = np.zeros(len(self.tasks))
                    for c in cs:
                        n_, d_ = self._sum_count(sub[sub[f"pos_{c}"] == k], self.flags[c])
                        num += np.nan_to_num(n_)
                        den += np.nan_to_num(d_)
                    _put(self.s, f"{prefix}.{group}.{name}.{k}", self.bs.estimate(num, den))

    def e2(self, prefix: str = "main.exploratory.e2") -> None:
        informative = {SLOT[slot]: positions for slot, positions in e2_informative_positions().items()}
        order = self.arm("order")
        for c, positions in informative.items():
            per_model = {}
            for m in self.models:
                sub = order[order.model_key == m]
                vals = {}
                for task, g in sub.groupby("task_id"):
                    diffs = []
                    for k in positions:
                        at = g[g[f"pos_{c}"] == k]
                        before = at[f"pos_{c}"] < at["pos_format"]
                        assert len(at) == 2 and before.sum() == 1, (m, task, c, k)
                        diffs.append(float(at[before][self.flags[c]].iloc[0]) - float(at[~before][self.flags[c]].iloc[0]))
                    vals[task] = float(np.mean(diffs))
                per_model[m] = pd.Series(vals).reindex(self.tasks).to_numpy()
                _put(self.s, f"{prefix}.{c}.{m}.diff", self.bs.estimate(per_model[m]))
            pooled = sum(per_model.values())
            _put(self.s, f"{prefix}.{c}.pooled.diff", self.bs.estimate(pooled, np.full(len(pooled), len(self.models))))
            self.s[f"{prefix}.{c}.informative_positions"] = positions

    def e3(self, difficulties: dict, prefix: str = "main.exploratory.e3") -> None:
        order = self.arm("order")
        pos = order.drop_duplicates("condition_id").set_index("condition_id")[[f"pos_{c}" for c in CONSTRAINTS]]
        for m in self.models:
            p = f"{prefix}.{m}"
            d = difficulties[m]["difficulty"]
            self.s[f"{p}.difficulty_source"] = f"{difficulties[m]['phase']}/{difficulties[m]['run_id']} (order arm)"
            for c in CONSTRAINTS:
                self.s[f"{p}.difficulty.{c}"] = d[c]
            dv = canonical([d[c] for c in CONSTRAINTS])
            if np.all(dv == dv[0]):
                self.s[f"{p}.status"] = "HE not estimable: all five difficulties are tied"
                continue
            he = {}
            for o in ORDER_IDS:
                he[o] = float(-st.spearmanr(pos.loc[o].to_numpy(dtype=float), dv).statistic)
                self.s[f"{p}.he.{o}"] = he[o]
            hev = np.array([he[o] for o in ORDER_IDS])
            sub = order[order.model_key == m]
            for outcome, col in (("csr", "_csr"), ("pcr", "_pcr")):
                mat = sub.pivot(index="task_id", columns="condition_id", values=col).reindex(self.tasks)[list(ORDER_IDS)]
                mat = mat.to_numpy(dtype=float)
                level = canonical(mat.mean(axis=0))
                key = f"{p}.he_vs_{outcome}"
                if np.all(hev == hev[0]) or np.all(level == level[0]):
                    self.s[f"{key}.status"] = NOT_APPLICABLE
                    continue
                rho = float(st.spearmanr(hev, level).statistic)
                reps_levels = (self.bs.counts @ mat) / self.bs.counts.sum(axis=1, keepdims=True)
                ra = st.rankdata(hev)
                rb = st.rankdata(canonical(reps_levels), axis=1)
                ra_c = ra - ra.mean()
                rb_c = rb - rb.mean(axis=1, keepdims=True)
                with np.errstate(invalid="ignore", divide="ignore"):
                    reps = (rb_c @ ra_c) / (np.sqrt((rb_c ** 2).sum(axis=1)) * np.sqrt((ra_c ** 2).sum()))
                lo, hi = self.bs.percentile_ci(reps)
                self.s.update({f"{key}.status": "estimated", f"{key}.rho": rho, f"{key}.ci_low": lo,
                               f"{key}.ci_high": hi})

    def e4(self, prefix: str = "main.exploratory.e4") -> None:
        for fam in FAMILIES:
            for m in self.models:
                tv = self.task_values("order", m)
                sub = self.arm("order", m)
                sub = sub[sub.family == fam]
                g = sub.groupby("task_id").q_primary
                tqs = (g.max() - g.min())
                ps = tv.loc[tqs.index, "ps"]
                key = f"{prefix}.{fam}.{m}"
                if tqs.nunique() < 2 or ps.nunique() < 2:
                    self.s[f"{key}.status"] = NOT_APPLICABLE
                else:
                    self.s.update({f"{key}.status": "estimated", f"{key}.rho_tqs_ps": float(st.spearmanr(tqs, ps).statistic),
                                   f"{key}.n_tasks": int(len(tqs))})

    def e5(self, prefix: str = "main.exploratory.e5") -> None:
        for arm in ARM_IDS:
            for m in self.models:
                sub = self.arm(arm, m)
                for tag in TAG_ORDER:
                    self.s[f"{prefix}.{arm}.{m}.{tag}"] = float(sub.error_tags.apply(lambda t: tag in t).mean())
        order = self.arm("order")
        for m in self.models:
            sub = order[order.model_key == m]
            for fam in FAMILIES:  # Q-C3 (decision G4b §2.1): invalid_json by family, order arm
                fs = sub[sub.family == fam]
                self.s[f"{prefix}.order.{m}.by_family.invalid_json.{fam}"] = float(
                    fs.error_tags.apply(lambda t: "invalid_json" in t).mean())
            for k in range(1, 6):
                at = sub[sub.pos_format == k]
                for tag in FORMAT_TAGS:
                    self.s[f"{prefix}.order.{m}.by_format_position.{tag}.{k}"] = float(at.error_tags.apply(lambda t: tag in t).mean())

    # ---- Post-hoc additions (decision G4a §2.1, §3.2, §3.3) ---------------------------------------------
    def p1_independence(self, prefix: str = "main.robustness.p1_independence") -> None:
        """Option B (post-hoc robustness, decision G4a §2.1): same mean model and clusters as P1, independence
        working correlation with robust SEs, constant models and constant family levels left out before fitting."""
        self.gee_family(prefix, interaction=False, working="independence", exclude_constant_families=True)
        self.s[f"{prefix}.label"] = "post-hoc robustness analysis (decision G4a §2.1), not a pre-specified test"

    def constraint_instability(self, prefix: str = "main.robustness.constraint_instability") -> None:
        """Post-hoc, descriptive (decision G4a §3.2): per model × constraint × arm, the share of tasks whose flag
        for that constraint is not constant across the arm's 10 prompts."""
        for arm in ARM_IDS:
            for name, ms in self.model_sets():
                for c in CONSTRAINTS:
                    num = np.zeros(len(self.tasks))
                    for m in ms:
                        g = self.arm(arm, m).groupby("task_id")[self.flags[c]].nunique()
                        num += self.bs.align(g > 1)
                    _put(self.s, f"{prefix}.{arm}.{name}.{c}", self.bs.estimate(num, np.full(len(num), len(ms))))
        self.s[f"{prefix}.label"] = "post-hoc descriptive analysis (decision G4a §3.2)"

    def presentation(self) -> None:
        """Keys for the table notes of decision G4a §3.3: evaluable rates per arm (overall and by family) and, for
        FORMAT, the pooled position profile over the models in the GEE sample (Gemma excluded)."""
        for arm in ARM_IDS:
            for m in self.models:
                sub = self.arm(arm, m)
                _put(self.s, f"main.{arm}.{m}.evaluable_rate", self.bs.estimate(*self._sum_count(sub, "evaluable")))
                for fam in FAMILIES:
                    self.s[f"main.{arm}.{m}.evaluable_rate_by_family.{fam}"] = float(sub[sub.family == fam].evaluable.mean())
        excluded = self.s.get("main.p1.format.excluded_models") or {}
        keep = [m for m in self.models if m not in excluded]
        name = "pooled_excl_" + "_".join(sorted(excluded)) if excluded else None
        if name:
            order = self.arm("order")
            sub = order[order.model_key.isin(keep)]
            for k in range(1, 6):
                at = sub[sub.pos_format == k]
                _put(self.s, f"main.order.{name}.position.format.{k}", self.bs.estimate(*self._sum_count(at, self.flags["format"])))
            self.s["main.order.format_gee_sample_pooled_key"] = name

    # ---- Checks and counts ----------------------------------------------------------------------------
    def counts(self, prefix: str = "main.counts") -> None:
        self.s[f"{prefix}.evaluation_records"] = int(len(self.df))
        self.s[f"{prefix}.tasks"] = len(self.tasks)
        self.s[f"{prefix}.models"] = len(self.models)
        for m in self.models:
            sub = self.df[self.df.model_key == m]
            self.s[f"{prefix}.{m}.evaluation_records"] = int(len(sub))
            self.s[f"{prefix}.{m}.truncated_rate"] = float((sub.finish_reason == "length").mean())
            self.s[f"{prefix}.{m}.evaluable_rate"] = float(sub.evaluable.mean())


def robustness(df: pd.DataFrame, models: list[str], n_boot: int, seed: int) -> dict:
    """E6 (exploratory robustness): key results of S1, P1-P3 under (a) cascade scoring and (b) the subset of
    outputs that pass FORMAT strictly; (c) the diagnostics containment_char and verbatim_min3."""
    s: dict = {}
    cascade = Analysis(df, models, n_boot, seed, flags={c: f"cascade_{c}" for c in CONSTRAINTS})
    cascade.s1(prefix="main.robustness.cascade")
    cascade.gee_family("main.robustness.cascade.p1", interaction=False)
    cascade.p2(prefix="main.robustness.cascade.tests")
    cascade.p3(prefix="main.robustness.cascade.p3")
    s.update(cascade.s)

    strict = df[df["format"] == 1]  # outputs that pass FORMAT strictly
    base = Analysis(df, models, n_boot, seed)
    for arm in ARM_IDS:
        for name, ms in base.model_sets():
            sub = strict[(strict.arm == arm) & strict.model_key.isin(ms)]
            key = f"main.robustness.strict_format.{arm}.{name}"
            s[f"{key}.n_outputs"] = int(len(sub))
            if sub.empty:
                s[f"{key}.status"] = "no output passes FORMAT strictly"
                continue
            sub = sub.assign(_csr=sub[list(CONSTRAINTS)].mean(axis=1), _pcr=sub[list(CONSTRAINTS)].min(axis=1))
            _put(s, f"{key}.csr", base.bs.estimate(*base._sum_count(sub, "_csr")))
            _put(s, f"{key}.pcr", base.bs.estimate(*base._sum_count(sub, "_pcr")))
            complete = sub.groupby(["task_id", "model_key"]).size()
            complete = complete[complete == 10].reset_index()[["task_id", "model_key"]]
            s[f"{key}.n_complete_task_model_pairs"] = int(len(complete))
            if len(complete):
                full = sub.merge(complete, on=["task_id", "model_key"])
                ps = full.groupby(["task_id", "model_key"])._csr.agg(lambda x: x.max() - x.min()).groupby("task_id")
                _put(s, f"{key}.ps", base.bs.estimate(base.bs.align(ps.sum()), base.bs.align(ps.count())))
    strict_order = strict[strict.arm == "order"]
    for c, r in {c: gee_position(strict_order, c, models) for c in CONSTRAINTS if c != "format"}.items():
        s[f"main.robustness.strict_format.p1.{c}.status"] = r["status"]
        s[f"main.robustness.strict_format.p1.{c}.excluded_models"] = r["excluded_models"]
        if r.get("reason"):
            s[f"main.robustness.strict_format.p1.{c}.reason"] = r["reason"]
        if r["status"] == "estimated":
            s.update({f"main.robustness.strict_format.p1.{c}.wald_chi2": r["wald_chi2"],
                      f"main.robustness.strict_format.p1.{c}.df": r["df"], f"main.robustness.strict_format.p1.{c}.p": r["p"]})

    for m in models:
        for arm in ARM_IDS:
            sub = base.arm(arm, m)
            _put(s, f"main.robustness.diagnostics.{arm}.{m}.verbatim_min3", base.bs.estimate(*base._sum_count(sub, "verbatim_min3")))
            _put(s, f"main.robustness.diagnostics.{arm}.{m}.verbatim_case_insensitive",
                 base.bs.estimate(*base._sum_count(sub, "verbatim_case_insensitive")))
        f1 = base.arm("order", m)
        f1 = f1[f1.family == "F1_QA"].assign(cc=lambda x: x.containment_char.fillna(0).astype(float))
        _put(s, f"main.robustness.diagnostics.order.{m}.f1_containment_char", base.bs.estimate(*base._sum_count(f1, "cc")))
    return s

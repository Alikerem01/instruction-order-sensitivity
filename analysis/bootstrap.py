"""Task-clustered bootstrap (ANALYSIS_PLAN §8; implementation specification §6.5).

Tasks are resampled with replacement within each family (20 per family); all prompts, arms and models of a task
move together; 5,000 replicates; seed 20261003; percentile intervals. One set of replicates serves every
statistic, so paired analyses automatically resample the same tasks for both quantities.

A statistic is given as per-task numerators and denominators (for example passes and outputs of one task); its
value is sum(numerators) / sum(denominators) over the (resampled) tasks. With equal denominators this is the mean
of the per-task means.
"""

from __future__ import annotations

import numpy as np


class TaskBootstrap:
    def __init__(self, task_ids: list[str], families: list[str], n_boot: int = 5000, seed: int = 20261003,
                 level: float = 0.95) -> None:
        self.task_ids = list(task_ids)
        self.families = np.asarray(families)
        self.index = {t: i for i, t in enumerate(self.task_ids)}
        self.n_boot, self.level = n_boot, level
        rng = np.random.default_rng(seed)
        counts = np.zeros((n_boot, len(self.task_ids)), dtype=np.float64)
        for fam in sorted(set(families)):
            members = np.flatnonzero(self.families == fam)
            draws = members[rng.integers(0, len(members), size=(n_boot, len(members)))]
            rows = np.repeat(np.arange(n_boot), len(members))
            np.add.at(counts, (rows, draws.ravel()), 1.0)
        self.counts = counts  # counts[b, t] = how often task t is drawn in replicate b

    def align(self, series) -> np.ndarray:
        """Per-task values (a pandas Series indexed by task id) in the bootstrap's task order."""
        return series.reindex(self.task_ids).to_numpy(dtype=float)

    def ratio(self, num: np.ndarray, den: np.ndarray | None = None) -> tuple[float, np.ndarray]:
        """Point estimate and bootstrap replicates of sum(num) / sum(den); den defaults to one per task.
        Tasks with a zero denominator (no observation) do not contribute."""
        num = np.nan_to_num(np.asarray(num, dtype=float))  # a task without observations contributes 0 / 0
        den = np.ones_like(num) if den is None else np.nan_to_num(np.asarray(den, dtype=float))
        num = np.where(den > 0, num, 0.0)
        point = num.sum() / den.sum() if den.sum() > 0 else float("nan")
        with np.errstate(invalid="ignore", divide="ignore"):
            reps = (self.counts @ num) / (self.counts @ den)
        return float(point), reps

    def percentile_ci(self, reps: np.ndarray) -> tuple[float, float]:
        alpha = (1 - self.level) / 2
        reps = reps[np.isfinite(reps)]
        if reps.size == 0:
            return float("nan"), float("nan")
        lo, hi = np.percentile(reps, [100 * alpha, 100 * (1 - alpha)])
        return float(lo), float(hi)

    def estimate(self, num: np.ndarray, den: np.ndarray | None = None) -> dict:
        point, reps = self.ratio(num, den)
        lo, hi = self.percentile_ci(reps)
        return {"mean": point, "ci_low": lo, "ci_high": hi}


def bootstrap_p(reps: np.ndarray) -> float:
    """Two-sided bootstrap p-value of a difference (decision D05 §3):
    p = min(1, 2 · min(#{Δ*_b ≤ 0} + 1, #{Δ*_b ≥ 0} + 1) / (B + 1))."""
    reps = np.asarray(reps, dtype=float)
    b = reps.size
    return float(min(1.0, 2 * min((reps <= 0).sum() + 1, (reps >= 0).sum() + 1) / (b + 1)))

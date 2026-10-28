"""Canonical values for equality/sign/rank decisions in this study (v3.1 correction).

Compliance comes from five binary flags and ten prompts per task. Decimal
subtraction and BLAS accumulation can turn an exact tie into a residual around
1e-16. Twelve decimal places are far finer than the resolution of these study
statistics, but remove those residuals. This is not display rounding and must
not be used to round arbitrary new continuous outcomes without a resolution
check. Original flags, raw outputs and estimands are unchanged.
"""
import numpy as np

TIE_DECIMALS = 12


def canonical(values):
    return np.round(np.asarray(values, dtype=float), TIE_DECIMALS)

"""Metrics for AI advisor panels.

Effective number of independent advisors. If n advisors' errors have average
pairwise correlation rho, the error variance of their average equals that of
n_eff = n / (1 + (n - 1) * rho) fully independent advisors (the Kish design
effect; the same algebra underlies the wisdom-of-crowds results of Surowiecki
and Lorenz et al., PNAS 2011). n_eff = n means five real opinions; n_eff = 1
means one opinion said five times.

Corroboration premium. A reader who takes agreeing advisors as independent
witnesses combines them like independent evidence:
    logit(p_naive) = logit(b) + sum_j [logit(p_j) - logit(b)],
with b the base rate. We compare how confident that reading is with how often
it is right.
"""
from __future__ import annotations

import numpy as np

EPS = 0.01


def logit(p):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def expit(x):
    return 1 / (1 + np.exp(-np.asarray(x, float)))


def brier(p, y) -> float:
    return float(np.mean((np.asarray(p, float) - np.asarray(y, float)) ** 2))


def log_loss(p, y) -> float:
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def mean_pairwise_corr(E: np.ndarray) -> float:
    """E: questions x advisors matrix of errors (p - y). Mean off-diagonal Pearson correlation."""
    C = np.corrcoef(E, rowvar=False)
    n = C.shape[0]
    off = C[~np.eye(n, dtype=bool)]
    return float(np.nanmean(off))


def conditional_corr(P: np.ndarray, y: np.ndarray) -> float:
    """Mean pairwise correlation of advisors' logit forecasts *within* each outcome class.

    Treating agreeing advisors as independent witnesses (the naive pool below,
    Condorcet, naive Bayes) assumes they are conditionally independent given
    the truth. This is the correlation that assumption sets to zero. Raw error
    correlation (p - y) is dominated by the shared outcome term and is close
    to 1 for almost any panel, so we report it only as a secondary number.
    """
    L = logit(P)
    tot, w = 0.0, 0
    for c in (0, 1):
        Lc = L[y == c]
        if len(Lc) < 4:
            continue
        sd = Lc.std(axis=0)
        keep = sd > 1e-9  # an advisor who never varies carries no correlation information
        if keep.sum() < 2:
            continue
        C = np.corrcoef(Lc[:, keep], rowvar=False)
        off = C[~np.eye(C.shape[0], dtype=bool)]
        tot += np.nanmean(off) * len(Lc)
        w += len(Lc)
    return float(tot / w) if w else float("nan")


def n_eff(rho: float, n: int = 5) -> float:
    return float(n / (1 + (n - 1) * rho))


def n_eff_variance(E: np.ndarray) -> float:
    """Assumption-light version: mean individual error variance / variance of the averaged error."""
    ind = np.mean(np.var(E, axis=0, ddof=1))
    avg = np.var(E.mean(axis=1), ddof=1)
    return float(ind / avg) if avg > 0 else float("inf")


def naive_pool(P: np.ndarray, base: float) -> np.ndarray:
    """Treat each advisor as independent evidence (what agreement 'feels like')."""
    lb = logit(base)
    return expit(lb + np.sum(logit(P) - lb, axis=1))


def neff_pool(P: np.ndarray, base: float, neff: float) -> np.ndarray:
    """Count the panel as neff independent advisors instead of n."""
    n = P.shape[1]
    lb = logit(base)
    return expit(lb + (neff / n) * np.sum(logit(P) - lb, axis=1))


def unanimity(P: np.ndarray, y: np.ndarray, thr: float = 0.5) -> dict:
    """How often a panel whose members all lean the same way is right."""
    side = P > thr
    unan = side.all(axis=1) | (~side).all(axis=1)
    if unan.sum() == 0:
        return {"share": 0.0, "acc": float("nan"), "k": 0}
    pred = side[:, 0][unan]
    return {"share": float(unan.mean()), "acc": float(np.mean(pred == y[unan].astype(bool))), "k": int(unan.sum())}


def bootstrap(fn, idx_n: int, B: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% percentile CI of fn(indices) resampling questions."""
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(B):
        ix = rng.integers(0, idx_n, idx_n)
        try:
            vals.append(fn(ix))
        except Exception:
            continue
    vals = np.array([v for v in vals if np.isfinite(v)])
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))

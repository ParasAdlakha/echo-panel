"""Summarise panel forecasts: accuracy, error correlation, effective N, corroboration premium.

    python -m echo.analyze            # prints a table and writes results/summary.json
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from . import metrics as M

ROOT = Path(__file__).resolve().parents[1]
FORECASTS = ROOT / "results" / "forecasts.jsonl"
SUMMARY = ROOT / "results" / "summary.json"


def load(path: Path = FORECASTS) -> dict[tuple, dict]:
    """Latest complete panel per (cond, base, qid), from forecasts*.jsonl."""
    panels: dict[tuple, dict] = {}
    lines = [l for f in sorted(path.parent.glob("forecasts*.jsonl")) for l in f.read_text(encoding="utf-8").splitlines()]
    for line in lines:
        if not line.strip():
            continue
        r = json.loads(line)
        ps = [a["p"] for a in r["answers"]]
        if len(ps) == 5 and all(p is not None for p in ps):
            panels[(r["cond"], r["base"], r["qid"])] = r
    return panels


def matrices(panels: dict, cond: str, base) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    rows = sorted((k, v) for k, v in panels.items() if k[0] == cond and k[1] == base)
    P = np.array([[a["p"] for a in v["answers"]] for _, v in rows])
    y = np.array([v["outcome"] for _, v in rows], float)
    c = np.array([v["crowd"] for _, v in rows], float)
    return P, y, c, [k[2] for k, _ in rows]


def summarise(P: np.ndarray, y: np.ndarray, crowd: np.ndarray, base_rate: float) -> dict:
    E = P - y[:, None]
    rho = M.conditional_corr(P, y)
    rho_err = M.mean_pairwise_corr(E)
    ne = M.n_eff(rho, P.shape[1])
    mean_p = P.mean(axis=1)
    naive = M.naive_pool(P, base_rate)
    k = len(y)
    out = {
        "k": k,
        "brier_individual": float(np.mean([M.brier(P[:, j], y) for j in range(P.shape[1])])),
        "brier_mean": M.brier(mean_p, y),
        "brier_naive": M.brier(naive, y),
        "brier_neff": M.brier(M.neff_pool(P, base_rate, ne), y),
        "brier_crowd": M.brier(crowd, y),
        "logloss_naive": M.log_loss(naive, y),
        "logloss_mean": M.log_loss(mean_p, y),
        "rho": rho,
        "rho_err": rho_err,
        "n_eff": ne,
        "n_eff_var": M.n_eff_variance(E),
        "spread_sd": float(np.mean(P.std(axis=1))),
        "naive_confidence": float(np.mean(np.abs(naive - 0.5)) * 2),
        "naive_accuracy": float(np.mean((naive > 0.5) == y.astype(bool))),
        "rho_with_crowd": M.conditional_corr(np.c_[mean_p, crowd], y),
        "brier_blend": M.brier((mean_p + crowd) / 2, y),
        "unanimity": M.unanimity(P, y),
    }
    out["rho_ci"] = M.bootstrap(lambda ix: M.conditional_corr(P[ix], y[ix]), k)
    out["n_eff_ci"] = tuple(sorted(M.n_eff(r, P.shape[1]) for r in out["rho_ci"]))
    out["premium_brier"] = out["brier_naive"] - out["brier_mean"]
    out["premium_ci"] = M.bootstrap(
        lambda ix: M.brier(M.naive_pool(P[ix], base_rate), y[ix]) - M.brier(P[ix].mean(axis=1), y[ix]), k)
    return out


PRIOR = 0.5  # the "independent witnesses" reader starts from even odds; fixed in advance, not fitted
MAIN = [("brief-oa", None), ("discuss-oa", None), ("discuss-r1-oa", None), ("mixed-oa", None),
        ("personas", "gpt-4.1-mini"), ("personas", "gpt-5.4-mini"),
        ("samples", "gpt-4.1-mini"), ("samples", "gpt-5.4-mini")]


def first_round(panels: dict) -> dict:
    """Recover the pre-discussion answers stored with each 'discuss' panel."""
    out = {}
    for k, v in panels.items():
        if k[0].startswith("discuss") and all(a.get("first_p") is not None for a in v["answers"]):
            out[(k[0].replace("discuss", "discuss-r1"), None, k[2])] = dict(v, answers=[{"p": a["first_p"]} for a in v["answers"]])
    return out


def main() -> None:
    panels = load()
    panels.update(first_round(panels))
    # Main design: the OpenAI panels, complete on all 190 questions. The cross-developer panels
    # (cond names without "-oa") are summarised separately on the questions they completed, and
    # partial pilot panels (e.g. Gemma 4 sampled five times) are left out.
    groups = [g for g in MAIN if any((g[0], g[1]) == (k[0], k[1]) for k in panels)]
    common = set.intersection(*[{k[2] for k in panels if (k[0], k[1]) == g} for g in groups])
    res = {}
    print(f"{len(common)} questions answered by every panel type")
    hdr = (f"{'panel':<40}{'k':>4}{'rho|y':>7}{'rho_e':>7}{'n_eff':>7}{'95% CI':>12}{'B_ind':>7}{'B_mean':>8}"
           f"{'B_naive':>8}{'prem':>7}{'B_crowd':>8}{'B_blend':>8}{'unan':>6}{'acc':>6}")
    print(hdr)
    for cond, base in groups:
        sub = {k: v for k, v in panels.items() if k[2] in common}
        P, y, c, _ = matrices(sub, cond, base)
        if len(y) < 8:
            continue
        s = summarise(P, y, c, PRIOR)
        name = f"{cond}" + (f" [{base}]" if base else "")
        res[name] = s
        ci = f"{s['n_eff_ci'][0]:.1f}-{s['n_eff_ci'][1]:.1f}"
        print(f"{name:<40}{s['k']:>4}{s['rho']:>7.2f}{s['rho_err']:>7.2f}{s['n_eff']:>7.2f}{ci:>12}"
              f"{s['brier_individual']:>7.3f}{s['brier_mean']:>8.3f}{s['brier_naive']:>8.3f}{s['premium_brier']:>7.3f}"
              f"{s['brier_crowd']:>8.3f}{s['brier_blend']:>8.3f}{s['unanimity']['share']:>6.2f}{s['unanimity']['acc']:>6.2f}")
    xdev = {}
    print("\ncross-developer panel (gpt-4.1-mini, gpt-5.4-mini, Gemma 4 31B, Qwen 3.8 27B, Nemotron 3.5 30B), own questions")
    for cond in ("mixed", "discuss-r1", "discuss", "brief"):
        P, y, c, _ = matrices(panels, cond, None)
        if len(y) < 30:
            continue
        s = summarise(P, y, c, PRIOR)
        xdev[cond] = s
        print(f"{cond:<40}{s['k']:>4}{s['rho']:>7.2f}{s['rho_err']:>7.2f}{s['n_eff']:>7.2f}"
              f"{s['n_eff_ci'][0]:>6.2f}-{s['n_eff_ci'][1]:.2f}{s['brier_mean']:>8.3f}{s['unanimity']['share']:>6.2f}"
              f"{s['unanimity']['acc']:>6.2f}")
    SUMMARY.write_text(json.dumps({"prior": PRIOR, "k_common": len(common), "panels": res, "cross_developer": xdev},
                                  indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

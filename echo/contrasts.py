"""Paired contrasts between panel types on the same questions (bootstrap over questions).

    python -m echo.contrasts
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from . import metrics as M
from .analyze import first_round, load, matrices

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "contrasts.json"

PAIRS = [
    ("discuss-oa", None, "discuss-r1-oa", None, "Five OpenAI models: after vs before discussion"),
    ("brief-oa", None, "mixed-oa", None, "Five OpenAI models: shared brief vs none"),
    ("mixed-oa", None, "personas", "gpt-5.4-mini", "Five OpenAI models vs five personas (gpt-5.4-mini)"),
    ("mixed-oa", None, "samples", "gpt-5.4-mini", "Five OpenAI models vs one model ×5 (gpt-5.4-mini)"),
    ("personas", "gpt-4.1-mini", "samples", "gpt-4.1-mini", "Personas vs samples (gpt-4.1-mini)"),
    ("personas", "gpt-5.4-mini", "samples", "gpt-5.4-mini", "Personas vs samples (gpt-5.4-mini)"),
    ("discuss", None, "discuss-r1", None, "Four developers: after vs before discussion"),
    ("brief", None, "mixed", None, "Four developers: shared brief vs none"),
]


def unan_share(P):
    s = P > 0.5
    return float((s.all(1) | (~s).all(1)).mean())


def stats(P, y):
    return {"n_eff": M.n_eff(M.conditional_corr(P, y)), "brier": M.brier(P.mean(1), y), "unan": unan_share(P),
            "spread": float(P.std(1).mean())}


def main() -> None:
    panels = load()
    panels.update(first_round(panels))
    res = {}
    rng = np.random.default_rng(1)
    for a, ab, b, bb, label in PAIRS:
        Pa, ya, _, qa = matrices(panels, a, ab)
        Pb, yb, _, qb = matrices(panels, b, bb)
        common = sorted(set(qa) & set(qb))
        if len(common) < 30:
            continue
        ia = [qa.index(q) for q in common]
        ib = [qb.index(q) for q in common]
        Pa, Pb, y = Pa[ia], Pb[ib], ya[ia]
        sa, sb = stats(Pa, y), stats(Pb, y)
        boots = {k: [] for k in sa}
        for _ in range(2000):
            ix = rng.integers(0, len(y), len(y))
            x, z = stats(Pa[ix], y[ix]), stats(Pb[ix], y[ix])
            for k in sa:
                boots[k].append(x[k] - z[k])
        res[label] = {"k": len(y), "a": sa, "b": sb,
                      "diff": {k: [sa[k] - sb[k], *np.percentile(v, [2.5, 97.5]).tolist()] for k, v in boots.items()}}
        d = res[label]["diff"]
        print(f"{label:<52} k={len(y):<4}" + "  ".join(f"Δ{k} {v[0]:+.3f} [{v[1]:+.3f},{v[2]:+.3f}]" for k, v in d.items()))
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

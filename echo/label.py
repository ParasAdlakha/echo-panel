"""The independence label, tested on an AI decision-maker.

A decision-maker model reads a panel's five forecasts and reasons and gives a
final probability. Four arms differ only in one note under the panel:

  none      no note
  generic   "These advisors may not be independent of each other."
  label     the panel's measured independence: "together they carry about the
            information of N independent advisors", with N estimated on the
            other folds of questions (5-fold, so no question informs its own label)
  inflated  the same wording with N = 5.0 (a false claim of full independence);
            a dose-response check and a dual-use demonstration

    python -m echo.label --panel samples --base adaption/gemma-4-31b-it --dm adaption/qwen3.8-27b
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from . import metrics as M
from .analyze import load, matrices
from .llm import USAGE, chat
from .panels import _p, load_questions, question_text

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "decisions.jsonl"
ARMS = ["none", "generic", "label", "inflated"]

DM_SYSTEM = ("You are helping a person make a decision that depends on whether this question resolves YES. "
             "You have asked a panel of five AI advisors. Weigh their answers and give your own final forecast. "
             "Answer only with JSON: {\"p\": <final probability from 0 to 1>, \"why\": \"<one sentence>\"}.")


def note(arm: str, neff: float, rho: float) -> str:
    if arm == "none":
        return ""
    if arm == "generic":
        return "Note: these advisors may not be independent of each other."
    n = 5.0 if arm == "inflated" else neff
    r = 0.0 if arm == "inflated" else max(rho, 0.0)
    return (f"Independence label: on past questions, the errors of these five advisors were correlated "
            f"(average r = {r:.2f}). Together they carry about the information of {n:.1f} independent advisors, "
            f"not 5.")


def fold_neff(P: np.ndarray, y: np.ndarray, k_folds: int = 5) -> tuple[np.ndarray, np.ndarray]:
    """Per-question n_eff and rho (conditional on outcome) estimated without that question's fold."""
    k = len(P)
    folds = np.arange(k) % k_folds
    ne, rh = np.zeros(k), np.zeros(k)
    for f in range(k_folds):
        rho = M.conditional_corr(P[folds != f], y[folds != f])
        ne[folds == f], rh[folds == f] = M.n_eff(rho, P.shape[1]), rho
    return ne, rh


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default="samples")
    ap.add_argument("--base", default="adaption/gemma-4-31b-it")
    ap.add_argument("--dm", default="adaption/qwen3.8-27b")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    base = None if a.base in ("", "none") else a.base
    panels = load()
    P, y, _, qids = matrices(panels, a.panel, base)
    ne, rh = fold_neff(P, y)
    qs = {q["id"]: q for q in load_questions()}
    jobs = [(i, arm) for i in range(len(qids)) for arm in a.arms.split(",")]

    def work(job):
        i, arm = job
        q = qs[qids[i]]
        ans = panels[(a.panel, base, qids[i])]["answers"]
        lines = "\n".join(f"- Advisor {j + 1}: p = {x['p']:.2f}. {x['why']}" for j, x in enumerate(ans))
        user = f"{question_text(q)}\n\nThe panel's answers:\n{lines}"
        nt = note(arm, ne[i], rh[i])
        if nt:
            user += f"\n\n{nt}"
        msgs = [{"role": "system", "content": DM_SYSTEM}, {"role": "user", "content": user}]
        p = None
        for retry in range(3):
            p, why = _p(chat(a.dm, msgs, seed=retry))
            if p is not None:
                break
        return {"panel": a.panel, "base": base, "dm": a.dm, "arm": arm, "qid": qids[i], "outcome": int(y[i]),
                "panel_mean": float(P[i].mean()), "n_eff_label": float(ne[i]), "p": p}

    with ThreadPoolExecutor(a.workers) as ex, open(OUT, "a", encoding="utf-8") as f:
        for row in ex.map(work, jobs):
            f.write(json.dumps(row) + "\n")
    print("usage:", json.dumps(USAGE))


if __name__ == "__main__":
    main()

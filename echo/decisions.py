"""Summarise the AI decision-maker arms (none / generic / label / inflated).

    python -m echo.decisions
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEC = ROOT / "results" / "decisions.jsonl"
OUT = ROOT / "results" / "decisions_summary.json"
ARMS = ["none", "generic", "label", "inflated"]


def main() -> None:
    rows = [json.loads(l) for l in DEC.read_text(encoding="utf-8").splitlines() if l.strip()]
    by = defaultdict(dict)  # (panel, base, dm, qid) -> arm -> row (last wins)
    for r in rows:
        if r["p"] is not None:
            by[(r["panel"], r["base"], r["dm"], r["qid"])][r["arm"]] = r
    cells = defaultdict(list)
    for (panel, base, dm, qid), arms in by.items():
        if all(a in arms for a in ARMS):
            cells[(panel, base, dm)].append(arms)
    res = {}
    rng = np.random.default_rng(0)
    print(f"{'panel':<34}{'dm':<14}{'k':>4}  " + "".join(f"{a:>10}" for a in ARMS) + f"{'panel':>9}{'lab-none':>10}{'95% CI':>18}{'|shift|':>9}")
    for key, items in sorted(cells.items(), key=lambda kv: str(kv[0])):
        y = np.array([it["none"]["outcome"] for it in items], float)
        m = np.array([it["none"]["panel_mean"] for it in items])
        B = {a: (np.array([it[a]["p"] for it in items]) - y) ** 2 for a in ARMS}
        d = B["label"] - B["none"]
        boots = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
        lo, hi = np.percentile(boots, [2.5, 97.5])
        p_none = np.array([it["none"]["p"] for it in items])
        shift = float(np.mean(np.abs(p_none - 0.5) - np.abs(m - 0.5)))  # >0: more extreme than the panel mean
        name = f"{key[0]} [{key[1]}]"
        res[f"{name} | {key[2]}"] = {"k": len(items), **{f"brier_{a}": float(B[a].mean()) for a in ARMS},
                                     "brier_panel_mean": float(((m - y) ** 2).mean()), "label_minus_none": float(d.mean()),
                                     "ci": [float(lo), float(hi)], "extremity_shift_none": shift,
                                     "mean_abs_move_label_vs_none": float(np.mean(np.abs(np.array([it['label']['p'] for it in items]) - p_none))),
                                     "mean_abs_move_inflated_vs_none": float(np.mean(np.abs(np.array([it['inflated']['p'] for it in items]) - p_none)))}
        print(f"{name:<34}{key[2][:13]:<14}{len(items):>4}  " + "".join(f"{B[a].mean():>10.3f}" for a in ARMS)
              + f"{((m - y) ** 2).mean():>9.3f}{d.mean():>10.4f}{f'[{lo:.3f}, {hi:.3f}]':>18}{shift:>9.3f}")
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Paper figures from results/summary.json and results/decisions_summary.json.

    python -m echo.figures
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "img"
BLUE, ORANGE, AQUA, GREY, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#0b0b0b", "#52514e", "#e6e5e0"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": GREY, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 220, "savefig.bbox": "tight",
})

LABELS = {
    "samples [gpt-4.1-mini]": "Same model ×5 · gpt-4.1-mini",
    "samples [gpt-5.4-mini]": "Same model ×5 · gpt-5.4-mini",
    "samples [adaption/gemma-4-31b-it]": "Same model ×5 · Gemma 4 31B",
    "personas [gpt-4.1-mini]": "Five personas · gpt-4.1-mini",
    "personas [gpt-5.4-mini]": "Five personas · gpt-5.4-mini",
    "personas [adaption/gemma-4-31b-it]": "Five personas · Gemma 4 31B",
    "mixed-oa": "Five OpenAI models",
    "discuss-r1-oa": "Five OpenAI models · before discussion",
    "discuss-oa": "Five OpenAI models · after one round of discussion",
    "brief-oa": "Five OpenAI models · after a shared brief",
    "mixed": "Five models, four developers",
    "discuss-r1": "Five models · before discussion",
    "discuss": "Five models · after one round of discussion",
    "brief": "Five models · after a shared brief",
}
ORDER = [k for k in LABELS if not k.startswith("discuss-r1")]  # round 1 = the plain mixed panel
FAMILY = {"samples": BLUE, "personas": BLUE, "mixed": AQUA, "discuss-r1": AQUA, "discuss": ORANGE, "brief": ORANGE,
          "mixed-oa": AQUA, "discuss-r1-oa": AQUA, "discuss-oa": ORANGE, "brief-oa": ORANGE}


def _panels():
    s = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))
    rows = [(k, s["panels"][k]) for k in ORDER if k in s["panels"]]
    return s, rows


def fig_neff():
    s, rows = _panels()
    fig, ax = plt.subplots(figsize=(6.6, 0.42 * len(rows) + 1.0))
    for i, (k, v) in enumerate(rows):
        c = FAMILY[k.split(" ")[0]]
        lo, hi = v["n_eff_ci"]
        ax.plot([lo, hi], [i, i], color=c, lw=2, solid_capstyle="round")
        ax.scatter([v["n_eff"]], [i], s=46, color=c, zorder=3, edgecolor="white", linewidth=1.5)
        ax.text(hi + 0.08, i, f"{v['n_eff']:.2f}", va="center", fontsize=8.5, color=INK)
    ax.axvline(5, color=GREY, lw=1, ls=(0, (3, 3)))
    ax.text(4.95, 0.02, "five independent\nadvisors", ha="right", va="bottom", fontsize=8, color=MUTED,
            transform=ax.get_xaxis_transform())
    ax.axvline(1, color=GREY, lw=1, ls=(0, (3, 3)))
    ax.text(1.05, 0.995, "one opinion", ha="left", va="top", fontsize=8, color=MUTED,
            transform=ax.get_xaxis_transform())
    ax.set_yticks(range(len(rows)), [LABELS[k] for k, _ in rows])
    ax.invert_yaxis()
    ax.set_xlim(0.8, 5.2)
    ax.set_xlabel("Effective number of independent advisors (of 5), with 95% bootstrap CI")
    ax.set_title(f"How many opinions does a five-advisor panel carry?  (n = {s['k_common']} questions)",
                 loc="left", fontsize=10.5, color=INK)
    ax.grid(axis="y", visible=False)
    fig.savefig(IMG / "fig2_neff.png")
    plt.close(fig)


def fig_premium():
    s, rows = _panels()
    rows = [(k, v) for k, v in rows if k != "discuss-r1"]
    fig, ax = plt.subplots(figsize=(6.6, 0.42 * len(rows) + 1.2))
    crowd = rows[0][1]["brier_crowd"]
    for i, (k, v) in enumerate(rows):
        a, b = v["brier_mean"], v["brier_naive"]
        ax.annotate("", xy=(b, i), xytext=(a, i), arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=1.6,
                                                                   shrinkA=4, shrinkB=2))
        ax.scatter([a], [i], s=40, color=BLUE, zorder=3, edgecolor="white", linewidth=1.5)
        ax.text(max(a, b) + 0.006, i, f"+{b - a:.3f}" if b >= a else f"{b - a:.3f}", va="center", fontsize=8.2,
                color=MUTED)
    xs = [x for _, v in rows for x in (v["brier_mean"], v["brier_naive"])] + [crowd, 0.25]
    ax.set_xlim(min(xs) - 0.01, max(xs) + 0.035)
    tr = ax.get_xaxis_transform()
    ax.axvline(crowd, color=GREY, lw=1.2)
    left, right = (crowd, 0.25) if crowd <= 0.25 else (0.25, crowd)
    ax.text(left, 1.01, (f"human market crowd {crowd:.3f} " if left == crowd else "always 50% "), ha="right",
            va="bottom", fontsize=7.8, color=MUTED, transform=tr)
    ax.text(right, 1.01, (" always 50%" if right == 0.25 else f" human market crowd {crowd:.3f}"), ha="left",
            va="bottom", fontsize=7.8, color=MUTED, transform=tr)
    ax.axvline(0.25, color=GREY, lw=1, ls=(0, (3, 3)))
    ax.set_yticks(range(len(rows)), [LABELS[k] for k, _ in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Brier score (lower is better)")
    ax.scatter([], [], s=40, color=BLUE, label="average the five advisors")
    ax.plot([], [], color=ORANGE, lw=1.6, label="count them as five independent witnesses (arrow)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.4, -0.16), ncol=2, frameon=False, fontsize=8.2)
    ax.set_title("The cost of reading agreement as corroboration", loc="left", fontsize=10.5, color=INK, pad=26)
    ax.grid(axis="y", visible=False)
    fig.savefig(IMG / "fig3_premium.png")
    plt.close(fig)


def fig_discussion():
    s = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))["panels"]
    keys = [("mixed-oa", "No exchange"), ("brief-oa", "Shared brief"), ("discuss-oa", "One round of discussion")]
    keys = [(k, l) for k, l in keys if k in s]
    fig, axes = plt.subplots(1, 3, figsize=(8.6, 2.5))
    metrics = [("n_eff", "Effective independent advisors", lambda v: v["n_eff"], (1, 1.6)),
               ("unan", "All five agree (share of questions)", lambda v: v["unanimity"]["share"], (0.4, 0.9)),
               ("acc", "Unanimous and right (share)", lambda v: v["unanimity"]["acc"], (0.4, 0.9))]
    cols = [AQUA, BLUE, ORANGE]
    for ax, (_, title, f, lim) in zip(axes, metrics):
        vals = [f(s[k]) for k, _ in keys]
        ax.barh(range(len(keys)), vals, color=cols[:len(keys)], height=0.55)
        for i, v in enumerate(vals):
            ax.text(v + (lim[1] - lim[0]) * 0.02, i, f"{v:.2f}" if title.startswith("Eff") else f"{v:.0%}",
                    va="center", fontsize=8.5, color=INK)
        ax.set_xlim(lim[0], lim[1] + (lim[1] - lim[0]) * 0.15)
        ax.set_yticks(range(len(keys)), [l for _, l in keys] if ax is axes[0] else [""] * len(keys))
        ax.invert_yaxis()
        ax.set_title(title, fontsize=8.8, loc="left")
        ax.grid(axis="y", visible=False)
    fig.suptitle("Five OpenAI models: talking makes them agree, not get it right", x=0.01, ha="left", fontsize=10.5,
                 y=1.06)
    fig.savefig(IMG / "fig4_discussion.png")
    plt.close(fig)


def fig_decisions():
    p = ROOT / "results" / "decisions_summary.json"
    if not p.exists():
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    arms = [("none", "no note", GREY), ("generic", "generic warning", BLUE), ("label", "true independence label", AQUA),
            ("inflated", "false label: 5.0 independent", ORANGE)]
    keys = list(d)
    fig, ax = plt.subplots(figsize=(6.8, 0.5 * len(keys) + 1.3))
    for i, k in enumerate(keys):
        v = d[k]
        for j, (a, lab, c) in enumerate(arms):
            ax.scatter([v[f"brier_{a}"] - v["brier_panel_mean"]], [i + (j - 1.5) * 0.12], s=30, color=c, zorder=3,
                       edgecolor="white", linewidth=1, label=lab if i == 0 else None)
    ax.axvline(0, color=GREY, lw=1, ls=(0, (3, 3)))
    sm = json.loads((ROOT / "results" / "summary.json").read_text(encoding="utf-8"))["panels"]
    prem = [v["premium_brier"] for k, v in sm.items() if not k.startswith(("discuss-r1",))]
    ax.axvspan(min(prem), max(prem), color=ORANGE, alpha=0.10, lw=0)
    ax.text((min(prem) + max(prem)) / 2, 0.5, "cost of counting\nthe panel as five\nindependent\nwitnesses",
            ha="center", va="center", fontsize=8, color=MUTED, transform=ax.get_xaxis_transform())
    ax.set_xlim(-0.03, max(prem) + 0.01)
    names = []
    for k in keys:
        panel, dm = k.split(" | ")
        names.append(LABELS.get(panel.replace(" [None]", ""), panel) + "\nread by " + dm)
    ax.set_yticks(range(len(keys)), names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Decision-maker's Brier minus the panel average's Brier\n(0 = repeats the average; higher is worse)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.4, -0.2), ncol=2, frameon=False, fontsize=8)
    ax.set_title("AI readers repeat the panel average, with or without a label", loc="left", fontsize=10.5)
    ax.grid(axis="y", visible=False)
    fig.savefig(IMG / "fig5_decisions.png")
    plt.close(fig)


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    fig_neff()
    fig_premium()
    fig_discussion()
    fig_decisions()
    print("figures ->", IMG)

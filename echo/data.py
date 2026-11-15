"""Build the question set from ForecastBench (Karger et al., ICLR 2025).

We keep binary market questions (Polymarket, Metaculus, Manifold, INFER) that
resolved to 0 or 1. Every question was frozen in July or August 2026 and
resolved between July and November 2026, after the training cutoff of every
model we query, so the models cannot have seen the answers. Each question
carries the market's probability at the freeze date: a real human crowd
forecast to compare the AI panels against.

    python -m echo.data
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "questions.jsonl"
SETS = ["2026-07-19", "2026-08-30"]
MARKETS = {"polymarket", "metaculus", "manifold", "infer"}


def build() -> list[dict]:
    rows: dict[str, dict] = {}
    for d in SETS:
        qs = {q["id"]: q for q in json.load(open(RAW / f"{d}-llm.json", encoding="utf-8"))["questions"]}
        res = json.load(open(RAW / f"{d}_resolution_set.json", encoding="utf-8"))["resolutions"]
        for r in res:
            q = qs.get(r["id"])
            if q is None or r["source"] not in MARKETS or not r["resolved"] or r["resolved_to"] not in (0.0, 1.0):
                continue
            try:
                crowd = float(q["freeze_datetime_value"])
            except (TypeError, ValueError):
                continue
            if r["id"] in rows:  # same question in both sets: keep the earlier freeze
                continue
            rows[r["id"]] = {
                "id": r["id"], "source": r["source"], "set": d,
                "question": q["question"].strip(),
                "background": (q.get("background") or "").strip()[:1500],
                "resolution_criteria": (q.get("resolution_criteria") or "").strip()[:800],
                "freeze_date": q["freeze_datetime"][:10],
                "close_date": (q.get("market_info_close_datetime") or "")[:10],
                "crowd": min(max(crowd, 0.0), 1.0),
                "outcome": int(r["resolved_to"]),
                "resolution_date": r["resolution_date"],
            }
    out = sorted(rows.values(), key=lambda x: x["id"])
    random.Random(2026).shuffle(out)  # fixed order; pilots take a prefix
    return out


if __name__ == "__main__":
    rows = build()
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    yes = sum(r["outcome"] for r in rows)
    print(f"{len(rows)} questions, {yes} resolved YES ({yes / len(rows):.0%}) -> {OUT}")

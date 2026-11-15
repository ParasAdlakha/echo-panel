"""The five kinds of AI advisor panel.

Every panel has five advisors. Each advisor sees the same question and gives a
probability and a one-sentence reason. Panels differ only in where the five
answers come from:

  samples   one model asked five times (temperature 1)
  personas  one model playing five named experts ("panel of experts" products)
  mixed     five different models from different developers
  discuss   the mixed panel after one round of seeing each other's answers
  brief     the five mixed models after all reading the same research brief

The forecast date is fixed to the question's freeze date and the human market
price is never shown to the advisors.

    python -m echo.panels --n 40 --conditions samples,personas,mixed
"""
from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .llm import USAGE, chat, parse_json

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "data" / "questions.jsonl"
OUT = ROOT / "results" / "forecasts.jsonl"

# Default rosters; override with --models / --base. Chosen to span developers.
MIXED = ["gpt-4.1-mini", "adaption/gemma-4-31b-it", "adaption/qwen3.8-27b", "nvidia/nemotron-3.5-lightning-30b-a3b",
         "gpt-5.4-mini"]
PERSONAS = [
    ("a political scientist who studies elections and institutions", "political scientist"),
    ("an economist who works with market and macro data", "economist"),
    ("a superforecaster who starts from base rates and adjusts carefully", "superforecaster"),
    ("an investigative journalist who follows current events closely", "journalist"),
    ("a risk analyst whose job is to notice what could go differently than expected", "risk analyst"),
]

SYSTEM = ("You are a careful forecaster advising someone who has to make a decision. "
          "Answer only with JSON: {\"p\": <probability from 0 to 1 that the question resolves YES>, "
          "\"why\": \"<one sentence, at most 30 words>\"}.")


def load_questions(n: int | None = None) -> list[dict]:
    rows = [json.loads(line) for line in QUESTIONS.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[:n] if n else rows


def question_text(q: dict) -> str:
    parts = [f"Today's date is {q['freeze_date']}.", f"Question: {q['question']}"]
    if q["resolution_criteria"]:
        parts.append(f"Resolution criteria: {q['resolution_criteria']}")
    if q["background"]:
        parts.append(f"Background: {q['background']}")
    if q["close_date"]:
        parts.append(f"The question closes on {q['close_date']}.")
    return "\n".join(parts)


def _p(text: str) -> tuple[float | None, str]:
    d = parse_json(text) or {}
    try:
        p = float(d.get("p"))
    except (TypeError, ValueError):
        return None, ""
    if p > 1 and p <= 100:  # some models answer in percent
        p /= 100
    return (min(max(p, 0.0), 1.0) if 0 <= p <= 1 else None), str(d.get("why", ""))[:300]


def ask(model: str, q: dict, seed: int = 0, persona: str | None = None, extra: str = "") -> dict:
    sys_msg = SYSTEM if persona is None else f"You are {persona}. " + SYSTEM
    user = question_text(q) + (("\n\n" + extra) if extra else "")
    msgs = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user}]
    for retry in range(3):  # re-ask on unparseable output, with a new cache key
        p, why = _p(chat(model, msgs, seed=seed + 1000 * retry))
        if p is not None:
            return {"model": model, "p": p, "why": why, "seed": seed}
    return {"model": model, "p": None, "why": "", "seed": seed}


def make_brief(q: dict, writer: str) -> str:
    """One research brief, written once, that every advisor in the 'brief' panel reads."""
    msgs = [{"role": "system", "content": "You write short, neutral research briefs for forecasters. "
             "Answer only with JSON: {\"brief\": \"<120 words at most: the key considerations, base rates and "
             "uncertainties, without giving a final probability>\"}."},
            {"role": "user", "content": question_text(q)}]
    d = parse_json(chat(writer, msgs, seed=7)) or {}
    return str(d.get("brief", ""))[:1200]


def run_panel(cond: str, q: dict, base: str, mixed: list[str]) -> list[dict]:
    if cond == "samples":
        return [ask(base, q, seed=s) for s in range(5)]
    if cond == "personas":
        return [dict(ask(base, q, seed=0, persona=full), persona=short) for full, short in PERSONAS]
    if cond == "mixed":
        return [ask(m, q, seed=0) for m in mixed]
    if cond == "discuss":
        first = [ask(m, q, seed=0) for m in mixed]
        out = []
        for i, m in enumerate(mixed):
            others = "\n".join(f"- Advisor {j + 1}: p = {a['p']:.2f}. {a['why']}" for j, a in enumerate(first)
                               if j != i and a["p"] is not None)
            mine = f"{first[i]['p']:.2f}" if first[i]["p"] is not None else "none"
            extra = (f"Your first forecast was p = {mine}. Four other advisors answered the same question:\n{others}\n"
                     "Give your final forecast. Change it only if their reasons give you a reason to.")
            out.append(dict(ask(m, q, seed=1, extra=extra), first_p=first[i]["p"]))
        return out
    if cond == "brief":
        brief = make_brief(q, writer=mixed[0])
        extra = f"A research assistant prepared this brief for you:\n{brief}"
        return [dict(ask(m, q, seed=2, extra=extra), brief=brief) for m in mixed]
    raise ValueError(cond)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--conditions", default="samples,personas,mixed,discuss,brief")
    ap.add_argument("--base", default="adaption/gemma-4-31b-it", help="model for samples and personas panels")
    ap.add_argument("--bases", default=None, help="comma list: run samples+personas for each")
    ap.add_argument("--models", default=",".join(MIXED))
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--tag", default="", help="suffix for cond names, e.g. oa -> mixed-oa")
    a = ap.parse_args()
    qs = load_questions(a.n)
    mixed = a.models.split(",")
    bases = a.bases.split(",") if a.bases else [a.base]
    jobs = []
    for cond in a.conditions.split(","):
        for b in (bases if cond in ("samples", "personas") else [None]):
            for q in qs:
                jobs.append((cond, b, q))

    def work(job):
        cond, b, q = job
        try:
            ans = run_panel(cond, q, b, mixed)
        except Exception as e:  # keep going; the analysis reports missing panels
            print(f"[fail] {cond} {b} {q['id'][:8]}: {str(e)[:120]}", flush=True)
            return None
        return {"cond": cond + (f"-{a.tag}" if a.tag else ""), "base": b, "qid": q["id"], "outcome": q["outcome"], "crowd": q["crowd"],
                "answers": ans}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = 0
    with ThreadPoolExecutor(a.workers) as ex, open(a.out, "a", encoding="utf-8") as f:
        for row in ex.map(work, jobs):
            done += 1
            if row:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
            if done % 25 == 0:
                print(f"{done}/{len(jobs)} panels", flush=True)
    print("usage:", json.dumps(USAGE))


if __name__ == "__main__":
    main()

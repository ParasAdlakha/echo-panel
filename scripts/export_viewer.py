"""Export the panels shown in the replay viewer to docs/data/panels.js.

    python scripts/export_viewer.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from echo.analyze import load  # noqa: E402
from echo.panels import load_questions  # noqa: E402

SHOW = [
    ("samples", "gpt-5.4-mini", "One model, asked five times", "gpt-5.4-mini ×5"),
    ("personas", "gpt-5.4-mini", "Five personas of one model", "gpt-5.4-mini as five experts"),
    ("mixed-oa", None, "Five different models", "gpt-4.1-mini · gpt-5.4-mini · gpt-4o-mini · gpt-5-mini · gpt-4.1"),
    ("brief-oa", None, "Five models after a shared brief", "all read one 120-word brief first"),
    ("discuss-oa", None, "Five models after one round of discussion", "each saw the other four answers, then revised"),
]
PERSONA = ["Political scientist", "Economist", "Superforecaster", "Journalist", "Risk analyst"]
MODELS = ["gpt-4.1-mini", "gpt-5.4-mini", "gpt-4o-mini", "gpt-5-mini", "gpt-4.1"]


def main():
    panels = load()
    qs = load_questions()
    out = []
    for q in qs:
        row = {"id": q["id"][:10], "q": q["question"], "src": q["source"], "date": q["freeze_date"],
               "close": q["close_date"], "crowd": round(q["crowd"], 3), "y": q["outcome"], "panels": []}
        ok = True
        for cond, base, title, sub in SHOW:
            v = panels.get((cond, base, q["id"]))
            if v is None:
                ok = False
                break
            ans = []
            for j, a in enumerate(v["answers"]):
                who = PERSONA[j] if cond == "personas" else (f"Sample {j + 1}" if cond == "samples" else MODELS[j])
                d = {"who": who, "p": round(a["p"], 3), "why": a.get("why", "")}
                if cond == "discuss-oa" and a.get("first_p") is not None:
                    d["p0"] = round(a["first_p"], 3)
                ans.append(d)
            pnl = {"key": cond, "title": title, "sub": sub, "a": ans}
            if cond == "brief-oa":
                pnl["brief"] = v["answers"][0].get("brief", "")
            row["panels"].append(pnl)
        if ok:
            out.append(row)
    dst = ROOT / "docs" / "data" / "panels.js"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("window.PANELS = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n",
                   encoding="utf-8")
    print(len(out), "questions ->", dst, f"{dst.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()

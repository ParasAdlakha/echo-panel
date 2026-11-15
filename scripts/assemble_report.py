"""Assemble report/report.final.md (input to build_report.py) from report.md, references.md and appendices.md.

    python scripts/assemble_report.py && python scripts/build_report.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "report"

FIGS = {
    # paragraph that starts with this text -> figure placed after it
    "**What is new here.**": ("Figure 1: The design. Five ways to build a five-advisor panel on the same "
                                              "question; the market price is the human benchmark and is never shown to the "
                                              "models.", "docs/img/fig1_design.png", 6.0),
    "Crossing developers did not buy": ("Figure 2: Effective number of independent advisors per panel (190 questions; "
                                        "95% bootstrap CIs). Dashed lines mark one opinion and five independent advisors.",
                                        "docs/img/fig2_neff.png", 4.7),
    "**Talking erases what diversity bought.**": ("Figure 3: Five OpenAI models with no exchange, after reading one "
                                                  "shared brief, and after one round of discussion.",
                                                  "docs/img/fig4_discussion.png", 5.6),
}


def main():
    src = (R / "report.md").read_text(encoding="utf-8")
    title = src.splitlines()[0].lstrip("# ").strip()
    abstract = src.split("## Abstract", 1)[1].split("## 1 Introduction", 1)[0].strip()
    body = "## 1 Introduction" + src.split("## 1 Introduction", 1)[1]
    # table caption convention: "Table N: caption" directly above the table
    body = re.sub(r"\*\*Table (\d+)\.\*\* (.*?)\n\n\|", lambda m: f"Table {m.group(1)}: {m.group(2)}\n|", body, flags=re.S)
    out = []
    for para in body.split("\n\n"):
        out.append(para)
        for start, (cap, path, w) in FIGS.items():
            if para.startswith(start):
                out.append(f"![{cap}]({path}){{width={w}}}")
    body = "\n\n".join(out)
    refs = (R / "references.md").read_text(encoding="utf-8").split("\n", 1)[1]
    refs = refs.split("\nTo check before final")[0].strip()
    refs = "\n\n".join(l for l in refs.splitlines() if l.strip())
    apps = (R / "appendices.md").read_text(encoding="utf-8")
    apps += ("\n\n## Appendix C. The cost of over-counting, prompts and reproducibility\n\n"
             "![Figure C1: Brier score of the plain average (dot) and of the same five advisors read as independent "
             "witnesses (arrow tip). Lower is better. Vertical lines mark the human market crowd and always answering "
             "50%.](docs/img/fig3_premium.png){width=5.6}\n\n"
             "![Figure C2: AI decision-makers' Brier score relative to the plain panel average, by note. The shaded "
             "band is the cost of reading the panel as five independent witnesses.](docs/img/fig5_decisions.png){width=5.2}\n\n" + (R / "appendix_c.md").read_text(encoding="utf-8"))
    authors = "Paras Adlakha | Independent researcher; Harshita Adlakha | Bangalore Institute of Technology"
    final = (f"title: {title}\nauthors: {authors}\nabstract: {abstract}\n\n{body.strip()}\n\n## References\n\n{refs}\n\n"
             f"\\pagebreak\n\n{apps.strip()}\n")
    (R / "report.final.md").write_text(final, encoding="utf-8")
    print("abstract words:", len(abstract.split()))


if __name__ == "__main__":
    main()

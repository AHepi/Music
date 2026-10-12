"""What this file does: turns the research results for chapter 2 (a JSON file made by the research
helpers) into the readable research ledger, in the same table layout as chapter 1's ledger.

Use: python3 -I write_research_ledger.py RESEARCH_RESULTS.json "OUTPUT LEDGER.md"
"""
import json
import sys

lane_titles = {
    "history": "History: Britain and Italy, 1914-1926, and what Mattei says (C2-H)",
    "cases": "Cases: when new money did and didn't push prices up (C2-C)",
    "now": "New Zealand (and Australia), 2020 to October 2026 (C2-N)",
    "mechanism": "How inflation works, and the main views (C2-M)",
}


def clean_cell(text):
    return str(text).replace("|", "/").replace("\n", " ").strip()


def main():
    results_path, ledger_path = sys.argv[1], sys.argv[2]
    research = json.load(open(results_path, encoding="utf-8"))["research"]
    lines = [
        "# 18 Research - chapter 2 - what really causes inflation",
        "",
        "What this file is: the fact ledger for chapter 2 of the austerity explainer (\"what really causes",
        "inflation\"). Every sentence the narration says, and every number drawn on screen, must trace to an",
        "entry here, as in chapter 1. Compiled 12 October 2026 by four research helpers working from the",
        "web, each told to use only sources they actually opened or saw. Confidence: high = two good sources",
        "or one authoritative source; medium = one decent source; low = do not use without more checking.",
        "",
        "Authority source for the whole project: Clara E. Mattei, *The Capital Order* (2022). As in chapter",
        "1, the book itself has not been read directly; her claims come from her interviews, articles and",
        "reviews, and are said in the film as hers (\"Mattei argues\").",
        "",
        "Figures from after June 2026 (the latest New Zealand inflation, interest rate and unemployment",
        "figures, the Royal Commission and the independent review) come partly from the report \"06 Report -",
        "budget deficits - when they are responsible\" and the news sources it names. Re-check them on the day",
        "of recording: the September quarter's inflation figure is due on 22 October 2026.",
        "",
    ]
    for lane in research:
        lines += [f"## {lane_titles.get(lane['lane'], lane['lane'])}", ""]
        lines += ["| Id | Claim (precise) | Plain version for narration | Source | Conf. | Simplified or contested |",
                  "|---|---|---|---|---|---|"]
        for entry in lane["entries"]:
            sources = " ; ".join(clean_cell(s) for s in entry["sources"])
            lines.append(
                f"| {entry['id']} | {clean_cell(entry['claim'])} | {clean_cell(entry['plain'])} | {sources} | "
                f"{entry['confidence']} | {clean_cell(entry['contested_or_simplified'])} |"
            )
        lines += ["", "**Could not verify (kept out of the film):**", ""]
        lines += [f"- {clean_cell(item)}" for item in lane["could_not_verify"]]
        lines += ["", "**Strongest pictures from this part of the research:**", ""]
        lines += [f"- {clean_cell(item)}" for item in lane["best_images_for_film"]]
        lines.append("")
    lines += [
        "## Traps",
        "",
        "- The plain versions were written by the research helpers. Several still use words the narration",
        "  rules replace (\"the crash\", \"rate\", \"bonds\"); the script uses the outline's plain names instead.",
        "- Medium-confidence entries were mostly read from search summaries, not the full page: open the page",
        "  before a medium entry goes into the script.",
        "- C2-M18 (\"a price rise that's mostly fuel\") is wrong arithmetic: fuel adds about 1.2 points of the",
        "  4.1%; prices without fuel still rose 2.9%. Don't use it as worded.",
        "- C2-H08's \"then came the crash\" implies the interest rate caused the 1920-21 slump; how much it did",
        "  is argued. Say what followed, not what caused it.",
        "- House prices are not counted in New Zealand's inflation figure (the 7.3%). Keep them apart.",
        "- Never call the view of \"economists who study how modern money works\" by its school's name.",
    ]
    open(ledger_path, "w", encoding="utf-8").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

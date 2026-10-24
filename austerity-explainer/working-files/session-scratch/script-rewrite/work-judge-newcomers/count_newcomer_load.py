"""What this does: times each newcomer draft of chapter 2 at a given speaking speed and counts,
in every 30-second stretch, how many NEW places (P), years or dates (Y), numbers (N) and terms (T)
a first-time viewer meets. The tags are hand-made (listed below, first mention only); the script
finds where each tagged phrase is first said and turns its word position into seconds.

Run: python3 -I count_newcomer_load.py <script-rewrite folder> [words_per_minute]
"""
import re
import sys
from pathlib import Path

SCRIPT_REWRITE_FOLDER = Path(sys.argv[1])
WORDS_PER_MINUTE = float(sys.argv[2]) if len(sys.argv) > 2 else 140.0
PAGE_TURN_SECONDS = 1.5
GUESS_HOLD_SECONDS = 3.0

DRAFTS = {
    "viewer-question": {
        "guess_pages": {3, 5, 10},
        "tags": {
            1: [("inflation", "T"), ("new money", "T"), ("the usual cure", "T")],
            2: [("new zealand", "P"), ("reserve bank", "T"),
                ("economists who study how modern money works", "T"),
                ("workers, materials and machines", "T")],
            3: [("britain", "P"), ("first world war", "Y"), ("one worker in a hundred", "N"),
                ("submarines", "T")],
            4: [("roughly doubled", "N")],
            5: [("japan", "P"), ("twenty thirteen", "Y"), ("version of our reserve bank", "T"),
                ("double the money", "N"), ("two years", "N")],
            6: [("eight years", "N"), ("half a percent", "N"), ("mainstream economists", "T")],
            7: [("quiet factory", "T"), ("new orders", "T")],
            8: [("flat out", "T")],
            9: [("things we can't make more of in a hurry", "T")],
            10: [("twenty twenty,", "Y"), ("twenty twenty-one", "Y")],
            11: [("three in every hundred", "N"), ("unemployment", "T"),
                 ("three point two percent", "N"), ("this september", "Y"),
                 ("independent review", "T")],
            12: [("june twenty twenty-six", "Y"), ("four point one", "N"), ("two point nine", "N"),
                 ("it's a cost", "T")],
            13: [("interest rate", "T")],
            14: [("late twenty twenty-one", "Y"), ("five point six", "N"),
                 ("a hundred and seventy-one thousand", "N")],
            15: [("unwanted side effect", "T"), ("/məˈteɪi/", "T")],
            16: [],
        },
    },
    "one-model": {
        "guess_pages": {4, 7},
        "tags": {
            1: [("inflation", "T"), ("new money", "T"), ("the usual cure", "T")],
            2: [("central bank", "T"), ("reserve bank", "T"),
                ("economists who study how modern money works", "T"),
                ("workers, materials and machines", "T")],
            3: [("quiet factory", "T"), ("orders for more things", "T")],
            4: [("flat-out factory", "T")],
            5: [],
            6: [("britain", "P"), ("first world war", "Y"), ("one worker in a hundred", "N"),
                ("submarines", "T"), ("roughly doubled", "N")],
            7: [("japan", "P"), ("twenty thirteen", "Y"), ("double the money", "N"),
                ("two years", "N")],
            8: [("eight years", "N"), ("half a percent", "N")],
            9: [("new zealand", "P"), ("twenty twenty.", "Y"), ("unemployment", "T"),
                ("twenty twenty-one", "Y"), ("three point two percent", "N")],
            10: [("thirty percent", "N"), ("royal commission", "T")],
            11: [("interest rate", "T")],
            12: [("five point six", "N"), ("a hundred and seventy thousand", "N"),
                 ("this year", "Y")],
            13: [("june", "Y"), ("four point one", "N"), ("two point nine", "N"),
                 ("one to three percent", "N"), ("rise in costs", "T")],
            14: [("unwanted side effect", "T"), ("/məˈteɪi/", "T")],
            15: [],
        },
    },
    "people-first": {
        "guess_pages": {5, 7},
        "tags": {
            1: [("inflation", "T"), ("new money", "T"), ("the usual cure", "T")],
            2: [("new zealand", "P"), ("reserve bank", "T"),
                ("economists who study how modern money works", "T"),
                ("workers, materials and machines", "T")],
            3: [("glasgow", "P"), ("scotland", "P"), ("nineteen fifteen", "Y"), ("britain", "P"),
                ("first world war", "Y"), ("shells", "T"), ("one worker in every hundred", "N"),
                ("roughly doubled", "N")],
            4: [("landlords", "T"), ("up to a quarter", "N"), ("mary barbour", "T"),
                ("november", "Y"), ("twenty thousand families", "N"), ("parliament", "T")],
            5: [("quiet factory", "T"), ("flat-out factory", "T")],
            6: [],
            7: [("japan", "P"), ("twenty thirteen", "Y"), ("version of our reserve bank", "T"),
                ("double the money", "N"), ("two years", "N")],
            8: [("eight years", "N"), ("half a percent", "N")],
            9: [("twenty twenty,", "Y"), ("billions", "N"), ("wage subsidy", "T"),
                ("twenty twenty-one", "Y"), ("three point two percent", "N"), ("this year", "Y"),
                ("outside experts", "T")],
            10: [("nineteen twenty", "Y"), ("bank of england", "T"), ("interest rate", "T"),
                 ("seven percent", "N")],
            11: [("two in every hundred", "N"), ("one in ten", "N")],
            12: [("/məˈteɪi/", "T"), ("a cost, not the goal", "T")],
            13: [("a quarter of a percent", "N"), ("five and a half percent", "N"),
                 ("twenty twenty-three", "Y"), ("five point six", "N"),
                 ("a hundred and seventy thousand", "N")],
            14: [],
        },
    },
}


def read_pages(narration_path):
    pages = []
    for block in re.split(r"^## .*$", narration_path.read_text(encoding="utf-8"), flags=re.M):
        text = " ".join(block.split())
        if text:
            pages.append(text)
    return pages


def spoken_words(text):
    return [w for w in text.split() if re.search(r"[A-Za-zəˈɪʊ]", w)]


def sentences(text):
    parts = re.split(r"(?<=[.?!])\s+(?=[A-Z/])", text)
    return [p for p in parts if spoken_words(p)]


def first_word_index(page_text, phrase):
    position = page_text.lower().find(phrase.lower())
    if position < 0:
        return None
    return len(spoken_words(page_text[:position]))


def main():
    print(f"Speaking speed: {WORDS_PER_MINUTE:.0f} words a minute; page turn {PAGE_TURN_SECONDS} s;"
          f" guess hold {GUESS_HOLD_SECONDS} s\n")
    for draft_name, setup in DRAFTS.items():
        pages = read_pages(SCRIPT_REWRITE_FOLDER / f"work-draft-{draft_name}" / "narration-final.txt")
        clock = 0.0
        events = []
        page_rows = []
        all_sentence_lengths = []
        for page_number, text in enumerate(pages, start=1):
            words = spoken_words(text)
            seconds = len(words) / WORDS_PER_MINUTE * 60
            sentence_lengths = [len(spoken_words(s)) for s in sentences(text)]
            all_sentence_lengths += sentence_lengths
            for phrase, kind in setup["tags"].get(page_number, []):
                index = first_word_index(text, phrase)
                if index is None:
                    print(f"  !! {draft_name} page {page_number}: tag not found: {phrase!r}")
                    continue
                events.append((clock + index / WORDS_PER_MINUTE * 60, kind, phrase, page_number))
            page_rows.append((page_number, len(words), seconds, clock))
            clock += seconds
            clock += GUESS_HOLD_SECONDS if page_number in setup["guess_pages"] else PAGE_TURN_SECONDS
        total_words = sum(r[1] for r in page_rows)
        print(f"=== {draft_name}: {len(pages)} pages, {total_words} spoken words, "
              f"{len(all_sentence_lengths)} sentences, mean {total_words/len(all_sentence_lengths):.1f}"
              f" words, longest {max(all_sentence_lengths)}; running time about {int(clock//60)}:"
              f"{clock%60:04.1f}")
        slice_count = int(clock // 30) + 1
        print("  slice   P  Y  N  T  all   items")
        worst = 0
        for s in range(slice_count):
            inside = [e for e in events if s * 30 <= e[0] < (s + 1) * 30]
            counts = {k: sum(1 for e in inside if e[1] == k) for k in "PYNT"}
            total = sum(counts.values())
            worst = max(worst, total)
            label = f"{s*30//60}:{s*30%60:02d}"
            names = "; ".join(f"{e[2]}({e[1]})" for e in inside)
            print(f"  {label:>5}  {counts['P']:2d} {counts['Y']:2d} {counts['N']:2d} {counts['T']:2d}"
                  f"  {total:3d}   {names}")
        kinds = {k: sum(1 for e in events if e[1] == k) for k in "PYNT"}
        print(f"  totals: P {kinds['P']}, Y {kinds['Y']}, N {kinds['N']}, T {kinds['T']}, all "
              f"{len(events)}; mean per 30 s {len(events)/(clock/30):.1f}; worst slice {worst}\n")


if __name__ == "__main__":
    main()

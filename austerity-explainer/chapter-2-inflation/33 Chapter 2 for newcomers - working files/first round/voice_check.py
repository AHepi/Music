# What this does: reads narration text (pages start with a line beginning "## ") and reports, page by
# page, anything that breaks the chapter 2 voice rules: Naomi Klein titles, coined phrases and
# near-copies; capitals used for emphasis; digits (numbers must be written as said); brackets (no
# delivery cues); exclamation marks; the forbidden school name; Mattei or Ruhr not written in sound
# symbols; words that need a plain explanation for a newcomer; long sentences; pauses ("...") per
# page; and the spoken length at Malina's pace of about 140 words a minute.
# Usage: python3 -I voice_check.py <narration file>
# It is a first filter only: it cannot judge facts, qualifications or whether Mattei's view is marked
# as hers. A person (or a fact checker) still reads every line against the research ledger.

import re
import sys

WORDS_PER_MINUTE = 140
LONG_SENTENCE_WORDS = 20

# Naomi Klein's titles, coined or strongly associated phrases, and near-copies likely in this chapter.
never_use_patterns = [
    r"\bshock", r"\bdisaster", r"\bdoctrine", r"changes everything", r"change everything",
    r"\bnot enough\b", r"\bon fire\b", r"\bburning\b", r"\bmirror\b", r"doppelg",
    r"\blogo\b", r"\bbrand", r"\bfences\b", r"\bwindows\b", r"\bthe take\b", r"blank slate",
    r"clean slate", r"capitalism", r"end times", r"apocalyp", r"sacrifice zone", r"extractiv",
    r"blockadia", r"\bthe leap\b", r"battle for", r"\bthe rise of\b", r"world we need",
    r"waste a crisis", r"crisis is an opportunity", r"only a crisis", r"greed", r"\bprofiteer",
    r"no space", r"no choice", r"green new deal", r"screen new deal", r"\bfascis",
]

# Terms a newcomer may not know: flag every use so a writer checks it is explained at first use or
# replaced. Some are allowed once explained (interest rate, central bank, unemployment, inflation).
newcomer_terms = [
    r"\bmmt\b", r"modern monetary", r"quantitative", r"\bqe\b", r"monetary base", r"\bocr\b",
    r"official cash rate", r"cash rate", r"\bcpi\b", r"consumers? price index", r"tradable",
    r"demand-pull", r"cost-push", r"output gap", r"hyperinflation", r"stimulus", r"wage-price",
    r"spiral", r"bargaining power", r"deflation", r"reparation", r"passive resistance",
    r"\bbonds?\b", r"\bassets?\b", r"basis points?", r"\bfiscal\b", r"\bmonetary\b", r"\bgdp\b",
    r"\bcentral bank\b", r"\binterest rate\b", r"\bunemployment\b", r"\binflation\b", r"tenement",
    r"\brecession\b", r"\bslump\b", r"\bboom\b",
]


def split_pages(text):
    pages = []
    current_title = "(untitled)"
    current_lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_lines:
                pages.append((current_title, "\n".join(current_lines).strip()))
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        pages.append((current_title, "\n".join(current_lines).strip()))
    return [page for page in pages if page[1]]


def split_sentences(text):
    pieces = re.split(r"(?<=[.?!])\s+", text.replace("...", "… "))
    return [piece.strip() for piece in pieces if piece.strip()]


def count_words(text):
    return len(re.findall(r"[A-Za-zɐ-ʯ'/ˈ-]+", text))


def check_page(title, text):
    report = []
    lower = text.lower()
    words = count_words(text)
    seconds = words / WORDS_PER_MINUTE * 60
    pauses = text.count("...")
    report.append(f"  words: {words}, about {seconds:.0f} seconds at {WORDS_PER_MINUTE} a minute, "
                  f"pauses (...): {pauses}, questions: {text.count('?')}")
    for pattern in never_use_patterns:
        for match in re.finditer(pattern, lower):
            report.append(f"  NEVER-USE LIST: '{text[match.start():match.end() + 20].strip()}'")
    capitals = [word for word in re.findall(r"\b[A-Z]{2,}\b", text)]
    if capitals:
        report.append(f"  CAPITALS (emphasis or abbreviation?): {sorted(set(capitals))}")
    if re.search(r"\d", text):
        report.append(f"  DIGITS (write numbers as said): {re.findall(r'[^ ]*\d[^ ]*', text)}")
    if re.search(r"[\[\]()]", text):
        report.append("  BRACKETS (no delivery cues in narration)")
    if "!" in text:
        report.append("  EXCLAMATION MARK (may push the voice)")
    if re.search(r"\bmattei\b", lower):
        report.append("  'Mattei' in letters: write /məˈteɪi/ for the voice")
    if re.search(r"\bruhr\b", lower):
        report.append("  'Ruhr' in letters: write /rʊə/ for the voice")
    found_terms = sorted({re.search(pattern, lower).group(0) for pattern in newcomer_terms
                          if re.search(pattern, lower)})
    if found_terms:
        report.append(f"  newcomer terms to check (explained at first use, or avoided?): {found_terms}")
    for sentence in split_sentences(text):
        length = count_words(sentence)
        if length > LONG_SENTENCE_WORDS:
            report.append(f"  LONG SENTENCE ({length} words): {sentence[:80]}...")
    if "/məˈteɪi/" in text:
        attributed = re.search(r"/məˈteɪi/ (argues|argued|says|said|sees|saw|calls|writes|wrote)|she (argues|argued|says|said)", text)
        if not attributed:
            report.append("  Mattei named but no 'argues / says' nearby: is her view marked as hers?")
    return report


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 -I voice_check.py <narration file>")
        sys.exit(1)
    with open(sys.argv[1], encoding="utf-8") as narration_file:
        text = narration_file.read()
    total_words = 0
    for title, page_text in split_pages(text):
        print(f"{title}")
        for line in check_page(title, page_text):
            print(line)
        total_words += count_words(page_text)
    print(f"TOTAL: {total_words} words, about {total_words / WORDS_PER_MINUTE * 60:.0f} seconds")


if __name__ == "__main__":
    main()

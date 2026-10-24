# What this does: pulls the narration out of the newcomer script (the first paragraph under each
# "### Page" heading), checks it matches the separate narration file, then reports, page by page:
# spoken words (hyphenated words split the way Malina says them), "..." pauses, the estimated length
# at 140 words a minute plus 0.6 seconds a pause, and anything that breaks the voice rules: digits,
# brackets, capitals used for emphasis, exclamation marks, the forbidden school name, Mattei not in
# sound symbols, words linked to Naomi Klein, stock phrases, and every use of words that can carry
# two senses (cost, pay, rise, raise, spend, money, bank, work, push, cure, price).
# Usage: python3 -I check_rules_and_voice.py <script .md> <narration .txt>
import re
import sys

WORDS_PER_MINUTE = 140
SECONDS_PER_PAUSE = 0.6


def narration_from_script(path):
    pages, title, grab = [], None, False
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.startswith("### Page"):
            title, grab = line[4:].strip(), True
            continue
        if grab and line.strip():
            pages.append((title, line.strip()))
            grab = False
    return pages


def narration_from_text(path):
    pages, title, lines = [], None, []
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            if title is not None:
                pages.append((title, " ".join(lines).strip()))
            title, lines = line[3:].strip(), []
        elif line.strip():
            lines.append(line.strip())
    if title is not None:
        pages.append((title, " ".join(lines).strip()))
    return pages


def spoken_words(text):
    text = text.replace("...", " ").replace("/məˈteɪi/", "Mattei")
    words = re.findall(r"[A-Za-z']+(?:-[A-Za-z']+)*", text)
    out = []
    for word in words:
        out.extend(piece for piece in word.split("-") if piece)
    return out


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.?!])\s+", text.replace("...", "… ")) if s.strip()]


KLEIN = [r"shock", r"disaster", r"doctrine", r"changes? everything", r"no logo", r"\blogo\b", r"\bbrand",
         r"this changes", r"not enough", r"on fire", r"doppelg", r"mirror world", r"blank slate",
         r"clean slate", r"capitalism", r"sacrifice zone", r"\bthe leap\b", r"never waste", r"crisis",
         r"greed", r"profiteer", r"no is not", r"\bsaying no\b", r"corporate", r"\belites?\b",
         r"\bthe few\b", r"\bthe many\b", r"\bwinners?\b", r"\blosers?\b", r"shock therapy",
         r"\bstun", r"\bexploit", r"opportunit", r"\bshell-?shock"]
STOCK = [r"it matters", r"next time", r"here's the", r"the answer is", r"let's", r"think about it",
         r"at the end of the day", r"make no mistake", r"the truth is", r"in other words",
         r"simply put", r"it turns out", r"the real question", r"here's the thing", r"that's the thing",
         r"\bjust\b", r"\bnow\b", r"so what", r"have a guess", r"what do you think", r"in our picture",
         r"not just", r"once it's spent", r"close to the"]
TWO_SENSE = {
    "cost": r"\bcosts?\b", "pay": r"\bpa(?:y|ys|id|ying)\b", "price": r"\bprices?\b",
    "go up / went up": r"\b(?:go|goes|going|went|gone) up\b", "rise/raise": r"\b(?:ris|rais)\w*",
    "spend/spent": r"\bspen(?:d|ds|t|ding)\b", "money": r"\bmoney\b", "bank": r"\bbanks?\b",
    "work (job / labour / function)": r"\bwork(?:s|ing|ers?)?\b", "push": r"\bpush\w*",
    "cure": r"\bcure\b", "factory": r"\bfactor(?:y|ies)\b", "gate": r"\bgate\b",
    "spare": r"\bspare\b", "fast/slow": r"\b(?:fast|slow\w*)\b", "loan/borrow": r"\b(?:loans?|borrow\w*)\b",
    "interest": r"\binterest\b", "make/made": r"\b(?:make|makes|made|making)\b",
    "things": r"\bthings?\b", "here": r"\bhere\b", "goal": r"\bgoal\b", "power": r"\bpower\b",
    "economist(s)": r"\beconomists?\b", "government": r"\bgovernment\b", "new money": r"\bnew money\b",
    "out of work": r"\bout of work\b", "the warning": r"\bwarning\b", "fuel/petrol/oil": r"\b(?:fuel|petrol|diesel|oil)\b",
    "homes/rent": r"\b(?:homes?|rents?)\b", "families/people": r"\b(?:families|people|everyone|no one)\b",
}

script_pages = narration_from_script(sys.argv[1])
text_pages = narration_from_text(sys.argv[2])
print(f"pages in script: {len(script_pages)}, in narration file: {len(text_pages)}")
for (st, sb), (tt, tb) in zip(script_pages, text_pages):
    if sb != tb:
        print(f"  MISMATCH on {st} / {tt}")
print()

total_words = total_pauses = 0
all_lengths = []
for title, body in script_pages:
    words = spoken_words(body)
    pauses = body.count("...")
    seconds = len(words) / WORDS_PER_MINUTE * 60 + pauses * SECONDS_PER_PAUSE
    total_words += len(words)
    total_pauses += pauses
    flags = []
    if re.search(r"\d", body):
        flags.append("digit")
    if re.search(r"[\[\]{}<>]", body):
        flags.append("bracket")
    if "!" in body:
        flags.append("exclamation mark")
    for cap in re.findall(r"\b[A-Z]{2,}\b", body):
        flags.append(f"capitals: {cap}")
    if re.search(r"\bMMT\b|modern monetary", body, re.I):
        flags.append("school name")
    if re.search(r"Mattei", body):
        flags.append("Mattei not in sound symbols")
    for pat in KLEIN:
        if re.search(pat, body, re.I):
            flags.append(f"Klein-linked word: {pat}")
    for sentence in sentences(body):
        n = len(spoken_words(sentence))
        all_lengths.append(n)
        if n >= 16:
            flags.append(f"long sentence ({n}): {sentence}")
    stock = [pat for pat in STOCK if re.search(pat, body, re.I)]
    print(f"{title}\n  words {len(words)}, pauses {pauses}, about {seconds:.1f} s")
    for flag in flags:
        print(f"  FLAG {flag}")
    if stock:
        print(f"  repeated formulas present: {', '.join(stock)}")

speech = total_words / WORDS_PER_MINUTE * 60
pause_time = total_pauses * SECONDS_PER_PAUSE
print()
print(f"TOTAL spoken words {total_words}, pauses {total_pauses}")
print(f"speech {speech:.1f} s + pauses {pause_time:.1f} s = {speech + pause_time:.1f} s = "
      f"{int((speech + pause_time) // 60)}:{round((speech + pause_time) % 60):02d}")
print(f"sentences {len(all_lengths)}, mean {sum(all_lengths) / len(all_lengths):.1f} words, max {max(all_lengths)}")
print()
print("WORDS THAT CAN CARRY TWO SENSES (every use, by page):")
for name, pat in TWO_SENSE.items():
    hits = []
    for title, body in script_pages:
        for sentence in sentences(body):
            if re.search(pat, sentence, re.I):
                hits.append(f"    p{title.split()[1]}: {sentence}")
    if hits:
        print(f"  {name} ({len(hits)} sentences)")
        print("\n".join(hits))

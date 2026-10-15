# What this does: counts the spoken words on each page of a narration file (pages start with "## "),
# two ways (hyphenated words as one word, and as the separate words Malina says), counts the "..."
# pauses, and estimates the spoken length at 140 words a minute plus 0.6 seconds for each pause.
# It also adds the page turns, guess holds and closing fade that the combined script assumes.
import re, sys

WORDS_PER_MINUTE = 140
SECONDS_PER_PAUSE = 0.6
PAGE_TURN_SECONDS = 1.5
GUESS_HOLD_SECONDS = 3.0
FADE_SECONDS = 4.0

def split_pages(text):
    pages, title, lines = [], None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if title is not None:
                pages.append((title, " ".join(lines).strip()))
            title, lines = line[3:].strip(), []
        else:
            lines.append(line)
    if title is not None:
        pages.append((title, " ".join(lines).strip()))
    return pages

def words_joined(text):
    return re.findall(r"[A-Za-zɐ-ʯˈ'/-]+", text.replace("...", " "))

def words_spoken(text):
    out = []
    for word in words_joined(text):
        out.extend([piece for piece in word.split("-") if piece])
    return out

text = open(sys.argv[1], encoding="utf-8").read()
total_joined = total_spoken = total_pauses = 0
guess_pages = 0
for title, body in split_pages(text):
    joined, spoken = len(words_joined(body)), len(words_spoken(body))
    pauses = body.count("...")
    seconds = spoken / WORDS_PER_MINUTE * 60 + pauses * SECONDS_PER_PAUSE
    if body.rstrip().endswith("Have a guess."):
        guess_pages += 1
    total_joined += joined; total_spoken += spoken; total_pauses += pauses
    print(f"{title:45s} words {joined:3d} (spoken {spoken:3d})  pauses {pauses}  about {seconds:4.1f} s")
page_count = len(split_pages(text))
speech = total_spoken / WORDS_PER_MINUTE * 60
pause_time = total_pauses * SECONDS_PER_PAUSE
extras = (page_count - 1) * PAGE_TURN_SECONDS + guess_pages * GUESS_HOLD_SECONDS + FADE_SECONDS
def mmss(s): return f"{int(s // 60)}:{int(round(s % 60)):02d}"
print(f"TOTAL words {total_joined} (spoken {total_spoken}), pauses {total_pauses}")
print(f"speech at {WORDS_PER_MINUTE}/min: {speech:.0f} s; plus pauses ({pause_time:.1f} s): {speech + pause_time:.0f} s = {mmss(speech + pause_time)}")
print(f"with {page_count - 1} page turns, {guess_pages} guess holds and the fade (+{extras:.0f} s): {speech + pause_time + extras:.0f} s = {mmss(speech + pause_time + extras)}")
joined_speech = total_joined / WORDS_PER_MINUTE * 60
print(f"(using the joined count {total_joined}: {joined_speech + pause_time:.0f} s speech+pauses, {joined_speech + pause_time + extras:.0f} s in all)")

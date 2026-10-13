"""What this does: writes caption files (.srt and .vtt) for a chapter from its timeline, so each
caption appears exactly while Malina says those words.

How it splits the words into captions:
  - a new caption starts after each sentence ends (a full stop, question mark, exclamation mark,
    colon or three dots), but not after a single initial such as the "E." in "Clara E. Mattei";
  - a caption longer than 42 letters is split at a comma near its middle, or else at the word
    nearest its middle, so every caption fits on one line of a phone screen;
  - each caption stays up until just after its last word (0.15 s), never overlapping the next one,
    and for at least 0.8 s.

Use: python3 -I make_captions.py TIMELINE.json OUTPUT_WITHOUT_EXTENSION
     (writes OUTPUT.srt and OUTPUT.vtt)
"""

import json
import re
import sys

MAX_LETTERS = 42
HOLD_AFTER_LAST_WORD = 0.15
SHORTEST_CAPTION = 0.8


def ends_sentence(text):
    if re.fullmatch(r"[A-Z]\.", text):  # an initial, like the E. in Clara E. Mattei
        return False
    return text.endswith((".", "?", "!", ":", "..."))


def split_long(words):
    """Splits a list of words into pieces of at most MAX_LETTERS letters, preferring commas."""
    text = " ".join(w["text"] for w in words)
    if len(text) <= MAX_LETTERS or len(words) < 2:
        return [words]
    middle = len(text) / 2
    best, best_score = None, None
    position = 0
    for i, word in enumerate(words[:-1]):
        position += len(word["text"]) + 1
        score = abs(position - middle) - (12 if word["text"].endswith(",") else 0)
        if best_score is None or score < best_score:
            best, best_score = i, score
    return split_long(words[:best + 1]) + split_long(words[best + 1:])


def captions_from(timeline):
    words = [w for page in timeline["pages"] for w in page["words"]]
    sentences, current = [], []
    for word in words:
        current.append(word)
        if ends_sentence(word["text"]):
            sentences.append(current)
            current = []
    if current:
        sentences.append(current)
    pieces = [piece for sentence in sentences for piece in split_long(sentence)]
    captions = []
    for i, piece in enumerate(pieces):
        start = piece[0]["start"]
        end = piece[-1]["end"] + HOLD_AFTER_LAST_WORD
        end = max(end, start + SHORTEST_CAPTION)
        if i + 1 < len(pieces):
            end = min(end, pieces[i + 1][0]["start"] - 0.02)
        captions.append((start, end, " ".join(w["text"] for w in piece)))
    return captions


def clock(seconds, separator):
    milliseconds = int(round(seconds * 1000))
    hours, rest = divmod(milliseconds, 3600000)
    minutes, rest = divmod(rest, 60000)
    whole, thousandths = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole:02d}{separator}{thousandths:03d}"


def main():
    timeline_path, output = sys.argv[1], sys.argv[2]
    with open(timeline_path, encoding="utf-8") as handle:
        captions = captions_from(json.load(handle))
    with open(f"{output}.srt", "w", encoding="utf-8") as srt:
        for number, (start, end, text) in enumerate(captions, start=1):
            srt.write(f"{number}\n{clock(start, ',')} --> {clock(end, ',')}\n{text}\n\n")
    with open(f"{output}.vtt", "w", encoding="utf-8") as vtt:
        vtt.write("WEBVTT\n\n")
        for start, end, text in captions:
            vtt.write(f"{clock(start, '.')} --> {clock(end, '.')}\n{text}\n\n")
    longest = max(len(text) for _, _, text in captions)
    print(f"{len(captions)} captions, longest {longest} letters, last ends at {captions[-1][1]:.2f} s")


if __name__ == "__main__":
    main()

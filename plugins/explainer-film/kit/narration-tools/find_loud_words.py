"""What this does: finds words Malina says much louder than the rest of their page (the "shouting"),
using the word times and the recordings. For each word it measures how loud it is and compares it
with the page's typical word; words well above it are listed.

Use: python3 -I find_loud_words.py WORD_TIMES.json [DECIBELS_ABOVE_TYPICAL, default 6]
(run from the project folder; recording paths in the file are relative to it)
"""

import json
import subprocess
import sys

import numpy

RATE = 48000


def load(path):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return numpy.frombuffer(raw, dtype=numpy.float32).astype(numpy.float64)


def word_peak_levels(audio, words):
    """(text, start, dB) for each word: the loudness of the loudest 50 ms inside it (a shout is a peak, not an average)."""
    levels = []
    for word in words:
        a, b = int(word["start"] * RATE), int(min(word["end"], word["start"] + 0.6) * RATE)
        chunk = audio[a:b]
        if len(chunk) < RATE // 50:
            continue
        block = RATE // 20
        blocks = [chunk[i:i + block] for i in range(0, max(1, len(chunk) - block + 1), block // 2)]
        peak_db = max(20 * numpy.log10(numpy.sqrt(numpy.mean(x * x)) + 1e-12) for x in blocks if len(x))
        levels.append((word["text"], word["start"], peak_db))
    return levels


def main():
    word_times = json.load(open(sys.argv[1], encoding="utf-8"))
    margin = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    for page in word_times["pages"]:
        levels = word_peak_levels(load(page["recording"]), page["words"])
        typical = float(numpy.median([db for _, _, db in levels]))
        loud = [(t, s, db - typical) for t, s, db in levels if db - typical >= margin]
        listed = ", ".join(f'"{t}" at {s:.1f}s (+{d:.1f} dB)' for t, s, d in loud) or "none"
        print(f"page {page['page']:>2}: typical word {typical:.1f} dB; words {margin:.0f}+ dB louder: {listed}")


if __name__ == "__main__":
    main()

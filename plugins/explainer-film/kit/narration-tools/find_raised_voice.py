"""What this does: measures how high Malina's voice sits (its pitch, in hertz) through each page, to
find where it jumps up (how "shouting" shows in a recording) and to compare pages with each other
(a page that sits much higher or lower than the rest sounds like a different delivery).

Pitch is measured with the YIN method (a standard way of finding the note a voice is on) on 40 ms
slices, ignoring slices that are silent or breathy. Results:
  - per page: the typical pitch and how widely it swings;
  - per word: words sitting 5 or more semitones above the page's typical pitch (one semitone is one
    step on a piano).

Use: python3 -I find_raised_voice.py WORD_TIMES.json [SEMITONES_ABOVE_TYPICAL, default 5]
"""

import json
import subprocess
import sys

import numpy

RATE = 16000
LOW, HIGH = 90.0, 400.0


def load(path):
    raw = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return numpy.frombuffer(raw, dtype=numpy.float32).astype(numpy.float64)


def yin_pitch(x, threshold=0.12):
    """Pitch of one slice by YIN, or None when the slice has no clear note."""
    tau_min, tau_max = int(RATE / HIGH), int(RATE / LOW)
    n = len(x) - tau_max
    if n <= 0:
        return None
    diff = numpy.array([numpy.sum((x[:n] - x[tau:tau + n]) ** 2) for tau in range(tau_max + 1)])
    cumulative = numpy.cumsum(diff[1:])
    cmnd = numpy.ones_like(diff)
    cmnd[1:] = diff[1:] * numpy.arange(1, tau_max + 1) / (cumulative + 1e-12)
    for tau in range(tau_min, tau_max):
        if cmnd[tau] < threshold and cmnd[tau] <= cmnd[tau + 1]:
            if 0 < tau < tau_max:  # parabolic interpolation for a finer estimate
                a, b, c = cmnd[tau - 1], cmnd[tau], cmnd[tau + 1]
                shift = 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
            else:
                shift = 0.0
            return RATE / (tau + shift)
    return None


def word_pitches(audio, start, end):
    frame, hop = int(0.04 * RATE), int(0.01 * RATE)
    a, b = int(start * RATE), int(end * RATE)
    found = []
    for i in range(a, b - frame, hop):
        x = audio[i:i + frame]
        if numpy.sqrt(numpy.mean(x * x)) < 0.02:
            continue
        p = yin_pitch(x - x.mean())
        if p:
            found.append(p)
    return found


def main():
    word_times = json.load(open(sys.argv[1], encoding="utf-8"))
    margin = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
    for page in word_times["pages"]:
        audio = load(page["recording"])
        per_word, every = [], []
        for word in page["words"]:
            p = word_pitches(audio, word["start"], min(word["end"], word["start"] + 0.7))
            every += p
            if len(p) >= 3:
                per_word.append((word["text"], word["start"], float(numpy.median(p))))
        typical = float(numpy.median(every))
        spread = 12 * numpy.log2(numpy.percentile(every, 90) / numpy.percentile(every, 10))
        raised = [(t, s, 12 * numpy.log2(p / typical)) for t, s, p in per_word if 12 * numpy.log2(p / typical) >= margin]
        listed = ", ".join(f'"{t}" {s:.1f}s (+{d:.0f})' for t, s, d in raised) or "none"
        print(f"page {page['page']:>2}: typical {typical:.0f} Hz, swing {spread:.1f} semitones; words {margin:.0f}+ above: {listed}")


if __name__ == "__main__":
    main()

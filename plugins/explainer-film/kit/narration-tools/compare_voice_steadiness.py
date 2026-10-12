"""What this does: compares how steady Malina's voice is across recordings, without needing word
times. For each recording: its typical pitch (how high the voice sits, in hertz), its swing (the
gap between its high and low notes, in semitones; one semitone is one piano step), and how much of
the time it jumps more than 7 semitones above its own typical pitch (bursts of raised voice).
Then the spread of typical pitch across all recordings: a big spread means pages sound like
different deliveries.

Use: python3 -I compare_voice_steadiness.py LABEL=FILE [LABEL=FILE ...]
"""

import subprocess
import sys

import numpy

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from find_raised_voice import RATE, load, yin_pitch  # noqa: E402


def pitches(path):
    audio = load(path)
    frame, hop = int(0.04 * RATE), int(0.01 * RATE)
    found = []
    for i in range(0, len(audio) - frame, hop):
        x = audio[i:i + frame]
        if numpy.sqrt(numpy.mean(x * x)) < 0.02:
            continue
        p = yin_pitch(x - x.mean())
        if p:
            found.append(p)
    return numpy.array(found)


def main():
    typicals = []
    for item in sys.argv[1:]:
        label, path = item.split("=", 1)
        p = pitches(path)
        typical = float(numpy.median(p))
        swing = 12 * numpy.log2(numpy.percentile(p, 90) / numpy.percentile(p, 10))
        bursts = 100 * float(numpy.mean(12 * numpy.log2(p / typical) > 7))
        typicals.append(typical)
        print(f"{label:<14} typical {typical:5.0f} Hz   swing {swing:4.1f} semitones   raised bursts {bursts:4.1f}% of voiced time")
    spread = 12 * numpy.log2(max(typicals) / min(typicals))
    print(f"spread of typical pitch across these recordings: {spread:.1f} semitones")


if __name__ == "__main__":
    main()

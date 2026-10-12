"""What this does: measures whether a finished film's sound lines up with the chapter mix it was
made from, at the first word of every page. A sound that arrives late or early by more than a few
milliseconds would show as lips and pictures out of step with the voice.

For each page it takes half a second of the mix starting at the page's first word, finds the same
stretch in the film's sound, and reports how far apart they are in milliseconds (0.00 = exact).

Use: python3 -I check_sound_alignment.py FILM.mp4 MIX.wav TIMELINE.json
"""

import json
import subprocess
import sys

import numpy

RATE = 48000


def mono_samples(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return numpy.frombuffer(raw, dtype=numpy.float32)


def offset_ms(film, mix, at_seconds, window=0.5, search=0.05):
    start = int(at_seconds * RATE)
    length = int(window * RATE)
    reach = int(search * RATE)
    target = mix[start:start + length]
    region = film[start - reach:start + length + reach]
    best, best_score = 0, -numpy.inf
    for shift in range(-reach, reach + 1):
        piece = region[reach + shift:reach + shift + length]
        if len(piece) < length:
            continue
        score = float(numpy.dot(piece, target)) / (numpy.linalg.norm(piece) * numpy.linalg.norm(target) + 1e-12)
        if score > best_score:
            best, best_score = shift, score
    return best * 1000.0 / RATE, best_score


def main():
    film_path, mix_path, timeline_path = sys.argv[1:4]
    film, mix = mono_samples(film_path), mono_samples(mix_path)
    with open(timeline_path, encoding="utf-8") as handle:
        timeline = json.load(handle)
    worst = 0.0
    for page in timeline["pages"]:
        shift, match = offset_ms(film, mix, page["first_word_at"])
        worst = max(worst, abs(shift))
        print(f"page {page['page']:2d}: sound {shift:+.2f} ms (match {match:.3f})")
    print(f"largest offset: {worst:.2f} ms")


if __name__ == "__main__":
    main()

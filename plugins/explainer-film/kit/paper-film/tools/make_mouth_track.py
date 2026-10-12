"""What this does: works out how far a paper mouth should be open on each frame, from how loud
Malina's voice is at that moment, so a cut-out jaw drops on her syllables and closes in the gaps.

It reads the chapter's narration track (the levelled voice on its own, no music), measures the
loudness of each 40-millisecond slice around every frame, and turns it into an opening from 0
(closed) to 1 (fully open). The jaw snaps open quickly and closes a little more slowly, like a
paper flap. Only the stretch asked for is written.

Use: python3 -I make_mouth_track.py NARRATION.wav START_SECONDS END_SECONDS OUTPUT.json
"""

import json
import subprocess
import sys

import numpy

SAMPLE_RATE = 48000
FRAMES_PER_SECOND = 30
QUIET_DB = -25.0   # at or below this the mouth is closed
LOUD_DB = -11.0    # at or above this it is fully open


def main():
    narration_path, start, end, output_path = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", narration_path, "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    samples = numpy.frombuffer(raw, dtype=numpy.float32)
    half_window = int(0.02 * SAMPLE_RATE)
    openings = []
    smoothed = 0.0
    frame_count = int(round((end - start) * FRAMES_PER_SECOND)) + 1
    for frame in range(frame_count):
        centre = int((start + frame / FRAMES_PER_SECOND) * SAMPLE_RATE)
        window = samples[max(0, centre - half_window): centre + half_window]
        level_db = 20 * numpy.log10(numpy.sqrt(numpy.mean(window ** 2)) + 1e-9) if len(window) else -120.0
        target = min(1.0, max(0.0, (level_db - QUIET_DB) / (LOUD_DB - QUIET_DB)))
        rate = 0.8 if target > smoothed else 0.55   # opens fast, closes a little slower
        smoothed += (target - smoothed) * rate
        openings.append(round(float(smoothed), 3))
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump({"note": "How open the paper mouth is on each frame (0 closed, 1 open), from the voice's loudness.",
                   "start": start, "frames_per_second": FRAMES_PER_SECOND, "open": openings}, handle)
    moving = sum(1 for value in openings if value > 0.2)
    print(f"{frame_count} frames from {start:.2f} s; mouth open past a fifth on {moving} of them")


if __name__ == "__main__":
    main()

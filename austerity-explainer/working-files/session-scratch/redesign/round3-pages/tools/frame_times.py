"""What this does: works out how many seconds a frame took while filming, stretch by stretch, from the logs that
film-chapter-parallel.sh keeps beside each chunk (render-paper-film.mjs prints the running average every 60 frames).
Each 60-frame stretch's own time is the difference of two running totals; the first stretch of each piece also holds
the page's loading, so it is listed apart. Each stretch is named by what the camera and the page do then
(KINDS below, chapter seconds), and the seconds a frame are summed up by kind.
Use: python3 -I frame_times.py CHUNKS_FOLDER
"""
import glob
import os
import re
import sys

FPS = 30
# (from, to, kind) in chapter seconds: pages 3 to 5 of chapter 2 for newcomers, on the estimated timeline
KINDS = [(47.37, 55.10, 'held, live effects (W3)'), (55.10, 58.00, 'held, live effects (W1)'), (58.00, 60.97, 'sliding (W1)'),
         (60.97, 75.13, 'held, live effects (W1)'), (75.13, 82.03, 'held, live effects (W2)'), (82.03, 84.83, 'sliding (W2)'),
         (84.83, 107.15, 'held, live effects (W2)'), (107.15, 123.47, 'held, live effects (W3)')]


def kind_of(a, b):
    """The kind covering most of frames a to b."""
    best, most = 'mixed', 0
    for start, end, kind in KINDS:
        overlap = min(b / FPS, end) - max(a / FPS, start)
        if overlap > most: best, most = kind, overlap
    return best + ('' if most >= (b - a) / FPS * 0.9 else ' (partly)')


rows, loads = [], []
for log in sorted(glob.glob(os.path.join(sys.argv[1], '*.mp4.log'))):
    first = None
    previous_total, previous_count = 0.0, 0
    for line in open(log):
        m = re.match(r'scene .* drawing (\d+) to (\d+)', line)
        if m:
            first = int(m.group(1)); previous_total, previous_count = 0.0, 0
            continue
        m = re.match(r'frame (\d+)/\d+, (\d+) ms a frame', line)
        if m and first is not None:
            frame, average = int(m.group(1)), int(m.group(2)) / 1000
            count = frame - first + 1
            total = average * count
            seconds = (total - previous_total) / (count - previous_count)
            a, b = first + previous_count, frame + 1
            (loads if previous_count == 0 else rows).append((a, b, seconds, kind_of(a, b)))
            previous_total, previous_count = total, count
rows.sort()
for a, b, seconds, kind in rows:
    print(f'frames {a}-{b - 1} ({a / FPS:6.2f}-{b / FPS:6.2f} s): {seconds:5.2f} s a frame  {kind}')
print('\nby kind (stretches without the page loading):')
kinds = {}
for a, b, seconds, kind in rows:
    kinds.setdefault(kind, []).append((b - a, seconds))
for kind, values in sorted(kinds.items()):
    frames = sum(n for n, _ in values)
    print(f'  {kind}: {sum(n * s for n, s in values) / frames:.2f} s a frame on average over {frames} frames '
          f'(stretches from {min(s for _, s in values):.2f} to {max(s for _, s in values):.2f})')
print('\nfirst stretch of each piece (holds the page loading):')
for a, b, seconds, kind in sorted(loads):
    print(f'  frames {a}-{b - 1}: {seconds:5.2f} s a frame ({kind})')

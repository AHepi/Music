"""What this does: finds, in the filmed pages, each moment new typed words arrive in the top band (rows 80 to 470): it
counts the words' pixels (the neutral light-grey letters and the amber ones, as in words_edges.py) in every frame and
lists each rise of more than 1500 pixels within half a second, with the spoken word nearest before it on the estimated
timeline, so "each line comes in on its spoken word" can be checked on the film itself.
Use: python3 -I words_arrive.py FILM.mp4 FIRST_CHAPTER_FRAME TIMELINE.json
"""
import json
import subprocess
import sys

import numpy as np

film, first, timeline = sys.argv[1], int(sys.argv[2]), json.load(open(sys.argv[3]))
words = [(w['start'], w['text']) for p in timeline['pages'] for w in p['words']]
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', film, '-vf', 'crop=1080:390:0:80', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                     capture_output=True, check=True).stdout
frames = np.frombuffer(raw, np.uint8).reshape(-1, 390, 1080, 3)
counts = []
for f in frames:
    seconds = (first + len(counts)) / 30
    a = f.astype(np.int16)
    if not (seconds < 55.1 or seconds >= 107.147): a = a[:340]   # in W1 and W2 the lit windows start below row 420
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    white = (r > 185) & (g > 182) & (b > 175) & (r < 236) & (abs(r - b) < 18)
    amber = (r > 165) & (g > 115) & (g < 175) & (b < 105) & (r - g > 35) & (g - b > 45)
    counts.append(int((white | amber).sum()))
counts = np.array(counts)
i = 0
while i < len(counts) - 15:
    if counts[i + 15] - counts[i] > 1500:
        # the first frame of the rise: the first frame more than 300 pixels above where the stretch began
        j = i
        while j + 1 < len(counts) and counts[j + 1] - counts[i] < 300: j += 1
        seconds = (first + j + 1) / 30
        said = [w for w in words if w[0] <= seconds + 0.05]
        near = said[-1] if said else (None, '')
        top = counts[min(len(counts) - 1, j + 20)]
        print(f'words arrive from {seconds:7.2f} s ({counts[j]} to {top} pixels); the spoken word just before: "{near[1]}" at {near[0]:.2f} s ({seconds - near[0]:+.2f} s)')
        i = j + 20
    else:
        i += 1

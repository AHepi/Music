"""What this does: measures where the typed words sit on each filmed still of pages 3 to 5: in the top band (rows 80 to
470 of the 1920-pixel frame in W3, 80 to 420 in W1 and W2) it finds the words' pixels (near-white letters, or the amber ones) and prints the leftmost
and rightmost of them and the top and bottom rows, as shares of the frame, so "every line ends before 0.90 across"
and "the heading's letters start below 0.06 down" can be checked on what is really in the film.
Use: python3 -I words_edges.py STILLS_FOLDER
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

worst = 0
for path in sorted(glob.glob(os.path.join(sys.argv[1], 'still-*.jpg')), key=lambda p: float(os.path.basename(p)[6:-4])):
    seconds = float(os.path.basename(path)[6:-4])
    # W3 (before the cut on "In", and from the cut on "Most") has sky behind its rule cards down to 0.24; in W1 and W2
    # the lit windows start about 0.22 down, below every typed line there, so the band stops at 420
    w3 = seconds < 55.1 or seconds >= 107.147
    bottom = 470 if w3 else 420
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)[80:bottom]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    # the paper-white letters are a neutral light grey (about 210, 206, 200 on screen); the amber ones about 196, 147, 75;
    # the lit windows are warmer (red well above blue) or brighter, so they are left out
    white = (r > 185) & (g > 182) & (b > 175) & (r < 236) & (abs(r - b) < 18)
    amber = (r > 165) & (g > 115) & (g < 175) & (b < 105) & (r - g > 35) & (g - b > 45)
    text = white | amber
    cols = np.nonzero(text.sum(axis=0) >= 4)[0]
    rows = np.nonzero(text.sum(axis=1) >= 3)[0]
    if len(cols) == 0:
        print(f'{os.path.basename(path)}: no words in the top band'); continue
    right = (cols.max() + 1) / 1080
    worst = max(worst, right)
    print(f'{os.path.basename(path)}: words from {cols.min() / 1080:.3f} to {right:.3f} across, {(rows.min() + 80) / 1920:.3f} to {(rows.max() + 81) / 1920:.3f} down'
          + ('   PAST 0.90' if right > 0.90 else ''))
print(f'rightmost word pixel on any still: {worst:.3f} across')

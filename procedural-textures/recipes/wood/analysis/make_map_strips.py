# What this does (plain words): makes two "what does this setting do?" strips for the MAPS of the wood (not the paint): (1) the normal-map STRENGTH (2, 5, 8, 12, 16) and (2) the
# height STRETCH (which brightness counts as black and which as white in the height). Both are made in numpy from the baked colour picture of the biggest traced class
# (the same maths the generator uses), cropped around a knot and enlarged. Output: guide_pictures/strip_normal_strength.png and strip_height_stretch.png. Plain Python (python3 -I).
import os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
WOOD = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import score_tools as st
bgr = cv2.imread(os.path.join(WOOD, 'outputs', 'ladder_L3_trace_480kw', 'colour.png'))
box = (slice(300, 470), slice(250, 480))
def label(im, text):
    im = cv2.resize(im, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_NEAREST)
    banner = np.full((34, im.shape[1], 3), 245, np.uint8)
    cv2.putText(banner, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([banner, im])
def save(cells, title, name):
    grid = np.hstack(cells)
    header = np.full((44, grid.shape[1], 3), 255, np.uint8)
    cv2.putText(header, title, (8, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.imwrite(os.path.join(WOOD, 'guide_pictures', name), np.vstack([header, grid]))
cells = []
h = st.height_from_colour(bgr)
for strength in (2, 5, 8, 12, 16):
    n = st.normal_from_height(h, strength) * 0.5 + 0.5
    cells.append(label(np.round(n[..., ::-1] * 255).astype(np.uint8)[box], f'strength {strength}' + (' (the reference)' if strength == 8 else '')))
save(cells, 'Normal-map strength: how steep the slopes look (strength 8 is what the reference used)', 'strip_normal_strength.png')
cells = []
for low, high in ((12, 128), (12, 90), (12, 200), (40, 128), (0, 60)):
    hh = st.height_from_colour(bgr, grey_low=low, grey_high=high)
    cells.append(label(np.round(hh).astype(np.uint8)[box][..., None].repeat(3, axis=2), f'black {low}, white {high}' + (' (fitted)' if (low, high) == (12, 128) else '')))
save(cells, 'Height stretch: which brightness is black and which is white in the height picture', 'strip_height_stretch.png')
print('done')

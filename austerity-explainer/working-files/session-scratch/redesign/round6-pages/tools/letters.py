# What this does: measures how bright the lettered things and the gate lamps are on filmed stills of the Works (round 6,
# finding 5: the subject must be the brightest thing, so the drums' PETROL and DIESEL must sit below the gate board's
# letters). It reads where the drums, boards and lamps stand from works-shot.json and the camera spot of the view, works
# out each one's box on the film frame (a level camera, the film's lens), and prints for each box the brightest
# pixels (the 99.5th percentile and the top) and the box's average, all in levels 0 to 255. It also saves a copy of each
# still with the boxes drawn on it (BOXES-<still>.jpg) so the boxes can be checked by eye.
# Use: python3 -I letters.py WORKS_SHOT_JSON VIEW SPOT STILL ...      (VIEW w1, w2 or w3; SPOT plate or composed)
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

shot = json.load(open(sys.argv[1]))
view, spot, stills = sys.argv[2], sys.argv[3], sys.argv[4:]
camera = shot['views'][view][spot] or shot['views'][view]['plate']
tan_half = math.tan(math.radians(shot.get('film_fov_degrees', 60.4) / 2))
W, H = 1080, 1920


def on_frame(x, y, z):
    """a Blender point on the film frame (pixels), for a level camera looking up the lane (+y)"""
    ahead = y - camera[1]
    return (W / 2 + W / 2 * (x - camera[0]) / (ahead * tan_half * W / H), H / 2 - H / 2 * (z - camera[2]) / (ahead * tan_half))


def box_of(x0, x1, y, z0, z1):
    a, b = on_frame(x0, y, z1), on_frame(x1, y, z0)
    return [int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1]))]


boxes = {}
for name, (x, y, z) in shot.get('drums', {}).items():
    boxes[name + ' letters'] = box_of(x - 0.24, x + 0.24, y - 0.29, z + 0.18, z + 0.78)
for name, (x, y, z) in shot.get('boards', {}).items():
    # the facts give the board's lower middle: its letters stand about 0.1 to 0.55 m above it
    boxes[name + ' letters'] = box_of(x - 0.55, x + 0.55, y - 0.05, z + 0.12, z + 0.55)
for name, (x, y, z) in shot.get('gate_lamps', {}).items():
    boxes[name + ' gate lamp'] = box_of(x - 0.22, x + 0.22, y, z - 0.3, z + 0.25)

for still in stills:
    picture = Image.open(still).convert('RGB')
    luma = np.asarray(picture).astype(float) @ [0.2126, 0.7152, 0.0722]
    print(os.path.basename(still))
    marked = picture.copy(); draw = ImageDraw.Draw(marked)
    for name, (l, t, r, b) in boxes.items():
        l, t, r, b = max(0, l), max(0, t), min(W, r), min(H, b)
        if r - l < 3 or b - t < 3:
            continue
        part = luma[t:b, l:r]
        print(f'  {name:28} box {l:4d},{t:4d},{r:4d},{b:4d}  99.5% {np.percentile(part, 99.5):5.0f}  top {part.max():5.0f}  average {part.mean():5.0f}')
        draw.rectangle([l, t, r, b], outline=(0, 255, 0), width=2)
    marked.save(os.path.join(os.path.dirname(still), 'BOXES-' + os.path.basename(still)), quality=85)

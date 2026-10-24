# What this does: measures the brazier's fire on filmed stills of the Works (round 6: after the time cut on "go" the
# fire must burn lower, so the cut reads as time passing). It reads where the brazier stands from works-shot.json and
# the view's camera spot, and prints for each still: the flames (how many pixels above the brazier's rim are brighter
# than 200 levels, and how high the bright flames reach above the rim, in pixels) and the glow round them (the average
# brightness of a box beside and above the fire, the brazier itself left out).
# Use: python3 -I fire_measure.py WORKS_SHOT_JSON VIEW SPOT STILL ...
import json
import math
import os
import sys

import numpy as np
from PIL import Image

shot = json.load(open(sys.argv[1]))
view, spot, stills = sys.argv[2], sys.argv[3], sys.argv[4:]
camera = shot['views'][view][spot] or shot['views'][view]['plate']
tan_half = math.tan(math.radians(shot.get('film_fov_degrees', 60.4) / 2))
W, H = 1080, 1920


def on_frame(x, y, z):
    ahead = y - camera[1]
    return W / 2 + W / 2 * (x - camera[0]) / (ahead * tan_half * W / H), H / 2 - H / 2 * (z - camera[2]) / (ahead * tan_half)


bx, by, _ = shot['brazier']
rim = shot['coals_z']
left, top = on_frame(bx - 0.45, by, rim + 1.0)
right, rim_y = on_frame(bx + 0.45, by, rim)
left, top, right, rim_y = int(left), int(top), int(right), int(rim_y)
glow_left, glow_top = on_frame(bx - 0.9, by, rim + 1.4)
glow_right, glow_bottom = on_frame(bx + 0.9, by, rim - 0.6)
glow_box = [int(glow_left), int(glow_top), int(glow_right), int(glow_bottom)]
for still in stills:
    luma = np.asarray(Image.open(still).convert('RGB')).astype(float) @ [0.2126, 0.7152, 0.0722]
    flames = luma[top:rim_y, left:right] > 200
    rows = np.nonzero(flames.any(axis=1))[0]
    reach = (rim_y - top - rows.min()) if len(rows) else 0
    g = luma[glow_box[1]:glow_box[3], glow_box[0]:glow_box[2]].copy()
    # leave out the brazier's drum and flames (the middle third across, below the flames' top)
    third = (glow_box[2] - glow_box[0]) // 3
    g[:, third:2 * third] = np.nan
    print(f'{os.path.basename(still)}: flames {int(flames.sum())} bright pixels, reaching {reach} px above the rim; '
          f'glow beside the fire {np.nanmean(g):.1f} levels')

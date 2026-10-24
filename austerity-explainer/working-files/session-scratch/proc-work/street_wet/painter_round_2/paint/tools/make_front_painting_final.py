"""What this file does (plain words)
-----------------------------------------------------------------------------------------------------------------------------------------
The FREE FALLBACK for the sky of the front painting. The painter again put pale clouds into the sky (the brief said not to), and the job's rule is then
"do not pay for another call: put a dark plain sky in for free". This file:
  1. reads the lined-up painting (front_painting_lined_up.png, 1536 x 2730),
  2. reads Blender's exact sky mask for the lockout camera (drawn 3072 x 5460 with smooth edges by make_sky_mask_blender.py and shrunk to 1536 x 2730):
     1 where only sky is seen, 0 where anything else is seen, fractions on the edge (so the roof lines, the chimney, the wheel spokes and the rope get a clean soft edge),
  3. makes the new sky from the PLATE's own sky: for each picture row, the middle colour of the plate's sky dots in that row (so the plate's own colours and its own
     dark-top-to-lighter-horizon gradient), smoothed along the height so the plate's hard curved band edge (a 3D set artefact) becomes a soft gradient,
  4. adds a very faint paint grain taken from the painting's own sky (only where the painting's sky is smooth, so no cloud edge can leak through),
  5. puts it in:  final = painting * (1 - sky) + new sky * sky.
Everything outside the sky is the painting, dot for dot.
Run: python3 -I tools/make_front_painting_final.py [--grain 1.0]
"""
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
grain_gain = float(sys.argv[sys.argv.index('--grain') + 1]) if '--grain' in sys.argv else 1.0
out_path = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else P('front_painting_final.png')

painting = cv2.imread(P('front_painting_lined_up.png')).astype(np.float32)
plate = cv2.imread(ROOT + 'painter_round_2/plate/lockout_plate_wet_round2.png').astype(np.float32)
H, W = painting.shape[:2]
alpha4 = cv2.imread(P('work/sky/sky_alpha_3072x5460.png'), cv2.IMREAD_UNCHANGED)
sky = cv2.resize(1.0 - alpha4[:, :, 3].astype(np.float32) / 255.0, (W, H), interpolation=cv2.INTER_AREA)

# 3. the plate's own sky colour, one colour per row
pure = cv2.erode((sky > 0.999).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
rows = np.zeros((H, 3), np.float32)
have = np.zeros(H, bool)
for y in range(H):
    m = pure[y]
    if m.sum() >= 40:
        rows[y] = np.median(plate[y][m], axis=0)
        have[y] = True
ys = np.nonzero(have)[0]
for c in range(3):
    rows[:, c] = np.interp(np.arange(H), ys, rows[ys, c])      # rows with little sky take the nearest rows' colour
k = 45.0                                                        # smoothing along the height, in dots
pad = int(k * 4)
for c in range(3):
    v = np.pad(rows[:, c], pad, mode='edge')
    rows[:, c] = cv2.GaussianBlur(v.reshape(-1, 1), (0, 0), k).ravel()[pad:-pad]
new_sky = np.repeat(rows[:, None, :], W, axis=1)

# 4. faint paint grain from the painting's own sky, only where it is smooth
lum = painting.mean(axis=2)
hp = lum - cv2.GaussianBlur(lum, (0, 0), 2.0)
local = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 6.0))           # how busy the painting is around each dot (edges and strokes are busy)
gain = 1.0 / (1.0 + (local / 2.0) ** 4)
grain = (hp * gain).clip(-6, 6) * grain_gain
new_sky = new_sky + grain[:, :, None]

# 4b. thin things (the wheels' spokes and rims, the lattice under them, the rope): the painter drew them thinner and a dot or two away from Blender's, so
#     the pale paint it left beside them would show as a light outline. Inside these thin zones only DARK paint (clearly darker than the painting's own
#     sky next to it) is kept as the thing; the rest becomes the new sky. Big things (roofs, chimneys, the headframe) use Blender's mask edge as it is.
nonsky = 1.0 - sky
wheels_pic = cv2.imread(P('alignment/facts/solo/winding wheels.png'))          # Blender's flat picture of the winding gear (1080 x 1920)
wheel_zone = cv2.resize((wheels_pic.sum(axis=2) > 24).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST)
wheel_zone = cv2.dilate(wheel_zone, np.ones((31, 31), np.uint8)) > 0
# what counts as a "big" thing: not removed by an opening 9 dots wide; round the winding gear 15 dots, so that the crossings of the lattice's rails do not count as big
big = np.where(wheel_zone, cv2.morphologyEx((nonsky > 0.5).astype(np.uint8), cv2.MORPH_OPEN, np.ones((15, 15), np.uint8)),
               cv2.morphologyEx((nonsky > 0.5).astype(np.uint8), cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))).astype(np.uint8)
big_near = cv2.dilate(big, np.ones((5, 5), np.uint8)) > 0
thin = (nonsky > 0.05) & ~big_near
thin_zone = (cv2.dilate(thin.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0) & ~big_near
lum_p = painting[:, :, 2] * 0.2126 + painting[:, :, 1] * 0.7152 + painting[:, :, 0] * 0.0722
pure = (cv2.erode((sky > 0.999).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0).astype(np.float32)
sky_old = np.where(cv2.GaussianBlur(pure, (0, 0), 7) > 0.02, cv2.GaussianBlur(lum_p * pure, (0, 0), 7) / np.maximum(cv2.GaussianBlur(pure, (0, 0), 7), 1e-4),
                   cv2.GaussianBlur(lum_p * pure, (0, 0), 25) / np.maximum(cv2.GaussianBlur(pure, (0, 0), 25), 1e-4))
ratio = lum_p / np.maximum(sky_old, 1.0)
t = np.clip((0.84 - ratio) / (0.84 - 0.62), 0, 1)
keep_thin = t * t * (3 - 2 * t) * thin_zone
nonsky_final = np.where(thin_zone, keep_thin, nonsky * (~thin_zone))
nonsky_final = np.maximum(nonsky_final, nonsky * big_near)
sky = 1.0 - nonsky_final

# 5. put it in
a = sky[:, :, None]
final = painting * (1 - a) + new_sky * a
cv2.imwrite(out_path, final.clip(0, 255).round().astype(np.uint8))
print('saved', out_path, 'sky share of the picture', float(sky.mean()), '; sky colour top / horizon (R,G,B):', rows[0][::-1].round(0), rows[min(H - 1, int(ys.max()))][::-1].round(0))

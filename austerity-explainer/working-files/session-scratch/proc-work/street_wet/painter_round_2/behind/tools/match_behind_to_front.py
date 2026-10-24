"""What this file does (plain words)
-----------------------------------------------------------------------------------------------------------------------------------------
A FREE colour-and-brightness match of the behind painting to the front painting. The painter was asked to match image 2 (the front painting) but painted the behind picture lighter
and warmer (measured in numbers/step1_raw_returned_measurements.json), so where the film hands over from the front painting to the behind painting (a ring round each prop, and
all the ground the props hid) a lighter or warmer patch would show. This tool changes ONLY the broad colour and brightness, never a stroke, a joint, a piece of rubbish or a puddle's shape:

  1. It looks only at the parts where BOTH paintings show the same street (the "visible in both" mask C of measure_behind_painting.py: not sky, not within 12 dots of a removed prop,
     and where the two plates agree, so the props' shadows, reflections and the glare pool are left out).
  2. For each kind of surface (road, gutter and kerb, pavement, walls, windows, roofs, the colliery, the far ground) separately it takes the local AVERAGE colour of the front painting
     and of the behind painting (a Gaussian average 30 dots wide; where there is too little common ground in reach it uses 90, then 250 dots, then the surface's overall average),
     and divides the one by the other, for red, green and blue. That is a smooth "gain" picture: it carries no detail.
  3. Where the props stood, the ground labels come from a picture Blender drew with the props hidden (work/ground_labels_no_props_1536x2730.png), so the road there takes the road's gain
     and the pavement there the pavement's. Anything standing in front of a wall (the notice board) takes the walls' gain.
  4. The behind painting is multiplied by the gain (limited to 0.55 .. 1.25 and softened by a 1.5-dot blur where two surfaces meet). The sky (already the front painting's own sky) is left alone.
Because the gain is smooth, the strokes, joints, rubbish, puddles and ink lines of the painter are kept exactly; only the overall colour balance and brightness follow the front painting.
Run: python3 -I tools/match_behind_to_front.py --in work/behind_with_free_sky.png --out work/behind_matched.png [--strength 1.0]
  (strength 0..1 mixes the gain in: 1 = full match, 0 = leave the painter's picture as it is)
"""
import json
import os
import sys

import cv2
import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
ROOT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/'
R2 = ROOT + 'painter_round_2/'
PAINT = R2 + 'paint/'
PLATE = R2 + 'plate/'
in_path = sys.argv[sys.argv.index('--in') + 1]
out_path = sys.argv[sys.argv.index('--out') + 1]
strength = float(sys.argv[sys.argv.index('--strength') + 1]) if '--strength' in sys.argv else 1.0
W, H = 1536, 2730
k = lambda n: np.ones((n, n), np.uint8)
bl = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)

F = cv2.imread(PAINT + 'front_painting_final.png').astype(np.float32)
B = cv2.imread(P(in_path)).astype(np.float32)
Pf = cv2.imread(PLATE + 'lockout_plate_wet_round2.png').astype(np.float32)
Pn = cv2.imread(PLATE + 'lockout_plate_wet_round2_no_props.png').astype(np.float32)
lum = lambda im: 0.0722 * im[:, :, 0] + 0.7152 * im[:, :, 1] + 0.2126 * im[:, :, 2]


def masks_from(folder):
    f = json.load(open(PAINT + folder + '/facts.json'))
    ids = cv2.cvtColor(cv2.imread(PAINT + folder + '/ids.png'), cv2.COLOR_BGR2RGB).astype(np.int32)
    return {g: cv2.resize(((np.abs(ids - np.array(i['colour'])).sum(axis=2) < 24)).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0 for g, i in f['groups'].items()}


S = masks_from('alignment/facts_surfaces')
Pm = masks_from('alignment/facts')
cov = cv2.imread(PAINT + 'work/sky/sky_coverage_1536x2730.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
sky = cov > 0.001
g = np.load(P('work/ground_labels_no_props.npz'))
HID = ['notice', 'board posts', 'drum', 'pail', 'handcart', 'sacks', 'coal pile', 'spade', 'dustbins']
Z = np.zeros((H, W), bool)
for n in HID:
    Z |= Pm[n]
Zd = cv2.dilate(Z.astype(np.uint8), k(25)) > 0
pd_ = np.abs(bl(lum(Pf), 3) - bl(lum(Pn), 3)) / 255 > 0.03
C = ~sky & ~Zd & ~(cv2.dilate(pd_.astype(np.uint8), k(9)) > 0)

# the label of every dot: which surface it belongs to
names = ['road', 'gutter_kerb', 'pavement', 'walls', 'windows', 'roofs', 'colliery', 'ground far']
lab = np.full((H, W), -1, np.int8)
for i, key in enumerate(['road', None, 'pavement', 'walls', 'windows', 'roofs', 'colliery', 'ground far']):
    if key:
        lab[S[key]] = i
lab[S['gutter'] | S['kerb']] = 1
# where the near props stood: the ground from the props-hidden picture; the rest of what they covered stands in front of the walls
zlab = np.full((H, W), 3, np.int8)
zlab[g['road']] = 0
zlab[g['gutter'] | g['kerb']] = 1
zlab[g['pavement']] = 2
lab = np.where(Z | S['props near'], zlab, lab)
lab[sky] = -1

# the averages are smooth, so they are worked out at a quarter of the size (4 dots become 1) and the gain picture is made big again afterwards
q = 4
sm = lambda a: cv2.resize(a, (W // q, H // q), interpolation=cv2.INTER_AREA)
F4, B4 = sm(F), sm(B)
C4 = sm(C.astype(np.float32)) > 0.99
lab4 = cv2.resize(lab.astype(np.float32), (W // q, H // q), interpolation=cv2.INTER_NEAREST).astype(np.int8)
gain4 = np.ones((H // q, W // q, 3), np.float32)
SIG = [30.0 / q, 90.0 / q, 250.0 / q]
report = {}
for i, name in enumerate(names):
    cls = lab4 == i
    if cls.sum() < 40:
        continue
    w = (C4 & (cv2.erode(cls.astype(np.uint8), k(3)) > 0)).astype(np.float32)
    if w.sum() < 30:
        continue
    est = np.zeros((H // q, W // q, 3), np.float32)
    done = np.zeros((H // q, W // q), bool)
    for s_ in SIG:
        den = bl(w, s_)
        ok = (den > 0.06) & ~done
        if not ok.any():
            continue
        for c in range(3):
            fm = bl(F4[:, :, c] * w, s_) / np.maximum(den, 1e-6)
            bm = bl(B4[:, :, c] * w, s_) / np.maximum(den, 1e-6)
            est[:, :, c] = np.where(ok, fm / np.maximum(bm, 1.0), est[:, :, c])
        done |= ok
    for c in range(3):                                         # the surface's overall average for what is still out of reach
        fm = (F4[:, :, c] * w).sum() / w.sum()
        bm = (B4[:, :, c] * w).sum() / w.sum()
        est[:, :, c] = np.where(done, est[:, :, c], fm / max(bm, 1.0))
    gain4 = np.where(cls[:, :, None], est, gain4)
    report[name] = {'quarter_size_dots_used_for_the_average': int(w.sum()), 'mean_gain_red_green_blue': [round(float(est[:, :, c][cls].mean()), 3) for c in (2, 1, 0)],
                    'least_and_most_gain': [round(float(est[cls].min()), 3), round(float(est[cls].max()), 3)]}
gain = cv2.resize(gain4, (W, H), interpolation=cv2.INTER_LINEAR)
gain = np.clip(gain, 0.55, 1.25)
gain = cv2.GaussianBlur(gain, (0, 0), 1.5)
gain = 1.0 + (gain - 1.0) * strength
gain = 1.0 + (gain - 1.0) * (1.0 - cov)[:, :, None]            # no change in the sky
out = np.clip(B * gain + 0.5, 0, 255).astype(np.uint8)
cv2.imwrite(P(out_path), out)
json.dump(report, open(P('numbers/match_gains_used.json'), 'w'), indent=1)
print(json.dumps(report, indent=1))
print('saved', out_path)

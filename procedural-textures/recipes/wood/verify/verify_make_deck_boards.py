# What this does (plain words): the TRANSFER test. It makes a surface the project was NOT given, SUN-BLEACHED SILVER DECK BOARDS (equal straight boards, narrow dark gaps, butt joints
# where two boards meet end to end, rows of nail heads, a few long straight cracks, very little rust and no knots), by changing ONLY THE DESCRIPTION: the palette, the paint
# model's colour spread, the gap lines (straight, equal), the cracks (a few long straight ones), and two short hand-written lists (butt joints as thin dark ribbons, nail heads as
# small round blobs). The generator code is not touched. It prints what was changed. Run: python3 -I make_deck_boards.py [seed]   (then bake with run_bake_and_score.sh)
import copy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
WOOD = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(WOOD, 'generator'))
import numpy as np
import sampler
import wood_layers as wl
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
dist = sampler.load_distributions()
# 1. a new palette (16 silver-grey and a few warm brown colours), dark to light, with its Lab values
palette = [[28, 25, 23], [48, 43, 39], [64, 59, 54], [82, 77, 71], [98, 93, 86], [112, 107, 99], [126, 121, 112], [138, 133, 123], [148, 143, 133], [158, 152, 141], [168, 161, 149], [178, 170, 157],
           [106, 90, 76], [124, 106, 88], [90, 76, 64], [148, 124, 100]]
lab = wl.srgb_to_lab(palette)
order = np.argsort(lab[:, 0])
palette = [palette[i] for i in order]; lab = lab[order]
dist = copy.deepcopy(dist)
dist['palette_rgb'], dist['palette_lab'] = palette, lab.tolist()
dist['board_lab'] = [58.0, 2.0, 5.0]
# 2. paint model: lighter, calmer zones (smaller colour spread), strips a bit longer and thinner
pm = dist['paint_model']
pm['zone']['lab_mean'] = [57.0, 2.0, 5.0]
pm['zone']['chol'] = [[5.5, 0, 0], [0.3, 0.9, 0], [0.5, 0.2, 1.8]]
pm['child']['0']['chol'] = [[3.0, 0, 0], [0.2, 0.6, 0], [0.3, 0.1, 1.2]]
pm['child']['1']['chol'] = [[3.5, 0, 0], [0.2, 0.7, 0], [0.4, 0.1, 1.4]]
for c in pm['classes']:
    c['aspect'][0] *= 1.4
dist['sampler']['rust_palette_lab'] = [[40.0, 6.0, 12.0]]
d = sampler.sample_description(seed, distributions=dist, boards=6, knots=0, cloud_scale=0.08, crack_scale=0.35, rate=1.1, zone_amp=0.9, child_amp=0.8, palette_jitter=1.5,
                               grain={'hatch': {'u': 30, 'v': 520, 'detail': 1.5, 'seed': 3, 'light_cut': 0.60, 'dark_cut': 0.40, 'light_gain': 1.35, 'dark_gain': 0.7},
                                      'hair': {'u': 4, 'v': 90, 'seed': 5, 'thickness': 0.014, 'gain': 0.55}})
d['palette'] = palette           # (the sampler jittered a copy; use the exact new palette)
# 3. the gap lines: six EQUAL boards with STRAIGHT narrow gaps
tile = 1254; n = 6
d['layers'][0]['gaps'] = [{'y': round(k * tile / n + 20, 1), 'wave': [], 'width': 4.2, 'width_wave': [[5, 0.6, 0.1]]} for k in range(n)]
d['layers'][0]['colours'] = [int(np.argmin(((lab - np.array([55 + 3 * (k % 3), 2, 5])) ** 2).sum(axis=1))) for k in range(n)]
# 4. butt joints: thin dark vertical ribbons where two boards meet end to end (staggered), and rows of nail heads near the joint ends and along each board
rng = np.random.default_rng(seed)
darkest = 0
joints, nails = [], []
gap_y = [g['y'] for g in d['layers'][0]['gaps']]
board_h = tile / n
nail_dark = int(np.argmin(((lab - np.array([30, 1, 2])) ** 2).sum(axis=1))); nail_light = int(np.argmin(((lab - np.array([72, 2, 4])) ** 2).sum(axis=1)))
for k, y in enumerate(gap_y):
    x = (rng.uniform(150, 1100) + k * 410) % tile
    joints.append({'c': darkest, 'pts': [[round(float(x)), round(y + 3), 3.4], [round(float(x)) + 1, round(y + board_h / 2), 3.0], [round(float(x)), round(y + board_h - 3), 3.4]]})
    for dx in (-26, 26):                                       # two nails on each side of the joint, near the board's edges
        for dy in (14, board_h - 14):
            nails.append([nail_dark, round(float(x) + dx), round(y + dy), 3.2]); nails.append([nail_light, round(float(x) + dx - 0.8), round(y + dy - 0.9), 1.3])
    for xx in np.arange(60 + 70 * (k % 3), tile, 220):         # nails along the board: a row near each edge every 220 dots
        for dy in (14, board_h - 14):
            if abs(xx - x) > 60:
                nails.append([nail_dark, round(float(xx)), round(y + dy), 3.2]); nails.append([nail_light, round(float(xx) - 0.8), round(y + dy - 0.9), 1.3])
for layer in d['layers']:
    if layer['type'] == 'gap_ribbons':
        layer['width_scale'] = 1.0
d['layers'].insert(next(i for i, l in enumerate(d['layers']) if l['type'] == 'gap_ribbons') + 1, {'type': 'cracks', 'list': joints})
d['layers'] = [l for l in d['layers'] if l['type'] != 'pebbles']
d['layers'].append({'type': 'blobs', 'seed': 3, 'list': nails})
d['note'] = 'TRANSFER: sun-bleached silver deck boards made from the wood generator by changing the description only'
path = os.path.join(HERE, 'deck_boards_seed%d.json' % seed)
json.dump(d, open(path, 'w'), separators=(',', ':'))
print('wrote', path, os.path.getsize(path), 'bytes;', len(joints), 'butt joints,', len(nails), 'nail dots')

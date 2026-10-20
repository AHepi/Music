# What this does (plain words): assembles the pictures that the two guide files show: the ladder of layers, the derivation check (how the reference height is made from the reference
# colour), the variations, the area picture with a close-up of where the four tiles meet, the resolution close-ups, the transfer pictures (snowy track and the golden mud) and the
# sweep strips. Writes into guide_pictures/. Plain Python; it reads the reference pictures only to put them next to the generated ones.
import json, os, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
PROC = os.path.abspath(os.path.join(ROOT, '..', '..'))
GP = os.path.join(ROOT, 'guide_pictures'); os.makedirs(GP, exist_ok=True)
def read(p): return cv2.imread(p)
def label(img, text, scale=0.7):
    img = img.copy(); cv2.rectangle(img, (0, 0), (img.shape[1], 30), (255, 255, 255), -1)
    cv2.putText(img, text, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), 1, cv2.LINE_AA); return img
def tile(p, text, size=420):
    return label(cv2.resize(read(p), (size, size), interpolation=cv2.INTER_AREA), text)
ref = os.path.join(PROC, 'reference', 'mud', 'colour.png')
# 1. the ladder
rows = [('reference', ref)] + [(n, os.path.join(ROOT, 'outputs', d, 'colour.png')) for n, d in (
    ('R0 flat ground', 'R0_flat_ground'), ('R1 + puddle outlines', 'R1_plus_puddle_outlines'), ('R2 + 40 big stones', 'R2_plus_40_big_stones'), ('R3 + wheel ruts', 'R3_plus_ruts'),
    ('S 7 KB: + clods', 'S_layout_ruts_clods'), ('M 64 KB: + tones, stones', 'M_puddle_tones_stone_faces'), ('L2 traced 2000 patches', 'L2_traced_ground_2000_patches'),
    ('L traced 5000 patches', 'L_traced_ground_5000_patches'), ('L final 503 KB', 'L_final_traced_ground_plus_corrections'))]
rows = [(n, p) for n, p in rows if os.path.exists(p)]
tiles = [tile(p, n) for n, p in rows]
while len(tiles) % 5: tiles.append(np.full_like(tiles[0], 255))
cv2.imwrite(os.path.join(GP, 'ladder.png'), np.vstack([np.hstack(tiles[i:i + 5]) for i in range(0, len(tiles), 5)]))
# 2. derivation check: reference colour | uploaded height | height made from the colour | difference x4
sys.path.insert(0, HERE)
import score_tools as st
c = read(ref); hup = cv2.imread(os.path.join(PROC, 'reference', 'mud', 'height_as_uploaded.png'), cv2.IMREAD_UNCHANGED)
hup = hup[..., 0] if hup.ndim == 3 else hup
hd = st.height_from_colour(c)
diff = np.clip(np.abs(hup.astype(float) - hd) * 4, 0, 255).astype(np.uint8)
cv2.imwrite(os.path.join(GP, 'derivation_check.png'), np.hstack([label(cv2.resize(x, (420, 420), interpolation=cv2.INTER_AREA), t) for x, t in (
    (c, 'reference colour'), (cv2.cvtColor(hup, cv2.COLOR_GRAY2BGR), 'uploaded height'), (cv2.cvtColor(np.round(hd).astype(np.uint8), cv2.COLOR_GRAY2BGR), 'height made from the colour'), (cv2.cvtColor(diff, cv2.COLOR_GRAY2BGR), 'difference x 4'))]))
# 3. the L-final difference sheet (copy, scaled)
p = os.path.join(ROOT, 'outputs', 'L_final_traced_ground_plus_corrections', 'diff_sheet.png')
if os.path.exists(p): cv2.imwrite(os.path.join(GP, 'diff_sheet_L_final.png'), read(p))
# 4. area picture and the close-up where four tiles meet
a = os.path.join(ROOT, 'area', 'area_2508', 'colour.png')
if os.path.exists(a):
    big = read(a)
    cv2.imwrite(os.path.join(GP, 'area_2508_small.png'), cv2.resize(big, (1254, 1254), interpolation=cv2.INTER_AREA))
    rolled = np.roll(big, (1254, 1254), axis=(0, 1))                     # the four quadrant corners now meet in the middle, so the seams and the wrap edge are in view
    cv2.imwrite(os.path.join(GP, 'area_seam_closeup.png'), np.hstack([label(big[954:1554, 954:1554], 'middle of the area (no seam expected)'), label(rolled[954:1554, 954:1554], 'the wrap-around edge brought to the middle')]))
# 5. resolution close-ups: the same 130 x 130 dot window (in 1254-dot units) at 512, 1254, 2508
sizes = [(512, 'resolution/size_512'), (1254, 'variations/tile_101'), (2508, 'resolution/size_2508')]
crops = []
for s, f in sizes:
    p = os.path.join(ROOT, f, 'colour.png')
    if os.path.exists(p):
        im = read(p); k = s / 1254.0; x0, y0, w = int(500 * k), int(560 * k), int(150 * k)
        crops.append(label(cv2.resize(im[y0:y0 + w, x0:x0 + w], (450, 450), interpolation=cv2.INTER_NEAREST), f'{s} dots (window shown at the same size)', 0.55))
if crops: cv2.imwrite(os.path.join(GP, 'resolution_closeups.png'), np.hstack(crops))
# 6. transfer: snow beside the mud reference; golden reference beside golden S, M, L
snow = os.path.join(ROOT, 'transfer', 'snow', 'colour.png')
if os.path.exists(snow): cv2.imwrite(os.path.join(GP, 'transfer_snow.png'), np.hstack([tile(ref, 'mud reference', 600), tile(snow, 'snowy track: same generator, new numbers', 600)]))
gold = os.path.join(PROC, 'reference', 'mud_golden', 'colour.png')
g_tiles = [tile(gold, 'golden reference', 420)] + [tile(os.path.join(ROOT, 'outputs_golden', n, 'colour.png'), t, 420) for n, t in (('S_layout_ruts_clods', 'golden S 7 KB'), ('M_puddle_tones_stone_faces', 'golden M'), ('L_final_traced_ground_plus_corrections', 'golden L final')) if os.path.exists(os.path.join(ROOT, 'outputs_golden', n, 'colour.png'))]
if len(g_tiles) > 1:
    while len(g_tiles) % 2: g_tiles.append(np.full_like(g_tiles[0], 255))
    cv2.imwrite(os.path.join(GP, 'transfer_golden.png'), np.vstack([np.hstack(g_tiles[i:i + 2]) for i in range(0, len(g_tiles), 2)]))
# 7. the sweep strips
for name in sorted(os.listdir(GP)):
    if name.startswith('sweep_') and os.path.exists(os.path.join(GP, name, 'sweep.json')):
        title = json.load(open(os.path.join(GP, name, 'sweep.json'))).get('title', name)
        subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', 'make_strip.py'), os.path.join(GP, name), os.path.join(GP, 'strip_' + name[6:] + '.png'), '--cell', '300', '--title', title], stdout=subprocess.DEVNULL)
# 8. normal-strength strip from one bake (numpy)
h16 = cv2.imread(os.path.join(ROOT, 'outputs', 'L_final_traced_ground_plus_corrections', 'height.png'), cv2.IMREAD_UNCHANGED)
if h16 is not None:
    h8 = np.round((h16[..., 0] if h16.ndim == 3 else h16).astype(np.float64) / 65535 * 255)
    cells = []
    for s in (2, 5, 9, 14):
        hx = (np.roll(h8, -1, 1) - np.roll(h8, 1, 1)) / 2.0; hy = (np.roll(h8, -1, 0) - np.roll(h8, 1, 0)) / 2.0
        n = np.stack([-s * hx / 255, s * hy / 255, np.ones_like(h8)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
        img = ((n * 0.5 + 0.5) * 255).astype(np.uint8)[..., ::-1]
        cells.append(label(cv2.resize(img[300:700, 300:700], (400, 400), interpolation=cv2.INTER_NEAREST), f'normal strength {s}' + (' (the reference uses 9)' if s == 9 else ''), 0.55))
    cv2.imwrite(os.path.join(GP, 'strip_normal_strength.png'), np.hstack(cells))
print('guide pictures:', sorted(f for f in os.listdir(GP) if f.endswith('.png')))

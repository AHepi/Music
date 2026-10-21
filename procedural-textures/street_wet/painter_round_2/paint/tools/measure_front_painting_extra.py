"""What this file does (plain words)
-----------------------------------------------------------------------------------------------------------------------------------------
Extra measuring of the round 2 front painting, next to measure_wet_cues_round2.py (which repeats the first test's measures). It adds what round 2 asked for:
  A. SKY of the final picture (painting with the free dark sky) against the plate's sky, and of the returned painting, the first test's painting.
  B. JOINTS visible on the road: with the plate step's own measure (measure_grid_visibility.py: for dots next to a joint, how much they differ from the stone beside them,
     compared with the stone's own mottling), using Blender's joint mask for the lockout camera at 1536 x 2730. Dots under puddles are left out.
  C. RUBBISH kept: small dark compact blobs (coal, cinders, mud, dark paper) found the same way in the plate and in each painting, on the ground (road, pavement, gutter, kerb,
     not under the props). "kept" = share of the plate's blobs that have a blob within 7 dots in the painting; "added" = share of the painting's blobs with none within 7 dots in the plate.
     A control shifts the painting 60 dots sideways to show what chance gives.
  D. PUDDLES: brightness inside the puddles (Blender's puddle mask) in the plate and in each painting, and how alike the pattern is.
  E. LAMP GLASS colour: the brightest dots of each gas lamp's head: red, green, blue, hue and strength of colour.
  F. NOTHING ADDED OR MOVED: where the painting differs from the plate most in broad brightness (blurred), as a picture, for a look by eye; and how far each part's edges moved.
Writes numbers/front_painting_extra.json. Plain Python (numpy, OpenCV); the first test's pictures and masks are only read.
Run: python3 -I tools/measure_front_painting_extra.py
"""
import json
import os
import sys

import cv2
import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
ROOT = 'proc-work/street_wet/'
PLATE_TOOLS = ROOT + 'painter_round_2/plate/'
sys.path.insert(0, PLATE_TOOLS + 'setts/tools')
sys.path.insert(0, PLATE_TOOLS + 'study/tools')
from measure_grid_visibility import grid_visibility  # noqa: E402
from b04_measure_joints import load_mask, load_puddles  # noqa: E402

W, H = 1536, 2730
def load(path): return cv2.resize(cv2.imread(path), (W, H), interpolation=cv2.INTER_AREA)
imgs = {
    'plate': load(PLATE_TOOLS + 'lockout_plate_wet_round2.png'),
    'paint_new': load(P('front_painting_lined_up.png')),
    'paint_final': load(P('front_painting_final.png')),
    'paint_test1': load(ROOT + 'painter_test/pictures/wet_painting_lined_up.png'),
    'plate_test1': load(ROOT + 'work/r35/main_wet_plate.png'),
    'paint_dry': load('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg'),
}
def lum(img):
    b, g, r = [img[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
L = {k: lum(v) for k, v in imgs.items()}
out = {'note': 'all at 1536 x 2730; brightness = picture brightness 0 (black) to 1 (white), Rec.709 weights'}

def masks_from(folder):
    f = json.load(open(P(folder, 'facts.json')))
    ids = cv2.cvtColor(cv2.imread(P(folder, 'ids.png')), cv2.COLOR_BGR2RGB).astype(np.int32)
    return {g: cv2.resize(((np.abs(ids - np.array(i['colour'])).sum(axis=2) < 24)).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0 for g, i in f['groups'].items()}, ids
S, ids_s = masks_from('alignment/facts_surfaces')
Pm, ids_p = masks_from('alignment/facts')
skymask = cv2.resize((ids_p.sum(axis=2) < 24).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
cov = cv2.imread(P('work/sky/sky_coverage_1536x2730.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255

# ---- A. sky
sk = (cov > 0.999) & (cv2.erode((cov > 0.999).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0) & (np.arange(H)[:, None] < 0.5 * H)
base_plate = cv2.GaussianBlur(np.where(sk, L['plate'], 0), (0, 0), 60) / np.maximum(cv2.GaussianBlur(sk.astype(np.float32), (0, 0), 60), 1e-4)
sky = {}
for k in ('plate', 'paint_new', 'paint_final', 'paint_test1', 'plate_test1', 'paint_dry'):
    v = L[k][sk]
    base = base_plate if k != 'plate_test1' and k != 'paint_test1' else cv2.GaussianBlur(np.where(sk, L['plate_test1'], 0), (0, 0), 60) / np.maximum(cv2.GaussianBlur(sk.astype(np.float32), (0, 0), 60), 1e-4)
    sky[k] = {'mean_brightness': float(v.mean()), 'p95': float(np.percentile(v, 95)), 'max': float(v.max()), 'share_over_0.5': float((v > 0.5).mean()),
              'share_brighter_than_its_plate_sky_by_0.12': float(((L[k] - base) > 0.12)[sk].mean()),
              'share_brighter_than_its_plate_sky_by_0.05': float(((L[k] - base) > 0.05)[sk].mean()),
              'share_darker_than_its_plate_sky_by_0.12': float(((base - L[k]) > 0.12)[sk].mean())}
out['sky'] = {'note': 'sky dots = Blender sky mask (fully sky, 4 dots away from any edge), top half; each painting is compared with the plate it was painted from (the first test with its own older plate)', **sky}

# ---- B. joints on the road
mask_path = PLATE_TOOLS + 'rubbish/work/plates04/mask_lockout_1536x2730.png'
pud_path = PLATE_TOOLS + 'rubbish/work/plates04/lockout_A_wet_1536x2730_puddlemask.png'
M = load_mask(mask_path)
pud = load_puddles(pud_path)
joints = {}
for k in ('plate', 'paint_new', 'paint_test1', 'plate_test1', 'paint_dry'):
    joints[k] = grid_visibility(L[k], M, pud)
out['joints_on_road'] = {'note': 'line = how much dots next to a joint differ from the stone beside them (0 = no grid, 0.3 = 30 percent); texture = the stone\'s own mottling; a grid is visible when line >= 0.12 and >= 2 x texture. Positions of the PLATE\'s joints are used for every picture.', **joints}

# ---- C. rubbish
ground = (S['road'] | S['pavement'] | S['gutter'] | S['kerb'])
props = np.zeros((H, W), bool)
for g in ('drum', 'sacks', 'handcart', 'dustbins', 'pail', 'coal pile', 'spade', 'notice', 'board posts'):
    props |= Pm[g]
exclude = cv2.dilate(props.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
zone = ground & ~exclude
zone_er = cv2.erode(zone.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
def blobs(k):
    g8 = (np.clip(L[k], 0, 1) * 255).astype(np.uint8)
    med = cv2.medianBlur(g8, 25).astype(np.float32) / 255
    dark = ((med - L[k]) > 0.07) & (L[k] < 0.22) & zone_er
    n, lab, stats, cent = cv2.connectedComponentsWithStats(dark.astype(np.uint8), connectivity=8)
    keep = []
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if 6 <= a <= 400 and max(w, h) / max(1, min(w, h)) < 3.2 and a / (w * h) > 0.35:
            keep.append(cent[i])
    return np.array(keep).reshape(-1, 2)
def match_share(A, B, tol=7.0):
    if len(A) == 0 or len(B) == 0: return 0.0
    m = np.zeros((H, W), np.uint8)
    for x, y in B.round().astype(int):
        if 0 <= x < W and 0 <= y < H: m[y, x] = 255
    dist = cv2.distanceTransform(255 - m, cv2.DIST_L2, 3)
    return float(np.mean([dist[int(round(y)), int(round(x))] <= tol for x, y in A if 0 <= int(round(y)) < H and 0 <= int(round(x)) < W]))
zone_area_100k = zone_er.sum() / 1e5
rub = {}
bl = {k: blobs(k) for k in ('plate', 'paint_new', 'paint_test1', 'plate_test1')}
for pa, pl in (('paint_new', 'plate'), ('paint_test1', 'plate_test1')):
    shifted = bl[pa] + np.array([60.0, 0.0])
    rub[pa] = {'against': pl, 'plate_blobs': int(len(bl[pl])), 'painting_blobs': int(len(bl[pa])),
               'plate_blobs_per_100k_dots_of_ground': float(len(bl[pl]) / zone_area_100k), 'painting_blobs_per_100k_dots_of_ground': float(len(bl[pa]) / zone_area_100k),
               'kept_share_of_plate_blobs_with_a_painting_blob_within_7_dots': match_share(bl[pl], bl[pa]),
               'chance_level_for_kept_share_(painting_shifted_60_dots)': match_share(bl[pl], shifted),
               'added_share_of_painting_blobs_with_no_plate_blob_within_7_dots': 1 - match_share(bl[pa], bl[pl]),
               'chance_level_for_added_share_(painting_shifted_60_dots)': 1 - match_share(shifted, bl[pl])}
out['rubbish_blobs'] = {'note': 'small dark compact blobs (6 to 400 dots, darker than the surroundings by 0.07 and under 0.22 bright) on road, pavement, gutter, kerb away from props; the first test used its own older plate with far fewer pieces', 'ground_area_dots': int(zone_er.sum()), **rub}
# per zone density
def dens(pts, m):
    c = sum(1 for x, y in pts.round().astype(int) if 0 <= x < W and 0 <= y < H and m[y, x])
    return c / max(1, m.sum()) * 1e5
zones = {'gutter and kerb': S['gutter'] | S['kerb'], 'pavement': S['pavement'], 'road': S['road']}
out['rubbish_blobs']['per_100k_dots_by_zone'] = {zn: {k: float(dens(bl[k], cv2.erode((zm & zone).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)) for k in bl} for zn, zm in zones.items()}

# ---- D. puddles
pm = cv2.erode(pud.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
pm &= S['road'] | S['gutter'] | S['pavement'] | S['kerb']
ring = (cv2.dilate(pud.astype(np.uint8), np.ones((41, 41), np.uint8)) > 0) & ~(cv2.dilate(pud.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0) & (S['road'] | S['gutter'] | S['pavement'] | S['kerb'])
pdres = {'puddle_share_of_ground': float(pm.sum() / max(1, ground.sum())), 'puddle_dots': int(pm.sum())}
sm = {k: cv2.GaussianBlur(L[k], (0, 0), 6) for k in ('plate', 'paint_new', 'paint_test1', 'plate_test1', 'paint_dry')}
for k in ('plate', 'paint_new', 'paint_test1', 'paint_dry'):
    pdres[k] = {'mean_brightness_in_puddles': float(L[k][pm].mean()), 'mean_brightness_of_ground_just_round_puddles': float(L[k][ring].mean()),
                'puddle_minus_round': float(L[k][pm].mean() - L[k][ring].mean()), 'roughness_in_puddles_(std_of_fine_detail)': float((L[k] - cv2.GaussianBlur(L[k], (0, 0), 3))[pm].std())}
for k in ('paint_new', 'paint_test1', 'paint_dry'):
    ref = 'plate' if k != 'paint_test1' else 'plate'
    pdres[k]['pattern_likeness_with_plate_inside_puddles_(correlation_of_blurred_brightness)'] = float(np.corrcoef(sm['plate'][pm], sm[k][pm])[0, 1])
out['puddles'] = pdres

# ---- E. lamp glass colour
def lamp_colour(img, group):
    m = Pm[group]
    ys, xs = np.nonzero(m)
    if len(ys) == 0: return None
    top = ys.min() + 0.30 * (ys.max() - ys.min())
    sel = m & (np.arange(H)[:, None] <= top)
    l = lum(img)[sel]
    thr = np.percentile(l, 90)
    px = img[sel][l >= thr][:, ::-1].astype(float)                    # RGB
    r, g, b = px.mean(axis=0)
    hsv = cv2.cvtColor(np.uint8([[[round(r), round(g), round(b)]]]), cv2.COLOR_RGB2HSV)[0, 0]
    return {'red_green_blue_(0-255)': [round(r), round(g), round(b)], 'hue_degrees_(30 = orange-amber, 50 = yellow, 60 = pale yellow)': round(float(hsv[0]) * 2), 'colour_strength_(0 grey - 1 full)': round(float(hsv[1]) / 255, 2), 'blue_over_red': round(b / max(r, 1), 2)}
out['lamp_glass'] = {'note': 'the brightest tenth of the dots in the top 30 percent of each lamp (the lamp head: glass and mantle); lamp left and lamp near right', **{k: {g: lamp_colour(imgs[k], g) for g in ('lamp left', 'lamp near right')} for k in ('plate', 'paint_new', 'paint_test1', 'paint_dry')}}

# ---- F. broad difference painting - plate (look by eye) and how much each prop's edges moved
d = cv2.GaussianBlur(L['paint_new'], (0, 0), 12) - cv2.GaussianBlur(L['plate'], (0, 0), 12)
d1 = cv2.GaussianBlur(L['paint_test1'], (0, 0), 12) - cv2.GaussianBlur(L['plate_test1'], (0, 0), 12)
vis = np.clip(0.5 + d * 2.0, 0, 1)
cv2.imwrite(P('work/broad_difference_painting_minus_plate.png'), (cv2.resize(vis, (540, 960)) * 255).astype(np.uint8))
nonsky = ~skymask
out['broad_brightness_difference_painting_minus_plate_(blurred,_not_sky)'] = {
    'paint_new': {'mean': float(d[nonsky].mean()), 'mean_absolute': float(np.abs(d[nonsky]).mean()), 'share_of_dots_brighter_than_plate_by_0.10': float((d[nonsky] > 0.10).mean()), 'share_darker_by_0.10': float((d[nonsky] < -0.10).mean())},
    'paint_test1_vs_its_plate': {'mean': float(d1[nonsky].mean()), 'mean_absolute': float(np.abs(d1[nonsky]).mean()), 'share_of_dots_brighter_than_plate_by_0.10': float((d1[nonsky] > 0.10).mean()), 'share_darker_by_0.10': float((d1[nonsky] < -0.10).mean())}}
json.dump(out, open(P('numbers/front_painting_extra.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))

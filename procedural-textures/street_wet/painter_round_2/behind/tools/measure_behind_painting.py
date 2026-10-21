"""What this file does (plain words)
-----------------------------------------------------------------------------------------------------------------------------------------
Measures the WET BEHIND PAINTING against the front painting and the plates (everything at 1536 x 2730; "brightness" = the picture's own pixel brightness from 0, black,
to 1, white, Rec.709 weights). The pictures: F = the front painting (final, free sky); B = the behind painting under test; Pn = the props-free plate it was painted from;
Pf = the plate with the props; OP and OB = the film's own old DRY painting and DRY behind painting of the same shot (read only, for comparison).

Masks (Blender's, for the lockout camera; the first test's / front step's files, read only; plus two pictures drawn for this step on the rented machine with the film's near props HIDDEN, so that
the ground where the props stood is known: work/ground_labels_no_props_1536x2730.png (road / gutter / kerb / pavement) and work/joint_mask_no_props_1536x2730.png (joints and stones of the road)):
  Z   where the near props stood in the front picture (the removed props' silhouettes: notice, board posts, drum, pail, handcart, sacks, coal pile, spade, dustbins)
  C   "visible in both": everything that is not sky, not within 12 dots of a removed prop, and where the two PLATES agree (blurred brightness differs by less than 0.03,
      so the props' shadows, reflections and the brazier light pool that changes when the drum is gone are left out). On C both paintings should show the same thing.
  SH  the props' shadows, reflections and the glare pool: where the plates differ, outside Z (the behind painting is allowed to differ from the front one there)
  RING  the ground within 60 dots of a removed prop that is in C (the film hands over from the front to the behind painting in a ring like this as soon as the camera moves)

Measures:
  1. MATCH: on C (and on RING), by surface (road far / middle / near thirds, pavement and kerb, gutter, walls): mean brightness of each, the difference B - F,
     the mean blue-minus-red, the mean absolute difference of the blurred brightness (sigma 4), the correlation of the blurred brightness, the share of "glint" dots;
     the same for the film's old pair OB - OP (how well the old pair matched).
  2. WHERE THE PROPS STOOD (Z, ground only): brightness, blue-minus-red and glint share of B there, against the common road around it in the same picture (a smooth local
     average of the ground in C) - the same for the props-free plate Pn and the film's old dry behind painting OB, so a dry ground would show as a high brightness.
  3. GHOST PROPS: how strong the picture's edges are along the removed props' outlines against inside the silhouettes (ratio), for F (props there), B, Pn and OB;
     and the share of Z that is much darker or brighter than the ground round it (something standing there).
  4. RUBBISH: small dark compact blobs per 100,000 dots of ground, inside Z and elsewhere, in Pn and B; and how many of the plate's blobs the painting kept (within 7 dots)
     against chance.
  5. JOINTS (the plate step's own measure): how much dots next to a sett joint differ from the stone beside them, whole road and only where the props stood.
  6. SKY: B against F inside Blender's sky mask. 7. WHOLE PICTURE brightness and warm-pool brightness.
Writes numbers/behind_painting_measurements.json. Use: python3 -I tools/measure_behind_painting.py --behind work/behind_with_free_sky.png [--tag NAME]
"""
import json
import os
import sys

import cv2
import numpy as np

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # behind/
P = lambda *a: os.path.join(HERE, *a)
ROOT = 'proc-work/street_wet/'
R2 = ROOT + 'painter_round_2/'
PAINT = R2 + 'paint/'
PLATE_TOOLS = R2 + 'plate/'
sys.path.insert(0, PLATE_TOOLS + 'setts/tools')
sys.path.insert(0, PLATE_TOOLS + 'study/tools')
from measure_grid_visibility import grid_visibility  # noqa: E402
from b04_measure_joints import load_mask, load_puddles  # noqa: E402

behind_path = sys.argv[sys.argv.index('--behind') + 1]
tag = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'behind_painting'
W, H = 1536, 2730


def load(path): return cv2.resize(cv2.imread(path), (W, H), interpolation=cv2.INTER_AREA)


imgs = {
    'F': load(PAINT + 'front_painting_final.png'),
    'B': load(P(behind_path)),
    'Pn': load(PLATE_TOOLS + 'lockout_plate_wet_round2_no_props.png'),
    'Pf': load(PLATE_TOOLS + 'lockout_plate_wet_round2.png'),
    'OP': load('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-painted.jpg'),
    'OB': load('/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout-behind.jpg'),
}


def lum(img):
    b, g, r = [img[:, :, i].astype(np.float32) / 255 for i in range(3)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


L = {k: lum(v) for k, v in imgs.items()}
bmr = {k: (v[:, :, 0].astype(np.float32) - v[:, :, 2]) / 255 for k, v in imgs.items()}      # blue minus red


def masks_from(folder):
    f = json.load(open(PAINT + folder + '/facts.json'))
    ids = cv2.cvtColor(cv2.imread(PAINT + folder + '/ids.png'), cv2.COLOR_BGR2RGB).astype(np.int32)
    return {g: cv2.resize(((np.abs(ids - np.array(i['colour'])).sum(axis=2) < 24)).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0 for g, i in f['groups'].items()}, ids


S, ids_s = masks_from('alignment/facts_surfaces')
Pm, ids_p = masks_from('alignment/facts')
sky_cov = cv2.imread(PAINT + 'work/sky/sky_coverage_1536x2730.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
sky = sky_cov > 0.001
HID = ['notice', 'board posts', 'drum', 'pail', 'handcart', 'sacks', 'coal pile', 'spade', 'dustbins']
Z = np.zeros((H, W), bool)
for g in HID:
    Z |= Pm[g]
k = lambda n: np.ones((n, n), np.uint8)
Zd = cv2.dilate(Z.astype(np.uint8), k(25)) > 0                      # 12 dots each side
ground = S['road'] | S['pavement'] | S['gutter'] | S['kerb']
_g = np.load(P('work/ground_labels_no_props.npz'))
road_np, gut_np, kerb_np, pav_np = _g['road'], _g['gutter'], _g['kerb'], _g['pavement']      # the ground as it is with the near props hidden
ground_np = road_np | gut_np | kerb_np | pav_np
er = lambda m, n=5: cv2.erode(m.astype(np.uint8), k(n)) > 0

bl = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
plate_diff = np.abs(bl(L['Pf'], 3) - bl(L['Pn'], 3)) > 0.03
plate_diff_d = cv2.dilate(plate_diff.astype(np.uint8), k(9)) > 0
C = ~sky & ~Zd & ~plate_diff_d
SH = plate_diff_d & ~Zd & ~sky
RING = (cv2.dilate(Z.astype(np.uint8), k(121)) > 0) & C
out = {'note': '1536 x 2730; brightness 0..1 (Rec.709); F front painting, B behind painting, Pn props-free plate, Pf plate with props, OP/OB the film\'s old dry painting and dry behind painting',
       'picture_measured': behind_path,
       'mask_sizes_share_of_picture': {'Z (where the props stood)': float(Z.mean()), 'C (visible in both)': float(C.mean()), 'SH (shadows, reflections, glare pool changed)': float(SH.mean()), 'RING (C within 60 dots of a prop)': float(RING.mean())}}

# surface classes
road = S['road']
ys = np.nonzero(road)[0]
y0, y1 = ys.min(), ys.max()
e = [y0, y0 + (y1 - y0) // 3, y0 + 2 * (y1 - y0) // 3, y1 + 1]
def rows(m, a, b):
    r = np.zeros_like(m); r[a:b] = m[a:b]; return r
classes = {'road far third': rows(road, e[0], e[1]), 'road middle third': rows(road, e[1], e[2]), 'road near third': rows(road, e[2], e[3]),
           'pavement and kerb': S['pavement'] | S['kerb'], 'gutter': S['gutter'], 'walls': S['walls']}


def glint(Lx, m):
    g8 = (np.clip(Lx, 0, 1) * 255).astype(np.uint8)
    med = cv2.medianBlur(g8, 31).astype(np.float32) / 255
    return float(((Lx - med) > 0.10)[m].mean())


# ---- 1. match on C and on the RING
def match_block(zone_mask):
    res = {}
    for name, cm in list(classes.items()) + [('all ground and walls (not sky)', ground | S['walls'])]:
        m = er(cm & zone_mask, 3)
        if m.sum() < 300:
            res[name] = {'dots': int(m.sum())}
            continue
        row = {'dots': int(m.sum())}
        for a, b, label in (('F', 'B', 'behind_vs_front'), ('OP', 'OB', 'old_dry_behind_vs_old_dry_painting')):
            la, lb = L[a], L[b]
            sa, sb = bl(la, 4), bl(lb, 4)
            row[label] = {'mean_brightness_front_or_painting': float(la[m].mean()), 'mean_brightness_behind': float(lb[m].mean()),
                          'difference_behind_minus_front': float(lb[m].mean() - la[m].mean()), 'ratio_behind_over_front': float(lb[m].mean() / la[m].mean()),
                          'blue_minus_red_front': float(bmr[a][m].mean()), 'blue_minus_red_behind': float(bmr[b][m].mean()),
                          'mean_absolute_difference_blurred_sigma4': float(np.abs(sa - sb)[m].mean()),
                          'correlation_blurred_sigma4': float(np.corrcoef(sa[m], sb[m])[0, 1]),
                          'glint_share_front': glint(la, m), 'glint_share_behind': glint(lb, m),
                          'mean_abs_difference_each_colour_0_255_(R,G,B)': [float(np.abs(imgs[a][:, :, c].astype(float) - imgs[b][:, :, c])[m].mean()) for c in (2, 1, 0)]}
        res[name] = row
    return res


out['1_match_on_the_parts_visible_in_both'] = match_block(C)
out['1b_match_in_the_ring_round_the_props'] = match_block(RING)

# ---- 2. where the props stood: the ground there against the common ground around it
def smooth_ref(Lx, valid, sigma=45):
    w = valid.astype(np.float32)
    return bl(Lx * w, sigma) / np.maximum(bl(w, sigma), 1e-4), bl(w, sigma)
zone_where = {'road': road_np & Z, 'pavement and kerb': (pav_np | kerb_np) & Z, 'all ground': ground_np & Z}
res2 = {}
for pic in ('B', 'Pn', 'OB'):
    row = {}
    for name, zm in zone_where.items():
        zm = er(zm, 3)
        if zm.sum() < 300: continue
        valid = C & ground & (road if name == 'road' else ground)   # the common ground (C) of the same kind round the spot
        ref, den = smooth_ref(L[pic], valid)
        refb, _ = smooth_ref(bmr[pic], valid)
        ok = zm & (den > 0.02)
        g8 = (np.clip(L[pic], 0, 1) * 255).astype(np.uint8)
        med = cv2.medianBlur(g8, 31).astype(np.float32) / 255
        gl_in = float(((L[pic] - med) > 0.10)[ok].mean())
        gl_around = float(((L[pic] - med) > 0.10)[valid & (cv2.dilate(Z.astype(np.uint8), k(241)) > 0)].mean())
        row[name] = {'dots': int(ok.sum()), 'mean_brightness_where_props_stood': float(L[pic][ok].mean()), 'mean_brightness_of_the_common_ground_round_it': float(ref[ok].mean()),
                     'ratio_brightness_where_stood_over_round_it': float(L[pic][ok].mean() / ref[ok].mean()),
                     'blue_minus_red_where_stood': float(bmr[pic][ok].mean()), 'blue_minus_red_round_it': float(refb[ok].mean()),
                     'glint_share_where_stood': gl_in, 'glint_share_on_the_common_ground_within_60_dots_of_it': gl_around}
    res2[pic] = row
out['2_where_the_props_stood_(road,_pavement)_against_the_common_ground_round_it'] = {'note': 'B = this behind painting; Pn = the plate it was painted from; OB = the film\'s old DRY behind painting. A dry ground would show as a ratio well above 1 for a dark wet street, a redder (less blue) colour and fewer glints.', **res2}

# ---- 3. ghost props
grad = {}
for pic in ('F', 'B', 'Pn', 'OB'):
    g = bl(L[pic], 1.2)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    grad[pic] = np.sqrt(gx * gx + gy * gy)
ghost = {}
# a control for each outline: the same kind of dots 12 to 28 dots away from the outline (outside and inside), away from every removed prop's outline, so the picture's general
# busy-ness (a painting has more brush edges than a plate) is divided out: ghost_excess = (B along the outline / B on the control) / (plate along the outline / plate on the control)
all_edges = np.zeros((H, W), bool)
for grp in HID:
    m_ = Pm[grp].astype(np.uint8)
    all_edges |= (m_ - cv2.erode(m_, k(3))) > 0
all_band = cv2.dilate(all_edges.astype(np.uint8), k(17)) > 0
for grp in HID:
    m = Pm[grp].astype(np.uint8)
    if m.sum() < 400: continue
    edge = (m - cv2.erode(m, k(3))) > 0
    band = cv2.dilate(edge.astype(np.uint8), k(7)) > 0
    outside = (cv2.dilate(m, k(57)) > 0) & ~(cv2.dilate(m, k(25)) > 0)
    inside_ring = (cv2.erode(m, k(25)) > 0) & ~(cv2.erode(m, k(57)) > 0)
    control = (outside | inside_ring) & ~all_band & ~sky
    inside = cv2.erode(m, k(15)) > 0
    inside_g = inside & ground_np
    row = {}
    for pic in ('F', 'B', 'Pn', 'OB'):
        a_ = float(grad[pic][band].mean()); c_ = float(grad[pic][control].mean())
        b_ = float(grad[pic][inside_g].mean()) if inside_g.sum() > 200 else None
        row[pic] = {'edge_strength_along_outline': a_, 'edge_strength_on_the_control_dots_12_to_28_away': c_, 'outline_over_control': a_ / c_, 'edge_strength_on_the_ground_inside': b_}
    for pic in ('B', 'OB', 'F'):
        row['ghost_excess_' + pic] = row[pic]['outline_over_control'] / row['Pn']['outline_over_control']
    ghost[grp] = row
out['3_ghost_props_edge_strength_along_the_removed_props_outlines'] = ghost
# something standing where the props stood: ground dots much darker or brighter than the common ground round them (blurred)
stand = {}
for pic in ('B', 'Pn', 'OB'):
    valid = C & ground
    ref, den = smooth_ref(L[pic], valid, 60)
    d = bl(L[pic], 6) - ref
    zm = er(Z & ground_np, 3) & (den > 0.02)
    stand[pic] = {'dots': int(zm.sum()), 'share_darker_than_the_ground_round_by_0.10': float((d[zm] < -0.10).mean()), 'share_brighter_than_the_ground_round_by_0.10': float((d[zm] > 0.10).mean()),
                  'share_darker_by_0.05': float((d[zm] < -0.05).mean()), 'share_brighter_by_0.05': float((d[zm] > 0.05).mean())}
out['3b_ground_where_props_stood_much_darker_or_brighter_than_the_ground_round_it_(blurred)'] = stand

# ---- 4. rubbish
zone_r = er(ground_np & ~(cv2.dilate(Pm['lamp left'].astype(np.uint8), k(9)) > 0), 5)
def blobs(Lx, zone):
    g8 = (np.clip(Lx, 0, 1) * 255).astype(np.uint8)
    med = cv2.medianBlur(g8, 25).astype(np.float32) / 255
    dark = ((med - Lx) > 0.07) & (Lx < 0.22) & zone
    n, lab, stats, cent = cv2.connectedComponentsWithStats(dark.astype(np.uint8), connectivity=8)
    keep = []
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if 6 <= a <= 400 and max(w, h) / max(1, min(w, h)) < 3.2 and a / (w * h) > 0.35:
            keep.append(cent[i])
    return np.array(keep).reshape(-1, 2)
def match_share(A, Bp, tol=7.0):
    if len(A) == 0 or len(Bp) == 0: return 0.0
    m = np.zeros((H, W), np.uint8)
    for x, y in Bp.round().astype(int):
        if 0 <= x < W and 0 <= y < H: m[y, x] = 255
    dist = cv2.distanceTransform(255 - m, cv2.DIST_L2, 3)
    return float(np.mean([dist[int(round(y)), int(round(x))] <= tol for x, y in A if 0 <= int(round(y)) < H and 0 <= int(round(x)) < W]))
zone_z = er(Z & ground_np, 5)          # where the props stood (the plate Pn has rubbish there; the front picture does not show it)
zone_c = zone_r & C
bpl, bpa, bfr = blobs(L['Pn'], zone_r), blobs(L['B'], zone_r), blobs(L['F'], zone_r)
def inside(pts, m): return np.array([p for p in pts if 0 <= int(round(p[1])) < H and 0 <= int(round(p[0])) < W and m[int(round(p[1])), int(round(p[0]))]]).reshape(-1, 2)
rub = {}
for name, zm in (('where the props stood', zone_z), ('visible in both (C)', zone_c), ('all ground', zone_r)):
    a100k = max(zm.sum(), 1) / 1e5
    pl, pa = inside(bpl, zm), inside(bpa, zm)
    shifted = pa + np.array([60.0, 0.0])
    rub[name] = {'ground_dots': int(zm.sum()), 'plate_blobs_per_100k': float(len(pl) / a100k), 'behind_painting_blobs_per_100k': float(len(pa) / a100k),
                 'kept_share_of_plate_blobs_found_in_the_painting_within_7_dots': match_share(pl, pa), 'chance_level_(painting_shifted_60_dots)': match_share(pl, shifted),
                 'added_share_of_painting_blobs_with_no_plate_blob_within_7_dots': 1 - match_share(pa, pl), 'chance_level_for_added_share': 1 - match_share(shifted, pl)}
out['4_rubbish_blobs'] = rub
a100k = zone_c.sum() / 1e5
out['4b_front_painting_blobs_per_100k_on_C_(for_comparison)'] = float(len(inside(bfr, zone_c)) / a100k)

# ---- 5. joints
mask_path = P('work/joint_mask_no_props_1536x2730.png')      # drawn with the near props hidden
pud_path = PLATE_TOOLS + 'rubbish/work/plates04/lockout_A_wet_1536x2730_puddlemask.png'
J_, S_, R_ = load_mask(mask_path)
pud = load_puddles(pud_path)
joints = {}
Zd2 = (cv2.dilate(Z.astype(np.uint8), k(9)) > 0).astype(np.float32)
for pic in ('Pn', 'F', 'B', 'OB'):
    joints[pic] = {'whole_road': grid_visibility(L[pic], (J_, S_, R_), pud)}
    joints[pic]['only_where_the_props_stood'] = grid_visibility(L[pic], (J_, S_, R_ * Zd2), pud)
    joints[pic]['only_the_common_road_(C)'] = grid_visibility(L[pic], (J_, S_, R_ * C.astype(np.float32)), pud)
out['5_joints_on_the_road_(line = how_much_dots_next_to_a_joint_differ_from_the_stone_beside_them)'] = joints

# ---- 6. sky and 7. whole picture
skm = (sky_cov > 0.999) & (cv2.erode((sky_cov > 0.999).astype(np.uint8), k(9)) > 0)
out['6_sky_(B_against_F_inside_the_sky_mask)'] = {'mean_brightness_F': float(L['F'][skm].mean()), 'mean_brightness_B': float(L['B'][skm].mean()),
                                                  'mean_absolute_difference_each_colour_0_255': float(np.abs(imgs['F'].astype(float) - imgs['B'])[skm].mean()),
                                                  'max_absolute_difference_0_255': float(np.abs(imgs['F'].astype(float) - imgs['B'])[skm].max()),
                                                  'share_of_sky_over_0.5_brightness_B': float((L['B'][skm] > 0.5).mean())}
low = np.zeros((H, W), bool); low[int(H * 2 / 3):] = True
glare = {}
for pic in ('F', 'B', 'Pn', 'OB'):
    glare[pic] = {'share_of_lower_third_over_0.95': float((L[pic][low] > 0.95).mean()), 'share_of_lower_third_over_0.85': float((L[pic][low] > 0.85).mean()),
                  'brightest_1_in_1000_of_road': float(np.percentile(L[pic][road], 99.9)), 'mean_of_road': float(L[pic][road].mean())}
lamp = {}
for pic in ('F', 'B', 'Pn'):
    m = Pm['lamp left']; yy = np.nonzero(m)[0]
    top = yy.min() + 0.3 * (yy.max() - yy.min())
    sel = m & (np.arange(H)[:, None] <= top)
    l = L[pic][sel]; px = imgs[pic][sel][l >= np.percentile(l, 90)][:, ::-1].astype(float)
    lamp[pic] = [round(float(v)) for v in px.mean(axis=0)]
out['7_whole_picture'] = {'not_sky_mean_brightness': {p: float(L[p][~sky].mean()) for p in ('F', 'B', 'Pn', 'Pf', 'OP', 'OB')}, 'glare_pool_and_road_brightness': glare,
                          'lamp_left_glass_RGB_(brightest_tenth_of_the_head)': lamp}

json.dump(out, open(P('numbers/%s_measurements.json' % tag), 'w'), indent=1)
print(json.dumps(out, indent=1))

# What this does (plain words): measures the GROUND of the mud picture (the brown earth, with the puddles and stones painted over) so a sampler can invent new ground of the
# same kind. It (1) keeps only the long, fairly straight rut curves found by find_ruts.py, (2) measures what a rut looks like from the side (how dark and how wide the
# groove is, how bright the banks are on the lit and the shaded side), (3) measures which earth colour is found how far from the nearest rut and on which side
# (a table of chances), and (4) measures the size, shape and direction of the flat ground patches. Saves analysis/ground_model_<name>.json and
# analysis/ruts_main_<name>.json. Analysis only (reads the reference).
import json, os, pickle, sys, math
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import trace_tools as tt
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
name = sys.argv[1] if len(sys.argv) > 1 else 'mud'
ground = cv2.imread(os.path.join(HERE, 'ground_trace_' + name, 'ground_inpainted.png'))
h, w = ground.shape[:2]
el = pickle.load(open(os.path.join(HERE, f'elements_{name}.pkl'), 'rb'))
palette_bgr = np.array(el['palette_bgr'], np.uint8); kinds = el['kinds']
sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
import describe_tools as dt, mud_layers as ml
_level = dict(puddle_eps=1.4, puddle_tones=True, tone_eps=2.5, tone_min_area=30, stone_min_area=0, stone_eps=1.4, max_stones=10**9, max_faces=6, face_eps=1.8, face_min_area=12)
_d = dt.make_description(el, _level); _d['palette'] = [[255, 255, 255]] * len(_d['palette'])
element_mask = cv2.dilate((ml.draw_preview(_d, shapes=ml.make_shape_list(_d)[1:])[..., 0] > 128).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0   # where puddles/stones are (and a margin)
earth_ids = [i for i, k in enumerate(kinds) if k == 'earth']
curves = pickle.load(open(os.path.join(HERE, sys.argv[2] if len(sys.argv) > 2 else f'ruts_{name}.pkl'), 'rb'))
MIN_LEN = float(sys.argv[3]) if len(sys.argv) > 3 else 110
MIN_STRAIGHT = float(sys.argv[4]) if len(sys.argv) > 4 else 0.55
# ------------------------------------------------------------------ 1. keep the real ruts
def straightness(p):
    seg = np.linalg.norm(np.diff(p, axis=0), axis=1).sum()
    return float(np.linalg.norm(p[-1] - p[0]) / max(seg, 1e-6))
main = [c for c in curves if c['length'] >= MIN_LEN and straightness(c['pts']) >= MIN_STRAIGHT]
print('curves', len(curves), '-> main ruts', len(main), 'total length', int(sum(c['length'] for c in main)))
vis = (ground * 0.6).astype(np.uint8)
for c in main:
    for ox in (-w, 0, w):
        for oy in (-h, 0, h):
            cv2.polylines(vis, [(c['pts'] + [ox, oy]).round().astype(np.int32)], False, (0, 255, 255), 2)
cv2.imwrite('/tmp/mudscratch/ruts_main.png', vis)
# ------------------------------------------------------------------ 2. rut profile from the side (light comes from the upper left)
lab = cv2.cvtColor(ground.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)[..., 0]
light = np.array([-0.7071, -0.7071])
offsets = np.arange(-40, 41)
profile_sum = np.zeros(len(offsets)); profile_n = 0
profile_all = []
for c in main:
    p = c['pts']
    dense = []
    for i in range(len(p) - 1):
        n = max(int(np.linalg.norm(p[i + 1] - p[i]) / 3), 1)
        for t in np.linspace(0, 1, n, endpoint=False):
            dense.append(p[i] + t * (p[i + 1] - p[i]))
    dense = np.array(dense)
    if len(dense) < 5:
        continue
    tang = np.gradient(dense, axis=0); tang /= np.maximum(np.linalg.norm(tang, axis=1, keepdims=True), 1e-9)
    normal = np.stack([-tang[:, 1], tang[:, 0]], axis=1)
    flip = (normal @ light) < 0
    normal[flip] *= -1                                   # normal points to the lit side
    for q, nrm in zip(dense, normal):
        xs = np.mod(np.round(q[0] + nrm[0] * offsets).astype(int), w); ys = np.mod(np.round(q[1] + nrm[1] * offsets).astype(int), h)
        profile_all.append(lab[ys, xs])
profile_all = np.array(profile_all)
prof = np.median(profile_all, axis=0)
print('rut profile (Lab lightness, offset -20 shaded side ... +20 lit side):', np.round(prof, 0).astype(int).tolist())
groove_centre = int(offsets[np.argmin(prof)])
base_level = float(np.median(np.concatenate([prof[:4], prof[-4:]])))
half = (base_level + prof.min()) / 2
inside = np.nonzero(prof < half)[0]
groove_width = float(len(inside))
lit_bank = float(prof[offsets > 0].max()); shaded_bank = float(prof[offsets < 0].max())
# ------------------------------------------------------------------ 3. colour chances by distance to the nearest rut and side
mask = np.zeros((h, w), np.uint8)
side_mask = np.zeros((h, w), np.int8)
for c in main:
    for ox in (-w, 0, w):
        for oy in (-h, 0, h):
            cv2.polylines(mask, [(c['pts'] + [ox, oy]).round().astype(np.int32)], False, 1, 1)
dist, lbl = cv2.distanceTransformWithLabels(1 - mask, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
ys0, xs0 = np.nonzero(mask)
table_pos = np.zeros(int(lbl.max()) + 1, np.int64)
table_pos[lbl[ys0, xs0]] = np.arange(len(ys0))
yy, xx = np.mgrid[0:h, 0:w]
near = table_pos[lbl]
dx, dy = xx - xs0[near], yy - ys0[near]
side = ((dx * light[0] + dy * light[1]) > 0).astype(np.int8)          # 1 = on the lit side
labels = tt.assign_labels(ground, tt.srgb_to_lab_float(palette_bgr.reshape(1, -1, 3))[0])
bins = [0, 2, 4, 6, 9, 13, 18, 25, 40, 70, 1e9]
table = np.zeros((2, len(bins) - 1, len(earth_ids)))
for s in (0, 1):
    for b in range(len(bins) - 1):
        m = (side == s) & (dist >= bins[b]) & (dist < bins[b + 1]) & ~element_mask
        counts = np.bincount(labels[m], minlength=len(kinds))[earth_ids].astype(float)
        table[s, b] = counts / max(counts.sum(), 1)
# ------------------------------------------------------------------ 4. flat ground patches: size, shape, direction
smooth = cv2.medianBlur(labels.astype(np.uint8), 3)
areas, aspects, angles_rel = [], [], []
tang_field = np.zeros((h, w, 2), np.float32)
for c in main:
    p = c['pts']
    for i in range(len(p) - 1):
        t = p[i + 1] - p[i]; t = t / max(np.linalg.norm(t), 1e-9)
        cv2.line(tang_field, tuple(np.round(p[i]).astype(int) % [w, h]), tuple(np.round(p[i + 1]).astype(int) % [w, h]), (float(t[0]), float(t[1])), 3)
for k in earth_ids:
    n, comp, stats, cent = cv2.connectedComponentsWithStats((smooth == k).astype(np.uint8), connectivity=4)
    for i in range(1, n):
        a = stats[i, cv2.CC_STAT_AREA]
        if a < 12 or a > 20000:
            continue
        ys_i, xs_i = np.nonzero(comp[stats[i, 1]:stats[i, 1] + stats[i, 3], stats[i, 0]:stats[i, 0] + stats[i, 2]] == i)
        pts = np.stack([xs_i, ys_i], 1).astype(np.float64)
        cov = np.cov(pts.T) if len(pts) > 3 else np.eye(2)
        ev, evec = np.linalg.eigh(cov)
        aspect = math.sqrt(max(ev[1], 1e-6) / max(ev[0], 1e-6))
        areas.append(a); aspects.append(aspect)
        major = evec[:, 1]
        cx, cy = int(cent[i][0]) % w, int(cent[i][1]) % h
        if element_mask[cy, cx]:
            continue
        if dist[cy, cx] < 40:
            idx = near[cy, cx]
            tv = tang_field[ys0[idx], xs0[idx]]
            if np.linalg.norm(tv) > 0:
                angles_rel.append(abs(float(major @ (tv / np.linalg.norm(tv)))))
areas = np.array(areas); aspects = np.array(aspects)
model = {
    'main_rut_count': len(main), 'main_rut_total_length': float(sum(c['length'] for c in main)),
    'rut_profile_offsets': offsets.tolist(), 'rut_profile_lightness': np.round(prof, 1).tolist(),
    'groove_centre_offset': groove_centre, 'groove_width': groove_width, 'groove_lightness': float(prof.min()), 'ground_lightness': base_level,
    'lit_bank_lightness': lit_bank, 'shaded_bank_lightness': shaded_bank,
    'distance_bins': bins[:-1] + [None], 'earth_palette_ids': earth_ids, 'tone_chance_by_side_and_distance': np.round(table, 4).tolist(),
    'patch_area_log_mean': float(np.log(areas).mean()), 'patch_area_log_sd': float(np.log(areas).std()), 'patch_count': int(len(areas)),
    'patch_aspect_median': float(np.median(aspects)), 'patch_aspect_p25_p75': [float(np.percentile(aspects, 25)), float(np.percentile(aspects, 75))],
    'patch_along_rut_cosine_mean': float(np.mean(angles_rel)) if angles_rel else None,
    'ground_share_by_tone': np.round([float(((labels == k) & ~element_mask).sum() / (~element_mask).sum()) for k in earth_ids], 4).tolist(),
    'element_share': float(element_mask.mean()),
}
json.dump(model, open(os.path.join(HERE, f'ground_model_{name}.json'), 'w'), indent=1)
json.dump([{'pts': np.round(c['pts']).astype(int).tolist(), 'length': round(c['length'], 1)} for c in main], open(os.path.join(HERE, f'ruts_main_{name}.json'), 'w'))
print(json.dumps({k: v for k, v in model.items() if k not in ('tone_chance_by_side_and_distance', 'rut_profile_offsets', 'rut_profile_lightness', 'distance_bins')}, indent=1))

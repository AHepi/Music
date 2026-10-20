# What this does (plain words): measures, on the things found in the mud picture (puddles, stones, ruts), the NUMBERS the sampler needs to invent new mud of the same kind:
# how many puddles and how big and ragged; how many stones, their size spread, their colours and flat faces, how clustered they are; how long the ruts are, which way they run
# and how fast they bend. Everything is a summary number or a short table (never a picture). Writes analysis/sampler_stats_<name>.json. Analysis only.
# Use: python3 -I fit_sampler_stats.py [mud|mud_golden] [ruts pickle name]
import json, math, os, pickle, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
name = sys.argv[1] if len(sys.argv) > 1 else 'mud'
el = pickle.load(open(os.path.join(HERE, f'elements_{name}.pkl'), 'rb'))
kinds = el['kinds']; palette_bgr = np.array(el['palette_bgr'], np.uint8)
TILE = 1254
lab = cv2.cvtColor(palette_bgr.reshape(1, -1, 3).astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)[0]
lightness = lab[:, 0]
stats = {'tile': TILE, 'palette_rgb': [[int(c[2]), int(c[1]), int(c[0])] for c in palette_bgr], 'palette_kinds': kinds, 'palette_lightness': np.round(lightness, 1).tolist()}
# ------------------------------------------------------------------ puddles
P = sorted(el['puddles'], key=lambda p: -p['area'])
big = [p for p in P if p['area'] >= 1500]
perim = []
for p in big:
    pts = np.asarray(p['p'], np.float32)
    perim.append(float(cv2.arcLength(pts.reshape(-1, 1, 2), True)))
areas = np.array([p['area'] for p in big])
water_ids = [i for i, k in enumerate(kinds) if k == 'water']
tone_share = {}
for p in big:
    tot = sum(t['a'] for t in p['tones']) or 1
    for t in p['tones']:
        tone_share[t['c']] = tone_share.get(t['c'], 0) + t['a'] / tot / len(big)
stats['puddles'] = {'count_per_tile': len(big), 'area_log_mean': float(np.log(areas).mean()), 'area_log_sd': float(np.log(areas).std()), 'area_min': float(areas.min()), 'area_max': float(areas.max()),
                    'raggedness_perimeter_over_sqrt_area': float(np.mean([pe / math.sqrt(a) for pe, a in zip(perim, areas)])), 'water_tone_ids': water_ids,
                    'tone_share': {int(k): round(v, 3) for k, v in tone_share.items()}, 'tone_patch_count_mean': float(np.mean([len(p['tones']) for p in big])),
                    'tone_patch_area_log_mean': float(np.log([t['a'] for p in big for t in p['tones']]).mean()), 'tone_patch_area_log_sd': float(np.log([t['a'] for p in big for t in p['tones']]).std())}
# ------------------------------------------------------------------ stones
S = el['stones']
sa = np.array([s['area'] for s in S], float)
cent = np.array([s['centre'] for s in S], float) % TILE
bases = np.array([s['base'] for s in S])
stone_ids = [i for i, k in enumerate(kinds) if k == 'stone']
tone_by_size = {}
for lo, hi in ((0, 30), (30, 150), (150, 600), (600, 1e9)):
    m = (sa >= lo) & (sa < hi)
    counts = np.bincount(bases[m], minlength=len(kinds)).astype(float)
    tone_by_size[f'{lo}-{int(hi) if hi < 1e8 else 99999}'] = {'count': int(m.sum()), 'base_tone_share': np.round(counts / max(counts.sum(), 1), 3).tolist()}
face_counts = np.array([len(s['faces']) for s in S if s['area'] >= 60])
trans = np.zeros((len(kinds), len(kinds)))
rel_area = []
for s in S:
    if s['area'] < 60:
        continue
    for k, p, a in s['faces']:
        trans[s['base'], k] += 1
        rel_area.append(a / s['area'])
trans = trans / np.maximum(trans.sum(1, keepdims=True), 1)
# nearest-neighbour distances (wrapping) of stones with area >= 30: clustering
big_idx = np.nonzero(sa >= 30)[0]
c = cent[big_idx]
d = c[:, None, :] - c[None, :, :]
d -= TILE * np.round(d / TILE)
dd = np.sqrt((d ** 2).sum(-1)); np.fill_diagonal(dd, 1e9)
nn = dd.min(1)
rng = np.random.default_rng(0)
u = rng.uniform(0, TILE, (len(c), 2))
du = u[:, None, :] - u[None, :, :]; du -= TILE * np.round(du / TILE)
ddu = np.sqrt((du ** 2).sum(-1)); np.fill_diagonal(ddu, 1e9)
stats['stones'] = {'count_per_tile': int(len(S)), 'count_area_ge_30': int(len(big_idx)), 'area_quantiles': {str(q): float(np.percentile(sa, q)) for q in (5, 25, 50, 75, 90, 99, 100)},
                   'area_log_mean': float(np.log(sa).mean()), 'area_log_sd': float(np.log(sa).std()), 'area_sorted_every_5th': [int(v) for v in np.sort(sa)[::-1][::5]],
                   'tone_by_size': tone_by_size, 'faces_per_stone_mean': float(face_counts.mean()), 'face_relative_area_median': float(np.median(rel_area)),
                   'face_tone_transition_from_base': np.round(trans, 3).tolist(), 'nearest_neighbour_median': float(np.median(nn)), 'nearest_neighbour_median_if_uniform': float(np.median(ddu.min(1))),
                   'share_of_stones_with_a_neighbour_within_40': float((nn < 40).mean()), 'share_if_uniform': float((ddu.min(1) < 40).mean())}
# ------------------------------------------------------------------ ruts
ruts_file = sys.argv[2] if len(sys.argv) > 2 else f'ruts_main_{name}.json'
ruts = json.load(open(os.path.join(HERE, ruts_file)))
lengths = np.array([r['length'] for r in ruts])
angles, turn = [], []
for r in ruts:
    p = np.asarray(r['pts'], float)
    v = np.diff(p, axis=0)
    ang = np.arctan2(v[:, 1], v[:, 0])
    angles += list((ang % math.pi))
    seg = np.linalg.norm(v, axis=1)
    dang = np.angle(np.exp(1j * (np.diff(ang) * 1.0)))
    if len(dang):
        turn += list(np.abs(dang) / np.maximum(0.5 * (seg[1:] + seg[:-1]), 1.0))
hist, _ = np.histogram(angles, bins=12, range=(0, math.pi))
stats['ruts'] = {'count_per_tile': len(ruts), 'length_log_mean': float(np.log(lengths).mean()), 'length_log_sd': float(np.log(lengths).std()), 'total_length': float(lengths.sum()),
                 'direction_histogram_12_bins_over_180_degrees': (hist / hist.sum()).round(3).tolist(), 'turning_rate_per_dot_mean': float(np.mean(turn)),
                 'band_width': 20.0, 'groove_width': 6.0, 'bank_width': 9.0}
json.dump(stats, open(os.path.join(HERE, f'sampler_stats_{name}.json'), 'w'), indent=1)
print(json.dumps({k: stats[k] for k in ('puddles', 'ruts')}, indent=1)[:2500])
print(json.dumps({k: v for k, v in stats['stones'].items() if k not in ('face_tone_transition_from_base', 'tone_by_size', 'area_sorted_every_5th')}, indent=1))

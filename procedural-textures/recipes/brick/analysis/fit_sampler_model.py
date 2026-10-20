import sys; sys.path.insert(0, "."); sys.path.insert(0, "../generator")
# What this does (plain words): measures the reference's own ELEMENTS so new tiles can be drawn from the same statistics: how big the bricks and
# the joints are, how the course heights vary, how often each brick base colour occurs, and, for patches of paint on bricks (five brick classes from
# dark to pale) and in the mortar: how many per area, how big (two radii, log-normal), how tilted, how ragged and which colours.
# Writes ../generator/sampler_model_brick.json (a few KB of numbers, no positions of anything in the reference). Analysis only.
import json
from region_tools import *
import region_tools
from fit_blobs import make_candidates, K
labels = np.load('labels_k16.npy')
pal = np.load('palette_k16.npy')
base = json.load(open('../generator/descriptions/stage1_bricks_only.json'))
rows = base['layers'][0]['rows']
L1 = mode_filter(labels, K, 3)
L2, _ = remove_small(L1, K, 12)
cands = make_candidates(L2, 30)
W = 1254
luma = pal @ np.array([.299, .587, .114])
# --- layout statistics (skip the seam rows: the very short sliver and the top row next to it)
face_h = [r['y1'] - r['y0'] for r in rows if 60 < r['y1'] - r['y0'] < 100]
row_pitch = [rows[i + 1]['y0'] - rows[i]['y0'] for i in range(1, len(rows) - 2)]
widths, gaps = [], []
for r in rows:
    if r['y1'] - r['y0'] < 60: continue
    b = r['bricks']
    for i in range(len(b)):
        nxt = b[(i + 1) % len(b)]
        widths.append(b[i][1] - b[i][0])
        gaps.append((nxt[0] - b[i][1]) % W)
pitch = [w + g for w, g in zip(widths, gaps)]
base_cols = [br[2] for r in rows if r['y1'] - r['y0'] > 60 for br in r['bricks']]
# brick class by the luma of its base colour: 5 classes
classes_edges = np.quantile([luma[c] for c in base_cols], [0.2, 0.4, 0.6, 0.8])
def brick_class(c):
    return int(np.searchsorted(classes_edges, luma[c]))
class_of_colour = [brick_class(c) for c in range(K)]
# --- container of every candidate patch
brick_index = np.full((W, W), -1, np.int32)
brick_cls = []
n = 0
for r in rows:
    for (x0, x1, c) in r['bricks']:
        for dx in (-W, 0, W):
            cv2.rectangle(brick_index, (x0 + dx, r['y0']), (x1 + dx, r['y1']), n, -1)
        brick_cls.append(class_of_colour[c])
        n += 1
brick_cls = np.array(brick_cls)
brick_area = np.zeros(5)
for i, cl in enumerate(brick_cls):
    brick_area[cl] += (brick_index == i).sum()
mortar_area = float((brick_index < 0).sum())
groups = {k: [] for k in range(6)}       # 0..4 brick classes, 5 mortar
for c in cands:
    cx, cy = int(min(max(c['cx'], 0), W - 1)), int(min(max(c['cy'], 0), W - 1))
    bi = brick_index[cy, cx]
    g = 5 if bi < 0 else int(brick_cls[bi])
    groups[g].append(c)
model = {'tile': W, 'palette': base['palette'], 'maps': base['maps'], 'backdrop': base['backdrop'],
         'layout': {'face_height': [float(np.mean(face_h)), float(np.std(face_h))], 'row_pitch_mean': float(np.mean(row_pitch)),
                    'brick_pitch': [float(np.mean(pitch)), float(np.std(pitch))], 'joint_gap': [float(np.mean(gaps)), float(np.std(gaps))],
                    'vertical_gap': float(np.mean(row_pitch) - np.mean(face_h)), 'corner_radius': 9.0},
         'brick_base_colour': {'class_of_colour': class_of_colour,
                               'frequency': [float(base_cols.count(c)) / len(base_cols) for c in range(K)]},
         'patch_groups': {}}
BIN_EDGES = [20, 40, 80, 160, 320, 640, 1300, 2600, 5200, 12000]
def coarse_of(area):
    return 0 if area < 160 else (1 if area < 1300 else 2)
def bin_stats(items, area_total):
    out = []
    for lo, hi in zip(BIN_EDGES[:-1], BIN_EDGES[1:]):
        sel = [c for c in items if lo <= c['area'] < hi]
        if not sel:
            out.append({'area_range': [lo, hi], 'count_per_10000_dots': 0.0})
            continue
        asp = np.array([np.log(max(c['rx'], 0.8) / max(c['ry'], 0.8)) for c in sel])
        ang = np.array([c['angle'] for c in sel])
        out.append({'area_range': [lo, hi], 'count_per_10000_dots': round(len(sel) / area_total * 10000.0, 4),
                    'log_aspect_mean_sd': [round(float(asp.mean()), 3), round(float(asp.std()), 3)],
                    'horizontal_share': round(float(np.mean(np.abs(((ang + 90) % 180) - 90) < 30)), 3),
                    'ragged_mean_sd': [round(float(np.mean([c['ragged'] for c in sel])), 3), round(float(np.std([c['ragged'] for c in sel])), 3)]})
    return out
brick_items = [c for g in range(5) for c in groups[g]]
model['brick_patches'] = {'bins': bin_stats(brick_items, brick_area.sum())}
# colours of patches, by brick class and by coarse size (small / medium / large), area-independent counts; fall back to all bricks when a cell is thin
model['brick_patches']['colour_probability'] = {}
allcols = np.array([c['label'] for c in brick_items]); allco = np.array([coarse_of(c['area']) for c in brick_items])
for g in range(5):
    for co in range(3):
        sel = [c for c in groups[g] if coarse_of(c['area']) == co]
        pool = sel if len(sel) >= 25 else [c for c in brick_items if coarse_of(c['area']) == co]
        lab = np.array([c['label'] for c in pool])
        model['brick_patches']['colour_probability'][f'{g}_{co}'] = [round(float((lab == k).sum()) / len(lab), 4) for k in range(K)]
# area-weighted colour shares (what a mosaic of cells needs: how much AREA each colour covers), per brick class and for the mortar
for g in range(5):
    pool = groups[g] if len(groups[g]) >= 40 else brick_items
    w = np.array([c['area'] for c in pool], float); lab = np.array([c['label'] for c in pool])
    model['brick_patches']['colour_probability'][f'{g}_area'] = [round(float(w[lab == k].sum() / w.sum()), 4) for k in range(K)]
model['mortar_patches'] = {'bins': bin_stats(groups[5], mortar_area), 'colour_probability': {}}
for co in range(3):
    pool = [c for c in groups[5] if coarse_of(c['area']) == co] or groups[5]
    lab = np.array([c['label'] for c in pool])
    model['mortar_patches']['colour_probability'][str(co)] = [round(float((lab == k).sum()) / len(lab), 4) for k in range(K)]
w = np.array([c['area'] for c in groups[5]], float); lab = np.array([c['label'] for c in groups[5]])
model['mortar_patches']['colour_probability']['area'] = [round(float(w[lab == k].sum() / w.sum()), 4) for k in range(K)]
model.pop('patch_groups')
json.dump(model, open('../generator/sampler_model_brick.json', 'w'), separators=(',', ':'))
print(len(json.dumps(model, separators=(',', ':'))), 'bytes')
for b in model['brick_patches']['bins']:
    print(b)

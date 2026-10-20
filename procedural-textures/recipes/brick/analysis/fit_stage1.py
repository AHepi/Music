import sys; sys.path.insert(0, ".")
# What this does (plain words): first fitting step: palette (16 colours), brick layout with one base colour per brick, the derivation rule.
# Writes ../generator/descriptions/stage1_bricks_only.json. Analysis only (reads the reference).
import json
from region_tools import *
W = 1254
bgr = load_reference()
K = 16
labels, centres = kmeans_labels(bgr, K, 'bilateral')
pal_bgr = cv2.cvtColor(centres.reshape(1, K, 3).astype(np.uint8), cv2.COLOR_LAB2BGR).reshape(K, 3)
pal_rgb = pal_bgr[:, ::-1]
# order the palette by brightness for readability
order = np.argsort(pal_rgb @ np.array([.299, .587, .114]))
remap = np.zeros(K, int); remap[order] = np.arange(K)
labels = remap[labels].astype(np.uint8)
pal_rgb = pal_rgb[order]
layout = json.load(open('layout_clean.json'))
rows = []
for r in layout['rows'][:-1]:
    rows.append(r)
# last found row was the wrap row 1224..1339 which is really two rows: the sliver at the bottom and the top row
sliver = {'top': 1224, 'bottom': 1254, 'bricks': [[104, 328], [349, 731], [750, 944], [965, 83 + W]]}
toprow = {'top': 0, 'bottom': 85, 'bricks': [[240, 469], [488, 657], [676, 946], [965, 221 + W]]}
rows = [toprow] + rows + [sliver]
big = np.tile(labels, (3, 3))
dark = int(np.argmin(pal_rgb.sum(1)))
mortar_mask = np.ones((W, W), bool)
out_rows = []
for r in rows:
    y0, y1 = r['top'], r['bottom']
    items = []
    for (x0, x1) in r['bricks']:
        patch = big[W + y0 + 6: W + y1 - 6, W + x0 + 8: W + x1 - 8]
        colour = int(np.bincount(patch.ravel(), minlength=K).argmax())
        items.append([int(x0), int(x1), colour])
    out_rows.append({'y0': int(y0), 'y1': int(y1), 'bricks': items})
# backdrop = the commonest label in the mortar band (middle of the joint between two courses)
mort = []
for a, b in zip(rows[:-1], rows[1:]):
    ym = (a['bottom'] + b['top']) // 2
    mort.append(labels[ym - 3: ym + 3].ravel())
backdrop = int(np.bincount(np.concatenate(mort), minlength=K).argmax())
chroma = pal_rgb.max(1) - pal_rgb.min(1)
roughness = (0.92 - 0.27 * np.clip(chroma / 110.0, 0, 1)).round(2)
d = json.load(open('derivation_ceiling.json'))
desc = {
    'format': 'painted-tile-1', 'surface': 'brick', 'tile': W, 'seed': 11,
    'palette': [[int(c) for c in rgb] + [float(rg)] for rgb, rg in zip(pal_rgb, roughness)],
    'maps': {'blur_sigma': 0.7, 'curve_x': d['tone_curve_and_blur']['curve_x'], 'curve_y': d['tone_curve_and_blur']['curve_y'], 'normal_strength': 6.0},
    'backdrop': backdrop,
    'layers': [{'type': 'bricks', 'corner_radius': 9.0, 'outline_width': 2.0, 'outline_colour': dark, 'ragged': 0.0, 'rows': out_rows}],
}
import os
os.makedirs('../generator/descriptions', exist_ok=True)
json.dump(desc, open('../generator/descriptions/stage1_bricks_only.json', 'w'), separators=(',', ':'))
np.save('labels_k16.npy', labels)
np.save('palette_k16.npy', pal_rgb)
print('palette', pal_rgb.tolist()); print('backdrop', backdrop, 'dark', dark)
print(len(json.dumps(desc, separators=(',', ':'))), 'bytes')

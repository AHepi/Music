# What this does (plain python, not inside Blender): measures the real line width (pixels) of the outline masks made by c05_outlines_in_shader.py,
# adds it to the timing numbers, and builds a picture sheet: rows = method, columns = requested width.
import os, sys, json, glob
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
res = json.load(open(os.path.join(BASE, 'data', 'c05_outline_methods.json')))
def width_of(mask_png):
    img = (cv2.imread(mask_png, cv2.IMREAD_GRAYSCALE) > 127).astype(np.uint8)
    dist = cv2.distanceTransform(img, cv2.DIST_L2, 5)
    local = cv2.dilate(dist, np.ones((3, 3), np.uint8))
    ridge = (dist >= local - 1e-6) & (dist >= 0.9)
    ridge_count = int(ridge.sum())
    return (float(img.sum() / ridge_count) if ridge_count else 0.0), float(img.mean())   # width = area / length of the centre line
for label, r in res.items():
    if '_none_' in label: continue
    r['median_line_width_px'], r['mask_share'] = width_of(os.path.join(BASE, 'pictures', 'c05_outline_' + label, 'mask.png'))
json.dump(res, open(os.path.join(BASE, 'data', 'c05_outline_methods.json'), 'w'), indent=1)
for k, v in res.items(): print(k, v)
# sheet
rows = []
for kind in ('cells', 'levels'):
    for method in ('edge_distance', 'offset2', 'offset4', 'bump'):
        if kind == 'levels' and method == 'edge_distance': continue
        tiles = []
        for width in (1, 2, 4, 8):
            im = cv2.imread(os.path.join(BASE, 'pictures', f'c05_outline_{kind}_{method}_{width}', 'colour.png'))
            im = cv2.resize(im, (300, 300), interpolation=cv2.INTER_AREA)
            r = res[f'{kind}_{method}_{width}']
            cv2.putText(im, f'{kind} {method} w={width}px  measured {r["median_line_width_px"]:.1f}', (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.putText(im, f'{kind} {method} w={width}px  measured {r["median_line_width_px"]:.1f}', (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1, cv2.LINE_AA)
            tiles.append(im)
        rows.append(np.hstack(tiles))
cv2.imwrite(os.path.join(BASE, 'pictures', 'c05_outline_methods_sheet.png'), np.vstack(rows))

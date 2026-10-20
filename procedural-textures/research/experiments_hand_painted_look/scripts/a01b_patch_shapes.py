# What this does: measures how STRETCHED the paint patches of each reference are (tall drips on slate and metal, long flat strips on wood)
# and which way they point. For each flat patch (a connected area of one palette colour, 12 colours from k-means in Lab) it works out the
# spread of the patch along x and along y (from the patch's own shape) and reports the area-weighted median of height/width.
# A value above 1 means taller than wide (vertical streaks); below 1 means wider than tall (horizontal streaks); about 1 = round blobs.
# Use: python3 -I a01b_patch_shapes.py   -> writes ../data/reference_patch_shapes.json
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a01_measure_references as m  # noqa: E402


def shapes_for(name):
    rgb = m.load_rgb_u8(os.path.join(m.REF, name, 'colour.png'))
    lab = m.to_lab(rgb)
    k = 12
    centres = m.kmeans_lab(lab, k)
    labels, _ = m.nearest_labels(lab, centres)
    labels = m.mode_filter(labels, k, 5)
    aspects, areas, widths, heights = [], [], [], []
    for index in range(k):
        mask = (labels == index).astype(np.uint8)
        count, comp, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
        for i in range(1, count):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < 150 or area > 60000:
                continue
            x, y, w, h = stats[i, 0], stats[i, 1], stats[i, 2], stats[i, 3]
            crop = (comp[y:y + h, x:x + w] == i)
            ys, xs = np.nonzero(crop)
            sx, sy = xs.std() + 0.5, ys.std() + 0.5
            aspects.append(sy / sx)
            areas.append(area)
            widths.append(sx * 4)
            heights.append(sy * 4)
    aspects, areas = np.array(aspects), np.array(areas, float)
    order = np.argsort(aspects)
    cumulative = np.cumsum(areas[order]) / areas.sum()
    pick = lambda q: float(aspects[order][np.searchsorted(cumulative, q)])
    return {'patches_used': int(len(aspects)), 'height_over_width_area_weighted_p25_p50_p75': [pick(0.25), pick(0.5), pick(0.75)],
            'share_of_area_in_patches_taller_than_1.5x_width': float(areas[aspects > 1.5].sum() / areas.sum()),
            'share_of_area_in_patches_wider_than_1.5x_height': float(areas[aspects < 1 / 1.5].sum() / areas.sum()),
            'typical_patch_width_px_area_weighted_median': float(np.median(np.array(widths)[order][np.searchsorted(cumulative, 0.5):][:1])),
            }


if __name__ == '__main__':
    out = {}
    for name in ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel']:
        out[name] = shapes_for(name)
        print(name, out[name])
    with open(os.path.join(m.DATA, 'reference_patch_shapes.json'), 'w') as handle:
        json.dump(out, handle, indent=1)

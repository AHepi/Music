# What this does: for each reference, measures how far you can walk along a row (x) or down a column (y) before the painted colour label
# changes (run length of one palette colour, 12 colours from k-means in Lab, then a small majority filter). Long runs along y and short along x = vertical
# streaks (drips); the reverse = horizontal streaks (wood grain). Pixel-weighted mean run length, in pixels, plus the x/y ratio.
# Use: python3 -I a01c_run_lengths.py  -> writes ../data/reference_run_lengths.json
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a01_measure_references as m


def run_lengths_axis(labels, axis):
    arr = labels if axis == 1 else labels.T
    lengths = []
    for row in arr:
        change = np.flatnonzero(np.diff(row) != 0)
        edges = np.r_[-1, change, len(row) - 1]
        lengths.append(np.diff(edges))
    lengths = np.concatenate(lengths).astype(float)
    # pixel-weighted mean: sum(l^2)/sum(l)
    return float((lengths ** 2).sum() / lengths.sum()), float(np.median(lengths))


out = {}
for name in ['brick', 'slate', 'wood', 'metal', 'mud', 'gravel']:
    rgb = m.load_rgb_u8(os.path.join(m.REF, name, 'colour.png'))
    lab = m.to_lab(rgb)
    centres = m.kmeans_lab(lab, 12)
    labels, _ = m.nearest_labels(lab, centres)
    labels = m.mode_filter(labels, 12, 5)
    # also only the interior of the tiles: ignore the darkest label (outlines)
    darkest = int(np.argmin(centres[:, 0]))
    rx, mx = run_lengths_axis(labels, 1)
    ry, my = run_lengths_axis(labels, 0)
    out[name] = {'mean_run_x_px': rx, 'mean_run_y_px': ry, 'ratio_y_over_x': ry / rx, 'median_run_x_px': mx, 'median_run_y_px': my}
    print(name, {k: round(v, 2) for k, v in out[name].items()})
json.dump(out, open(os.path.join(m.DATA, 'reference_run_lengths.json'), 'w'), indent=1)

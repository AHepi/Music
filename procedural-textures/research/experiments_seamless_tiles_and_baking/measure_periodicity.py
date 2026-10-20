# What this does: the EXACT tiling test. exp1_pattern_seams.py (run with the word 'shift') renders every pattern four extra times with its
# coordinates moved by one whole tile (+1 in x, +1 in y, +1 in both, and by -3 in x and +2 in y). A pattern that really tiles must give the
# same picture every time. This script compares those pictures with the unmoved one and prints the biggest and the average difference
# (picture values run 0 to 1). Unlike the seam ratio it cannot be fooled by hard edges (checker squares, saw-tooth, brick outlines).
# Run (plain Python):  python3 -I measure_periodicity.py out/patterns_shift out/patterns_seams.json out/pattern_table.json
import json
import os
import sys

import cv2
import numpy as np


def load(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image.ndim == 3:
        image = image[..., :3].mean(axis=-1)
    image = image.astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0)


def main():
    folder, seam_json, out_json = sys.argv[1], sys.argv[2], sys.argv[3]
    seams = json.load(open(seam_json))
    names = sorted({f.split('__')[0] for f in os.listdir(folder) if f.endswith('__base.png')})
    table = {}
    for name in names:
        base = load(os.path.join(folder, f'{name}__base.png'))
        worst_max, worst_mean = 0.0, 0.0
        for label in ('plus_x', 'plus_y', 'plus_xy', 'minus_xy_3_2'):
            other = load(os.path.join(folder, f'{name}__{label}.png'))
            difference = np.abs(base - other)
            worst_max = max(worst_max, float(difference.max()))
            worst_mean = max(worst_mean, float(difference.mean()))
        row = dict(seams.get(name, {}))
        row['shift_max_error'] = round(worst_max, 4)
        row['shift_mean_error'] = round(worst_mean, 5)
        row['tiles_exactly'] = bool(worst_mean < 0.002)
        table[name] = row
    json.dump(table, open(out_json, 'w'), indent=1)
    print(f"{'pattern':40s} {'tiles?':7s} shift_mean shift_max  seam_ratio peak  mirror_tell spread")
    for name, r in table.items():
        print(f"{name:40s} {'YES' if r['tiles_exactly'] else 'no':7s} {r['shift_mean_error']:10} {r['shift_max_error']:9} {r.get('seam_ratio','-'):10} {r.get('seam_peak','-'):5} {r.get('mirror_tell','-'):6} {r.get('spread','-')}")


main()

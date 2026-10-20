# What this file does (plain words)
# Measures the "dark drawing" of a slate picture in a few plain numbers, so the recipe can be compared with the reference as a GUIDE (nothing
# is traced or fitted; these are the same measurements for both pictures):
#   * how long the black core under a row is (in dots, up and down), median of many columns;
#   * how bright the picture is just above and just below that black core (distance 1, 2, 4 ... dots) = the lip and the shadow band;
#   * how wide the dark vertical joints between slates are;
#   * how bright the slate is at 1-2, 2-4, 4-6 ... dots away from the nearest dark dot (the "darkening toward edges").
# Pictures of another size are first brought to 1254 dots per tile, so every number is in dots at the reference size.
# Use (plain python):  python3 -I profile_tools.py PICTURE.png DOTS_PER_TILE      (DOTS_PER_TILE = picture dots across ONE tile;
#   for a picture that shows only a window of the tile, e.g. 627 dots across half a tile, give 1254)
import json
import sys

import cv2
import numpy as np


def measure(image_path, dots_per_tile):
    img = cv2.imread(image_path)
    scale = 1254.0 / float(dots_per_tile)
    if abs(scale - 1.0) > 1e-6:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = grey.shape
    result = {}
    # ---- the black core under a row: dark runs (< 22) of 6..22 dots in a column
    above, below, lengths = [], [], []
    for x in range(w):
        col = grey[:, x]
        dark = col < 22
        y = 0
        while y < h:
            if dark[y]:
                y0 = y
                while y < h and dark[y]:
                    y += 1
                length = y - y0
                if 6 <= length <= 22 and y0 >= 30 and y + 45 <= h:
                    lengths.append(length)
                    above.append(col[y0 - 30:y0].copy())
                    below.append(col[y:y + 45].copy())
            else:
                y += 1
    above, below = np.array(above), np.array(below)
    result['columns_with_core'] = int(len(lengths))
    result['core_length_median'] = float(np.median(lengths)) if lengths else None
    if lengths:
        result['above_core'] = {d: round(float(np.median(above[:, -d])), 1) for d in (1, 2, 3, 4, 6, 8, 12, 20, 30)}
        result['below_core'] = {d: round(float(np.median(below[:, d - 1])), 1) for d in (1, 2, 4, 6, 8, 10, 14, 18, 22, 26, 30, 40)}
    result['median_not_dark'] = float(np.median(grey[grey > 30]))
    # ---- vertical joints
    widths = []
    for y in range(8, h - 8):
        row = grey[y, :]
        dark = row < 26
        x = 0
        while x < w:
            if dark[x]:
                x0 = x
                while x < w and dark[x]:
                    x += 1
                L = x - x0
                if 2 <= L <= 12 and x0 > 5 and x < w - 5 and grey[y - 8, x0:x].mean() < 40 and grey[y + 8, x0:x].mean() < 40:
                    widths.append(L)
            else:
                x += 1
    result['vertical_joint_width_median'] = float(np.median(widths)) if widths else None
    result['vertical_joint_width_p10_p90'] = [float(v) for v in np.percentile(widths, [10, 90])] if widths else None
    # ---- darkening toward dark dots
    dark_mask = (grey < 26).astype(np.uint8)
    dist = cv2.distanceTransform(1 - dark_mask, cv2.DIST_L2, 3)
    non_dark = grey > 26
    result['brightness_by_distance_from_dark'] = {}
    for d0, d1 in ((1, 2), (2, 4), (4, 6), (6, 9), (9, 14), (14, 22), (22, 35), (35, 60)):
        sel = non_dark & (dist >= d0) & (dist < d1)
        result['brightness_by_distance_from_dark'][f'{d0}-{d1}'] = round(float(np.median(grey[sel])), 1) if sel.any() else None
    result['share_dark_under_26'] = round(float((grey < 26).mean()), 4)
    return result


def show(result, title):
    print('==', title)
    print('  columns with a black core:', result['columns_with_core'], ' core length median', result['core_length_median'], ' median brightness of not-dark dots', round(result['median_not_dark'], 1))
    print('  above the core (lip):  ', result.get('above_core'))
    print('  below the core (shadow):', result.get('below_core'))
    print('  vertical joint dark width median', result['vertical_joint_width_median'], ' 10-90%', result['vertical_joint_width_p10_p90'])
    print('  brightness by distance from a dark dot:', result['brightness_by_distance_from_dark'])
    print('  share of dots darker than 26:', result['share_dark_under_26'])


if __name__ == '__main__':
    r = measure(sys.argv[1], float(sys.argv[2]))
    show(r, sys.argv[1])

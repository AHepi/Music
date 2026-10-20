# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Prints a few plain numbers about the PAINT inside the slates of a colour picture (joints and the rim next to them are left out), so
# a picture of the COLOUR AND FADE layer can be compared with the reference picture BY HAND while tuning. Nothing here is fed back into
# the recipe: I read the numbers, look at the pictures, and change a setting by hand.
# The numbers:
#   brightness percentiles   how light or dark the paint is (0..255; the dots of the blue-grey paint only: joints dark < 24 left out, and
#                            for the reference also the olive moss and tan lichen, which this layer does not make)
#   top to bottom            mean brightness in ten bands from the top of a slate to its bottom (the fade); rise = last band minus first
#   edge density             share of paint dots where the lightness jumps by more than 8 across two dots (how busy the patch edges are)
#   flat share               share of dots whose 5 x 5 neighbourhood has a lightness spread under 1 / under 2 (how flat the patches are)
#   sideways / upright jumps share of neighbouring pairs that differ by more than 3 steps, sideways and up-down: a ratio above 1 means
#                            the paint has more vertical edges than horizontal ones (streaks that stand upright)
#   long range               standard deviation of the paint brightness after blurring over 60 dots: how much whole areas differ
# Use (plain python): python3 -I paint_stats.py PICTURE.png [PICTURE2.png ...]   (the reference slate is always printed first)
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REFERENCE = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', 'reference', 'slate', 'colour.png'))


def statistics(path, is_reference=False):
    image = cv2.imread(path)
    if image.shape[0] != 1254:
        image = cv2.resize(image, (1254, 1254), interpolation=cv2.INTER_AREA)
    rgb = image[:, :, ::-1].astype(np.float32) / 255.0
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2Lab)
    grey = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]) * 255.0
    paint = (grey > 24)
    if is_reference:
        paint &= lab[..., 2] < 4.0
    inside = cv2.erode(paint.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    out = {}
    out['brightness percentiles 1/10/25/50/75/90/99'] = np.percentile(grey[inside], [1, 10, 25, 50, 75, 90, 99]).round(0).astype(int).tolist()
    out['mean lab (L, a, b)'] = lab[inside].mean(axis=0).round(1).tolist()
    # top to bottom profile
    row_mean = grey.mean(axis=1)
    smooth = np.convolve(np.r_[row_mean[-15:], row_mean, row_mean[:15]], np.ones(9) / 9, mode='same')[15:-15]
    rows, last = [], -999
    for y in range(1, 1253):
        if smooth[y] < smooth[y - 1] and smooth[y] <= smooth[y + 1] and smooth[y] < np.percentile(smooth, 30) and y - last > 100:
            rows.append(y)
            last = y
    profile = []
    for a, b in zip(rows[:-1], rows[1:]):
        seg, msk = grey[a + 12:b - 8], paint[a + 12:b - 8]
        height = seg.shape[0]
        vals = []
        for step in range(10):
            s, e = int(step * height / 10), int((step + 1) * height / 10)
            m = msk[s:e]
            vals.append(float(seg[s:e][m].mean()) if m.any() else np.nan)
        profile.append(vals)
    profile = np.nanmean(np.array(profile), axis=0)
    out['top to bottom (10 bands)'] = profile.round(0).astype(int).tolist()
    out['rise (last band - first)'] = round(float(profile[-1] - profile[0]), 0)
    L = lab[..., 0]
    gx = np.abs(np.roll(L, -1, axis=1) - np.roll(L, 1, axis=1))
    gy = np.abs(np.roll(L, -1, axis=0) - np.roll(L, 1, axis=0))
    out['edge density %'] = round(float(((gx > 8) | (gy > 8))[inside].mean() * 100), 1)
    window = (cv2.dilate(L, np.ones((5, 5), np.uint8)) - cv2.erode(L, np.ones((5, 5), np.uint8)))
    out['flat share % (spread <1 / <2)'] = [round(float((window[inside] < 1).mean() * 100), 0), round(float((window[inside] < 2).mean() * 100), 0)]
    dx = np.abs(np.roll(grey, -1, axis=1) - grey)
    dy = np.abs(np.roll(grey, -1, axis=0) - grey)
    sideways, upright = float((dx[inside] > 3).mean() * 100), float((dy[inside] > 3).mean() * 100)
    out['sideways / upright jumps %'] = [round(sideways, 1), round(upright, 1), round(sideways / max(upright, 1e-6), 2)]
    blur = cv2.blur(np.where(inside, grey, grey[inside].mean()).astype(np.float32), (61, 61))
    out['long range std'] = round(float(blur[inside].std()), 1)
    return out


if __name__ == '__main__':
    names = [('reference', REFERENCE, True)] + [(p, p, False) for p in sys.argv[1:]]
    for label, path, is_ref in names:
        print('==', label if is_ref else os.path.relpath(path))
        for key, value in statistics(path, is_ref).items():
            print(f'   {key:42s} {value}')

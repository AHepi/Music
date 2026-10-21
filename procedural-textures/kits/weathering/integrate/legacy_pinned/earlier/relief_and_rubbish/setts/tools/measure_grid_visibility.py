# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# A SECOND way to measure the joints between the setts, added because the study's measure only counts a joint as "seen" when it is DARKER than the stone beside it. In a blaze of
# light a rounded stone edge that faces the light can be brighter than the stone top (a thin bright line instead of a dark one) and the grid is still plainly visible, but the
# darkness measure calls that a failure. This measure counts the grid whether its lines are dark or bright.
# For every road dot within about 2 dots of a joint (the "joint zone": the joint and the lit or shaded edge of the stones beside it), it takes how much that dot differs from the
# stone beside it, as a share of the stone's brightness, IN EITHER DIRECTION:  difference = |dot - local stone| / local stone. Then, per band of the road (near / middle / far):
#     line      the average of that difference over the joint zone (0 = the grid is not there, 0.3 = the grid lines differ from the stone by 30 %)
#     texture   the same number for the stone's own dots (the stone's grit and mottling, no grid): the noise the grid has to stand out from
#     dark_share / bright_share   how many joint-zone dots are at least 15 % darker / at least 15 % brighter than the stone (so you can tell dark lines from lit edges)
# A grid is "visible" when line is clearly above texture. (Pass line, mine, first try: line >= 0.12 and line >= 2 x texture in the near and middle bands.)
# Same inputs as the study's measure (the picture, the road's joint / stone mask picture, the puddle mask picture; dots under a puddle plus a 2-dot margin are left out).
# Plain Python (numpy, OpenCV); no Blender.
# Use:  python3 -I measure_grid_visibility.py FOLDER     (a folder made by the runner: it reads measurements.json and writes grid_visibility.json there)
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'study', 'tools')))
sys.dont_write_bytecode = True
from b04_measure_joints import load_mask, load_puddles, luminance  # noqa: E402

LINE_MIN, TEXTURE_FACTOR = 0.12, 2.0


def grid_visibility(picture, mask, puddles=None, radius=8, bands=3):
    L = luminance(picture) if isinstance(picture, str) else picture
    J, S, R = load_mask(mask) if isinstance(mask, str) else mask
    road = R > 0.99
    if puddles is not None:
        road = road & ~(load_puddles(puddles) if isinstance(puddles, str) else puddles)
    rows = np.where(road.any(axis=1))[0]
    top, bottom = rows.min(), rows.max()
    edges = np.linspace(top, bottom + 1, bands + 1).astype(int)
    stone = (S > 0.9) & road
    weight = stone.astype(np.float32)
    k = 2 * radius + 1
    num = cv2.GaussianBlur(L * weight, (k, k), radius / 2.0)
    den = cv2.GaussianBlur(weight, (k, k), radius / 2.0)
    local = np.where(den > 0.02, num / np.maximum(den, 1e-6), np.nan)
    zone = (cv2.dilate((J > 0.5).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & road & ~stone & np.isfinite(local)
    stone = stone & np.isfinite(local)
    diff = (L - local) / np.maximum(local, 0.02)
    out = {}
    for name, (r0, r1) in zip(('far', 'middle', 'near'), zip(edges[:-1], edges[1:])):
        band = np.zeros_like(road)
        band[r0:r1] = True
        z, s = zone & band, stone & band
        if z.sum() >= 60 and s.sum() >= 60:
            out[name] = dict(line=round(float(np.abs(diff[z]).mean()), 3), texture=round(float(np.abs(diff[s]).mean()), 3),
                             dark_share=round(float((diff[z] <= -0.15).mean()), 3), bright_share=round(float((diff[z] >= 0.15).mean()), 3), nzone=int(z.sum()))
        else:
            out[name] = dict(line=None, texture=None, dark_share=None, bright_share=None, nzone=int(z.sum()))
    return out


def visible(entry):
    return entry['line'] is not None and entry['line'] >= LINE_MIN and entry['line'] >= TEXTURE_FACTOR * entry['texture']


def folder(path):
    store = json.load(open(os.path.join(path, 'measurements.json')))
    result = {}
    for name, m in store.items():
        job = m['job']
        picture = os.path.join(path, name + '.jpg')
        mask = os.path.join(path, f"mask_{job['camera']}_{job['w']}x{job['h']}.png")
        puddle = os.path.join(path, f"{name.split('_')[0]}_A_{job['state']}_puddlemask.png")
        if not (os.path.exists(picture) and os.path.exists(mask)):
            continue
        result[name] = grid_visibility(picture, mask, puddle if os.path.exists(puddle) else None)
    json.dump(result, open(os.path.join(path, 'grid_visibility.json'), 'w'), indent=1)
    return result


if __name__ == '__main__':
    for name, r in folder(sys.argv[1]).items():
        f = lambda e: 'n/a' if e['line'] is None else f"line {e['line']:.2f} tex {e['texture']:.2f} dark {e['dark_share']:.2f} bright {e['bright_share']:.2f} {'VISIBLE' if visible(e) else 'not seen'}"   # noqa: E731
        print(f"{name:26s} near: {f(r['near'])} | middle: {f(r['middle'])}")

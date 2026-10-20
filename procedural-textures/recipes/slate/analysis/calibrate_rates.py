# What this does (plain words): the stamps are drawn on top of each other, so the share of the slate that stays VISIBLE for each size class is
# smaller than the share the stamps cover when counted one by one. This script draws the stamps with a different number for each size class
# (instead of a colour), measures the visible share per class, compares with the share measured on the reference (the 'coverage' numbers in the
# paint model) and nudges the stamp counts until they agree. The corrected counts are stored in the description as 'rate_scale'.
# Plain Python (python3 -I): uses the same stamp maker as the generator, no Blender.
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SLATE = os.path.abspath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(SLATE, 'generator'))
import slate_layers as sl  # noqa: E402


def visible_share(description, scale_vector, seed=1):
    paint = dict(description['paint'])
    paint['rate_scale'] = list(scale_vector)
    paint['seed'] = seed
    bands = paint['model']['band']
    tile = description['tile']
    # make the shape list but remember which band each stamp came from: expand_paint with a hook
    infos = []
    tones = paint['slates']
    for r, row in enumerate(description['layout']['rows']):
        for i, slate in enumerate(sl.row_slates(row, tile)):
            tone, olive, tan = tones[r][i]
            infos.append({'x0': slate[0], 'x1': slate[1], 'top': row['top'] + slate[4], 'bottom': row['bottom'] + slate[5], 'tone': tone, 'olive': olive, 'tan': tan})
    tagged = sl.expand_paint(paint, infos, description['palette'], tile, tag_band=True)
    canvas = np.zeros((tile, tile), np.uint8)
    slate_mask = np.zeros((tile, tile), np.uint8)
    for points, colour in sl.expand_layout(description['layout'], tile):
        for ox in (-tile, 0, tile):
            for oy in (-tile, 0, tile):
                cv2.fillPoly(slate_mask, [(points + [ox, oy]).round().astype(np.int32)], 1)
    for (points, band_index) in tagged:
        pts = points.round().astype(np.int32)
        for ox in (-tile, 0, tile):
            for oy in (-tile, 0, tile):
                cv2.fillPoly(canvas, [pts + [ox, oy]], int(band_index) + 1)
    inside = slate_mask > 0
    counts = np.bincount(canvas[inside], minlength=len(bands) + 1).astype(float)
    return counts[1:] / inside.sum(), counts[0] / inside.sum()


def calibrate(description, rounds=8):
    bands = description['paint']['model']['band']
    used = description['paint'].get('bands_used', list(range(len(bands))))
    target = np.array([bands[b]['coverage'] if b in used else 1e-9 for b in range(len(bands))])
    target = target / target.sum()
    scale = np.ones(len(bands))
    for step in range(rounds):
        share, unpainted = visible_share(description, scale)
        visible = share / max(share.sum(), 1e-9)
        factor = np.clip((target / np.maximum(visible, 1e-4)) ** 0.7, 0.4, 2.5)
        scale *= np.where(np.array([b in used for b in range(len(bands))]), factor, 1.0)
        print('round', step, 'visible share', np.round(visible, 3).tolist(), 'unpainted', round(unpainted, 3))
    return [round(float(v), 3) for v in scale], target


if __name__ == '__main__':
    d = json.load(open(sys.argv[1]))
    scale, target = calibrate(d)
    print('target', np.round(target, 3).tolist())
    print('rate_scale', scale)

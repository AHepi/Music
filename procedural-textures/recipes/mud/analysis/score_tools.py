# What this does (plain words): helper functions that (1) turn a colour picture into the height and normal pictures the way the reference ones were
# made (proved in derivation_ceiling.py: height = a straight-line stretch of the brightness, blurred 0.5 dots; normal = slope of the 8-bit height,
# strength 9) and write a folder with colour.png / height.png / normal.png, and (2) score such a folder with BOTH project tools (pixel_compare.py =
# "is it the same picture dot for dot", texture_compare.py = "is it the same kind of surface"). Used for fast previews without Blender and for scoring
# every Blender bake. Plain Python (python3 -I); it reads reference pictures only to compare.
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
import pixel_compare as pc  # noqa: E402
import texture_compare as tc  # noqa: E402

HEIGHT_GREY_LOW, HEIGHT_GREY_HIGH, HEIGHT_BLUR, NORMAL_STRENGTH = 20.0, 128.0, 0.5, 9.0      # fitted in derivation_ceiling.py


def height_from_colour(bgr_uint8, grey_low=HEIGHT_GREY_LOW, grey_high=HEIGHT_GREY_HIGH, blur=HEIGHT_BLUR):
    grey = cv2.cvtColor(bgr_uint8, cv2.COLOR_BGR2GRAY).astype(np.float64)       # 0.299 R + 0.587 G + 0.114 B of the sRGB numbers
    h = np.clip((grey - grey_low) / (grey_high - grey_low), 0, 1) * 255.0
    if blur > 0:
        pad = int(np.ceil(4 * blur)) + 1
        h = cv2.GaussianBlur(np.pad(h, pad, mode='wrap'), (0, 0), blur)[pad:-pad, pad:-pad]
    return h


def normal_from_height(h255, strength=NORMAL_STRENGTH):
    h = np.round(h255)
    hx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2.0
    hy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) / 2.0
    nx, ny, nz = -strength * hx / 255.0, strength * hy / 255.0, np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)


def write_folder(bgr_uint8, folder, **kwargs):
    os.makedirs(folder, exist_ok=True)
    cv2.imwrite(os.path.join(folder, 'colour.png'), bgr_uint8)
    h = height_from_colour(bgr_uint8, **{k: v for k, v in kwargs.items() if k in ('grey_low', 'grey_high', 'blur')})
    cv2.imwrite(os.path.join(folder, 'height.png'), np.round(h / 255.0 * 65535.0).astype(np.uint16))
    n = normal_from_height(h, kwargs.get('strength', NORMAL_STRENGTH)) * 0.5 + 0.5
    cv2.imwrite(os.path.join(folder, 'normal.png'), np.round(n[..., ::-1] * 255.0).astype(np.uint8))      # RGB -> BGR for cv2


def score_folder(folder, reference='mud', texture=True, sheet=None):
    """pixel_compare + texture_compare numbers for a folder holding colour.png, height.png, normal.png. Returns one flat dict."""
    pixel = pc.pixel_report(reference, folder)
    result = {k: v for k, v in pixel.items() if k not in ('tier_rules', 'reference', 'candidate')}
    if sheet:
        pc.difference_sheet(reference, folder, sheet)
    if texture:
        text = tc.score_set(reference, folder)
        result['texture_compare_overall'] = text['overall']
        result['texture_compare_groups'] = text['groups']
        result['texture_compare_scores'] = text['scores']
        result['seam_ratio'] = text['facts']['seam_ratio_candidate']
    return result

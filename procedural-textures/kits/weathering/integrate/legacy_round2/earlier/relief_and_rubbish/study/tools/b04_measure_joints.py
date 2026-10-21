# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Measures HOW VISIBLE THE JOINTS BETWEEN THE ROAD SETTS ARE in a picture drawn by the study's runner (b03_render_jobs.py). It needs the picture and the mask picture
# of the same camera and size (R = joint, G = stone face, B = road). Plain Python (numpy and OpenCV), no Blender.
# The measure ("joint contrast", my own, defined here):
#   brightness  = the picture as shown (8 bit, 0 black to 1 white): L = 0.2126 R + 0.7152 G + 0.0722 B of the finished picture.
#   For every dot that is JOINT (mask R above 0.5, on the road), look at the stone faces next to it: their average brightness over a 17-dot neighbourhood
#   ("local stone brightness", worked out only from stone-face dots). The joint's contrast at that dot is (local stone brightness - the dot's brightness) / local stone brightness.
#   1.0 = the joint is black, 0.25 = a quarter darker than the stone beside it, 0 = the same, negative = the joint is BRIGHTER than the stone (a glare or a sheen fills it).
#   The road is split into three bands by picture row (near = lowest third of the rows that hold road, middle, far). In each band:
#       contrast   average joint contrast over the band's joint dots
#       delta      average (local stone brightness - joint brightness), in brightness units: a contrast of 0.3 on a stone of 0.05 is invisible, delta says so
#       seen       the share of joint dots that are at least 15 % darker than the stone beside them AND at least 0.015 darker in brightness ("seen")
#       stone      average brightness of the stone faces in the band; njoint = how many joint dots the band has (under 60: not reliable, shown as None)
#   The mask is drawn with 32 samples per dot, so a dot that is part joint, part stone has fractional values: only dots with R above 0.5 count as joint, and a stone dot
#   needs G above 0.9; at a distance the joints are narrower than a dot and the far band says "None" or a small number: that is the limit of the picture, not a fault.
# Run (as a library): from b04_measure_joints import measure; measure(picture_path, mask_path) -> dict
#   or: python3 -I b04_measure_joints.py MASK PICTURE [PICTURE ...]     (prints one table)
import json
import os
import sys

import cv2
import numpy as np


def luminance(path):
    a = cv2.imread(path, cv2.IMREAD_COLOR)[..., ::-1].astype(np.float32) / 255
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def load_mask(path):
    m = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    m = m[..., ::-1].astype(np.float32) / (65535.0 if m.dtype == np.uint16 else 255.0)
    return m[..., 0], m[..., 1], m[..., 2]          # joint, stone, road


def load_puddles(path):
    """The puddle mask picture of the checking view (red = puddle, raw numbers): a True where the road is under standing water, grown by 2 dots so that a puddle's edge is not counted."""
    import cv2 as _cv2
    image = _cv2.imread(path, _cv2.IMREAD_COLOR)[..., ::-1].astype(np.float32) / 255
    wet = (image[..., 0] > 0.5).astype(np.uint8)
    return _cv2.dilate(wet, np.ones((5, 5), np.uint8)) > 0


def measure(picture, mask, bands=3, seen_ratio=0.15, seen_delta=0.015, radius=8, puddles=None):
    """puddles: optional path of a puddle mask picture. With it, dots under a puddle are left out of BOTH the joint dots and the stone dots (water at a grazing angle hides what lies under it, and
    the study judges the road that is not under standing water); the result then also says 'puddle_share' (the share of the road under a puddle)."""
    L = luminance(picture) if isinstance(picture, str) else picture
    J, S, R = load_mask(mask) if isinstance(mask, str) else mask
    road = R > 0.99
    puddle_share = None
    if puddles is not None:
        under_water = load_puddles(puddles) if isinstance(puddles, str) else puddles
        puddle_share = float((under_water & road).sum() / max(1, road.sum()))
        road = road & ~under_water
    rows = np.where(road.any(axis=1))[0]
    top, bottom = rows.min(), rows.max()
    edges = np.linspace(top, bottom + 1, bands + 1).astype(int)
    stone = (S > 0.9) & road
    weight = stone.astype(np.float32)
    k = 2 * radius + 1
    num = cv2.GaussianBlur(L * weight, (k, k), radius / 2.0)
    den = cv2.GaussianBlur(weight, (k, k), radius / 2.0)
    local_stone = np.where(den > 0.02, num / np.maximum(den, 1e-6), np.nan)
    joint = (J > 0.5) & road & np.isfinite(local_stone)
    result = {}
    for name, (r0, r1) in zip(('far', 'middle', 'near'), zip(edges[:-1], edges[1:])):
        band = np.zeros_like(road)
        band[r0:r1] = True
        j = joint & band
        s = stone & band
        n = int(j.sum())
        entry = dict(rows=[int(r0), int(r1)], njoint=n, nstone=int(s.sum()), stone=round(float(L[s].mean()), 4) if s.any() else None)
        if n >= 60:
            ls = local_stone[j]
            contrast = (ls - L[j]) / np.maximum(ls, 0.02)
            entry.update(contrast=round(float(contrast.mean()), 3), delta=round(float((ls - L[j]).mean()), 4),
                         seen=round(float(((contrast >= seen_ratio) & ((ls - L[j]) >= seen_delta)).mean()), 3))
        else:
            entry.update(contrast=None, delta=None, seen=None)
        result[name] = entry
    result['road_mean'] = round(float(L[road].mean()), 4)
    if puddle_share is not None:
        result['puddle_share'] = round(puddle_share, 3)
    return result


def table(rows):
    print(f"{'picture':34s} {'road':>6s} | {'near contrast/delta/seen':>26s} | {'middle':>26s} | {'far':>26s}")
    for name, r in rows:
        def cell(b):
            e = r[b]
            return 'n/a'.rjust(26) if e['contrast'] is None else f"{e['contrast']:6.2f} {e['delta']:7.3f} {e['seen']:6.2f} ({e['njoint']:5d})".rjust(26)
        print(f"{name:34s} {r['road_mean']:6.3f} | {cell('near')} | {cell('middle')} | {cell('far')}")


if __name__ == '__main__':
    mask_path, pictures = sys.argv[1], sys.argv[2:]
    out = []
    for p in pictures:
        out.append((os.path.basename(p), measure(p, mask_path)))
    table(out)

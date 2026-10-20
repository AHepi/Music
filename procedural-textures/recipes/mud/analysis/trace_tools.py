# What this does (plain words): ANALYSIS tools for the mud colour picture (copied from the wood work, unchanged) (they READ the reference picture; the Blender generator never does).
# They turn a painted picture into a short list of flat colour shapes ("patches"):
#   1. make_palette: pick N colours that stand in for the whole picture (k-means in Lab, a colour space where distances look like what the eye sees);
#   2. assign_labels / mode_filter / remove_small_areas: give every dot the number of its nearest palette colour, clean single-dot noise, and
#      repaint tiny areas with the colour of the nearest bigger area;
#   3. trace_regions: cut the picture into connected same-colour areas and write each as a simplified outline (a polygon);
#   4. draw_regions: a quick numpy "painter" preview (big shapes first, small ones on top) so the accuracy of a list can be measured without Blender.
# This is the "tracing the picture" end of the description ladder, so it is reported honestly as tracing, not as procedural generation.
# Coordinates: a corner is stored as whole numbers in "dot-centre units" (the centre of the picture dot in column 3 is x = 3); the generator adds 0.5.
import json

import cv2
import numpy as np


def srgb_to_lab_float(bgr_uint8):
    return cv2.cvtColor(bgr_uint8.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)


def make_palette(bgr, count, seed=1):
    """k-means palette in Lab from a random sample of dots. Returns centres in Lab (count x 3)."""
    lab = srgb_to_lab_float(bgr).reshape(-1, 3)
    rng = np.random.default_rng(seed)
    sample = lab[rng.choice(len(lab), min(250000, len(lab)), replace=False)]
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.01)
    cv2.setRNGSeed(seed)
    _, _, centres = cv2.kmeans(sample, count, None, criteria, 4, cv2.KMEANS_PP_CENTERS)
    return centres


def assign_labels(bgr, centres):
    lab = srgb_to_lab_float(bgr).reshape(-1, 3)
    labels = np.empty(len(lab), np.int32)
    for start in range(0, len(lab), 150000):
        chunk = lab[start:start + 150000]
        labels[start:start + 150000] = ((chunk[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
    return labels.reshape(bgr.shape[:2])


def palette_to_bgr(centres):
    return (np.clip(cv2.cvtColor(centres.reshape(1, -1, 3).astype(np.float32), cv2.COLOR_Lab2BGR)[0], 0, 1) * 255).round().astype(np.uint8)


def mode_filter(labels, count, radius=1):
    """Each dot takes the most common label in its (2 radius + 1)^2 neighbourhood (wrap-around edges)."""
    size = 2 * radius + 1
    padded = np.pad(labels, radius, mode='wrap')
    best = np.zeros(labels.shape, np.float32)
    best_label = labels.copy()
    for k in range(count):
        votes = cv2.boxFilter((padded == k).astype(np.float32), -1, (size, size), normalize=False, borderType=cv2.BORDER_CONSTANT)
        votes = votes[radius:-radius, radius:-radius] if radius else votes
        better = votes > best
        best[better] = votes[better]
        best_label[better] = k
    return best_label


def remove_small_areas(labels, count, min_area):
    """Repaint connected areas smaller than min_area with the label of the nearest dot of a bigger area."""
    keep = np.zeros(labels.shape, bool)
    for k in range(count):
        n, comp, stats, _ = cv2.connectedComponentsWithStats((labels == k).astype(np.uint8), connectivity=4)
        big = np.zeros(n, bool)
        big[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
        keep |= big[comp] & (labels == k)
    if keep.all():
        return labels
    drop_mask = (~keep).astype(np.uint8)
    _, nearest = cv2.distanceTransformWithLabels(drop_mask, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    flat_positions = np.flatnonzero(keep.ravel())
    table = np.zeros(int(nearest.max()) + 1, np.int64)
    table[nearest.ravel()[flat_positions]] = flat_positions
    out = labels.copy().ravel()
    dropped = np.flatnonzero(~keep.ravel())
    out[dropped] = labels.ravel()[table[nearest.ravel()[dropped]]]
    return out.reshape(labels.shape)


def trace_regions(labels, count, epsilon, min_area):
    """Outline of every connected same-label area: list of dicts {'c': label, 'p': [[x, y], ...], 'a': filled area}, big to small."""
    regions = []
    for k in range(count):
        mask = (labels == k).astype(np.uint8)
        n, comp, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
        for i in range(1, n):
            x, y, w, h, area = stats[i]
            if area < min_area:
                continue
            sub = np.pad((comp[y:y + h, x:x + w] == i).astype(np.uint8), 1)
            contours, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            for contour in contours:
                simple = cv2.approxPolyDP(contour, epsilon, True)[:, 0, :] + np.array([x - 1, y - 1])
                if len(simple) < 3:
                    continue
                filled = abs(cv2.contourArea(simple.astype(np.int32)))
                regions.append({'c': int(k), 'p': simple.astype(int).tolist(), 'a': float(max(filled, area))})
    regions.sort(key=lambda r: -r['a'])
    return regions


def grow_polygon(points, distance):
    """Push every corner outwards by `distance` dots (mitred, never more than 3 x distance). Works for either direction of travel."""
    pts = np.asarray(points, np.float64)
    if distance == 0 or len(pts) < 3:
        return pts
    nxt, prv = np.roll(pts, -1, axis=0), np.roll(pts, 1, axis=0)
    area = 0.5 * np.sum(pts[:, 0] * nxt[:, 1] - nxt[:, 0] * pts[:, 1])
    sign = 1.0 if area > 0 else -1.0

    def outward(a, b):
        edge = b - a
        length = np.maximum(np.linalg.norm(edge, axis=1, keepdims=True), 1e-9)
        return sign * np.stack([edge[:, 1], -edge[:, 0]], axis=1) / length

    n1, n2 = outward(prv, pts), outward(pts, nxt)
    scale = 1.0 / np.maximum(1.0 + (n1 * n2).sum(axis=1, keepdims=True), 0.34)
    offset = (n1 + n2) * scale * distance
    length = np.linalg.norm(offset, axis=1, keepdims=True)
    limit = 3.0 * abs(distance)
    offset = np.where(length > limit, offset / np.maximum(length, 1e-9) * limit, offset)
    return pts + offset


def draw_regions(regions, palette_bgr, size=1254, scale=4, grow=0.5, background=0):
    """Painter's algorithm preview: big shapes first, small on top. Drawn at `scale` x resolution and shrunk back (anti-aliased)."""
    big = np.zeros((size * scale, size * scale, 3), np.uint8)
    big[:] = palette_bgr[background]
    for region in regions:
        pts = grow_polygon(np.array(region['p'], np.float64) + 0.5, grow) * scale
        cv2.fillPoly(big, [pts.round().astype(np.int32)], tuple(int(v) for v in palette_bgr[region['c']]), lineType=cv2.LINE_8)
    return cv2.resize(big, (size, size), interpolation=cv2.INTER_AREA)


def delta_encode(points):
    """[[x, y], ...] -> flat [x0, y0, dx1, dy1, ...] (small steps make shorter text)."""
    pts = np.asarray(points, np.int64)
    steps = np.diff(pts, axis=0, prepend=np.zeros((1, 2), np.int64))
    return steps.reshape(-1).tolist()


def json_size(regions, palette):
    text = json.dumps({'palette': palette, 'patches': [[r['c'], delta_encode(r['p'])] for r in regions]}, separators=(',', ':'))
    return len(text.encode())

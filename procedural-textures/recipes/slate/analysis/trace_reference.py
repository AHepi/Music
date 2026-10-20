# What this does (plain words): ANALYSIS of the slate colour picture (reads the reference; the Blender generator never does).
# It finds, in this order:
#   1. a colour palette (k-means in Lab, 24 colours);
#   2. the "gap network" = the black joints between the slates (the darkest dots, joined up), the black part of the picture;
#   3. every slate body = one closed area of the picture that is NOT gap (its outline is a polygon with a ragged lower edge);
#   4. the paint patches inside each slate = connected same-palette-colour areas, tiny specks dropped, each as a simplified polygon.
# Everything is done on a picture padded by wrapping around the edges (the tile repeats), so slates and patches that cross the edge are
# found whole; their coordinates then run outside 0..1254 (the generator draws shifted copies, so the tile still repeats).
# Output: analysis/trace_full.json (large; the description files in ../description are cut from it by describe.py).
# Run: python3 -I trace_reference.py
import json
import os
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vector_trace as vt  # noqa: E402

TILE = 1254
PAD = 260


def wrap_pad(image, pad=PAD):
    return np.pad(image, ((pad, pad), (pad, pad)) + ((0, 0),) * (image.ndim - 2), mode='wrap')


def polygon_centroid(points):
    m = cv2.moments(points.astype(np.float32))
    if m['m00'] == 0:
        return points.mean(axis=0)
    return np.array([m['m10'] / m['m00'], m['m01'] / m['m00']])


def inside_tile(point):
    return 0 <= point[0] < TILE and 0 <= point[1] < TILE



def find_row_bands(grey, threshold=30.0, share=0.45):
    """Rows of the wrap-padded picture that are mostly black = the horizontal joints. Returns [(y_first, y_last), ...] in padded coordinates."""
    dark_share = (grey < threshold).mean(axis=1)
    bands, start = [], None
    for y, value in enumerate(dark_share):
        if value > share and start is None:
            start = y
        if value <= share and start is not None:
            bands.append((start, y - 1))
            start = None
    return bands


def find_joint_lines(grey, bands):
    """The vertical joints between neighbouring slates, as straight line segments (x_top, y_top, x_bottom, y_bottom) in padded coordinates.
    Between two horizontal bands: count, for every column, how many of the dots are dark (below 50); the columns where most are dark are
    joints; a straight line is then fitted through the dark dots near each one (joints lean a little)."""
    lines = []
    for (a0, a1), (b0, b1) in zip(bands[:-1], bands[1:]):
        top, bottom = a1 + 12, b0 - 12
        if bottom - top < 60:
            continue
        band = grey[top:bottom] < 50
        profile = band.mean(axis=0)
        smooth = np.convolve(profile, np.ones(5) / 5, mode='same')
        x = 3
        while x < len(smooth) - 3:
            if smooth[x] > 0.55 and smooth[x] >= smooth[x - 3:x + 4].max():
                ys, xs = np.where(band[:, max(x - 12, 0):x + 13])
                xs = xs + max(x - 12, 0)
                if len(ys) > 200:
                    slope, offset = np.polyfit(ys, xs, 1)
                    # one round of throwing out dots far from the line, then refit
                    keep = np.abs(xs - (slope * ys + offset)) < 6
                    if keep.sum() > 100:
                        slope, offset = np.polyfit(ys[keep], xs[keep], 1)
                    # accept only a line that is dark along (almost) its whole length: along the line (looking +-1 dot sideways) at least 80 %
                    # of the dots are dark and no stretch of 20 or more dots in a row is light (dark paint blotches are not joints)
                    line_ys = np.arange(0, bottom - top)
                    line_xs = np.clip(np.round(offset + slope * line_ys).astype(int), 1, grey.shape[1] - 2)
                    along = np.min([grey[top + line_ys, line_xs + d] for d in (-1, 0, 1)], axis=0) < 50
                    longest_gap, run = 0, 0
                    for flag in along:
                        run = 0 if flag else run + 1
                        longest_gap = max(longest_gap, run)
                    if along.mean() >= 0.8 and longest_gap < 20:
                        lines.append((offset + slope * 0, top, offset + slope * (bottom - top), bottom))
                x += 25
            else:
                x += 1
    return lines


def trace(palette_count=24, gap_threshold=21.0, epsilon_outline=1.2, epsilon_paint=1.5, min_area=12, seed=1):
    bgr = vt.load_reference_colour()
    grey = bgr[..., ::-1].astype(np.float64) @ np.array([0.299, 0.587, 0.114])
    centres = vt.make_palette(bgr, palette_count, seed)
    palette_bgr = vt.palette_to_bgr(centres)
    labels = vt.assign_labels(bgr, centres)
    # order the palette from dark to light so that index 0 is the darkest (the gap colour)
    order = np.argsort(centres[:, 0])
    remap = np.empty(palette_count, np.int32)
    remap[order] = np.arange(palette_count)
    labels = remap[labels]
    centres = centres[order]
    palette_bgr = palette_bgr[order]

    # ---- 2. gap network: the darkest dots, joined, small specks inside slates dropped
    padded_grey = wrap_pad(grey)
    # hysteresis: sure-black dots (below the threshold), plus slightly lighter dots (below 1.5 x the threshold) that lie within 2 dots of sure-black
    sure = (padded_grey < gap_threshold).astype(np.uint8)
    near_sure = cv2.dilate(sure, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    core = (sure | ((padded_grey < gap_threshold * 1.5) & (near_sure > 0))).astype(np.uint8)
    core = cv2.morphologyEx(core, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    count, comp, stats, _ = cv2.connectedComponentsWithStats(core, connectivity=8)
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    network = core.astype(bool)
    print('gap network: dark dots', int(core.sum()), 'components', count - 1, 'biggest', int(stats[biggest, cv2.CC_STAT_AREA]))

    # ---- 3. slates = areas that are not network. Thin joints leak (a 1-3 dot break in a black line would join two slates), so slate
    # identity comes from "cores": close the network with a 7 x 7 disk (bridges the breaks), open the rest with a 9 x 9 disk (thin
    # bridges vanish), name each core, then grow the cores out over the true (unbridged) not-network dots.
    # long thin vertical dark lines (the joints between slates) found with a tall 1 x 35 kernel on a more generous dark mask, and
    # stretched upwards/downwards by 12 dots so that they reach the horizontal bands even where the black line is faint
    generous = (padded_grey < gap_threshold * 1.9).astype(np.uint8)
    vertical_lines = cv2.morphologyEx(generous, cv2.MORPH_OPEN, np.ones((35, 1), np.uint8))
    vertical_lines = cv2.dilate(vertical_lines, np.ones((25, 3), np.uint8))
    bands = find_row_bands(padded_grey)
    joints = find_joint_lines(padded_grey, bands)
    print('horizontal bands found:', len(bands), ' vertical joints found:', len(joints))
    joint_picture = np.zeros(core.shape, np.uint8)
    for x0, y0, x1, y1 in joints:
        cv2.line(joint_picture, (int(round(x0)), int(y0)), (int(round(x1)), int(y1)), 1, 5)
    bridged = cv2.morphologyEx(core | vertical_lines | joint_picture, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    cv2.imwrite(os.path.join(HERE, 'bridged_network.png'), bridged[PAD:-PAD, PAD:-PAD] * 255)
    cores = cv2.morphologyEx((1 - bridged).astype(np.uint8), cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    n, core_labels, core_stats, _ = cv2.connectedComponentsWithStats(cores, connectivity=4)
    id_picture = np.zeros(core.shape, np.int32)
    names = {}
    for i in range(1, n):
        if core_stats[i, cv2.CC_STAT_AREA] >= 3000:
            names[i] = len(names) + 1
            id_picture[core_labels == i] = names[i]
    not_network = (~network).astype(np.uint8)
    allowed = not_network.astype(bool)
    grow = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    for _ in range(14):
        grown = cv2.dilate(id_picture.astype(np.float32), grow).astype(np.int32)
        id_picture = np.where((id_picture == 0) & allowed, grown, id_picture)
    slates = []
    for new_id in range(1, len(names) + 1):
        mask = (id_picture == new_id)
        ys, xs = np.where(mask)
        x, y, w, h = int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
        sub = np.pad(mask[y:y + h, x:x + w].astype(np.uint8), 1)
        contours, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        contour = max(contours, key=cv2.contourArea)
        simple = cv2.approxPolyDP(contour, epsilon_outline, True)[:, 0, :] + np.array([x - 1 - PAD, y - 1 - PAD])
        centre = polygon_centroid(simple)
        slates.append({'outline': simple.astype(int).tolist(), 'area': int(mask.sum()), 'centre': [float(centre[0]), float(centre[1])],
                       'bbox': [int(x - PAD), int(y - PAD), int(w), int(h)], 'old_id': new_id})
    # keep only slates whose centre lies in the tile; give them new ids sorted by row then column
    kept = [s for s in slates if inside_tile(s['centre']) and s['area'] > 3000 and s['bbox'][2] < 800]
    kept.sort(key=lambda s: (round(s['centre'][1] / 100), s['centre'][0]))
    remap_ids = np.zeros(len(names) + 1, np.int32)
    for new_id, s in enumerate(kept, 1):
        remap_ids[s['old_id']] = new_id
        s['id'] = new_id
    id_every_copy = id_picture.copy()        # slates whose centre lies outside the tile are still needed: their paint shows at the tile edge
    id_picture = remap_ids[id_picture]
    slates = kept
    print('slates found:', len(slates))

    # ---- 4. paint patches inside the slates
    padded_labels = wrap_pad(labels)
    padded_labels = vt.mode_filter(padded_labels, palette_count, 1)
    inside = id_every_copy > 0
    work = np.where(inside, padded_labels, -1).astype(np.int32)
    # drop tiny areas: re-paint with the nearest bigger area of the same slate (only inside slates)
    cleaned = work.copy()
    keep = np.zeros(work.shape, bool)
    for k in range(palette_count):
        nn, cc, ss, _ = cv2.connectedComponentsWithStats((work == k).astype(np.uint8), connectivity=4)
        big = np.zeros(nn, bool)
        big[1:] = ss[1:, cv2.CC_STAT_AREA] >= min_area
        keep |= big[cc] & (work == k)
    keep |= ~inside
    drop = (~keep).astype(np.uint8)
    _, nearest = cv2.distanceTransformWithLabels(drop, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)
    flat_keep = np.flatnonzero(keep.ravel())
    table = np.zeros(int(nearest.max()) + 1, np.int64)
    table[nearest.ravel()[flat_keep]] = flat_keep
    flat = cleaned.ravel()
    dropped = np.flatnonzero(~keep.ravel())
    flat[dropped] = work.ravel()[table[nearest.ravel()[dropped]]]
    cleaned = flat.reshape(work.shape)
    # a dropped dot may have copied "-1" (outside) from the nearest kept dot: leave those at -1
    patches = []
    for k in range(palette_count):
        mask = (cleaned == k).astype(np.uint8)
        nn, cc, ss, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
        for i in range(1, nn):
            x, y, w, h, area = ss[i]
            if area < min_area:
                continue
            sub = np.pad((cc[y:y + h, x:x + w] == i).astype(np.uint8), 1)
            contours, _ = cv2.findContours(sub, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            for contour in contours:
                simple = cv2.approxPolyDP(contour, epsilon_paint, True)[:, 0, :] + np.array([x - 1 - PAD, y - 1 - PAD])
                if len(simple) < 3:
                    continue
                centre = polygon_centroid(simple)
                if not inside_tile(centre):
                    continue
                slate_id = int(id_picture[min(max(int(centre[1]) + PAD, 0), id_picture.shape[0] - 1), min(max(int(centre[0]) + PAD, 0), id_picture.shape[1] - 1)])
                ys, xs = np.where(cc[y:y + h, x:x + w] == i)
                slate_here = int(np.bincount(id_picture[y:y + h, x:x + w][ys, xs]).argmax())
                patches.append({'c': int(k), 'p': simple.astype(int).tolist(), 'area': int(area), 'filled': float(max(abs(cv2.contourArea(simple.astype(np.int32))), area)),
                                'slate': slate_here, 'bbox': [int(x - PAD), int(y - PAD), int(w), int(h)]})
    print('paint patches:', len(patches))
    result = {'palette_bgr': palette_bgr.tolist(), 'palette_lab': centres.tolist(), 'slates': slates, 'patches': patches,
              'settings': {'palette_count': palette_count, 'gap_threshold': gap_threshold, 'epsilon_outline': epsilon_outline,
                           'epsilon_paint': epsilon_paint, 'min_area': min_area}}
    return result, id_picture


if __name__ == '__main__':
    started = time.time()
    result, id_picture = trace()
    json.dump(result, open(os.path.join(HERE, 'trace_full.json'), 'w'))
    preview = (id_picture[PAD:-PAD, PAD:-PAD] * 37 % 255).astype(np.uint8)
    cv2.imwrite(os.path.join(HERE, 'slate_ids.png'), cv2.applyColorMap(preview, cv2.COLORMAP_JET))
    print('seconds', round(time.time() - started, 1))

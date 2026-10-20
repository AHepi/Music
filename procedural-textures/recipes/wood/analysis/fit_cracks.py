# What this does (plain words): ANALYSIS (reads the reference picture). Finds the very dark thin structure of the wood picture (board gaps and cracks) and
# writes each as a CENTRE LINE with a WIDTH at every corner: [[x, y, width], ...]. How: take the very dark dots (lightness under a threshold), peel the dark areas
# down to a one-dot-wide skeleton (Zhang-Suen thinning, done with numpy), walk the skeleton from end to end, straighten each walk into a few corners
# (Douglas-Peucker, OpenCV), and read the local width off a distance map (twice the distance from the skeleton dot to the nearest light dot).
# Output: analysis/cracks_fitted.json (a list of lines, longest/heaviest first). The generator draws such a line as a ribbon of changing width.
# Run: python3 -I fit_cracks.py [lightness_threshold]
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import trace_tools as tt  # noqa: E402


def zhang_suen(mask):
    """Skeleton (one dot wide) of a boolean picture. Vectorised Zhang-Suen thinning."""
    img = np.pad(mask.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            p = img
            P2, P3, P4, P5 = p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:], p[2:, 2:]
            P6, P7, P8, P9 = p[2:, 1:-1], p[2:, :-2], p[1:-1, :-2], p[:-2, :-2]
            center = p[1:-1, 1:-1]
            neighbours = [P2, P3, P4, P5, P6, P7, P8, P9]
            B = sum(n.astype(np.int16) for n in neighbours)
            A = sum(((neighbours[i] == 0) & (neighbours[(i + 1) % 8] == 1)).astype(np.int16) for i in range(8))
            if step == 0:
                cond = (P2 * P4 * P6 == 0) & (P4 * P6 * P8 == 0)
            else:
                cond = (P2 * P4 * P8 == 0) & (P2 * P6 * P8 == 0)
            delete = (center == 1) & (B >= 2) & (B <= 6) & (A == 1) & cond
            if delete.any():
                img[1:-1, 1:-1][delete] = 0
                changed = True
        if not changed:
            break
    return img[1:-1, 1:-1] > 0


def skeleton_paths(skel):
    """Walk a skeleton: returns a list of paths, each a list of (x, y) dots from one end or junction to the next."""
    ys, xs = np.nonzero(skel)
    dots = set(zip(xs.tolist(), ys.tolist()))
    offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]

    def neighbours(d):
        return [(d[0] + a, d[1] + b) for a, b in offsets if (d[0] + a, d[1] + b) in dots]

    degree = {d: len(neighbours(d)) for d in dots}
    visited_edges = set()
    paths = []
    nodes = [d for d, k in degree.items() if k != 2]
    for start in nodes + list(dots):
        for first in neighbours(start):
            if (start, first) in visited_edges:
                continue
            path = [start, first]
            visited_edges.add((start, first))
            visited_edges.add((first, start))
            previous, current = start, first
            while degree[current] == 2:
                nxt = [n for n in neighbours(current) if n != previous]
                if not nxt:
                    break
                step = nxt[0]
                if (current, step) in visited_edges:
                    break
                visited_edges.add((current, step))
                visited_edges.add((step, current))
                path.append(step)
                previous, current = current, step
            if len(path) >= 3:
                paths.append(path)
    return paths


def fit(threshold=13.0, min_component=30, min_path=8, epsilon=1.6, bgr=None):
    bgr = bgr if bgr is not None else cv2.imread(os.path.join(PROC, 'reference', 'wood', 'colour.png'))
    lab = tt.srgb_to_lab_float(bgr)
    dark = (lab[..., 0] < threshold).astype(np.uint8)
    n, comp, stats, _ = cv2.connectedComponentsWithStats(dark, connectivity=8)
    keep = np.isin(comp, np.nonzero(stats[:, cv2.CC_STAT_AREA] >= min_component)[0]) & (comp > 0)
    distance = cv2.distanceTransform(keep.astype(np.uint8), cv2.DIST_L2, 5)
    skel = zhang_suen(keep)
    lines = []
    for path in skeleton_paths(skel):
        if len(path) < min_path:
            continue
        arr = np.array(path, np.float32).reshape(-1, 1, 2)
        simple = cv2.approxPolyDP(arr, epsilon, False)[:, 0, :]
        if len(simple) < 2:
            continue
        # width at every corner: twice the distance to the nearest light dot, averaged over the neighbouring skeleton dots
        pts = np.array(path)
        widths = []
        for corner in simple:
            near = np.argsort(np.abs(pts - corner).sum(axis=1))[:5]
            widths.append(float(2.0 * np.mean([distance[pts[i][1], pts[i][0]] for i in near]) - 0.5))
        length = float(np.sum(np.hypot(*np.diff(simple, axis=0).T)))
        lines.append({'length': round(length, 1), 'mean_width': round(float(np.mean(widths)), 2),
                      'pts': [[int(x), int(y), round(max(w, 1.0), 1)] for (x, y), w in zip(simple, widths)]})
    lines.sort(key=lambda l: -(l['length'] * max(l['mean_width'], 1.0)))
    return lines, skel, keep


if __name__ == '__main__':
    threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 13.0
    lines, skel, keep = fit(threshold)
    print('dark share kept', round(float(keep.mean()), 4), '; skeleton dots', int(skel.sum()), '; lines', len(lines), '; corners', sum(len(l['pts']) for l in lines),
          '; total length', round(sum(l['length'] for l in lines)))
    for l in lines[:8]:
        print('  length', l['length'], 'mean width', l['mean_width'], 'corners', len(l['pts']))
    json.dump(lines, open(os.path.join(HERE, 'cracks_fitted.json'), 'w'))
    cv2.imwrite(os.path.join(HERE, 'cracks_skeleton.png'), cv2.dilate(skel.astype(np.uint8) * 255, np.ones((2, 2), np.uint8)))

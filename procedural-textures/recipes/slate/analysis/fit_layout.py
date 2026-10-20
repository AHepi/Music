# What this does (plain words): ANALYSIS. Measures the LAYOUT of the slate picture from the traced slate outlines (trace_full.json): how many rows,
# where each row starts and ends, and for every slate its left and right edge (and how much each edge leans), top and bottom, plus how
# ragged the edges are. Writes analysis/layout_fit.json: the small "layout" block that the generator can expand into slate outlines
# by itself, and the measured spreads that the sampler uses to invent NEW layouts. Plain Python (python3 -I); reads trace_full.json only.
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TILE = 1254


def edge_profiles(outline):
    pts = np.array(outline, float)
    off = np.array([pts[:, 0].min() - 1, pts[:, 1].min() - 1])
    mask = np.zeros((int(pts[:, 1].max() - pts[:, 1].min() + 3), int(pts[:, 0].max() - pts[:, 0].min() + 3)), np.uint8)
    cv2.fillPoly(mask, [(pts - off).round().astype(np.int32)], 1)
    height, width = mask.shape
    top = np.array([np.argmax(mask[:, x]) if mask[:, x].any() else np.nan for x in range(width)])
    bottom = np.array([height - 1 - np.argmax(mask[::-1, x]) if mask[:, x].any() else np.nan for x in range(width)])
    left = np.array([np.argmax(mask[y]) if mask[y].any() else np.nan for y in range(height)])
    right = np.array([width - 1 - np.argmax(mask[y, ::-1]) if mask[y].any() else np.nan for y in range(height)])
    return mask, off, top, bottom, left, right


def robust_line(ys, xs, rounds=4):
    """Straight line x = slope * y + offset through the edge dots, ignoring chips and notches (dots far from the line are thrown out and the line refitted)."""
    keep = np.ones(len(ys), bool)
    for _ in range(rounds):
        slope, offset = np.polyfit(ys[keep], xs[keep], 1)
        residual = xs - (slope * ys + offset)
        spread = 1.4826 * np.median(np.abs(residual[keep] - np.median(residual[keep]))) + 0.5
        keep = np.abs(residual - np.median(residual[keep])) < 2.5 * spread
        if keep.sum() < 10:
            break
    return slope, offset


def fit():
    trace = json.load(open(os.path.join(HERE, 'trace_full.json')))
    slates = []
    for s in trace['slates']:
        mask, off, top, bottom, left, right = edge_profiles(s['outline'])
        height, width = mask.shape
        mid_x = slice(int(width * 0.15), int(width * 0.85))
        mid_y = slice(int(height * 0.2), int(height * 0.8))
        ys = np.arange(height)
        slope_l, offset_l = robust_line(ys[mid_y], left[mid_y])
        slope_r, offset_r = robust_line(ys[mid_y], right[mid_y])
        slope_l, slope_r = float(np.clip(slope_l, -0.06, 0.06)), float(np.clip(slope_r, -0.06, 0.06))
        y_mid = off[1] + height / 2
        centre_row = np.nanmedian(top[mid_x]) + off[1]
        slates.append({
            'cx': s['centre'][0], 'cy': s['centre'][1],
            'x0': float(offset_l + slope_l * (height / 2) + off[0]),        # left edge at mid height
            'x1': float(offset_r + slope_r * (height / 2) + off[0] + 1),    # right edge at mid height
            'slant_l': float(slope_l), 'slant_r': float(slope_r),
            'top': float(np.nanmedian(top[mid_x]) + off[1]), 'bottom': float(np.nanmedian(bottom[mid_x]) + off[1] + 1),
            'rag_top': float(np.nanstd(top[mid_x])), 'rag_bottom': float(np.nanstd(bottom[mid_x])),
            'rag_side': float(np.nanstd(np.concatenate([left[mid_y] - (offset_l + slope_l * ys[mid_y]), right[mid_y] - (offset_r + slope_r * ys[mid_y])]))),
        })
    # rows: cluster by top edge
    slates.sort(key=lambda s: s['top'])
    rows, current = [], [slates[0]]
    for s in slates[1:]:
        if s['top'] - np.mean([c['top'] for c in current]) > 40:
            rows.append(current)
            current = []
        current.append(s)
    rows.append(current)
    layout_rows = []
    for row in rows:
        row.sort(key=lambda s: s['cx'])
        layout_rows.append({'top': round(float(np.median([s['top'] for s in row])), 1), 'bottom': round(float(np.median([s['bottom'] for s in row])), 1),
                            'slates': [[round(s['x0'], 1), round(s['x1'], 1), round(s['slant_l'], 3), round(s['slant_r'], 3), round(s['top'] - np.median([r['top'] for r in row]), 1),
                                        round(s['bottom'] - np.median([r['bottom'] for r in row]), 1)] for s in row]})
    layout_rows.sort(key=lambda r: r['top'])
    # joints: the line between two neighbouring slates of a row, shared by both (centre at mid height, lean, width of the black gap)
    for row in layout_rows:
        entries = row['slates']
        joints = []
        for a, b in zip(entries, entries[1:] + [[entries[0][0] + TILE] + entries[0][1:]]):
            gap = float(np.clip(b[0] - a[1], 2.0, 9.0))
            joints.append([round(0.5 * (a[1] + b[0]), 1), round(float(np.clip(0.5 * (a[3] + b[2]), -0.06, 0.06)), 3), round(gap, 1)])
        row['joints'] = joints
        row['top_shift'] = [e[4] for e in entries]
        row['bottom_shift'] = [e[5] for e in entries]
    stats = {
        'rag_top': float(np.mean([s['rag_top'] for s in slates])), 'rag_bottom': float(np.mean([s['rag_bottom'] for s in slates])),
        'rag_side': float(np.mean([s['rag_side'] for s in slates])),
        'slant_mean': float(np.mean([s['slant_l'] for s in slates] + [s['slant_r'] for s in slates])),
        'slant_std': float(np.std([s['slant_l'] for s in slates] + [s['slant_r'] for s in slates])),
        'width_log_mean': float(np.mean(np.log([s['x1'] - s['x0'] for s in slates]))), 'width_log_std': float(np.std(np.log([s['x1'] - s['x0'] for s in slates]))),
        'row_height': [float(np.mean([r['bottom'] - r['top'] for r in layout_rows])), float(np.std([r['bottom'] - r['top'] for r in layout_rows]))],
        'slates_per_row': [len(r['slates']) for r in layout_rows],
    }
    # gaps between neighbouring slates in a row, and between rows
    horizontal_gaps, vertical_gaps = [], []
    for row in layout_rows:
        edges = row['slates']
        for a, b in zip(edges, edges[1:] + [[edges[0][0] + TILE] + edges[0][1:]]):
            horizontal_gaps.append(b[0] - a[1])
    for upper, lower in zip(layout_rows, layout_rows[1:] + [{'top': layout_rows[0]['top'] + TILE}]):
        vertical_gaps.append(lower['top'] - upper['bottom'])
    stats['gap_between_slates'] = [float(np.mean(horizontal_gaps)), float(np.std(horizontal_gaps))]
    stats['gap_between_rows'] = [float(np.mean(vertical_gaps)), float(np.std(vertical_gaps))]
    return {'rows': layout_rows, 'stats': stats}


if __name__ == '__main__':
    result = fit()
    json.dump(result, open(os.path.join(HERE, 'layout_fit.json'), 'w'), indent=1)
    print(json.dumps(result['stats'], indent=1))
    for r in result['rows']:
        print(r['top'], r['bottom'], [(s[0], s[1]) for s in r['slates']])

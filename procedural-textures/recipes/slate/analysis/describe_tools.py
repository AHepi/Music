# What this does (plain words): turns the big trace of the reference (trace_full.json, made by trace_reference.py) into a SMALL
# description file for the slate generator, at a chosen size: fewer palette colours, rougher outlines, only the bigger paint patches.
# It also holds a quick numpy "preview painter" that draws a description with plain Python so that many sizes can be compared in seconds
# (the real picture always comes from Blender; the preview is only to choose settings and to check the Blender picture against).
# Plain Python (python3 -I). Reads the reference only through trace_full.json (analysis side).
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
TILE = 1254


def simplify(points, epsilon):
    pts = np.array(points, np.int32).reshape(-1, 1, 2)
    out = cv2.approxPolyDP(pts, epsilon, True)[:, 0, :]
    return out if len(out) >= 3 else np.array(points, np.int32)


def delta_encode(points):
    """[[x, y], ...] -> [x0, y0, dx1, dy1, ...] (whole numbers; the small steps make the text shorter)."""
    flat = [int(points[0][0]), int(points[0][1])]
    for previous, current in zip(points[:-1], points[1:]):
        flat += [int(current[0] - previous[0]), int(current[1] - previous[1])]
    return flat


def delta_decode(flat):
    x, y = flat[0], flat[1]
    points = [(x, y)]
    for index in range(2, len(flat), 2):
        x += flat[index]
        y += flat[index + 1]
        points.append((x, y))
    return points


def reduce_palette(palette_rgb, weights, target_count):
    """Merge palette colours down to target_count (k-means on the palette colours weighted by how much picture each covers).
    Returns (new_palette_rgb, mapping old index -> new index). Colour 0 (the gap colour) always stays its own entry."""
    if target_count >= len(palette_rgb):
        return [list(map(int, c)) for c in palette_rgb], list(range(len(palette_rgb)))
    rgb = np.array(palette_rgb, np.float32)
    lab = cv2.cvtColor((rgb / 255.0).reshape(1, -1, 3), cv2.COLOR_RGB2Lab)[0]
    keep_zero = lab[0:1]
    rest = lab[1:]
    w = np.array(weights[1:], np.float32)
    # weighted k-means by repeating colours in proportion to weight (cheap and good enough for 24 colours)
    repeats = np.maximum((w / w.sum() * 4000).astype(int), 1)
    samples = np.repeat(rest, repeats, axis=0)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.01)
    _, labels, centres = cv2.kmeans(samples, target_count - 1, None, criteria, 5, cv2.KMEANS_PP_CENTERS)
    mapping = [0]
    for colour in rest:
        mapping.append(1 + int(((centres - colour) ** 2).sum(1).argmin()))
    new_lab = np.vstack([keep_zero, centres])
    new_rgb = (np.clip(cv2.cvtColor(new_lab.reshape(1, -1, 3).astype(np.float32), cv2.COLOR_Lab2RGB)[0], 0, 1) * 255).round().astype(int)
    return new_rgb.tolist(), mapping


def build_description(trace, palette_count=24, epsilon_outline=1.2, epsilon_paint=1.5, min_area=12, drop_same_as_base=True):
    palette_rgb = [[c[2], c[1], c[0]] for c in trace['palette_bgr']]
    weights = np.zeros(len(palette_rgb))
    for patch in trace['patches']:
        weights[patch['c']] += patch['area']
    weights[0] += 1e6
    new_palette, mapping = reduce_palette(palette_rgb, weights, palette_count)
    slates = []
    for slate in trace['slates']:
        slates.append({'id': slate['id'], 'o': delta_encode(simplify(slate['outline'], epsilon_outline).tolist())})
    # base colour of each slate = the colour covering the most dots
    cover = {}
    for patch in trace['patches']:
        cover.setdefault(patch['slate'], {}).setdefault(mapping[patch['c']], 0)
        cover[patch['slate']][mapping[patch['c']]] += patch['area']
    for slate in slates:
        table = cover.get(slate['id'], {1: 1})
        slate['c'] = int(max(table, key=table.get))
    patches = []
    for patch in sorted(trace['patches'], key=lambda p: -p['filled']):
        if patch['area'] < min_area:
            continue
        colour = mapping[patch['c']]
        base = next((s['c'] for s in slates if s['id'] == patch['slate']), None)
        if drop_same_as_base and colour == base and patch['area'] > 0 and len(patch['p']) <= 4 and False:
            continue
        patches.append([int(colour), delta_encode(simplify(patch['p'], epsilon_paint).tolist())])
    return {'format': 'slate_painter_1', 'tile': TILE, 'palette': new_palette, 'gap': 0,
            'slates': [{'o': s['o'], 'c': s['c']} for s in slates], 'patches': patches}


def layout_block(trace, layout_fit, palette_mapping, corner=8.0, seed=1):
    """The 'layout' block of a description: rows of slates (edges, leans, top and bottom shifts) and the base colour of each slate."""
    cover = {}
    for patch in trace['patches']:
        cover.setdefault(patch['slate'], {}).setdefault(palette_mapping[patch['c']], 0)
        cover[patch['slate']][palette_mapping[patch['c']]] += patch['area']
    # match each fitted slate to the traced slate with the nearest centre, to read off its base colour
    traced = [(s['id'], s['centre']) for s in trace['slates']]
    rows = []
    for row in layout_fit['rows']:
        colours = []
        for entry in row['slates']:
            cx, cy = 0.5 * (entry[0] + entry[1]), 0.5 * (row['top'] + row['bottom'])
            best = min(traced, key=lambda t: (((t[1][0] - cx + TILE / 2) % TILE - TILE / 2) ** 2 + ((t[1][1] - cy + TILE / 2) % TILE - TILE / 2) ** 2))
            table = cover.get(best[0], {1: 1})
            colours.append(int(max(table, key=table.get)))
        rows.append({'top': row['top'], 'bottom': row['bottom'], 'joints': row['joints'], 'top_shift': [round(v, 1) for v in row['top_shift']],
                     'bottom_shift': [round(v, 1) for v in row['bottom_shift']], 'colour': colours})
    stats = layout_fit['stats']
    return {'rows': rows, 'corner': corner, 'rough': {'top': round(stats['rag_top'], 2), 'bottom': round(stats['rag_bottom'], 2), 'side': round(stats['rag_side'], 2), 'scale': 14.0}, 'seed': seed}


def draw_description(description, size=TILE, scale=4):
    """The quick numpy painter: gap colour everywhere, then slates, then patches (each polygon drawn also shifted by +-1 tile so it wraps)."""
    palette = np.array(description['palette'], np.uint8)[:, ::-1]      # to BGR for opencv
    factor = size / description['tile'] * scale
    big = size * scale
    canvas = np.zeros((big, big, 3), np.uint8)
    canvas[:] = palette[description['gap']]
    tile = description['tile']

    def polygon(flat):
        return np.array(delta_decode(flat), np.float64)

    def draw(points, colour):
        low, high = points.min(axis=0), points.max(axis=0)
        for shift_x in (-tile, 0, tile):
            if high[0] + shift_x < 0 or low[0] + shift_x >= tile:
                continue
            for shift_y in (-tile, 0, tile):
                if high[1] + shift_y < 0 or low[1] + shift_y >= tile:
                    continue
                moved = (points + [shift_x, shift_y] + 0.5) * factor
                cv2.fillPoly(canvas, [moved.round().astype(np.int32)], tuple(int(v) for v in colour), lineType=cv2.LINE_8)

    for slate in description['slates']:
        draw(polygon(slate['o']), palette[slate['c']])
    for patch in description['patches']:
        draw(polygon(patch[1]), palette[patch[0]])
    return cv2.resize(canvas, (size, size), interpolation=cv2.INTER_AREA)


def quick_score(picture_bgr):
    import pixel_compare as pc
    ref = cv2.imread(os.path.join(PROC, 'reference', 'slate', 'colour.png')).astype(np.float64)
    cand = picture_bgr.astype(np.float64)
    grey = lambda x: cv2.cvtColor(np.clip(x, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
    ssim = pc.ssim(grey(ref), grey(cand))
    lab_ref = pc.tc.srgb_to_lab(ref[..., ::-1] / 255.0)
    lab_cand = pc.tc.srgb_to_lab(cand[..., ::-1] / 255.0)
    de = float(np.sqrt(((lab_ref - lab_cand) ** 2).sum(-1)).mean())
    return round(ssim, 3), round(de, 2)


if __name__ == '__main__':
    trace = json.load(open(os.path.join(HERE, 'trace_full.json')))
    rows = []
    for palette_count in (24, 16, 10):
        for eo, ep, ma in ((1.2, 1.5, 12), (2.0, 2.5, 30), (3.0, 3.5, 80), (4.0, 5.0, 250)):
            d = build_description(trace, palette_count, eo, ep, ma)
            text = json.dumps(d, separators=(',', ':'))
            picture = draw_description(d)
            ssim, de = quick_score(picture)
            row = dict(palette=palette_count, eps_outline=eo, eps_paint=ep, min_area=ma, patches=len(d['patches']), kilobytes=round(len(text) / 1024, 1), ssim=ssim, delta_e=de)
            print(row, flush=True)
            rows.append(row)
    json.dump(rows, open(os.path.join(HERE, 'describe_experiment.json'), 'w'), indent=1)

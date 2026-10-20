# What this does (plain words): ANALYSIS. Measures how the paint patches sit on the slates and writes a small "paint model" (analysis/paint_model.json)
# that the generator's stamp scatter can use to paint NEW slates: for six size classes of patch (tiny specks ... big areas) how much of a slate
# each class covers, how wide and tall its patches are, which colour family (blue-grey, olive moss, tan lichen, black) it uses and how that
# changes from the top of the slate to the bottom, how much lighter or darker than the slate's own average tone it is; plus, per slate, its
# average tone, its moss share and its lichen share (the per-slate numbers the generator needs to reproduce THIS slate). Plain Python (python3 -I).
import colorsys
import json
import os

import sys
import numpy as np
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'generator')))
import slate_layers as sl

HERE = os.path.dirname(os.path.abspath(__file__))
TILE = 1254
BANDS = [(12, 30), (30, 100), (100, 300), (300, 1000), (1000, 3000), (3000, 1e9)]     # patch area classes, in dots
FAMILIES = ['blue', 'olive', 'tan', 'black']
Y_BINS = 6


def family_of(rgb):
    r, g, b = [c / 255.0 for c in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    grey = 255 * (0.299 * r + 0.587 * g + 0.114 * b)
    hue, chroma = h * 360, (max(r, g, b) - min(r, g, b)) * 255
    if grey < 26:
        return 'black'
    if chroma > 8 and 55 <= hue <= 140:
        return 'olive'
    if chroma > 8 and 15 <= hue < 55:
        return 'tan'
    return 'blue'


def locate(patch_centre, layout):
    """Which fitted slate (row, index) a point lies in, with wrap-around in both directions; returns (row, slate, x_rel, y_rel) or None."""
    x, y = patch_centre
    for row in layout['rows']:
        for shift_y in (-TILE, 0, TILE):
            if row['top'] - 2 <= y + shift_y <= row['bottom'] + 2:
                for index, slate in enumerate(row['slates']):
                    for shift_x in (-TILE, 0, TILE):
                        if slate[0] - 2 <= x + shift_x <= slate[1] + 2:
                            return (row, index, (x + shift_x - slate[0]) / max(slate[1] - slate[0], 1), (y + shift_y - row['top']) / (row['bottom'] - row['top']))
    return None


def fit():
    trace = json.load(open(os.path.join(HERE, 'trace_full.json')))
    layout = json.load(open(os.path.join(HERE, 'layout_fit.json')))
    palette = [[c[2], c[1], c[0]] for c in trace['palette_bgr']]
    grey = np.array([0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in palette])
    family = [family_of(c) for c in palette]
    records = []
    for patch in trace['patches']:
        x, y, w, h = patch['bbox']
        placed = locate((x + w / 2.0, y + h / 2.0), layout)
        if placed is None:
            continue
        row, index, x_rel, y_rel = placed
        records.append({'row': layout['rows'].index(row), 'slate': index, 'x_rel': float(np.clip(x_rel, 0, 1)), 'y_rel': float(np.clip(y_rel, 0, 0.999)), 'w': w, 'h': h,
                        'area': patch['area'], 'colour': patch['c'], 'grey': grey[patch['c']], 'family': family[patch['c']]})
    print('patches placed on a fitted slate:', len(records), 'of', len(trace['patches']))
    slate_area = {}
    for r_index, row in enumerate(layout['rows']):
        for s_index, slate in enumerate(row['slates']):
            slate_area[(r_index, s_index)] = (slate[1] - slate[0]) * (row['bottom'] - row['top'])
    # per-slate numbers
    per_slate = {}
    for rec in records:
        per_slate.setdefault((rec['row'], rec['slate']), []).append(rec)
    slate_params = {}
    for key, recs in per_slate.items():
        area = np.array([r['area'] for r in recs], float)
        total = area.sum()
        g = np.array([r['grey'] for r in recs])
        fam = np.array([r['family'] for r in recs])
        slate_params[key] = {'tone': float((g * area).sum() / total), 'olive': float(area[fam == 'olive'].sum() / total), 'tan': float(area[fam == 'tan'].sum() / total),
                             'black': float(area[fam == 'black'].sum() / total)}
    model = {'bands': [[lo, min(hi, 1e6)] for lo, hi in BANDS], 'families': FAMILIES, 'y_bins': Y_BINS}
    all_area = sum(slate_area.values())
    band_info = []
    family_by_y = np.zeros((len(BANDS), Y_BINS, len(FAMILIES)))
    for b, (lo, hi) in enumerate(BANDS):
        sel = [r for r in records if lo <= r['area'] < hi]
        area = np.array([r['area'] for r in sel], float)
        w = np.array([r['w'] for r in sel], float)
        h = np.array([r['h'] for r in sel], float)
        coverage = area.sum() / all_area
        # stamp bounding-box size: log-normal, with width and height correlated
        lw, lh = np.log(np.maximum(w, 2)), np.log(np.maximum(h, 2))
        corr = float(np.corrcoef(lw, lh)[0, 1])
        # tone of blue patches relative to the slate's average
        deltas = [r['grey'] - slate_params[(r['row'], r['slate'])]['tone'] for r in sel if r['family'] == 'blue']
        info = {'count_per_1000_area': round(1000.0 * len(sel) / all_area, 4), 'coverage': round(coverage, 4), 'log_w': [round(float(lw.mean()), 3), round(float(lw.std()), 3)],
                'log_h': [round(float(lh.mean()), 3), round(float(lh.std()), 3)], 'log_corr': round(corr, 3), 'tone_delta': [round(float(np.mean(deltas)), 2), round(float(np.std(deltas)), 2)],
                'area_mean': round(float(area.mean()), 1)}
        band_info.append(info)
        for r in sel:
            family_by_y[b, int(r['y_rel'] * Y_BINS), FAMILIES.index(r['family'])] += r['area']
    # tone offset of blue patches by y bin (a dark shadow at the top, light chips at the bottom), then the spread that is left over
    y_tone = []
    for yb in range(Y_BINS):
        d = [r['grey'] - slate_params[(r['row'], r['slate'])]['tone'] for r in records if r['family'] == 'blue' and int(r['y_rel'] * Y_BINS) == yb]
        y_tone.append(round(float(np.mean(d)), 2))
    model['tone_by_y'] = y_tone
    for b, (lo, hi) in enumerate(BANDS):
        residual = [r['grey'] - slate_params[(r['row'], r['slate'])]['tone'] - y_tone[int(r['y_rel'] * Y_BINS)] for r in records if lo <= r['area'] < hi and r['family'] == 'blue']
        band_info[b]['tone_residual_std'] = round(float(np.std(residual)), 2)
    model['band'] = band_info
    # where in the slate (top to bottom, 6 slices) the patches of each size class sit (count share)
    y_hist = np.zeros((len(BANDS), Y_BINS))
    for r in records:
        for b, (lo, hi) in enumerate(BANDS):
            if lo <= r['area'] < hi:
                y_hist[b, int(r['y_rel'] * Y_BINS)] += 1
    model['y_hist'] = np.round(y_hist / y_hist.sum(axis=1, keepdims=True), 3).tolist()
    colour_area = np.zeros(len(palette))
    for r in records:
        colour_area[r['colour']] += r['area']
    model['colour_weight'] = [round(float(v / colour_area.sum()), 4) for v in colour_area]
    # family mix by band and y bin (area-weighted)
    sums = family_by_y.sum(axis=2, keepdims=True)
    model['family_by_y'] = np.round(family_by_y / np.maximum(sums, 1), 3).tolist()
    # colours of each family, sorted by brightness (the generator picks the one nearest the wanted tone)
    model['family_colours'] = {f: sorted([i for i in range(len(palette)) if family[i] == f], key=lambda i: grey[i]) for f in FAMILIES}
    # per-slate parameters (rows x slates) for reproducing the reference, and their spread for inventing new slates
    model['slates'] = [[[round(slate_params[(r, s)]['tone'], 1), round(slate_params[(r, s)]['olive'], 3), round(slate_params[(r, s)]['tan'], 3)]
                        for s in range(len(layout['rows'][r]['slates']))] for r in range(len(layout['rows']))]
    allp = np.array([v for v in slate_params.values()] and [[v['tone'], v['olive'], v['tan']] for v in slate_params.values()])
    model['slate_spread'] = {'tone': [round(float(allp[:, 0].mean()), 2), round(float(allp[:, 0].std()), 2)],
                             'olive': [round(float(allp[:, 1].mean()), 3), round(float(allp[:, 1].std()), 3)], 'tan': [round(float(allp[:, 2].mean()), 3), round(float(allp[:, 2].std()), 3)]}
    return model, records


if __name__ == '__main__':
    model, records = fit()
    json.dump(model, open(os.path.join(HERE, 'paint_model.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in model.items() if k not in ('slates', 'family_by_y')}, indent=1)[:3500])
    print('family by y (band 3):', model['family_by_y'][3])

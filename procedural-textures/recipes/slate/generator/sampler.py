# What this does (plain words): INVENTS a new slate roof. sample_description(seed) draws a new layout (how tall each row is, where every joint between
# slates sits, how it leans, how ragged the slate edges are) and new per-slate paint settings (how light or dark each slate is, how mossy, how much
# lichen) from the spreads measured on the reference (fitted_distributions.json), and returns a complete description of the same form as the
# fitted one, ready for slate_generator.py. A bigger tile (tile=2508) gives a bigger roof of new unique content with more rows and more slates.
# Plain Python (numpy only). It never reads the reference picture.
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FITTED = json.load(open(os.path.join(HERE, 'fitted_distributions.json')))


def sample_description(seed, tile=None, rows=None, overrides=None, fitted=None):
    """fitted: another set of fitted numbers (same form as fitted_distributions.json) for a different kind of roof; default = the slate fit."""
    rng = np.random.default_rng(seed)
    f = fitted or FITTED
    tile = int(tile or f['tile'])
    scale = tile / f['tile']
    n_rows = int(rows or round(f['rows_per_tile'] * scale))
    slates_per_row = int(round(f['slates_per_row'] * scale))
    # rows: heights and gaps drawn, then stretched a little so that the rows exactly fill one tile (the tile must repeat)
    heights = np.clip(rng.normal(f['row_height'][0], f['row_height'][1], n_rows), 128, 170)
    gaps = np.clip(rng.normal(f['row_gap'][0], f['row_gap'][1], n_rows), 9, 12.5)
    stretch = (tile - gaps.sum()) / heights.sum()
    heights = heights * stretch
    top = -0.5 * heights[0] + rng.uniform(-12, 12)               # the tile edge runs through the middle of a row of slates, not along a joint
    spare = f['paint_model']['family_colours']['blue']
    palette_grey = [0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2] for c in f['palette']]
    pool = np.array(f['slate_pool'])                                  # (tone, olive, tan) of the fitted slates
    layout_rows, tones = [], []
    y = top
    for r in range(n_rows):
        widths = np.exp(rng.normal(f['width_log'][0], f['width_log'][1], slates_per_row))
        widths = widths * tile / widths.sum()                         # the slates of a row exactly fill the tile width
        phase = rng.uniform(0, tile) if f.get('phase_mode', 'random') == 'random' else (0.5 * (tile / slates_per_row) * (r % 2) + rng.uniform(-1.5, 1.5))
        edges = phase + np.cumsum(widths)
        joints = [[round(float(x), 1), round(float(np.clip(rng.normal(*f['joint_lean']), -0.06, 0.06)), 3), round(float(np.clip(rng.normal(*f['joint_gap']), 2.0, 9.0)), 1)] for x in edges]
        tone_row, colours = [], []
        for _ in range(slates_per_row):
            pick = pool[rng.integers(len(pool))]
            tone = float(rng.normal(f['paint_model']['slate_spread']['tone'][0], f['paint_model']['slate_spread']['tone'][1]))
            olive = float(np.clip(pick[1] * np.exp(rng.normal(0, 0.3)), 0, 0.6))
            tan = float(np.clip(pick[2] * np.exp(rng.normal(0, 0.3)), 0, 0.4))
            tone_row.append([round(tone, 1), round(olive, 3), round(tan, 3)])
            colours.append(int(min(spare, key=lambda i: abs(palette_grey[i] - tone))))
        layout_rows.append({'top': round(float(y), 1), 'bottom': round(float(y + heights[r]), 1), 'joints': joints,
                            'top_shift': [round(float(v), 1) for v in rng.normal(0, f['top_shift_std'], slates_per_row)],
                            'bottom_shift': [round(float(v), 1) for v in rng.normal(0, f['bottom_shift_std'], slates_per_row)], 'colour': colours})
        tones.append(tone_row)
        y += heights[r] + gaps[r]
    paint_model = dict(f['paint_model'])
    description = {'format': 'slate_painter_1', 'tile': tile, 'palette': f['palette'], 'gap': f['gap'], 'grow': 0.5, 'maps': f['maps'], 'roughness': f['roughness'],
                   'layout': {'rows': layout_rows, 'corner': f['corner'], 'rough': f['rough'], 'seed': int(rng.integers(1, 10 ** 6)), 'bottom_round': f.get('bottom_round', 0.0)},
                   'paint': {'model': paint_model, 'slates': tones, 'seed': int(rng.integers(1, 10 ** 6)), **f['paint_settings']}}
    description['paint']['model'] = dict(paint_model)
    if overrides:
        for key, value in overrides.items():
            description[key] = value
    return description


if __name__ == '__main__':
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    tile = int(sys.argv[2]) if len(sys.argv) > 2 else None
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, '..', 'description', f'sample_{seed}.json')
    d = sample_description(seed, tile)
    json.dump(d, open(out, 'w'), separators=(',', ':'))
    print(out, os.path.getsize(out), 'bytes')

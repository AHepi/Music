# What this does (plain words): cuts the big trace of the reference into description files of different sizes, adds the map settings
# (the height stretch and the normal strength found in derivation_ceiling.py) and a roughness for each palette colour, and checks each file
# with description_audit.py. Output goes to ../description/. Analysis side (plain Python, python3 -I).
import colorsys
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import describe_tools as dt  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, '..', 'description'))


def roughness_for(rgb):
    """A plausible roughness for a palette colour (the reference has no roughness map; this is a documented choice, not a measurement)."""
    r, g, b = [c / 255.0 for c in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    grey = 255 * (0.299 * r + 0.587 * g + 0.114 * b)
    hue = h * 360
    chroma = max(r, g, b) - min(r, g, b)
    if grey < 22:
        return 0.92                       # black joint: dusty
    if chroma * 255 > 8 and 55 <= hue <= 120:
        return 0.95                       # olive moss: soft, matt
    if chroma * 255 > 8 and 15 <= hue < 55:
        return 0.90                       # tan lichen / bare chip: matt
    return round(0.45 + 0.40 * float(np.clip((grey - 35) / 60.0, 0, 1)), 2)   # blue-grey slate: darker = wetter = smoother


def finish(description, height_blur=0.5):
    description['grow'] = 0.5
    description['maps'] = {'height': {'grey_low': 9.5, 'grey_high': 111.5, 'blur': height_blur}, 'normal': {'strength': 7}}
    description['roughness'] = [roughness_for(c) for c in description['palette']]
    return description


def write(description, name):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, 'w') as handle:
        json.dump(description, handle, separators=(',', ':'))
    audit = subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', 'description_audit.py'), path, '--limit-kilobytes', '512'], capture_output=True, text=True)
    print(name, os.path.getsize(path), 'bytes;', audit.stdout.strip().replace('\n', ' ')[:300])
    return path


def layout_only_description(trace, palette_count=24):
    """Class S0: just the layout block (rows of slates drawn with procedural ragged outlines), one flat colour per slate, black joints."""
    full = dt.build_description(trace, palette_count, 4.0, 5.0, 100000)       # (no patches: used only for the palette and the colour mapping)
    layout_fit = json.load(open(os.path.join(HERE, 'layout_fit.json')))
    palette_rgb = [[c[2], c[1], c[0]] for c in trace['palette_bgr']]
    weights = np.zeros(len(palette_rgb))
    for patch in trace['patches']:
        weights[patch['c']] += patch['area']
    weights[0] += 1e6
    _, mapping = dt.reduce_palette(palette_rgb, weights, palette_count)
    d = {'format': 'slate_painter_1', 'tile': dt.TILE, 'palette': full['palette'], 'gap': 0, 'layout': dt.layout_block(trace, layout_fit, mapping)}
    return d


if __name__ == '__main__':
    trace = json.load(open(os.path.join(HERE, 'trace_full.json')))
    settings = {
        'L_trace_fine': dict(palette_count=24, epsilon_outline=1.2, epsilon_paint=1.5, min_area=12),
        'L_trace_medium': dict(palette_count=24, epsilon_outline=2.0, epsilon_paint=2.5, min_area=30),
        'M_trace_coarse': dict(palette_count=16, epsilon_outline=3.0, epsilon_paint=4.0, min_area=520),
        'L_trace_small': dict(palette_count=24, epsilon_outline=2.5, epsilon_paint=3.0, min_area=100),
        'M_trace_small': dict(palette_count=12, epsilon_outline=4.0, epsilon_paint=5.0, min_area=900),
        'M_trace_tiny': dict(palette_count=8, epsilon_outline=5.0, epsilon_paint=7.0, min_area=2500),
    }
    write(finish(layout_only_description(trace)), 'S0_layout_only.json')
    for name, kwargs in settings.items():
        write(finish(dt.build_description(trace, **kwargs)), name + '.json')

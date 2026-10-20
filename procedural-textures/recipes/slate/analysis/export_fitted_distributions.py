# What this does (plain words): gathers the numbers the SAMPLER needs to invent new slate roofs (how tall the rows are, how wide the slates are, how
# much the joints lean, how the moss and lichen are spread, the paint model and the palette) into one small file next to the generator
# (generator/fitted_distributions.json). The sampler reads only this file, never the reference picture. Plain Python (python3 -I).
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SLATE = os.path.abspath(os.path.join(HERE, '..'))
layout = json.load(open(os.path.join(HERE, 'layout_fit.json')))
model = json.load(open(os.path.join(HERE, 'paint_model.json')))
base = json.load(open(os.path.join(SLATE, 'description', 'S1_layout_stamps.json')))
tops = [v for r in layout['rows'] for v in r['top_shift']]
bottoms = [v for r in layout['rows'] for v in r['bottom_shift']]
leans = [j[1] for r in layout['rows'] for j in r['joints']]
gaps = [j[2] for r in layout['rows'] for j in r['joints']]
stats = layout['stats']
export = {
    'tile': 1254,
    'rows_per_tile': 8, 'slates_per_row': 6,
    'row_height': stats['row_height'], 'row_gap': stats['gap_between_rows'],
    'width_log': [stats['width_log_mean'], stats['width_log_std']],
    'joint_lean': [float(np.mean(leans)), float(np.std(leans))], 'joint_gap': [float(np.mean(gaps)), float(np.std(gaps))],
    'top_shift_std': float(np.std(tops)), 'bottom_shift_std': float(np.std(bottoms)),
    'rough': base['layout']['rough'], 'corner': base['layout']['corner'],
    'slate_pool': [v for row in model['slates'] for v in row],           # (tone, olive share, tan share) of the 48 fitted slates
    'palette': base['palette'], 'roughness': base['roughness'], 'maps': json.load(open(os.path.join(SLATE, 'description', 'S2_stamps_grain.json')))['maps'], 'gap': base['gap'],
    'paint_model': base['paint']['model'],
    'paint_settings': {k: v for k, v in base['paint'].items() if k not in ('model', 'slates', 'seed')},
}
json.dump(export, open(os.path.join(SLATE, 'generator', 'fitted_distributions.json'), 'w'), separators=(',', ':'))
print('written', os.path.getsize(os.path.join(SLATE, 'generator', 'fitted_distributions.json')), 'bytes')

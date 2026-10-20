# What this does (plain words): makes NEW gravel descriptions. sample_description(seed) starts from the fitted procedural description (soil recipe + stone
# recipe) and changes it a little in the ways the reference itself varies from place to place: how many stones of each size, how tightly they are
# packed, how the colours are mixed, the soil clod counts, the tone of every colour, a new random seed. The size of each change is taken from
# scores/window_spread.json (how much 418-dot windows of the reference differ from each other: stone share 4.5 %, big stone share 7.4 %, soil clumps
# 14 %). Because the stone and soil blocks only hold numbers and a seed, every call gives a different, equally plausible tile.
# area=2 makes a description for a picture 2 x 2 tiles big (2508 dots) with 4 times the stones and soil lumps (new unique content, no copies).
# Plain Python, no Blender. Use:  python3 -I sampler.py BASE.json OUT_FOLDER N_SAMPLES [first_seed] [area]
import copy
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def sample_description(seed, base, area=1, spread=None):
    rng = np.random.default_rng(1000 + int(seed))
    d = copy.deepcopy(base)
    spread = spread or {'count': 0.07, 'radius': 0.05, 'spacing': 0.03, 'weights': 0.18, 'tone': 2.0, 'soil_count': 0.12, 'rust': 0.03}
    d['tile'] = int(round(base['tile'] * area))
    area_factor = float(area) ** 2
    stones = d['stones']
    stones['seed'] = int(rng.integers(1, 10 ** 6))
    for cls in stones['classes']:
        cls['count'] = int(round(cls['count'] * area_factor * float(np.exp(rng.normal(0, spread['count'])))))
        scale = float(np.exp(rng.normal(0, spread['radius'])))
        cls['radius'] = [round(cls['radius'][0] * scale, 2), round(cls['radius'][1] * scale, 2)]
        cls['spacing'] = round(float(np.clip(cls.get('spacing', 0.8) + rng.normal(0, spread['spacing']), 0.45, 1.0)), 3)
        w = np.asarray(cls['weights'], np.float64) * np.exp(rng.normal(0, spread['weights'], len(cls['weights'])))
        cls['weights'] = (w / w.sum()).round(4).tolist()
        cls['rust'] = round(float(np.clip(cls.get('rust', 0.1) + rng.normal(0, spread['rust']), 0.0, 0.4)), 3)
    stones['tones'] = np.clip(np.asarray(stones['tones'], np.float64) + rng.normal(0, spread['tone'], (len(stones['tones']), 3)), 0, 255).round().astype(int).tolist()
    soil = d['soil']
    soil['seed'] = int(rng.integers(1, 10 ** 6))
    for layer in soil['layers'] + soil.get('specks', []):
        layer['count'] = int(round(layer['count'] * area_factor * float(np.exp(rng.normal(0, spread['soil_count'])))))
    if 'weights' in soil['layers'][0]:
        w = np.asarray(soil['layers'][0]['weights'], np.float64) * np.exp(rng.normal(0, spread['weights'], len(soil['layers'][0]['weights'])))
        for layer in soil['layers']:
            layer['weights'] = (w / w.sum()).round(4).tolist()
    soil['tones'] = np.clip(np.asarray(soil['tones'], np.float64) + rng.normal(0, spread['tone'], (len(soil['tones']), 3)), 0, 255).round().astype(int).tolist()
    d['ground'] = soil['tones'][2]
    angle = float(rng.normal(0, 0.12))                       # the light direction wobbles a few degrees (0, -1 = from the top)
    d['light'] = [round(float(np.sin(angle)), 3), round(float(-np.cos(angle)), 3)]
    d['sample'] = {'seed': int(seed), 'area': area}
    return d


if __name__ == '__main__':
    base = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    n = int(sys.argv[3])
    first = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    area = float(sys.argv[5]) if len(sys.argv) > 5 else 1
    os.makedirs(out, exist_ok=True)
    spread_path = os.path.join(HERE, '..', 'scores', 'sampler_spread.json')
    spread = json.load(open(spread_path)) if os.path.exists(spread_path) else None
    for k in range(first, first + n):
        d = sample_description(k, base, area, spread)
        path = os.path.join(out, f'sample_{k:02d}.json')
        json.dump(d, open(path, 'w'), separators=(',', ':'))
        print(path, len(json.dumps(d, separators=(',', ':'))), 'bytes')

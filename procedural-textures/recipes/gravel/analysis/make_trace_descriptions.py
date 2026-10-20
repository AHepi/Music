# What this does (plain words): ANALYSIS script (reads the reference picture; the generator never does). It builds the TRACED gravel descriptions: the
# colour picture is snapped to a palette of k colours, cut into same-colour areas ("patches"), small ones dropped, and each remaining patch written as a
# simple outline (first corner, then small steps). The list is written big patches first. Several sizes of list are made (the smallest patch kept sets
# the size). This is the "tracing the picture" end of the ladder: it is reported as tracing, not as procedural.
# Use: python3 -I make_trace_descriptions.py   (writes description/T_*.json)
import json, os, sys, time
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import trace_tools as tt

OUT = os.path.join(HERE, '..', 'description')
bgr = tt.load_reference_colour()
variants = [('T_k24_a600', 24, 600, 2.0), ('TS_k24_a120', 24, 120, 1.6), ('TS_k24_a300', 24, 300, 1.8), ('TS_k24_a60', 24, 60, 1.4), ('T_k24_a250', 24, 250, 1.6), ('T_k24_a100', 24, 100, 1.4), ('T_k24_a50', 24, 50, 1.3), ('T_k24_a25', 24, 25, 1.2),
            ('T_k16_a100', 16, 100, 1.4), ('T_k12_a250', 12, 250, 1.6)]
if len(sys.argv) > 1:
    variants = [v for v in variants if v[0] in sys.argv[1:]]
cache = {}
for name, k, min_area, epsilon in variants:
    if k not in cache:
        centres = tt.make_palette(bgr, k)
        raw = tt.assign_labels(bgr, centres)
        cache[k] = (tt.palette_to_bgr(centres), tt.mode_filter(raw, k, 1))
    palette_bgr, filtered = cache[k]
    started = time.time()
    cleaned = tt.remove_small_areas(filtered, k, min_area)
    regions = tt.trace_regions(cleaned, k, epsilon, min_area)
    palette_rgb = palette_bgr[:, ::-1].astype(int).tolist()
    share = np.bincount(cleaned.ravel(), minlength=k)
    ground = palette_rgb[int(share.argmax())]
    patches = []
    stone_only = name.startswith('TS_')           # TS_ = trace only the STONE-coloured patches (soil is left to the soil recipe)
    for region in regions:
        if stone_only and (palette_rgb[region['c']][0] - palette_rgb[region['c']][2]) >= 14:
            continue
        pts = np.array(region['p'], dtype=int)
        steps = np.concatenate([pts[:1], np.diff(pts, axis=0)], axis=0)
        patches.append([region['c'], steps.ravel().tolist()])
    description = {'format': 'gravel_painter_1', 'tile': 1254, 'ground': ground, 'palette': palette_rgb, 'order': ['patches'], 'grow': 0.5,
                   'maps': {'height': {'mix': [267.15, 91.48, 210.5], 'offset': -17.7, 'blur': 0.5}, 'normal': {'strength': 10}}, 'patches': patches}
    if stone_only:
        base = json.load(open(os.path.join(OUT, 'S_first_guess.json')))
        description['ground'] = base['ground']
        description['soil'] = base['soil']
        description['stones'] = dict(base['stones'])
        description['stones']['classes'] = [dict(c, only_on='soil') for c in base['stones']['classes'][3:]]   # only the small pebbles, on soil
        description['order'] = ['soil', 'patches', 'stones']
        description['stamp_mask'] = {'default': True}
    text = json.dumps(description, separators=(',', ':'))
    open(os.path.join(OUT, name + '.json'), 'w').write(text)
    print(name, 'patches', len(patches), 'KB', round(len(text) / 1024, 1), 'seconds', round(time.time() - started, 1), flush=True)

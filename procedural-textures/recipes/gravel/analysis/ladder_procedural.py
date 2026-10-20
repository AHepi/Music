# What this does (plain words): the rate-distortion ladder of the PROCEDURAL gravel description: it adds the layers one at a time (ground colour; + soil lumps;
# + tiny soil specks; + the stone size classes from small to big; + facets and flaky patches) and for each stage reports the description size in bytes, the
# dot-for-dot scores against the reference (SSIM, Delta E, edge skill) and the "same kind of surface" score. It draws with OpenCV (no Blender) so it is quick;
# the real Blender bake of the full description is scored separately. Run: python3 -I ladder_procedural.py DESCRIPTION.json
import copy, json, os, subprocess, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
sys.path.insert(0, HERE)
import preview_tools as pt
import numpy_bake as nb
import tune_texture as tt_
base = json.load(open(sys.argv[1]))
stages = []
d = copy.deepcopy(base); d.pop('soil'); d.pop('stones'); stages.append(('0 ground colour only', d))
d1 = copy.deepcopy(base); d1.pop('stones'); d1['soil']['specks'] = []; stages.append(('1 + soil lumps', d1))
d2 = copy.deepcopy(base); d2.pop('stones'); stages.append(('2 + tiny soil specks', d2))
classes = base['stones']['classes']
for n, label in ((2, '3 + tiny and small stones'), (3, '4 + medium stones'), (4, '5 + large stones'), (5, '6 + biggest stones (all classes)')):
    d3 = copy.deepcopy(base); d3['stones']['classes'] = classes[::-1][:n] if n < 5 else classes
    stages.append((label, d3))
d4 = copy.deepcopy(base); d4['stones'].update({'facets': 0, 'mottle_per_radius': 0.0}); d4['stones']['rim'] = 0.0; d4['stones']['shadow'] = 0.0
stages.insert(len(stages) - 1, ('5b all stones but no shadow, rim, facets, flaky patches', d4))
rows = []
for name, desc in stages:
    r = tt_.evaluate(desc, 'ladder')
    folder = os.path.join(HERE, '..', 'scores', 'tmp_tune', 'ladder')
    import pixel_compare as pc
    p = pc.pixel_report('gravel', folder)
    rows.append({'stage': name, 'bytes': len(json.dumps(desc, separators=(',', ':'))), 'colour_ssim': round(p['colour_ssim'], 3), 'delta_e': round(p['colour_mean_delta_e'], 2), 'edge_skill': round(p['edge_skill_2px'], 3),
                 'texture_overall': r['overall'], 'texture_colour': r['colour'], 'texture_height': r['height'], 'texture_normal': r['normal'], 'shapes': r['shapes']})
    print(rows[-1], flush=True)
    cv2.imwrite(os.path.join(HERE, '..', 'scores', 'ladder_' + name.split()[0] + '.png'), cv2.resize(cv2.imread(os.path.join(folder, 'colour.png')), (400, 400), interpolation=cv2.INTER_AREA))
json.dump(rows, open(os.path.join(HERE, '..', 'scores', 'ladder_procedural.json'), 'w'), indent=1)

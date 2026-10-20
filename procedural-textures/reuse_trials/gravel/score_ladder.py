# What this does (plain words): the "what each layer adds" ladder of the gravel trial. run_views.py baked four partial recipes at 1254 dots (the layout
# is always there): 1 = COLOUR AND FADE only, 2 = + OUTLINE AND SHADOW (which paints the soil's flat colour), 3 = + DAMAGE, 4 = + FACETS. The fifth step,
# + SOIL, is the finished recipe (final/seeds_1). This script makes the normal map of each at strength 10, scores each against the gravel reference
# (lib/texture_compare.py, same-kind score, seed set 1), writes ladder/ladder_scores.json and draws ladder_strip.jpg (the same 300 x 300 dot
# corner of all five steps, enlarged, with scores). The big pictures are deleted after scoring to save disk (scores and the strip stay).
# Use: python3 -I score_ladder.py
import json
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
MAKE_NORMAL = os.path.join(PROC, 'recipes', 'slate_layers', 'integration', 'make_normal.py')
COMPARE = os.path.join(PROC, 'lib', 'texture_compare.py')
ladder = os.path.join(HERE, 'ladder')
steps = ['step_1_colour_and_fade_only', 'step_2_plus_outline_and_shadow', 'step_3_plus_damage', 'step_4_plus_facets']
results, crops = {}, []
for name in steps:
    folder = os.path.join(ladder, name + '_set')
    os.makedirs(folder, exist_ok=True)
    shutil.copyfile(os.path.join(ladder, name + '_colour.png'), os.path.join(folder, 'colour.png'))
    shutil.copyfile(os.path.join(ladder, name + '_height.png'), os.path.join(folder, 'height.png'))
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(folder, 'height.png'), os.path.join(folder, 'normal.png'), '10'], check=True)
    subprocess.run([sys.executable, '-I', COMPARE, 'gravel', folder, '--json', os.path.join(folder, 'score.json')], check=True, stdout=subprocess.DEVNULL)
    report = json.load(open(os.path.join(folder, 'score.json')))
    results[name] = {'overall': report['overall'], **report['groups']}
    crops.append((name, cv2.imread(os.path.join(folder, 'colour.png'))[300:600, 300:600]))
final = json.load(open(os.path.join(HERE, 'final_scores.json')))['table']['seeds_1']
results['step_5_plus_soil (the finished recipe)'] = final
crops.append(('step_5_plus_soil', cv2.imread(os.path.join(HERE, 'final', 'seeds_1', 'colour.png'))[300:600, 300:600]))
cells = []
for (name, crop), key in zip(crops, results):
    cell = cv2.resize(crop, (360, 360), interpolation=cv2.INTER_NEAREST)
    row = results[key]
    for y, text in ((22, name.replace('step_', '').replace('_', ' ')), (344, f"same-kind {row['overall']:.3f}  colour {row['colour']:.3f}")):
        cv2.putText(cell, text, (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(cell, text, (6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    cells.append(cell)
cv2.imwrite(os.path.join(HERE, 'ladder_strip.jpg'), np.hstack(cells), [cv2.IMWRITE_JPEG_QUALITY, 88])
with open(os.path.join(ladder, 'ladder_scores.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
for name in steps:
    shutil.rmtree(os.path.join(ladder, name + '_set'))
    os.remove(os.path.join(ladder, name + '_colour.png'))
    os.remove(os.path.join(ladder, name + '_height.png'))
for name, row in results.items():
    print(f"{name:45s} overall {row['overall']:.3f}  colour {row['colour']:.3f}  height {row['height']:.3f}  normal {row['normal']:.3f}")

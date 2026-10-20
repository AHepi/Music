# What this does (plain words): finds out how much of the finished height should come from the colour (the GRAVEL HEIGHT RULE) and how much from the
# real relief the layers make (COMBINE's own height: soil dips, stone domes). The recipe mixes the two with ONE straight-line setting
# (height_rule.blend: height = (1 - blend) x real relief + blend x colour rule), so ONE bake of each end is enough: this script mixes the two
# baked 16-bit height pictures for several blends, makes the normal map of each at strength 10, and scores each against the gravel reference with
# lib/texture_compare.py (same colour picture, so only the height and normal groups change). It also scores COMBINE's own colour-brightness rule
# (the slate rule, combine.tone_blend 1) when its picture is there. Scratch folders are deleted after scoring.
# Use: python3 -I score_height_blends.py ROUND_FOLDER COLOUR_PICTURE RULE_HEIGHT REAL_HEIGHT [COMBINE_RULE_HEIGHT]
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
BLENDS = [float(x) for x in os.environ.get('BLENDS', '0,0.3,0.5,0.7,0.85,1').split(',')]
round_folder, colour_path, rule_path, real_path = sys.argv[1:5]
combine_path = sys.argv[5] if len(sys.argv) > 5 else None
rule, real = (cv2.imread(p, cv2.IMREAD_UNCHANGED)[..., 0].astype(np.float64) for p in (rule_path, real_path))
options = {f'blend {b:.2f}': (1 - b) * real + b * rule for b in BLENDS}
if combine_path:
    options["COMBINE's own rule (tone_blend 1)"] = cv2.imread(combine_path, cv2.IMREAD_UNCHANGED)[..., 0].astype(np.float64)
results = {}
scratch = os.path.join(round_folder, 'blend_scratch')
for name, height in options.items():
    os.makedirs(scratch, exist_ok=True)
    shutil.copyfile(colour_path, os.path.join(scratch, 'colour.png'))
    cv2.imwrite(os.path.join(scratch, 'height.png'), np.clip(np.round(height), 0, 65535).astype(np.uint16))
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(scratch, 'height.png'), os.path.join(scratch, 'normal.png'), '10'], check=True)
    subprocess.run([sys.executable, '-I', COMPARE, 'gravel', scratch, '--json', os.path.join(scratch, 'score.json')], check=True, stdout=subprocess.DEVNULL)
    report = json.load(open(os.path.join(scratch, 'score.json')))
    results[name] = {'overall': report['overall'], **report['groups']}
    print(f"{name:40s} overall {report['overall']:.3f}  colour {report['groups']['colour']:.3f}  height {report['groups']['height']:.3f}  normal {report['groups']['normal']:.3f}", flush=True)
    shutil.rmtree(scratch)
with open(os.path.join(round_folder, 'height_blend_scores.json'), 'w') as handle:
    json.dump(results, handle, indent=1)

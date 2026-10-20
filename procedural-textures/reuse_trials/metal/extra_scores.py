# What this does (plain words): DIAGNOSTIC scores, not part of the trial's main result. It answers one question: "how much of the height
# and normal score the layered tile loses is only because a shader cannot blur?" The metal reference's height picture was made from its
# colour and then blurred a little (about 0.7 of a dot). A shader sees one dot at a time and cannot blur, so the layered tile's height
# follows its colour TOO exactly (correlation 0.997 against the reference's 0.968).
# For each final tile (final/seeds_1..3) this script takes the saved 16-bit height, blurs it by 0.7 and by 1.0 dot (a Gaussian blur done
# AFTER baking, in Python, wrapping round the tile edge), makes the normal from the blurred height with make_normal.py at strength 5, and
# scores it against the metal reference with lib/texture_compare.py. The colour picture is unchanged. It also scores the same tile with a
# second height (final_extra/<set>_combine_height_rule/height.png) when that file exists (made by final_bake.py with
# recipe.height_rule = combine: COMBINE's own height rule, which is slate's, not metal's).
# It works in a temporary folder outside this trial folder and keeps only numbers: extra_scores.json.
# Use: python3 -I extra_scores.py TEMP_FOLDER
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
temp = sys.argv[1]
os.makedirs(temp, exist_ok=True)
results = {}


def score(height16, colour_path, label):
    cv2.imwrite(os.path.join(temp, 'height.png'), height16)
    shutil.copyfile(colour_path, os.path.join(temp, 'colour.png'))
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(temp, 'height.png'), os.path.join(temp, 'normal.png'), '5'], check=True)
    subprocess.run([sys.executable, '-I', COMPARE, 'metal', temp, '--json', os.path.join(temp, 'score.json')], check=True, stdout=subprocess.DEVNULL)
    with open(os.path.join(temp, 'score.json')) as handle:
        report = json.load(handle)
    results[label] = {'overall': report['overall'], **report['groups'], 'scores': report['scores'], 'facts': {
        'height_colour_corr_candidate': report['facts']['height_colour_corr_candidate'],
        'normal_height_corr_candidate': report['facts']['normal_height_corr_candidate']}}
    print(f"{label:60s} overall {report['overall']:.3f} colour {report['groups']['colour']:.3f} height {report['groups']['height']:.3f} normal {report['groups']['normal']:.3f}", flush=True)


for name in ('seeds_1', 'seeds_2', 'seeds_3', 'seeds_4'):
    folder = os.path.join(HERE, 'final', name)
    colour_path = os.path.join(folder, 'colour.png')
    height = cv2.imread(os.path.join(folder, 'height.png'), cv2.IMREAD_UNCHANGED)
    height = height[..., 0] if height.ndim == 3 else height
    for sigma in (0.7, 1.0):
        padded = np.pad(height.astype(np.float64), 8, mode='wrap')
        blurred = cv2.GaussianBlur(padded, (0, 0), sigma)[8:-8, 8:-8]
        score(np.clip(blurred.round(), 0, 65535).astype(np.uint16), colour_path, f'{name}, height blurred by {sigma} dot after baking (diagnostic)')
    extra = os.path.join(HERE, 'final_extra', f'{name}_combine_height_rule', 'height.png')
    if os.path.exists(extra):
        other = cv2.imread(extra, cv2.IMREAD_UNCHANGED)
        score(other[..., 0] if other.ndim == 3 else other, colour_path, f'{name}, height by COMBINE\'s own rule (slate\'s)')
shutil.rmtree(temp)
with open(os.path.join(HERE, 'extra_scores.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
print('wrote extra_scores.json')

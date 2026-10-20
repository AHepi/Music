# What this does (plain words): the like-for-like scores of the metal trial (the same idea as the brick trial's final_scores.py).
#   1. For every baked set in ROOT (made by final_bake.py at 1254 dots) it makes the normal map from the 16-bit height with
#      recipes/slate_layers/integration/make_normal.py at the metal reference strength 5, then scores the set against the metal reference with
#      lib/texture_compare.py (the "same kind" score: overall, and the colour, height, normal and tiling groups) and keeps the report as score.json.
#      A set folder that holds a second height (height_<name>.png, for example height_combine_rule.png) is scored a second time with that height.
#   2. With --baseline: THE BASELINE, scored the same way: the metal's own earlier small recipe, first new tile (recipes/metal/variations/seed_1,
#      1254 dots). It is scored twice: as stored (its own normal map), and with its normal remade from its height by the same make_normal.py at
#      strength 5 (copied into baseline_seed_1/ here; the original folder is not touched), so the normal-making is the same as the trial's.
#   3. Writes OUT_JSON with a small table and the full reports, and prints the table.
# Use: python3 -I final_scores.py ROOT OUT_JSON [--baseline]
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
MAKE_NORMAL = os.path.join(PROC, 'recipes', 'slate_layers', 'integration', 'make_normal.py')
COMPARE = os.path.join(PROC, 'lib', 'texture_compare.py')
STRENGTH = '5'
root, out_json = sys.argv[1], sys.argv[2]


def score(folder, name='score.json'):
    out = os.path.join(folder, name)
    subprocess.run([sys.executable, '-I', COMPARE, 'metal', folder, '--json', out], check=True, stdout=subprocess.DEVNULL)
    with open(out) as handle:
        return json.load(handle)


results = {}
for folder in sorted(glob.glob(os.path.join(root, '*'))):
    if not os.path.exists(os.path.join(folder, 'height.png')) or not os.path.exists(os.path.join(folder, 'colour.png')):
        continue
    name = os.path.basename(folder)
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(folder, 'height.png'), os.path.join(folder, 'normal.png'), STRENGTH], check=True)
    results[name] = score(folder)
    for other in sorted(glob.glob(os.path.join(folder, 'height_*.png'))):          # a second height made by another rule: score it in a side folder
        rule = os.path.basename(other)[len('height_'):-len('.png')]
        side = os.path.join(folder, 'with_' + rule)
        os.makedirs(side, exist_ok=True)
        shutil.copyfile(os.path.join(folder, 'colour.png'), os.path.join(side, 'colour.png'))
        shutil.copyfile(other, os.path.join(side, 'height.png'))
        subprocess.run([sys.executable, '-I', MAKE_NORMAL, other, os.path.join(side, 'normal.png'), STRENGTH], check=True)
        results[f'{name}, height by {rule}'] = score(side)
        for file_name in ('colour.png', 'height.png', 'normal.png'):                 # keep only the score (disk is tight)
            os.remove(os.path.join(side, file_name))
if '--baseline' in sys.argv:
    original = os.path.join(PROC, 'recipes', 'metal', 'variations', 'seed_1')
    copy = os.path.join(HERE, 'baseline_seed_1')
    os.makedirs(copy, exist_ok=True)
    for file_name in ('colour.png', 'height.png'):
        shutil.copyfile(os.path.join(original, file_name), os.path.join(copy, file_name))
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(copy, 'height.png'), os.path.join(copy, 'normal.png'), STRENGTH], check=True)
    results['baseline seed_1, normal remade at strength 5'] = score(copy)
    stored = subprocess.run([sys.executable, '-I', COMPARE, 'metal', original], check=True, capture_output=True, text=True).stdout
    results['baseline seed_1, as stored'] = json.loads(stored)
table = {name: {'overall': r['overall'], **r['groups']} for name, r in results.items()}
with open(out_json, 'w') as handle:
    json.dump({'table': table, 'full_reports': results}, handle, indent=1)
print(f"{'set':55s} overall colour height normal tiling")
for name, row in table.items():
    print(f"{name:55s} {row['overall']:.3f}  {row['colour']:.3f}  {row['height']:.3f}  {row['normal']:.3f}  {row['tiling']:.3f}")

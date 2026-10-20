# What this does (plain words): the like-for-like scores of the gravel trial.
#   1. For every baked set in final/ (made by final_bake.py at 1254 dots) it makes the normal map from the 16-bit height with
#      recipes/slate_layers/integration/make_normal.py at the gravel reference strength 10, then scores the set against the gravel reference with
#      lib/texture_compare.py (the "same kind" score: overall, and the colour, height, normal and tiling groups) and keeps the report as score.json.
#      Sets whose folder name ends in "_combine_height" were baked with COMBINE's own height rule and are scored the same way.
#   2. THE BASELINE, scored the same way: the gravel's own earlier small recipe, first new tile (recipes/gravel/variations/out/sample_01, 1254 dots,
#      made by baseline_scores.py into baseline_sample_01/ with its normal remade at strength 10), and the mean of all eight of its new tiles
#      (baseline_scores.json).
#   3. Writes final_scores.json and prints a small table.
# Use: python3 -I final_scores.py
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
MAKE_NORMAL = os.path.join(PROC, 'recipes', 'slate_layers', 'integration', 'make_normal.py')
COMPARE = os.path.join(PROC, 'lib', 'texture_compare.py')
STRENGTH = '10'


def score(folder):
    out = os.path.join(folder, 'score.json')
    subprocess.run([sys.executable, '-I', COMPARE, 'gravel', folder, '--json', out], check=True, stdout=subprocess.DEVNULL)
    with open(out) as handle:
        return json.load(handle)


results = {}
final = os.path.join(HERE, 'final')
baseline = os.path.join(HERE, 'baseline_sample_01')
if not os.path.exists(os.path.join(baseline, 'height.png')):          # the big baseline pictures are deleted after scoring to save disk: make them again
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'baseline_scores.py')], check=True, stdout=subprocess.DEVNULL)
temporary = []
for name in sorted(os.listdir(final)):
    folder = os.path.join(final, name)
    if not os.path.exists(os.path.join(folder, 'height.png')):
        continue
    if not os.path.exists(os.path.join(folder, 'colour.png')):        # the COMBINE-rule set baked only its height: the colour is the same as seed set 1's
        shutil.copyfile(os.path.join(final, 'seeds_1', 'colour.png'), os.path.join(folder, 'colour.png'))
        temporary.append(os.path.join(folder, 'colour.png'))
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(folder, 'height.png'), os.path.join(folder, 'normal.png'), STRENGTH], check=True)
    results[name] = score(folder)
results['baseline sample_01, normal remade at strength 10'] = score(baseline)
for path in temporary:                                                # keep the disk use down: those copies are not kept
    os.remove(path)
    os.remove(os.path.join(os.path.dirname(path), 'normal.png'))
for name in ('height.png', 'normal.png'):
    os.remove(os.path.join(baseline, name))
table = {name: {'overall': r['overall'], **r['groups']} for name, r in results.items()}
trial = [n for n in ('seeds_1', 'seeds_2', 'seeds_3') if n in table]
if trial:
    table['trial mean of the three seed sets'] = {k: round(sum(table[n][k] for n in trial) / len(trial), 3) for k in ('overall', 'colour', 'height', 'normal', 'tiling')}
with open(os.path.join(HERE, 'baseline_scores.json')) as handle:
    table['baseline mean of its eight new tiles'] = json.load(handle)['mean_of_eight']
with open(os.path.join(HERE, 'final_scores.json'), 'w') as handle:
    json.dump({'_what_this_is': 'The like-for-like scores of the gravel trial (made by final_scores.py): table = overall, colour, height, normal and tiling groups of every final set and of the earlier recipes tiles; full_reports = every single measure.', 'table': table, 'full_reports': results}, handle, indent=1)
print(f"{'set':55s} overall colour height normal tiling")
for name, row in table.items():
    print(f"{name:55s} {row['overall']:.3f}  {row['colour']:.3f}  {row['height']:.3f}  {row['normal']:.3f}  {row['tiling']:.3f}")

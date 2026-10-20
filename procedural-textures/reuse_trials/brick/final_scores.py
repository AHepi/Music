# What this does (plain words): the like-for-like scores of the brick trial.
#   1. For every baked set in final/ (made by final_bake.py at 1254 dots) it makes the normal map from the 16-bit height with
#      recipes/slate_layers/integration/make_normal.py at the brick reference strength 6, then scores the set against the brick reference with
#      lib/texture_compare.py (the "same kind" score: overall, and the colour, height, normal and tiling groups) and keeps the report as score.json.
#   2. THE BASELINE, scored the same way: the brick's own earlier small recipe, first new tile (recipes/brick/variations/tile_11, 1254 dots).
#      It is scored twice: as stored (its own normal map), and with its normal remade from its height by the same make_normal.py at strength 6
#      (copied into baseline_tile_11/ here; the original folder is not touched), so the normal-making is the same as the trial's too.
#   3. Writes final_scores.json and prints a small table. The earlier layered brick (recipes/slate_layers/reuse, first settings) is read from its
#      stored score.json for the record (it was scored with the same tool at the same size).
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
STRENGTH = '6'


def score(folder):
    out = os.path.join(folder, 'score.json')
    subprocess.run([sys.executable, '-I', COMPARE, 'brick', folder, '--json', out], check=True, stdout=subprocess.DEVNULL)
    with open(out) as handle:
        return json.load(handle)


results = {}
final = os.path.join(HERE, 'final')
for name in sorted(os.listdir(final)):
    folder = os.path.join(final, name)
    if not os.path.exists(os.path.join(folder, 'metallic.png')):
        continue
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(folder, 'height.png'), os.path.join(folder, 'normal.png'), STRENGTH], check=True)
    results[name] = score(folder)
baseline_original = os.path.join(PROC, 'recipes', 'brick', 'variations', 'tile_11')
baseline_copy = os.path.join(HERE, 'baseline_tile_11')
os.makedirs(baseline_copy, exist_ok=True)
for file_name in ('colour.png', 'height.png'):
    shutil.copyfile(os.path.join(baseline_original, file_name), os.path.join(baseline_copy, file_name))
subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(baseline_copy, 'height.png'), os.path.join(baseline_copy, 'normal.png'), STRENGTH], check=True)
results['baseline tile_11, normal remade at strength 6'] = score(baseline_copy)
stored = subprocess.run([sys.executable, '-I', COMPARE, 'brick', baseline_original], check=True, capture_output=True, text=True).stdout
results['baseline tile_11, as stored'] = json.loads(stored)
with open(os.path.join(PROC, 'recipes', 'slate_layers', 'reuse', 'score_against_brick', 'score.json')) as handle:
    results['earlier layered brick (first settings, stored score)'] = json.load(handle)
table = {name: {'overall': r['overall'], **r['groups']} for name, r in results.items()}
trial = [n for n in table if n.startswith('seeds_')]
if trial:
    table['trial mean of the three seed sets'] = {k: round(sum(table[n][k] for n in trial) / len(trial), 3) for k in ('overall', 'colour', 'height', 'normal', 'tiling')}
with open(os.path.join(HERE, 'final_scores.json'), 'w') as handle:
    json.dump({'table': table, 'full_reports': results}, handle, indent=1)
print(f"{'set':55s} overall colour height normal tiling")
for name, row in table.items():
    print(f"{name:55s} {row['overall']:.3f}  {row['colour']:.3f}  {row['height']:.3f}  {row['normal']:.3f}  {row['tiling']:.3f}")

# What this does (plain words): the like-for-like scores of the mud trial.
#   1. For every baked set in the folder given (default final/; made by final_bake.py at 1254 dots) it makes the normal map from the 16-bit height with
#      recipes/slate_layers/integration/make_normal.py at the mud reference strength 9, then scores the set against the mud reference with
#      lib/texture_compare.py (the "same kind" score: overall, and the colour, height, normal and tiling groups) and keeps the report as score.json.
#   2. THE BASELINE, scored the same way: the mud's own earlier small recipe, first new tile (recipes/mud/variations/tile_101, 1254 dots). It is scored
#      twice: as stored (its own normal map), and with its normal remade from its height by the same make_normal.py at strength 9 (copied into
#      baseline_tile_101/ here; the original folder is not touched), so the normal-making is the same as the trial's too.
#   3. THE CONTROL (the surveyor's warning: the mud score is weak at telling mud from other surfaces): every trial set and the baseline are also scored
#      against the brick, slate, wood, metal and gravel references. A score against mud that is clearly higher than these shows the tool can tell the tile is mud.
#   4. Writes final_scores.json (or the name given) and prints a small table.
# Use: python3 -I final_scores.py [FOLDER_WITH_SETS (default final)] [OUT_JSON (default final_scores.json)] [--no-control] [--no-baseline]
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
MAKE_NORMAL = os.path.join(PROC, 'recipes', 'slate_layers', 'integration', 'make_normal.py')
COMPARE = os.path.join(PROC, 'lib', 'texture_compare.py')
STRENGTH = '9'
OTHERS = ['brick', 'slate', 'wood', 'metal', 'gravel']
arguments = [a for a in sys.argv[1:] if not a.startswith('--')]
flags = [a for a in sys.argv[1:] if a.startswith('--')]
final = os.path.join(HERE, arguments[0] if arguments else 'final')
out_json = os.path.join(HERE, arguments[1] if len(arguments) > 1 else 'final_scores.json')


def score(folder, reference='mud', keep=True):
    out = os.path.join(folder, 'score.json') if (keep and reference == 'mud') else None
    command = [sys.executable, '-I', COMPARE, reference, folder] + (['--json', out] if out else [])
    done = subprocess.run(command, check=True, capture_output=True, text=True)
    if out:
        with open(out) as handle:
            return json.load(handle)
    return json.loads(done.stdout)


results, control = {}, {}
for name in sorted(os.listdir(final)):
    folder = os.path.join(final, name)
    if not os.path.exists(os.path.join(folder, 'height.png')) or not os.path.exists(os.path.join(folder, 'colour.png')):
        continue
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(folder, 'height.png'), os.path.join(folder, 'normal.png'), STRENGTH], check=True)
    results[name] = score(folder)
    if '--no-control' not in flags:
        control[name] = {ref: score(folder, ref)['overall'] for ref in OTHERS}
if '--no-baseline' not in flags:
    baseline_original = os.path.join(PROC, 'recipes', 'mud', 'variations', 'tile_101')
    baseline_copy = os.path.join(HERE, 'baseline_tile_101')
    os.makedirs(baseline_copy, exist_ok=True)
    for file_name in ('colour.png', 'height.png'):
        shutil.copyfile(os.path.join(baseline_original, file_name), os.path.join(baseline_copy, file_name))
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(baseline_copy, 'height.png'), os.path.join(baseline_copy, 'normal.png'), STRENGTH], check=True)
    results['baseline tile_101, normal remade at strength 9'] = score(baseline_copy)
    stored = subprocess.run([sys.executable, '-I', COMPARE, 'mud', baseline_original], check=True, capture_output=True, text=True).stdout
    results['baseline tile_101, as stored'] = json.loads(stored)
    if '--no-control' not in flags:
        control['baseline tile_101, normal remade at strength 9'] = {ref: score(baseline_copy, ref)['overall'] for ref in OTHERS}
table = {name: {'overall': r['overall'], **r['groups']} for name, r in results.items()}
trial = [n for n in table if n.startswith('seeds_')]
if len(trial) > 1:
    table['trial mean of the sets'] = {k: round(sum(table[n][k] for n in trial) / len(trial), 3) for k in ('overall', 'colour', 'height', 'normal', 'tiling')}
with open(out_json, 'w') as handle:
    json.dump({'table': table, 'control_overall_against_other_references': control, 'full_reports': results}, handle, indent=1)
print(f"{'set':55s} overall colour height normal tiling")
for name, row in table.items():
    print(f"{name:55s} {row['overall']:.3f}  {row['colour']:.3f}  {row['height']:.3f}  {row['normal']:.3f}  {row['tiling']:.3f}")
for name, row in control.items():
    print(f'control {name}:', {k: round(v, 3) for k, v in row.items()})

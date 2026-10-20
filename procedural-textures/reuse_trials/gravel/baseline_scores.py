# What this does (plain words): scores the gravel's OWN EARLIER small recipe the same way the layered gravel is scored, so the comparison is like for
# like: same tool (lib/texture_compare.py, "same kind" score against the gravel reference), same size (1254 dots), and the normal map remade from the
# height by make_normal.py at the gravel strength 10 (the same as for the layered tiles). The earlier recipe (recipes/gravel/variations) made eight new
# tiles from its sampler; the first one is the baseline kept in baseline_sample_01/ (colour, height, normal and score.json), the other seven are
# scored one at a time in a scratch folder that is deleted after. Writes baseline_scores.json. Nothing in recipes/ is changed.
# Use: python3 -I baseline_scores.py
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
MAKE_NORMAL = os.path.join(PROC, 'recipes', 'slate_layers', 'integration', 'make_normal.py')
COMPARE = os.path.join(PROC, 'lib', 'texture_compare.py')
results = {}
for number in range(1, 9):
    source = os.path.join(PROC, 'recipes', 'gravel', 'variations', 'out', f'sample_{number:02d}')
    folder = os.path.join(HERE, 'baseline_sample_01' if number == 1 else 'baseline_scratch')
    os.makedirs(folder, exist_ok=True)
    for name in ('colour.png', 'height.png'):
        shutil.copyfile(os.path.join(source, name), os.path.join(folder, name))
    subprocess.run([sys.executable, '-I', MAKE_NORMAL, os.path.join(folder, 'height.png'), os.path.join(folder, 'normal.png'), '10'], check=True)
    out = os.path.join(folder, 'score.json')
    subprocess.run([sys.executable, '-I', COMPARE, 'gravel', folder, '--json', out], check=True, stdout=subprocess.DEVNULL)
    with open(out) as handle:
        report = json.load(handle)
    results[f'sample_{number:02d}'] = {'overall': report['overall'], **report['groups']}
    if number != 1:
        shutil.rmtree(folder)
names = list(results)
mean = {key: round(sum(results[n][key] for n in names) / len(names), 3) for key in ('overall', 'colour', 'height', 'normal', 'tiling')}
with open(os.path.join(HERE, 'baseline_scores.json'), 'w') as handle:
    json.dump({'what': 'the earlier gravel recipe (recipes/gravel/variations, new tiles 1 to 8), 1254 dots, normal remade by make_normal.py at strength 10, scored by lib/texture_compare.py gravel',
               'per_tile': results, 'mean_of_eight': mean}, handle, indent=1)
print(json.dumps(results, indent=0))
print('mean of eight', mean)

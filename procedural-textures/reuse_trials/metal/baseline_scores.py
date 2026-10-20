# What this does (plain words): collects the "same kind" scores of the metal surface's OWN EARLIER small recipe on its eight stored new tiles
# (recipes/metal/variations/seed_1 ... seed_8) into one small file, baseline_scores.json, with the mean over the first three tiles (to set
# beside the layered trial's three seed sets) and over all eight.
# Where the numbers come from, honestly:
#   * Only seed_1 still has its height and normal pictures (the other tiles kept only their colour picture). So seed_1 was re-scored today,
#     by final_scores.py --baseline, with its normal made again by make_normal.py at strength 5 (the same way as the layered tiles).
#   * The numbers for the eight tiles come from the earlier file recipes/metal/variations/summary.json, scored by the same tool
#     (lib/texture_compare.py, against the metal reference) at the same size (1254 dots), with each tile's own stored normal map. For seed_1 the
#     two ways agree (0.578 stored, 0.579 remade), so the stored numbers are a fair stand-in for the other seven.
# Use: python3 -I baseline_scores.py
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
with open(os.path.join(PROC, 'recipes', 'metal', 'variations', 'summary.json')) as handle:
    stored = json.load(handle)
per_tile = {}
for number in range(1, 9):
    row = stored[str(number)]
    per_tile[f'seed_{number}'] = {'overall': row['texture_overall'], **row['texture_groups']}
with open(os.path.join(HERE, 'final_scores.json')) as handle:                    # written by final_scores.py --baseline
    remade = json.load(handle)['table']['baseline seed_1, normal remade at strength 5']
per_tile['seed_1 (re-scored today, normal remade at strength 5)'] = remade


def mean(names, key):
    return round(sum(per_tile[name][key] for name in names) / len(names), 3)


first_three = ['seed_1', 'seed_2', 'seed_3']
all_eight = [f'seed_{n}' for n in range(1, 9)]
means = {key: {'first three': mean(first_three, key), 'all eight': mean(all_eight, key)} for key in ('overall', 'colour', 'height', 'normal', 'tiling')}
with open(os.path.join(HERE, 'baseline_scores.json'), 'w') as handle:
    json.dump({'per_tile': per_tile, 'means': means}, handle, indent=1)
print(json.dumps(means, indent=1))

# What this does (plain words): the counting half of the round-2 independence re-test (see independence_two_layers_bake.py). It reads the baked pictures and,
# for MOSS and OUTLINE AND SHADOW, counts dot by dot what changed when the layer was switched off (Amount 0) or given a new seed (Seed + 1): in the finished colour,
# height and roughness, in every layer's own mask, and whether anything changed OUTSIDE the changed layer's own region (it must be 0). It uses the helper functions of
# the earlier full test (tests/independence_full.py) so the rules are the same. Writes independence_two_layers_table.md and .json next to the pictures.
# Use: python3 -I independence_two_layers_analysis.py PICTURES_FOLDER [SIZE]
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
folder = sys.argv[1]
size = sys.argv[2] if len(sys.argv) > 2 else '384'
sys.argv = ['independence_full.py', size, folder]          # independence_full reads SIZE and OUT from the command line when it is loaded
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', 'tests')))
import independence_full as ind  # noqa: E402
import numpy as np  # noqa: E402

LAYERS = ['moss', 'outline_and_shadow']
base = ind.load_all(os.path.join(folder, 'base_final'), os.path.join(folder, 'base_masks'))
rows = []
for layer in LAYERS:
    for variant, suffix in (('Amount 0', 'Amount_0'), ('Seed + 1', 'Seed_plus_1')):
        name = f'{layer}_{suffix}'
        data = ind.load_all(os.path.join(folder, name + '_final'), os.path.join(folder, name + '_masks'))
        diff = ind.changes(base, data)
        region = ind.own_region(layer, base, data)
        outside = ~region
        row = {'layer changed': layer, 'variant': variant, 'own region share %': round(100 * region.mean(), 2)}
        for kind in ('colour', 'height', 'roughness'):
            row[f'{kind} changed %'] = round(100 * diff[kind].mean(), 3)
            row[f'{kind} changed outside own region %'] = round(100 * (diff[kind] & outside).mean(), 4)
        for other in ind.LAYERS[1:]:
            key = 'm_' + other
            row[f'{other} mask changed %'] = round(100 * diff[key].mean(), 3)
            row[f'{other} mask changed outside {layer} region %'] = round(100 * (diff[key] & outside).mean(), 4)
        row['slates changed (piece_id) %'] = round(100 * diff['m_piece_id'].mean(), 3)
        rows.append(row)
columns = ['layer changed', 'variant', 'own region share %', 'colour changed %', 'colour changed outside own region %', 'height changed %', 'height changed outside own region %',
           'roughness changed %', 'roughness changed outside own region %']
lines = ['| ' + ' | '.join(columns) + ' |', '|' + '---|' * len(columns)]
for row in rows:
    lines.append('| ' + ' | '.join(str(row[c]) for c in columns) + ' |')
lines += ['', "Which other layers' own patterns (masks) changed (share of all dots; 'outside' = outside the changed layer's own region):", '',
          '| layer changed | variant | slates (piece_id) | colour_and_fade mask | damage mask | moss mask | outline_and_shadow mask |', '|---|---|---|---|---|---|---|']
for row in rows:
    cells = [row['layer changed'], row['variant'], str(row['slates changed (piece_id) %'])]
    for other in ind.LAYERS[1:]:
        if other == row['layer changed']:
            cells.append('(itself) ' + str(row[other + ' mask changed %']))
        else:
            cells.append(str(row[other + ' mask changed %']) + ' (outside ' + str(row[other + ' mask changed outside ' + row['layer changed'] + ' region %']) + ')')
    lines.append('| ' + ' | '.join(cells) + ' |')
with open(os.path.join(folder, 'independence_two_layers_table.md'), 'w') as handle:
    handle.write('\n'.join(lines) + '\n')
with open(os.path.join(folder, 'independence_two_layers_results.json'), 'w') as handle:
    json.dump(rows, handle, indent=1)
print('\n'.join(lines))

# What this does (plain words): the verifier's analysis of its own independence bakes (verify/independence/<variant>/). For each variant it
# counts the dots that changed against 'base' in the finished colour, height and roughness, INSIDE and OUTSIDE the changed layer's own region
# (its mask above exactly 0 in base or in the variant), with TWO thresholds: STRICT (any change at all: 1 step of 255 in colour, 1 step of 65535
# in height and roughness) and the builders' own (more than 1 step of 255, 0.0005 height, 0.004 roughness). It also checks every OTHER layer's
# mask and piece_id: changed anywhere, and changed outside the region (only the declared link moss <- damage may change, inside damage).
# Use: python3 -I analyse_independence.py
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.join(os.path.dirname(HERE), 'independence')
MASKS = ['colour_and_fade_mask', 'damage_mask', 'moss_mask', 'outline_and_shadow_mask', 'bundle_piece_id']


def load(name):
    folder = os.path.join(FOLDER, name)
    data = {'colour': cv2.imread(os.path.join(folder, 'colour.png')).astype(np.int32)}
    for kind in ('height', 'roughness'):
        data[kind] = cv2.imread(os.path.join(folder, kind + '.png'), cv2.IMREAD_UNCHANGED).astype(np.int64)[..., 0]
    for mask in MASKS:
        data[mask] = cv2.imread(os.path.join(folder, 'mask_' + mask + '.png'), cv2.IMREAD_UNCHANGED).astype(np.int64)[..., 0]
    return data


base = load('base')
rows = []
for name in sorted(os.listdir(FOLDER)):
    path = os.path.join(FOLDER, name)
    if name == 'base' or not os.path.isdir(path) or len(os.listdir(path)) < 8:
        continue
    layer = name.rsplit('_', 1)[0]
    variant = load(name)
    if layer == 'layout':
        region = np.ones(base['colour'].shape[:2], bool)
    elif layer == 'colour_and_fade':
        region = (base['bundle_piece_id'] >= 0)          # placeholder; replaced below by the slate dots
        region = np.zeros_like(region)
    else:
        region = (base[layer + '_mask'] > 0) | (variant[layer + '_mask'] > 0)
    row = {'variant': name, 'own region %': round(100 * region.mean(), 2)}
    colour_diff = np.abs(base['colour'] - variant['colour']).max(axis=2)
    checks = {'colour': (colour_diff >= 1, colour_diff > 1),
              'height': (np.abs(base['height'] - variant['height']) >= 1, np.abs(base['height'] - variant['height']) > 0.0005 * 65535),
              'roughness': (np.abs(base['roughness'] - variant['roughness']) >= 1, np.abs(base['roughness'] - variant['roughness']) > 0.004 * 65535)}
    for kind, (strict, lax) in checks.items():
        row[f'{kind} changed % (strict)'] = round(100 * strict.mean(), 3)
        row[f'{kind} OUTSIDE region % strict'] = round(100 * (strict & ~region).mean(), 4) if layer != 'colour_and_fade' else 'n/a'
        row[f'{kind} OUTSIDE region % builders threshold'] = round(100 * (lax & ~region).mean(), 4) if layer != 'colour_and_fade' else 'n/a'
        row[f'{kind} max change outside (steps)'] = int((np.abs(base[kind] - variant[kind]).max(axis=-1) if kind == 'colour' else np.abs(base[kind] - variant[kind]))[~region].max()) if (~region).any() and layer != 'colour_and_fade' else 'n/a'
    others = {}
    for mask in MASKS:
        if mask == layer + '_mask':
            continue
        changed = base[mask] != variant[mask]
        others[mask] = {'changed %': round(100 * changed.mean(), 4), 'changed OUTSIDE region %': round(100 * (changed & ~region).mean(), 4) if layer not in ('colour_and_fade',) else 'n/a',
                        'max change (of 65535)': int(np.abs(base[mask] - variant[mask]).max())}
    row['other masks'] = others
    rows.append(row)

with open(os.path.join(os.path.dirname(HERE), 'independence_results_verify.json'), 'w') as handle:
    json.dump(rows, handle, indent=1)
for row in rows:
    print(json.dumps(row))

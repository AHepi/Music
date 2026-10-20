# What this does (plain words): measures the proof pictures that checks_run.py baked, and writes the answers as plain tables (a copy of the brick
# trial's checks_analyse.py with the wood layers).
#   HALF-TILE TEST: the slid picture must equal the plain picture rolled by half its size. It prints the average difference (in steps of 255)
#     and the share of dots that differ by more than 40 steps; a WRONGLY rolled copy (7 dots off) is measured too as a control (it must differ
#     a lot, or the test proves nothing). With two base tiles across, the finished colour is also compared with itself rolled by one base tile:
#     it must differ a lot, because a 2 x 2 area is new content, but GRAIN repeats once per base tile, so the difference will be smaller than for a
#     layer that makes new content.
#   SWITCH-OFF TEST: for every layer, Amount 0: the share of dots whose colour (more than 2 steps of 255) or height (more than 0.002) changed, and the
#     share that changed OUTSIDE that layer's own mask (should be 0, except where a declared link allows it: MOSS reads DAMAGE's Mask, so switching
#     DAMAGE off may change MOSS; the layout and COLOUR AND FADE paint everywhere).
# Use: python3 -I checks_analyse.py OUT_ROOT     (writes OUT_ROOT/half_tile_results.json, switch_off_results.json and checks_tables.md)
import json
import os
import sys

import cv2
import numpy as np

root = sys.argv[1]
lines = []


def load(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64)
    image /= 65535.0 if image.max() > 255 else 255.0
    return image if image.ndim == 3 else image[..., None]


def roll_difference(first, second, roll):
    rolled = np.roll(first, (roll, roll), axis=(0, 1))
    difference = np.abs(rolled - second).max(axis=2) * 255.0
    return round(float(difference.mean()), 3), round(float(100 * (difference > 40).mean()), 3)


half = []
folder = os.path.join(root, 'half_tile')
if os.path.isdir(folder):
    lines += ['## Half-tile test (512 dots)', '', '| base tiles across | picture | mean difference (of 255) | dots differing by > 40 % | control: wrongly rolled, mean | control share % |', '|---|---|---|---|---|---|']
    for tiles, views in ((1, (('finished', 'colour'), ('pieces', 'colour'), ('edge_distance', 'height'), ('cracks_mask', 'height'), ('knots_mask', 'height'), ('grain_mask', 'height'))),
                         (2, (('finished', 'colour'),))):
        for view, kind in views:
            a = load(os.path.join(folder, f't{tiles}_plain_{view}_{kind}.png'))
            b = load(os.path.join(folder, f't{tiles}_shifted_{view}_{kind}.png'))
            size = a.shape[0]
            mean, share = roll_difference(a, b, size // 2)
            wrong_mean, wrong_share = roll_difference(a, b, size // 2 + 7)
            row = {'tiles_across': tiles, 'picture': f'{view} ({kind})', 'mean_difference': mean, 'share_over_40_percent': share,
                   'control_wrong_roll_mean': wrong_mean, 'control_wrong_roll_share': wrong_share}
            half.append(row)
            lines.append(f"| {tiles} | {row['picture']} | {mean} | {share} | {wrong_mean} | {wrong_share} |")
        if tiles == 2:
            a = load(os.path.join(folder, 't2_plain_finished_colour.png'))
            mean, share = roll_difference(a, a, a.shape[0] // 2)
            half.append({'tiles_across': 2, 'picture': 'finished colour against itself rolled by ONE base tile (must differ a lot)', 'mean_difference': mean,
                         'share_over_40_percent': share})
            lines.append(f'| 2 | finished colour against itself rolled by one base tile (a copy would give 0) | {mean} | {share} | | |')
    with open(os.path.join(root, 'half_tile_results.json'), 'w') as handle:
        json.dump(half, handle, indent=1)
    lines.append('')

folder = os.path.join(root, 'switch_off')
if os.path.isdir(folder):
    base = {kind: load(os.path.join(folder, f'base_{kind}.png')) for kind in ('colour', 'height')}
    limits = {'colour': 2 / 255, 'height': 0.002}
    allowed = {'damage': ['moss']}
    rows = []
    lines += ['## Switch-off test (320 dots, Amount 0)', '',
              '| layer switched off | colour changed % | colour changed outside own mask % | height changed % | height changed outside own mask % | own mask covers % |',
              '|---|---|---|---|---|---|']
    for layer in ('colour_and_fade', 'grain', 'moss', 'damage', 'cracks', 'knots', 'outline_and_shadow'):
        own = load(os.path.join(folder, f'mask_{layer}_height.png'))[..., 0] > 0.01
        mask = np.ones(base['colour'].shape[:2], bool) if layer == 'colour_and_fade' else own.copy()
        for other in allowed.get(layer, []):                     # a declared link: the reading layer may change too
            mask |= load(os.path.join(folder, f'mask_{other}_height.png'))[..., 0] > 0.01
        row = {'layer switched off': layer, 'own mask covers %': round(100 * float(own.mean()), 2)}
        for kind in ('colour', 'height'):
            changed = np.abs(load(os.path.join(folder, f'{layer}_amount_0_{kind}.png')) - base[kind]).max(axis=2) > limits[kind]
            row[f'{kind} changed %'] = round(100 * float(changed.mean()), 3)
            row[f'{kind} changed outside own mask %'] = round(100 * float((changed & ~mask).mean()), 3)
        rows.append(row)
        lines.append(f"| {layer} | {row['colour changed %']} | {row['colour changed outside own mask %']} | {row['height changed %']} | "
                     f"{row['height changed outside own mask %']} | {row['own mask covers %']} |")
    with open(os.path.join(root, 'switch_off_results.json'), 'w') as handle:
        json.dump(rows, handle, indent=1)
    lines.append('')
with open(os.path.join(root, 'checks_tables.md'), 'w') as handle:
    handle.write('# What this is: the measured results of the wood trial\'s half-tile and switch-off tests (made by checks_analyse.py)\n\n' + '\n'.join(lines) + '\n')
print('\n'.join(lines))

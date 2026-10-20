# What this does (plain words): measures the proof pictures that checks_run.py baked, and writes the answers as plain tables.
#   HALF-TILE TEST: the slid picture must equal the plain picture rolled by half its size. It prints the average difference (in steps of 255)
#     and the share of dots that differ by more than 40 steps; a WRONGLY rolled copy (7 dots off) is measured too as a control (it must differ
#     a lot, or the test proves nothing). With two base tiles across, the picture must ALSO not simply repeat per base tile (a 2 x 2 area is
#     new content): it is compared with itself rolled by one base tile, which must differ a lot.
#   INDEPENDENCE TEST: for every layer, Amount 0 and Seed + 1: the share of dots that changed (colour more than 2 steps of 255, height more than
#     0.002, roughness more than 0.005), and the share that changed OUTSIDE that layer's own mask (must be 0, except where a declared link
#     allows it: MOSS reads DAMAGE's Mask; the layout feeds everything).
# Use: python3 -I checks_analyse.py OUT_ROOT     (writes OUT_ROOT/half_tile_results.json, independence_results.json and checks_tables.md)
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
    for tiles in (1, 2):
        for view, kind in (('finished', 'colour'), ('pieces', 'colour'), ('edge_distance', 'height'), ('grime_mask', 'height')):
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
            lines.append(f'| 2 | finished colour against itself rolled by one base tile (must differ a lot: new content, not a copy) | {mean} | {share} | | |')
    with open(os.path.join(root, 'half_tile_results.json'), 'w') as handle:
        json.dump(half, handle, indent=1)
    lines.append('')

folder = os.path.join(root, 'independence')
if os.path.isdir(folder):
    base = {kind: load(os.path.join(folder, f'base_{kind}.png')) for kind in ('colour', 'height', 'roughness')}
    limits = {'colour': 2 / 255, 'height': 0.002, 'roughness': 0.005}
    allowed = {'damage': ['moss']}
    rows = []
    lines += ['## Independence test (320 dots)', '',
              '| layer changed | variant | colour changed % | colour changed outside own mask % | height changed % | height outside % | roughness changed % | roughness outside % |',
              '|---|---|---|---|---|---|---|---|']
    variants = []
    for layer in ('colour_and_fade', 'damage', 'moss', 'outline_and_shadow', 'grime'):
        variants += [(layer, 'Amount 0', f'{layer}_amount_0'), (layer, 'Seed + 1', f'{layer}_seed_plus_1')]
    variants.append(('brick_layout', 'Seed + 1', 'brick_layout_seed_plus_1'))
    for layer, variant, stem in variants:
        if layer in ('colour_and_fade', 'brick_layout'):
            mask = np.ones(base['colour'].shape[:2], bool)          # the bottom layer and the layout paint everywhere
        else:
            mask = load(os.path.join(folder, f'mask_{layer}_height.png'))[..., 0] > 0.01
            for other in allowed.get(layer, []):                     # a declared link: the reading layer may change too
                mask |= load(os.path.join(folder, f'mask_{other}_height.png'))[..., 0] > 0.01
        row = {'layer changed': layer, 'variant': variant}
        for kind in ('colour', 'height', 'roughness'):
            changed = np.abs(load(os.path.join(folder, f'{stem}_{kind}.png')) - base[kind]).max(axis=2) > limits[kind]
            row[f'{kind} changed %'] = round(100 * float(changed.mean()), 3)
            row[f'{kind} changed outside own mask %'] = round(100 * float((changed & ~mask).mean()), 3)
        rows.append(row)
        lines.append(f"| {layer} | {variant} | {row['colour changed %']} | {row['colour changed outside own mask %']} | {row['height changed %']} | "
                     f"{row['height changed outside own mask %']} | {row['roughness changed %']} | {row['roughness changed outside own mask %']} |")
    with open(os.path.join(root, 'independence_results.json'), 'w') as handle:
        json.dump(rows, handle, indent=1)
    lines.append('')
    lines.append('(MOSS is switched off in the brick settings, so its rows must be 0. DAMAGE may change MOSS through the declared link; with MOSS off it cannot.)')
with open(os.path.join(root, 'checks_tables.md'), 'w') as handle:
    handle.write('# What this is: the measured results of the brick trial\'s half-tile and independence tests (made by checks_analyse.py)\n\n' + '\n'.join(lines) + '\n')
print('\n'.join(lines))

# What this does (plain words): proves that the recipe repeats EXACTLY at the edge of the tile.
# The test bakes the recipe normally, then bakes it again with the whole pattern slid by half a picture (parameter shift = [0.5, 0.5]).
# If the pattern really repeats every picture, the second picture must be the first picture "rolled" by half its size (what leaves on the
# right comes back on the left). It prints how much the two differ: the average difference (steps of 255) and the share of dots that differ
# by more than 40 steps. A WRONGLY rolled copy is measured as a control (it must differ a lot, otherwise the test proves nothing).
# It runs for the colour picture and for the exact 16-bit data of several layout bundle numbers (shown through debug_view).
# Also with tiles_across = 2: the picture must again repeat exactly when slid by half a picture, but must NOT repeat when slid by one
# base tile (= half of the picture), because a 2 x 2 area is new content, not a copy.
# Use (plain python, not Blender):  python3 -I half_tile_test.py [SIZE] [OUT_FOLDER]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 512
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'half_tile')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
VIEWS = ['none', 'bundle.piece_colour', 'bundle.local_x', 'bundle.local_y', 'bundle.edge_distance', 'bundle.base_height', 'bundle.row']


def bake(name, params, views):
    folder = os.path.join(OUT, name)
    base = dict(params)
    arguments = {v.replace('.', '_'): dict(debug_view=v) for v in views}
    subprocess.run(BLENDER + [os.path.join(HERE, 'bake_tools.py'), '--', RECIPE, folder, str(SIZE), '4', json.dumps(arguments), json.dumps(base)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def read(folder, view, kind):
    path = os.path.join(folder, view.replace('.', '_') + ('_colour.png' if kind == 'colour' else '_height.png'))
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64)
    return image / (65535.0 if kind == 'height' else 255.0) * 255.0     # both on a 0..255 scale


def compare(first, second, roll):
    rolled = np.roll(first, (roll, roll), axis=(0, 1))
    difference = np.abs(rolled - second).mean(axis=2)
    return float(difference.mean()), float(100 * (difference > 40).mean())


def run(tiles):
    rows = []
    base = {'recipe.tiles_across': tiles}
    first = bake(f'n{tiles}_plain', base, VIEWS)
    shifted = bake(f'n{tiles}_shifted', dict(base, shift=[0.5, 0.5]), VIEWS)
    for view in VIEWS:
        for kind in ('colour', 'height'):
            if view == 'none' and kind == 'height':
                continue
            if view != 'none' and kind == 'colour' and view != 'bundle.piece_colour':
                continue
            a, b = read(first, view, kind), read(shifted, view, kind)
            mean, share = compare(a, b, SIZE // 2)
            wrong_mean, wrong_share = compare(a, b, SIZE // 2 + 7)
            rows.append({'tiles_across': tiles, 'view': view, 'picture': kind, 'mean_difference': round(mean, 3), 'share_over_40_percent': round(share, 3),
                         'control_wrong_roll_mean': round(wrong_mean, 3), 'control_wrong_roll_share': round(wrong_share, 3)})
    if tiles > 1:       # a bigger area must NOT repeat per base tile: roll by one base tile (= SIZE / tiles) and compare with itself
        a = read(first, 'none', 'colour')
        step = SIZE // tiles
        mean, share = compare(a, a, step)
        rows.append({'tiles_across': tiles, 'view': 'none', 'picture': 'colour (picture against itself rolled by ONE base tile; must differ a lot)',
                     'mean_difference': round(mean, 3), 'share_over_40_percent': round(share, 3)})
    return rows


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    results = run(1) + run(2)
    with open(os.path.join(OUT, 'half_tile_results.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    for row in results:
        print(row)

# What this does (plain words): proves that the OUTLINE AND SHADOW layer (and the whole recipe with it) repeats EXACTLY at the tile edge.
# It bakes the layer's own Mask, Colour, Height and Roughness views and the finished colour, once normally and once with the whole pattern slid by
# half a picture (parameter shift = [0.5, 0.5]). If the layer really repeats every tile, the slid picture must equal the first picture "rolled" by
# half its size. It prints the average difference (steps of 255) and the share of dots that differ by more than 40 steps. A WRONGLY rolled copy
# (rolled 7 dots too far) is measured as a control: it must differ a lot, otherwise the test proves nothing. Also with recipe.tiles_across = 2
# (a 2 x 2 area of new content): it must repeat exactly when slid by half a picture but NOT when rolled by one base tile.
# Use (plain python):  python3 -I half_tile_test.py [SIZE] [OUT_FOLDER]       Output: half_tile_results.json and half_tile_table.md
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
BAKE_TOOLS = os.path.join(HERE, '..', 'tests', 'bake_tools.py')
VIEWS = ['none', 'outline_and_shadow.mask', 'outline_and_shadow.colour', 'outline_and_shadow.height', 'outline_and_shadow.roughness']


def bake(name, params):
    folder = os.path.join(OUT, name)
    arguments = {v.replace('.', '_'): dict(debug_view=v) for v in VIEWS}
    subprocess.run(BLENDER + [BAKE_TOOLS, '--', RECIPE, folder, str(SIZE), '4', json.dumps(arguments), json.dumps(params)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def read(folder, view, kind):
    path = os.path.join(folder, view.replace('.', '_') + ('_colour.png' if kind == 'colour' else '_height.png'))
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64)
    image = image if image.ndim == 3 else image[..., None]
    return image / (65535.0 if kind == 'height' else 255.0) * 255.0


def compare(first, second, roll):
    rolled = np.roll(first, (roll, roll), axis=(0, 1))
    difference = np.abs(rolled - second).max(axis=2)
    return float(difference.mean()), float(100 * (difference > 40).mean())


def run(tiles):
    rows = []
    base = {'recipe.tiles_across': tiles}
    first = bake(f'n{tiles}_plain', base)
    shifted = bake(f'n{tiles}_shifted', dict(base, shift=[0.5, 0.5]))
    for view in VIEWS:
        for kind in ('colour', 'height'):
            if view == 'none' and kind == 'height':
                continue
            if kind == 'colour' and view not in ('none', 'outline_and_shadow.colour'):
                continue
            a, b = read(first, view, kind), read(shifted, view, kind)
            mean, share = compare(a, b, SIZE // 2)
            wrong_mean, wrong_share = compare(a, b, SIZE // 2 + 7)
            rows.append({'tiles_across': tiles, 'view': view, 'picture': kind, 'mean_difference': round(mean, 3), 'share_over_40_percent': round(share, 3),
                         'control_wrong_roll_mean': round(wrong_mean, 3), 'control_wrong_roll_share': round(wrong_share, 3)})
    if tiles > 1:
        a = read(first, 'none', 'colour')
        mean, share = compare(a, a, SIZE // tiles)
        rows.append({'tiles_across': tiles, 'view': 'none', 'picture': 'colour (picture against itself rolled by ONE base tile; must differ a lot)',
                     'mean_difference': round(mean, 3), 'share_over_40_percent': round(share, 3)})
        a = read(first, 'outline_and_shadow.mask', 'height')
        mean, share = compare(a, a, SIZE // tiles)
        rows.append({'tiles_across': tiles, 'view': 'outline_and_shadow.mask', 'picture': 'height (the layer mask against itself rolled by ONE base tile; the layer follows the layout, so slates differ)',
                     'mean_difference': round(mean, 3), 'share_over_40_percent': round(share, 3)})
    return rows


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    results = run(1) + run(2)
    with open(os.path.join(OUT, 'half_tile_results.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    lines = ['| tiles across | view | picture | mean difference (of 255) | share of dots over 40 % | wrong-roll control mean | wrong-roll control share % |', '|---|---|---|---|---|---|---|']
    for r in results:
        lines.append(f"| {r['tiles_across']} | {r['view']} | {r['picture']} | {r['mean_difference']} | {r['share_over_40_percent']} | {r.get('control_wrong_roll_mean', '')} | {r.get('control_wrong_roll_share', '')} |")
    with open(os.path.join(OUT, 'half_tile_table.md'), 'w') as handle:
        handle.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))

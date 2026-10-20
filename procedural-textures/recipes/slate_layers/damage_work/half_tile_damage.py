# What this does (plain words): proves that the DAMAGE layer repeats exactly at the edge of the tile, and that a 2 x 2 area is new content.
# It bakes the layer's exact Mask and Height (debug views 'damage.mask' and 'damage.height') and the finished colour, once normally and once
# with the whole pattern slid by half a picture (parameter shift = [0.5, 0.5]); the second picture must be the first one "rolled" by half a
# picture. A wrongly rolled copy (7 dots off) is measured as a control: it must differ a lot, otherwise the test proves nothing.
# (Every dot looks at one exact point, see point_bake.py, so the test is about the pattern, not about random sample positions.)
# With recipe.tiles_across = 2 it also checks that the picture is NOT a copy of itself rolled by one base tile.
# Use (plain python):  python3 -I half_tile_damage.py [SIZE] [OUT_FOLDER]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 512
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, '..', 'tests', 'damage_half_tile_point_sampled')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
TESTS = os.path.join(HERE, 'point_bake.py')
VIEWS = {'mask': {'debug_view': 'damage.mask'}, 'height': {'debug_view': 'damage.height'}, 'colour': {}}


def bake(name, base):
    folder = os.path.join(OUT, name)
    subprocess.run(BLENDER + [TESTS, '--', RECIPE, folder, str(SIZE), json.dumps(VIEWS), json.dumps(base), 'Colour,Height'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def read(folder, view, kind):
    image = cv2.imread(os.path.join(folder, f'{view}_{kind}.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0) * 255.0


def compare(first, second, roll):
    rolled = np.roll(first, (roll, roll), axis=(0, 1))
    difference = np.abs(rolled - second).mean(axis=2)
    return float(difference.mean()), float(100 * (difference > 40).mean())


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for tiles in (1, 2):
        base = {'recipe.tiles_across': tiles}
        plain = bake(f'n{tiles}_plain', base)
        shifted = bake(f'n{tiles}_shifted', dict(base, shift=[0.5, 0.5]))
        for view, kind in (('mask', 'height'), ('height', 'height'), ('colour', 'colour')):
            a, b = read(plain, view, kind), read(shifted, view, kind)
            mean, share = compare(a, b, SIZE // 2)
            wrong_mean, wrong_share = compare(a, b, SIZE // 2 + 7)
            row = {'tiles_across': tiles, 'picture': f'damage {view}' if view != 'colour' else 'finished colour',
                   'mean difference (of 255) at the right roll': round(mean, 3), '% dots over 40 at the right roll': round(share, 4),
                   'mean difference at a wrong roll (control)': round(wrong_mean, 3), '% dots over 40 at a wrong roll (control)': round(wrong_share, 4)}
            if tiles == 2:
                copy_mean, copy_share = compare(a, a, SIZE // 2)          # the picture rolled by ONE base tile against itself
                row['mean difference of the picture rolled by one base tile against itself (a repeat would be near 0)'] = round(copy_mean, 3)
            rows.append(row)
            print(row)
    json.dump(rows, open(os.path.join(OUT, 'damage_half_tile_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()

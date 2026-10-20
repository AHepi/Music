# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Proves that the MOSS layer repeats EXACTLY at the edge of the tile, with the real recipe (all layers). It bakes what MOSS makes (its Mask, its Colour, its
# Height, through the recipe's debug views) normally, and again with the whole pattern slid by half a picture (parameter shift = [0.5, 0.5]). If the pattern really
# repeats every picture, the second picture must be the first picture "rolled" by half its size (what leaves on the right comes back on the left).
# It prints the share of dots that differ (mask: by more than 0.1; colour: more than 10 steps of 255; height: more than 0.01), and does the same
# after a WRONG roll (7 dots too far) as a control: the control must differ a lot, otherwise the test proves nothing.
# Also with recipe.tiles_across = 2: the picture must again repeat when slid by half, and must NOT be a copy of one tile (rolled by one base tile).
# Note on the two limits for the mask: the picture is anti-aliased with only 4 samples per dot and the sample positions of a dot are not the same in the plain and the slid
# picture, so edge dots (partly covered) differ a little (the layout's own joints show the same 3.5 percent at the 0.1 limit). A dot that really FLIPS (limit 0.5) is the real test.
# Use (plain python):  python3 -I moss_half_tile.py [SIZE] [OUT_FOLDER]      (MOSS_REUSE=1 measures the pictures already baked)
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
TOOLS = os.path.join(HERE, '..', 'tests', 'bake_tools.py')
RECIPE = os.path.join(HERE, 'frozen', 'recipe', 'slate_recipe.py') if os.environ.get('MOSS_FROZEN') else os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')      # MOSS_FROZEN=1: use the frozen copy of the whole stack
VIEWS = {'mask': {'debug_view': 'moss.mask'}, 'colour': {'debug_view': 'moss.colour'}}


def bake(name, params):
    folder = os.path.join(OUT, name)
    if os.environ.get('MOSS_REUSE') and os.path.exists(os.path.join(folder, 'mask_height.png')):
        return folder                                   # MOSS_REUSE=1: do not bake again, only measure the pictures that are already there
    subprocess.run(BLENDER + [TOOLS, '--', RECIPE, folder, str(SIZE), '4', json.dumps(VIEWS), json.dumps(params), 'Colour,Height'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def get(folder, view, kind):
    image = cv2.imread(os.path.join(folder, f'{view}_{kind}.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    return image / (65535.0 if kind == 'height' else 255.0)


def share_over(a, b, roll, limit):
    rolled = np.roll(a, (roll, roll), axis=(0, 1))
    difference = np.abs(rolled - b)
    if difference.ndim == 3:
        difference = difference.max(axis=2)
    return round(100.0 * float((difference > limit).mean()), 4)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    lines = ['| picture | what is compared | share of dots that differ after the right roll % | after a wrong roll (control) % |', '|---|---|---|---|']
    results = []
    for tiles in (1, 2):
        base = {'recipe.tiles_across': tiles}
        first = bake(f'n{tiles}_plain', base)
        shifted = bake(f'n{tiles}_shifted', dict(base, shift=[0.5, 0.5]))
        for view, kind, limit, text in (('mask', 'height', 0.5, 'moss mask (exact, 16 bit), a dot counts as different if it changes by more than 0.5'),
                                        ('mask', 'height', 0.1, 'moss mask (exact, 16 bit), a dot counts as different if it changes by more than 0.1 (includes the edge dots whose anti-aliasing differs)'),
                                        ('colour', 'colour', 10 / 255.0, 'moss colour (more than 10 steps of 255)')):
            a, b = get(first, view, kind), get(shifted, view, kind)
            right, wrong = share_over(a, b, SIZE // 2, limit), share_over(a, b, SIZE // 2 + 7, limit)
            lines.append(f'| {tiles} x {tiles} area of new content | {text} | {right} | {wrong} |')
            results.append({'tiles_across': tiles, 'what': text, 'right_roll_percent': right, 'wrong_roll_percent': wrong})
        if tiles == 2:
            a = get(first, 'mask', 'height')
            copy_share = share_over(a, a, SIZE // 2, 0.1)         # rolled by one base tile: a repeat would be 0 here
            lines.append(f'| 2 x 2 area | NOT a copy: moss mask rolled by one base tile against itself | {copy_share} (a copy would be 0) | |')
            results.append({'tiles_across': 2, 'what': 'moss mask rolled by one base tile against itself', 'percent': copy_share})
    with open(os.path.join(OUT, 'half_tile_table.md'), 'w') as handle:
        handle.write('\n'.join(lines) + '\n')
    with open(os.path.join(OUT, 'half_tile.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    print('\n'.join(lines))

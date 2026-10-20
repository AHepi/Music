# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# PROVES that the WHOLE finished recipe, and EVERY LAYER ON ITS OWN, repeats exactly at the tile edge. The "half-tile shift test": bake the picture,
# bake it again with the whole pattern slid by half a picture (the recipe's parameter shift = [0.5, 0.5]); if the pattern really wraps round the edge, the
# second picture must be the first one "rolled" by half its size (what leaves on the right comes back on the left; same for top and bottom).
# It compares: the finished colour, height and roughness, and the Mask of each of the four layers (baked alone as debug views), and the layout's
# piece_id. It does this for one tile (recipe.tiles_across = 1) and for a 2 x 2 area (tiles_across = 2, where the shift of half the picture is
# one whole base tile: the 2 x 2 area must still wrap round its own edge). Controls: a copy rolled by 7 dots too many must differ a lot (otherwise the
# test proves nothing), and for the 2 x 2 area the picture rolled by exactly ONE base tile must NOT equal itself (new content, not a copy).
# Numbers: mean difference in steps of 255 (colour, height, roughness) or of 100 (masks, in percent of full); and the share of dots that differ by
# more than 10 steps of 255 (a hard edge that moved by one dot counts here, so a few hundredths of a percent is the expected size of the one-dot noise).
# Use (plain python): python3 -I half_tile_layers.py [SIZE] [OUT_FOLDER]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 512
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'half_tile_layers')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
MASKS = {'colour_and_fade_mask': 'colour_and_fade.mask', 'damage_mask': 'damage.mask', 'moss_mask': 'moss.mask', 'outline_and_shadow_mask': 'outline_and_shadow.mask',
         'piece_id': 'bundle.piece_id'}


def bake(name, parameters, channels, views):
    folder = os.path.join(OUT, name)
    if os.path.isdir(folder) and len(os.listdir(folder)) >= len(views):
        return folder                                         # already baked: the analysis can be run again without baking
    subprocess.run(BLENDER + [os.path.join(HERE, 'bake_tools.py'), '--', RECIPE, folder, str(SIZE), '4', json.dumps(views), json.dumps(parameters), channels],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def read(folder, name, kind):
    path = os.path.join(folder, name + {'colour': '_colour.png', 'height': '_height.png', 'roughness': '_roughness.png'}[kind])
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64)
    image = image / (65535.0 if image.max() > 255 else 255.0) * 255.0
    return image if image.ndim == 2 else image.max(axis=2) if kind != 'colour' else image


def compare(first, second, roll, blur=0.0):
    """mean difference and share of dots over 10 steps between the rolled first picture and the second. With blur > 0 both pictures are first blurred
    by that many dots (a Gaussian): this removes the one-dot jitter that the renderer's random sample positions give to every hard edge (the sample positions
    belong to the dot, not to the pattern, so a pattern slid by exactly half a picture is sampled at different sub-dot places)."""
    rolled = np.roll(first, (roll, roll), axis=(0, 1))
    if blur > 0:
        rolled, second = cv2.GaussianBlur(rolled, (0, 0), blur), cv2.GaussianBlur(second, (0, 0), blur)
    difference = np.abs(rolled - second)
    if difference.ndim == 3:
        difference = difference.max(axis=2)
    return float(difference.mean()), float(100 * (difference > 10).mean())


def run(tiles):
    rows = []
    base = {'recipe.tiles_across': tiles}
    plain_final = bake(f'n{tiles}_plain_final', base, 'Colour,Height,Roughness', {'view': {}})
    shift_final = bake(f'n{tiles}_shifted_final', dict(base, shift=[0.5, 0.5]), 'Colour,Height,Roughness', {'view': {}})
    views = {name: {'debug_view': view} for name, view in MASKS.items()}
    plain_masks = bake(f'n{tiles}_plain_masks', base, 'Height', views)
    shift_masks = bake(f'n{tiles}_shifted_masks', dict(base, shift=[0.5, 0.5]), 'Height', views)
    checks = [('finished colour', plain_final, shift_final, 'view', 'colour'), ('finished height', plain_final, shift_final, 'view', 'height'),
              ('finished roughness', plain_final, shift_final, 'view', 'roughness')]
    checks += [(name.replace('_', ' '), plain_masks, shift_masks, name, 'height') for name in MASKS]
    for title, first, second, name, kind in checks:
        a, b = read(first, name, kind), read(second, name, kind)
        mean, share = compare(a, b, SIZE // 2)
        blurred_mean, blurred_share = compare(a, b, SIZE // 2, blur=2.0)
        wrong_mean, wrong_share = compare(a, b, SIZE // 2 + 7, blur=2.0)
        rows.append({'tiles_across': tiles, 'what': title, 'mean difference (of 255)': round(mean, 3), 'share of dots over 10 steps %': round(share, 3),
                     'blurred 2 dots: mean difference': round(blurred_mean, 3), 'blurred 2 dots: share over 10 steps %': round(blurred_share, 3),
                     'control (rolled 7 dots wrong, blurred): mean': round(wrong_mean, 2), 'control: share %': round(wrong_share, 2)})
    if tiles > 1:
        a = read(plain_final, 'view', 'colour')
        mean, share = compare(a, a, SIZE // tiles)
        blurred_mean, blurred_share = compare(a, a, SIZE // tiles, blur=2.0)
        rows.append({'tiles_across': tiles, 'what': 'colour against ITSELF rolled by one base tile (must differ a lot: new content)',
                     'mean difference (of 255)': round(mean, 3), 'share of dots over 10 steps %': round(share, 3),
                     'blurred 2 dots: mean difference': round(blurred_mean, 3), 'blurred 2 dots: share over 10 steps %': round(blurred_share, 3)})
    return rows


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    results = run(1) + run(2)
    with open(os.path.join(OUT, 'half_tile_results.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    columns = ['tiles_across', 'what', 'mean difference (of 255)', 'share of dots over 10 steps %', 'blurred 2 dots: mean difference', 'blurred 2 dots: share over 10 steps %',
               'control (rolled 7 dots wrong, blurred): mean', 'control: share %']
    lines = ['| ' + ' | '.join(columns) + ' |', '|' + '---|' * len(columns)]
    for row in results:
        lines.append('| ' + ' | '.join(str(row.get(c, '')) for c in columns) + ' |')
    with open(os.path.join(OUT, 'half_tile_table.md'), 'w') as handle:
        handle.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))

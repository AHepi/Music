# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# The tests of the COLOUR AND FADE layer that need only plain pictures from the layer-only recipe (layout + this layer + dark joints):
#   1. TILING (the half-tile test): bake the picture, bake it again with the whole pattern slid by half a tile in both directions, and
#      compare the second picture with the first one rolled by half its size. If the layer repeats exactly at the tile edge, the two
#      are the same picture (a tiny difference is allowed for the edge dots). A WRONG roll is measured too, as the control: it must
#      differ a lot, otherwise the test would pass for any picture. Done for one tile and for a 2 x 2 area (recipe.tiles_across = 2).
#   2. NEW CONTENT in the 2 x 2 area: the picture compared with itself rolled by one base tile must differ a lot (a repeated tile would not).
#   3. INDEPENDENCE of the layer from the others: change this layer's Seed and see that the joints, the slate outlines (the layout) and
#      everything outside the slates stay exactly the same; change the LAYOUT seed and see that the slates change; Amount 0 = a flat
#      picture with no fade (and Height and Roughness exactly 0 inside the slates).
# Use (plain python):  python3 -I layer_tests.py [SIZE]       writes layer_tests_results.json and layer_tests_table.md next to this file.
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 512
PARTS = sys.argv[2:] or ['tiling', 'independence']          # which tests to run (results of the others are kept from the last run)
OUT = os.path.join(HERE, 'layer_tests_pictures')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, 'layer_only_recipe.py')
BAKE_TOOLS = os.path.join(HERE, '..', 'bake_tools.py')
P = 'colour_and_fade.'


def bake(name, size, views, base=None, channels='Colour,Height'):
    folder = os.path.join(OUT, name)
    subprocess.run(BLENDER + [BAKE_TOOLS, '--', RECIPE, folder, str(size), '4', json.dumps(views), json.dumps(base or {}), channels],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def load(folder, name, kind='colour'):
    image = cv2.imread(os.path.join(folder, f'{name}_{kind}.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0)


def differences(a, b, limit=40 / 255.0):
    delta = np.abs(a - b).max(axis=2)
    return {'mean difference (of 255)': round(float(delta.mean() * 255), 3), 'share of dots over 40 (%)': round(float((delta > limit).mean() * 100), 4)}


def main():
    results_path = os.path.join(HERE, 'layer_tests_results.json')
    results = json.load(open(results_path)) if os.path.exists(results_path) else {}
    # ---- 1. tiling, one tile and 2 x 2
    for tiles in ((1, 2) if 'tiling' in PARTS else ()):
        size = SIZE * tiles
        base = {'recipe.tiles_across': tiles}
        folder = bake(f'tiling_{tiles}', size, {'plain': {}, 'shifted': {'shift': [0.5, 0.5]}, 'plain_mask': {'view': 'mask'}, 'shifted_mask': {'view': 'mask', 'shift': [0.5, 0.5]}}, base)
        plain, shifted = load(folder, 'plain'), load(folder, 'shifted')
        rolled = np.roll(np.roll(plain, size // 2, axis=0), size // 2, axis=1)
        wrong = np.roll(plain, size // 2, axis=1)
        mask_plain, mask_shifted = load(folder, 'plain_mask'), load(folder, 'shifted_mask')
        results[f'tiling, tiles_across {tiles}'] = {
            'colour: shifted vs rolled': differences(shifted, rolled), 'colour: WRONG roll (control)': differences(shifted, wrong),
            'fade strength: shifted vs rolled': differences(mask_shifted, np.roll(np.roll(mask_plain, size // 2, axis=0), size // 2, axis=1))}
        delta = np.abs(shifted - rolled).max(axis=2)
        band = np.zeros(delta.shape, bool)                                          # dots within 3 dots of the lines where the ORIGINAL tile edge now sits
        band[:, size // 2 - 3:size // 2 + 3] = True
        band[size // 2 - 3:size // 2 + 3, :] = True
        results[f'tiling, tiles_across {tiles}']['colour: share of dots over 10/255 inside the 6-dot band along the old tile edge vs elsewhere (%)'] = [
            round(float((delta[band] > 10 / 255.0).mean() * 100), 3), round(float((delta[~band] > 10 / 255.0).mean() * 100), 3)]
        if tiles == 2:
            one_tile = plain[:, :, :]
            by_one_tile = np.roll(np.roll(one_tile, size // 2, axis=0), size // 2, axis=1)      # base tile = half of the picture
            results['new content in the 2 x 2 area'] = {'picture vs itself rolled by one base tile (a repeat would be near 0.9)': differences(plain, by_one_tile)}
    if 'independence' in PARTS:
        # ---- 3. independence
        folder = bake('independence', SIZE, {'base': {}, 'seed12': {P + 'seed': 12.0}, 'amount0': {P + 'amount': 0.0}, 'layout_seed2': {'layout.seed': 2.0},
                                            'layout_only': {'view': 'layout_only'}, 'joints': {'view': 'joints'}, 'mask_base': {'view': 'mask'}, 'mask_amount0': {'view': 'mask', P + 'amount': 0.0}},
                      channels='Colour,Height,Roughness')
        base_c = load(folder, 'base')
        mask_picture = load(folder, 'joints')[..., 0]                                          # LAYOUT's piece_mask as grey (sRGB-encoded 0..1): 1 on a slate, 0 in a joint
        inside = cv2.erode((mask_picture > 0.99).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)         # slate dots at least 3 dots from a joint
        outside = cv2.erode((mask_picture < 0.01).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)        # joint dots at least 1 dot from a slate
        height_base, height_seed12 = load(folder, 'base', 'height')[..., 0], load(folder, 'seed12', 'height')[..., 0]
        height_layout, height_amount0 = load(folder, 'layout_only', 'height')[..., 0], load(folder, 'amount0', 'height')[..., 0]

        def where(a, b):
            delta = np.abs(a - b).max(axis=2)
            return {'changed inside slates (% of slate dots)': round(float((delta[inside] > 2 / 255.0).mean() * 100), 2),
                    'changed in joints (% of joint dots)': round(float((delta[outside] > 2 / 255.0).mean() * 100), 4)}
        tone_relief = (height_base - height_layout)[inside]
        results['independence'] = {
            'this layer seed 11 -> 12 (colour)': where(base_c, load(folder, 'seed12')),
            'this layer seed 11 -> 12 (height, exact 16 bit): changed in joints (% of joint dots, > 0.0005)': round(float((np.abs(height_base - height_seed12)[outside] > 0.0005).mean() * 100), 4),
            'layout seed 1 -> 2 (the slates move): colour changed in joints (% of the old joint dots)': where(base_c, load(folder, 'layout_seed2'))['changed in joints (% of joint dots)'],
            'the layer\'s own tone relief inside slates (height): lowest / highest / spread': [round(float(tone_relief.min()), 3), round(float(tone_relief.max()), 3), round(float(tone_relief.std()), 3)],
            'amount 0: height minus layout height, largest absolute value (must be 0)': round(float(np.abs(height_amount0 - height_layout).max()), 6),
            'amount 0: roughness, lowest / highest (must both be the base 0.8; the 8-bit picture has a dither of plus or minus 1/255)': [round(float(load(folder, 'amount0', 'roughness').min()), 4), round(float(load(folder, 'amount0', 'roughness').max()), 4)],
            'amount 1: roughness inside slates, lowest / highest': [round(float(load(folder, 'base', 'roughness')[inside].min()), 3), round(float(load(folder, 'base', 'roughness')[inside].max()), 3)],
            'amount 0: fade strength picture, largest value (must be 0; 8-bit dither 0.004)': round(float(load(folder, 'mask_amount0').max()), 4),
        }
        flat = load(folder, 'amount0')
        slate_values = flat[inside].reshape(-1, 3)
        results['independence']['amount 0 (colour): % of slate dots that are not the single flat middle tone'] = round(float((np.abs(slate_values - np.median(slate_values, axis=0)).max(axis=1) > 3 / 255.0).mean() * 100), 3)
    with open(os.path.join(HERE, 'layer_tests_results.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    lines = ['# COLOUR AND FADE - layer tests (written by layer_tests.py)', '', f'Size {SIZE} dots per base tile (2 x 2 area: {SIZE * 2}).', '']
    for key, value in results.items():
        lines.append(f'## {key}')
        for k, v in value.items():
            lines.append(f'* {k}: {v}')
        lines.append('')
    with open(os.path.join(HERE, 'layer_tests_table.md'), 'w') as handle:
        handle.write('\n'.join(lines))
    print(json.dumps(results, indent=1))


if __name__ == '__main__':
    main()

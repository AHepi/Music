# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Makes the overview pictures of the COLOUR AND FADE layer by itself (LAYOUT + this layer + dark joints):
#   before_after.png   the layer switched OFF (Amount 0: every slate the one middle tone) next to the fade switched off (per-slate tones only) and the
#                      finished default
#   variations.png     eight settings variations of the layer (fresh, faded and sun-bleached, damp, heavy drips, reversed fade, green-tinted, ...)
#   resolution.png     the SAME small area of the tile baked at 512, 1254 and 2508 dots across the tile, shown at one size (sizes are in tile units,
#                      so the look must not change, only the sharpness)
# Pictures are written to ../../variations/colour_and_fade/ and ../../resolution/colour_and_fade/ (my own sub-folders) and this folder.
# Use (plain python): python3 -I make_sheets.py [before_after] [variations] [resolution]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SLATE_LAYERS = os.path.abspath(os.path.join(HERE, '..', '..'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, 'layer_only_recipe.py')
P = 'colour_and_fade.'

VARIATIONS = {
    'default (seed 11)': {},
    'another roll of the paint (seed 21)': {P + 'seed': 21.0},
    'fresh slate: little fade, no bleach or damp': {P + 'fade_amount': 0.25, P + 'bleach_amount': 0.0, P + 'stain_amount': 0.0, P + 'speck_amount': 0.3, P + 'streak_contrast': 0.4, P + 'tone_centre': 4.8},
    'faded and sun-bleached': {P + 'tone_centre': 5.3, P + 'bleach_amount': 1.0, P + 'bleach_cover': 0.45, P + 'fade_amount': 1.3, P + 'drift_amount': 1.0, P + 'tint_amount': 0.3},
    'damp and dark': {P + 'tone_centre': 3.2, P + 'stain_amount': 1.0, P + 'stain_cover': 0.4, P + 'fade_amount': 1.2},
    'heavy long drips': {P + 'fade_length': 0.15, P + 'streak_width': 0.024, P + 'fade_amount': 1.7, P + 'streak_contrast': 1.5},
    'reversed fade (bleached above, dark below)': {P + 'fade_direction': -1.0},
    'old roof: green-tinted slates and patches': {P + 'tint_amount': 1.0, P + 'tint_green_share': 1.0, P + 'patch_tint': 0.9, P + 'tone_spread': 0.9},
}
BEFORE_AFTER = {'layer OFF (amount 0): every slate the same middle tone': {P + 'amount': 0.0},
                'fade OFF (fade_amount 0): per-slate tones, tints, big patches only': {P + 'fade_amount': 0.0},
                'default': {}}


def bake(name, size, views, region=(0, 0, 1, 1)):
    folder = os.path.join(HERE, 'sheet_pictures', name)
    subprocess.run(BLENDER + [os.path.join(HERE, 'bake_region.py'), '--', RECIPE, folder, str(size), *[str(v) for v in region], '4', json.dumps(views), '{}', 'Colour'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def banner(image, text):
    bar = np.full((30, image.shape[1], 3), 245, np.uint8)
    cv2.putText(bar, text[:80], (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([bar, image])


def grid(items, columns, cell=None):
    tiles = []
    for image, label in items:
        if cell:
            image = cv2.resize(image, (cell, int(image.shape[0] * cell / image.shape[1])), interpolation=cv2.INTER_AREA)
        tiles.append(banner(image, label))
    while len(tiles) % columns:
        tiles.append(np.full_like(tiles[0], 255))
    return np.vstack([np.hstack([np.hstack([t, np.full((t.shape[0], 6, 3), 255, np.uint8)]) for t in tiles[i:i + columns]]) for i in range(0, len(tiles), columns)])


def main():
    what = sys.argv[1:] or ['before_after', 'variations', 'resolution']
    if 'before_after' in what:
        views = {f'v{i}': s for i, s in enumerate(BEFORE_AFTER.values())}
        folder = bake('before_after', 800, views)
        items = [(cv2.imread(os.path.join(folder, f'v{i}_colour.png')), label) for i, label in enumerate(BEFORE_AFTER)]
        out = grid(items, 3, 620)
        cv2.imwrite(os.path.join(HERE, 'before_after.png'), out)
        print('wrote before_after.png', flush=True)
    if 'variations' in what:
        views = {f'v{i}': s for i, s in enumerate(VARIATIONS.values())}
        folder = bake('variations', 640, views)
        out_folder = os.path.join(SLATE_LAYERS, 'variations', 'colour_and_fade')
        os.makedirs(out_folder, exist_ok=True)
        items = []
        for i, label in enumerate(VARIATIONS):
            image = cv2.imread(os.path.join(folder, f'v{i}_colour.png'))
            cv2.imwrite(os.path.join(out_folder, f'variation_{i + 1}.png'), image)
            items.append((image, label))
        cv2.imwrite(os.path.join(out_folder, 'colour_and_fade_variations.png'), grid(items, 4, 480))
        json.dump({label: s for label, s in VARIATIONS.items()}, open(os.path.join(out_folder, 'variations_settings.json'), 'w'), indent=1)
        print('wrote variations', flush=True)
    if 'resolution' in what:
        region = (0.0, 0.06, 0.25, 0.18)
        shown = []
        out_folder = os.path.join(SLATE_LAYERS, 'resolution', 'colour_and_fade')
        os.makedirs(out_folder, exist_ok=True)
        for size in (512, 1254, 2508):
            path = os.path.join(out_folder, f'crop_{size}.png')
            if not os.path.exists(path) or 'rebake' in sys.argv:
                folder = bake(f'resolution_{size}', size, {'a': {}}, region)
                image = cv2.imread(os.path.join(folder, 'a_colour.png'))
                cv2.imwrite(path, image)
            image = cv2.imread(path)
            shown.append((cv2.resize(image, (627, 301), interpolation=cv2.INTER_NEAREST if size < 2508 else cv2.INTER_AREA), f'{size} dots per tile ({image.shape[1]} x {image.shape[0]} dots here, shown at 627 x 301)'))
        cv2.imwrite(os.path.join(out_folder, 'colour_and_fade_resolution.png'), grid(shown, 3))
        print('wrote resolution', flush=True)


if __name__ == '__main__':
    main()

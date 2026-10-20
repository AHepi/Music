# What this does (plain words): checks that the OUTLINE AND SHADOW layer is INDEPENDENT of the other layers, in both directions.
#  (1) The layer alone: its own Mask, Height and Roughness (debug views) must NOT change at all when another layer (colour_and_fade, damage, moss)
#      is switched off (Amount 0) or given another Seed, because it only reads the layout bundle. (Expected: 0.000 percent of dots changed.)
#  (2) The finished picture: when THIS layer is switched off (Amount 0) or given another Seed, the finished colour, height and roughness may change
#      only where this layer paints: inside the union of its mask before and its mask after (> 0.01). (Expected: 0.000 percent outside.)
#  (3) When the LAYOUT seed changes, this layer changes (it reads the layout): shown for completeness, no pass/fail.
# It bakes at a small size (default 384 dots), 4 samples. The Seed numbers are the layers' defaults + 1.
# Use (plain python):  python3 -I independence_test.py [SIZE] [OUT_FOLDER]       Output: independence_results.json and independence_table.md
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 384
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'independence')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
BAKE_TOOLS = os.path.join(HERE, '..', 'tests', 'bake_tools.py')
DEFAULT_SEEDS = {'layout': 1.0, 'colour_and_fade': 11.0, 'damage': 21.0, 'moss': 31.0, 'outline_and_shadow': 41.0}
OWN = 'outline_and_shadow'
VIEWS = {'full': {}, 'own_mask': {'debug_view': OWN + '.mask'}, 'own_height': {'debug_view': OWN + '.height'}, 'own_roughness': {'debug_view': OWN + '.roughness'}}


def bake(name, params):
    folder = os.path.join(OUT, name)
    subprocess.run(BLENDER + [BAKE_TOOLS, '--', RECIPE, folder, str(SIZE), '4', json.dumps(VIEWS), json.dumps(params), 'Colour,Height'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def load(folder, view, kind):
    image = cv2.imread(os.path.join(folder, view + ('_colour.png' if kind == 'colour' else '_height.png')), cv2.IMREAD_UNCHANGED).astype(np.float64)
    image = image if image.ndim == 3 else image[..., None]
    return image / (65535.0 if kind == 'height' else 255.0)


def changed(a, b, limit):
    return (np.abs(a - b).max(axis=2) > limit)


def main():
    os.makedirs(OUT, exist_ok=True)
    base = bake('base', {})
    # the finished roughness is not in the 'full' view (bake_tools shows Colour and Height); the layer's own roughness is, as a debug view
    rows = []
    mask_base = load(base, 'own_mask', 'height').max(axis=2) > 0.01
    variants = []
    for layer in ('colour_and_fade', 'damage', 'moss'):
        variants.append((f'{layer} Amount 0', {f'{layer}.amount': 0.0}, 'other'))
        variants.append((f'{layer} Seed + 1', {f'{layer}.seed': DEFAULT_SEEDS[layer] + 1.0}, 'other'))
    variants.append((f'{OWN} Amount 0', {f'{OWN}.amount': 0.0}, 'own'))
    variants.append((f'{OWN} Seed + 1', {f'{OWN}.seed': DEFAULT_SEEDS[OWN] + 1.0}, 'own'))
    variants.append(('layout Seed + 1', {'layout.seed': DEFAULT_SEEDS['layout'] + 1.0}, 'layout'))
    for name, params, kind in variants:
        folder = bake(name.replace(' ', '_').replace('+', 'plus'), params)
        row = {'variant': name}
        # (1) the layer alone
        own_changed = np.zeros((SIZE, SIZE), bool)
        for view, limit in (('own_mask', 0.002), ('own_height', 0.0003), ('own_roughness', 0.0003)):
            own_changed |= changed(load(base, view, 'height'), load(folder, view, 'height'), limit)
        row['layer alone (mask, height, roughness): dots changed %'] = round(100 * own_changed.mean(), 4)
        # (2) the finished picture
        mask_variant = load(folder, 'own_mask', 'height').max(axis=2) > 0.01
        union = mask_base | mask_variant
        full_colour = changed(load(base, 'full', 'colour'), load(folder, 'full', 'colour'), 2 / 255)
        full_height = changed(load(base, 'full', 'height'), load(folder, 'full', 'height'), 0.002)
        row['finished colour: dots changed %'] = round(100 * full_colour.mean(), 3)
        row['finished colour: changed outside this layer\'s mask %'] = round(100 * (full_colour & ~union).mean(), 4)
        row['finished height: dots changed %'] = round(100 * full_height.mean(), 3)
        row['finished height: changed outside this layer\'s mask %'] = round(100 * (full_height & ~union).mean(), 4)
        row['kind'] = kind
        rows.append(row)
    with open(os.path.join(OUT, 'independence_results.json'), 'w') as handle:
        json.dump(rows, handle, indent=1)
    lines = ['| what was changed | layer alone changed % (expect 0 unless it is this layer or the layout) | finished colour changed % | colour changed outside this layer\'s mask % | finished height changed % | height changed outside this layer\'s mask % |', '|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['variant']} | {r['layer alone (mask, height, roughness): dots changed %']} | {r['finished colour: dots changed %']} | "
                     f"{r['finished colour: changed outside this layer\'s mask %']} | {r['finished height: dots changed %']} | {r['finished height: changed outside this layer\'s mask %']} |")
    with open(os.path.join(OUT, 'independence_table.md'), 'w') as handle:
        handle.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()

# What this does (plain words): checks that the layers are INDEPENDENT of each other: change one layer (its Amount to 0, or its Seed)
# and only that layer's part of the picture may change.
# How: it bakes the colour, the exact height and the roughness of the recipe at a small size (default 384 dots), once as it is and once per
# variant, and for each variant counts the dots that changed (colour: more than 2 steps of 255; height: more than 0.002; roughness: more
# than 0.005) as a share of all dots. It also says WHERE the changes are: inside the layer's own mask (read from a debug bake of that
# layer's Mask) or outside it. "Outside the mask" must be 0 except for the declared links (listed in the layer files' DECLARED_LINKS).
# The result is written as independence_results.json and a plain table in independence_table.md.
# Use (plain python, not Blender):  python3 -I independence_test.py [SIZE] [OUT_FOLDER]
# With the placeholder layers only the layout and the colour layer can change anything; once the real layers exist this same script
# is the independence table of the guide (add the declared-link rows to LINKS below).
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
LAYERS = ['layout', 'colour_and_fade', 'damage', 'moss', 'outline_and_shadow']
# changes that are ALLOWED outside a layer's own mask, because the layer files declare a link: {changed layer: [layers whose result may change too]}
LINKS = {'layout': ['colour_and_fade', 'damage', 'moss', 'outline_and_shadow'],      # every layer reads the layout bundle
         'damage': ['moss']}                                                           # moss reads damage's Mask ('Damage Mask')


def bake(name, params, channels='Colour,Height,Roughness', views=None):
    folder = os.path.join(OUT, name)
    views = views or {'view': {}}
    subprocess.run(BLENDER + [os.path.join(HERE, 'bake_tools.py'), '--', RECIPE, folder, str(SIZE), '4', json.dumps(views), json.dumps(params), channels],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def load(folder, name, kind):
    suffix = {'colour': '_colour.png', 'height': '_height.png', 'roughness': '_roughness.png'}[kind]
    image = cv2.imread(os.path.join(folder, name + suffix), cv2.IMREAD_UNCHANGED).astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0)


def changed(base_folder, variant_folder):
    result = {}
    for kind, limit in (('colour', 2 / 255), ('height', 0.002), ('roughness', 0.005)):
        a, b = load(base_folder, 'view', kind), load(variant_folder, 'view', kind)
        result[kind] = np.abs(a - b).max(axis=2) > limit
    return result


def layer_mask(layer_key):
    """The layer's own Mask (> 0.01) from a debug bake; for the layout and the colour layer it is the whole slate."""
    if layer_key == 'layout':
        return np.ones((SIZE, SIZE), bool)
    folder = bake(f'mask_{layer_key}', {}, 'Height', {'view': {'debug_view': f'{layer_key}.mask'}})
    data = load(folder, 'view', 'height').max(axis=2)
    return data > 0.01


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    base = bake('base', {})
    rows = []
    for layer in LAYERS:
        mask = layer_mask(layer)
        for variant, params in (('Amount 0', {f'{layer}.amount': 0.0}), ('Seed + 1', {f'{layer}.seed': (1.0 if layer == 'layout' else {'colour_and_fade': 11.0, 'damage': 21.0, 'moss': 31.0, 'outline_and_shadow': 41.0}[layer]) + 1.0})):
            if layer == 'layout' and variant == 'Amount 0':
                continue                      # the layout has no Amount: it is the surface itself
            folder = bake(f'{layer}_{variant.replace(" ", "_").replace("+", "plus")}', params)
            diffs = changed(base, folder)
            row = {'layer changed': layer, 'variant': variant}
            for kind, d in diffs.items():
                row[f'{kind}: share of dots changed %'] = round(100 * d.mean(), 3)
                row[f'{kind}: changed outside the layer mask %'] = round(100 * (d & ~mask).mean(), 3)
            rows.append(row)
    with open(os.path.join(OUT, 'independence_results.json'), 'w') as handle:
        json.dump(rows, handle, indent=1)
    lines = ['| layer changed | variant | colour changed % | colour changed outside own mask % | height changed % | height outside own mask % | roughness changed % | roughness outside own mask % |', '|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['layer changed']} | {r['variant']} | {r['colour: share of dots changed %']} | {r['colour: changed outside the layer mask %']} | "
                     f"{r['height: share of dots changed %']} | {r['height: changed outside the layer mask %']} | {r['roughness: share of dots changed %']} | {r['roughness: changed outside the layer mask %']} |")
    with open(os.path.join(OUT, 'independence_table.md'), 'w') as handle:
        handle.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))

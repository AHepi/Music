# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# PROVES that the layers of the slate recipe are independent. For every layer it bakes the WHOLE recipe once as it is and once with
# (a) that layer's Amount set to 0 (layer switched off) and (b) that layer's Seed changed by +1 (a new random pattern). Then it counts, dot by dot,
# what changed:
#   * in the FINISHED colour, height and roughness pictures;
#   * in every layer's own Mask (baked alone as a debug picture): "did the damage pattern change when I changed the moss seed?";
#   * and WHERE the finished picture changed: inside the layer's own region (fine: that is the layer's contribution) or OUTSIDE it (must be 0).
# A layer's own region = the dots where its Mask is above 0 in the baseline or in the variant (for COLOUR AND FADE, the bottom layer that paints
# the whole slate: every dot of a slate; for LAYOUT: everything). Differences outside the region must be exactly zero, except the DECLARED link
# (MOSS reads DAMAGE's Mask, so a new damage pattern may change MOSS, but only on dots where the damage Mask is above 0).
# Dots count as changed when colour differs by more than 1/255 in any channel, height by more than 0.0005 (about 33 steps of 16 bit) or
# roughness by more than 0.004. Output: independence_table.md, independence_results.json, a picture sheet.
# Use (plain python, not Blender):  python3 -I independence_full.py [SIZE] [OUT_FOLDER] [SETTINGS_JSON_TO_START_FROM]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 384
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'independence_full')
BASE_SETTINGS = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
LAYERS = ['layout', 'colour_and_fade', 'damage', 'moss', 'outline_and_shadow']
DEFAULT_SEEDS = {'layout': 1.0, 'colour_and_fade': 11.0, 'damage': 21.0, 'moss': 31.0, 'outline_and_shadow': 41.0}
MASK_VIEWS = {'m_colour_and_fade': {'debug_view': 'colour_and_fade.mask'}, 'm_damage': {'debug_view': 'damage.mask'},
              'm_moss': {'debug_view': 'moss.mask'}, 'm_outline_and_shadow': {'debug_view': 'outline_and_shadow.mask'},
              'm_piece_id': {'debug_view': 'bundle.piece_id'}, 'm_piece_mask': {'debug_view': 'bundle.piece_mask'}}
# the one declared link: {layer that is changed: [layers allowed to change as a result, but only inside the changed layer's own region]}
DECLARED = {'damage': ['moss']}
LIMIT = {'colour': 1.0 / 255.0, 'height': 0.0005, 'roughness': 0.004, 'mask': 1.5 / 65535.0}


def bake(name, parameters, channels, views):
    folder = os.path.join(OUT, name)
    if os.path.isdir(folder) and len(os.listdir(folder)) >= len(views):
        return folder                                         # already baked (pictures are kept so that the analysis can be run again)
    params = dict(BASE_SETTINGS)
    params.update(parameters)
    subprocess.run(BLENDER + [os.path.join(HERE, 'bake_tools.py'), '--', RECIPE, folder, str(SIZE), '4', json.dumps(views), json.dumps(params), channels],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return folder


def read(folder, name, kind):
    suffix = {'colour': '_colour.png', 'height': '_height.png', 'roughness': '_roughness.png'}[kind]
    image = cv2.imread(os.path.join(folder, name + suffix), cv2.IMREAD_UNCHANGED).astype(np.float64)
    image = image / (65535.0 if image.dtype != np.uint8 and image.max() > 255 else 255.0)
    return image


def read_mask(folder, name):
    # a mask is shown exactly in the Height picture (16 bit)
    image = cv2.imread(os.path.join(folder, name + '_height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0
    return image.max(axis=2) if image.ndim == 3 else image


def bake_variant(name, parameters):
    final = bake(name + '_final', parameters, 'Colour,Height,Roughness', {'view': {}})
    masks = bake(name + '_masks', parameters, 'Height', MASK_VIEWS)
    return final, masks


def load_all(final, masks):
    data = {'colour': np.abs(read(final, 'view', 'colour')), 'height': read(final, 'view', 'height').max(axis=2), 'roughness': read(final, 'view', 'roughness').max(axis=2)}
    for key in MASK_VIEWS:
        data[key] = read_mask(masks, key)
    return data


def own_region(layer, base, variant):
    if layer == 'layout':
        return np.ones((SIZE, SIZE), bool)
    if layer == 'colour_and_fade':
        return (np.maximum(base['m_piece_mask'], variant['m_piece_mask']) > 0.001)
    key = {'damage': 'm_damage', 'moss': 'm_moss', 'outline_and_shadow': 'm_outline_and_shadow'}[layer]
    return np.maximum(base[key], variant[key]) > 0.5 / 65535.0           # any mask above exactly zero (16-bit)


def dilate(region, dots):
    return cv2.dilate(region.astype(np.uint8), np.ones((2 * dots + 1, 2 * dots + 1), np.uint8)).astype(bool)


def changes(base, variant):
    out = {}
    out['colour'] = np.abs(base['colour'] - variant['colour']).max(axis=2) > LIMIT['colour']
    out['height'] = np.abs(base['height'] - variant['height']) > LIMIT['height']
    out['roughness'] = np.abs(base['roughness'] - variant['roughness']) > LIMIT['roughness']
    for key in MASK_VIEWS:
        out[key] = np.abs(base[key] - variant[key]) > LIMIT['mask']
    return out


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    base = load_all(*bake_variant('base', {}))
    rows, pictures = [], {}
    for layer in LAYERS:
        for variant, parameters in (('Amount 0', {f'{layer}.amount': 0.0}), ('Seed + 1', {f'{layer}.seed': DEFAULT_SEEDS[layer] + 1.0})):
            if layer == 'layout' and variant == 'Amount 0':
                continue                                       # the layout has no Amount: it is the surface itself
            name = f'{layer}_{variant.replace(" ", "_").replace("+", "plus")}'
            data = load_all(*bake_variant(name, parameters))
            diff = changes(base, data)
            region = own_region(layer, base, data)
            allowed = np.zeros_like(region)
            for other in DECLARED.get(layer, []):
                allowed |= region                              # the declared link may change the other layer, only inside this layer's own region
            outside = ~region
            row = {'layer changed': layer, 'variant': variant, 'own region share %': round(100 * region.mean(), 2)}
            for kind in ('colour', 'height', 'roughness'):
                row[f'{kind} changed %'] = round(100 * diff[kind].mean(), 3)
                row[f'{kind} changed outside own region %'] = round(100 * (diff[kind] & outside).mean(), 4)
            for other in LAYERS[1:]:
                key = 'm_' + other
                row[f'{other} mask changed %'] = round(100 * diff[key].mean(), 3)
                row[f'{other} mask changed outside {layer} region %'] = round(100 * (diff[key] & outside).mean(), 4)
            row['slates changed (piece_id) %'] = round(100 * diff['m_piece_id'].mean(), 3)
            rows.append(row)
            shown = np.zeros((SIZE, SIZE, 3), np.uint8)
            shown[..., 2] = (diff['colour'] * 255).astype(np.uint8)                     # red = finished colour changed
            shown[..., 1] = (region * 90).astype(np.uint8)                              # green = the layer's own region
            shown[..., 0] = (np.stack([diff[k] for k in ('height', 'roughness')]).any(0) * 255).astype(np.uint8)   # blue = height or roughness changed
            pictures[name] = shown
            cv2.imwrite(os.path.join(OUT, name + '_where.png'), shown)
    with open(os.path.join(OUT, 'independence_results.json'), 'w') as handle:
        json.dump(rows, handle, indent=1)
    columns = ['layer changed', 'variant', 'own region share %', 'colour changed %', 'colour changed outside own region %', 'height changed %', 'height changed outside own region %',
               'roughness changed %', 'roughness changed outside own region %']
    lines = ['| ' + ' | '.join(columns) + ' |', '|' + '---|' * len(columns)]
    for row in rows:
        lines.append('| ' + ' | '.join(str(row[c]) for c in columns) + ' |')
    lines += ['', 'Which other layers\' own patterns (Masks) changed (share of all dots; "outside" = outside the changed layer\'s own region):', '',
              '| layer changed | variant | slates (piece_id) | colour_and_fade mask | damage mask | moss mask | outline_and_shadow mask |', '|---|---|---|---|---|---|---|']
    for row in rows:
        cells = [row['layer changed'], row['variant'], str(row['slates changed (piece_id) %'])]
        for other in LAYERS[1:]:
            if other == row['layer changed']:
                cells.append('(itself) ' + str(row[other + ' mask changed %']))
            else:
                inside_name = other + ' mask changed outside ' + row['layer changed'] + ' region %'
                cells.append(str(row[other + ' mask changed %']) + ' (outside ' + str(row[inside_name]) + ')')
        lines.append('| ' + ' | '.join(cells) + ' |')
    with open(os.path.join(OUT, 'independence_table.md'), 'w') as handle:
        handle.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))

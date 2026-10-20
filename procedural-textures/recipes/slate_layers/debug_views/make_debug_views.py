# What this does (plain words): bakes every layer of the slate recipe ALONE (the "debug views"): for each of COLOUR AND FADE, DAMAGE, MOSS and
# OUTLINE AND SHADOW its MASK (white = where the layer paints) and its COLOUR (what the layer would paint, on every dot), at 1254 dots, and its HEIGHT and
# ROUGHNESS change at 640 dots (grey 0.5 = no change). Also the layout's slates in random colours. Then it puts them on one sheet per layer and one overview sheet.
# Use (plain python): python3 -I make_debug_views.py [bake|sheets|all]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
LAYERS = ['colour_and_fade', 'damage', 'moss', 'outline_and_shadow']
TITLES = {'colour_and_fade': 'COLOUR AND FADE', 'damage': 'DAMAGE', 'moss': 'MOSS', 'outline_and_shadow': 'OUTLINE AND SHADOW'}
step = sys.argv[1] if len(sys.argv) > 1 else 'all'


def run(size, views):
    subprocess.run(BLENDER + [os.path.join(HERE, '..', 'tests', 'bake_tools.py'), '--', RECIPE, HERE, str(size), '4', json.dumps(views), '{}', 'Colour'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if step in ('bake', 'all'):
    big = {'layout_slates': {'debug_view': 'bundle.piece_colour'}}
    small = {}
    for layer in LAYERS:
        big[f'{layer}_mask'] = {'debug_view': f'{layer}.mask'}
        big[f'{layer}_colour'] = {'debug_view': f'{layer}.colour'}
        small[f'{layer}_height_640'] = {'debug_view': f'{layer}.height'}
        small[f'{layer}_roughness_640'] = {'debug_view': f'{layer}.roughness'}
    run(1254, big)
    run(640, small)
if step in ('sheets', 'all'):
    def read(name, size):
        picture = cv2.imread(os.path.join(HERE, name + '_colour.png'))
        return cv2.resize(picture, (size, size), interpolation=cv2.INTER_AREA)

    def label(picture, text):
        cv2.putText(picture, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return picture
    cell = 500
    final = cv2.resize(cv2.imread(os.path.join(HERE, '..', 'outputs', 'default', 'colour.png')), (cell, cell), interpolation=cv2.INTER_AREA)
    overview = [[label(read('layout_slates', cell), 'LAYOUT: one random colour per slate'), label(final.copy(), 'FINISHED colour (all layers)')]]
    for layer in LAYERS:
        sheet = np.hstack([label(read(f'{layer}_mask', cell), f'{TITLES[layer]} mask'), label(read(f'{layer}_colour', cell), f'{TITLES[layer]} colour (everywhere)'),
                           label(read(f'{layer}_height_640', cell), 'height change (grey = none)'), label(read(f'{layer}_roughness_640', cell), 'roughness change (grey = none)')])
        cv2.imwrite(os.path.join(HERE, f'sheet_{layer}.png'), sheet)
    rows = [np.hstack([label(read(f'{l}_mask', cell), f'{TITLES[l]} mask'), label(read(f'{l}_colour', cell), f'{TITLES[l]} colour')]) for l in LAYERS]
    cv2.imwrite(os.path.join(HERE, 'overview_masks_and_colours.png'), np.vstack([np.hstack(overview[0])] + rows))

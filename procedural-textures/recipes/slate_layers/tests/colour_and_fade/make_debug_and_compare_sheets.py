# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Makes two overview pictures with the REAL recipe (recipe/slate_recipe.py, all the layers that exist when you run it):
#   ../../debug_views/colour_and_fade/colour_and_fade_debug_views.png   the whole recipe next to this layer's own outputs through the
#       recipe's debug_view setting: Colour, Mask (fade strength), Height (tone relief, stretched 2x around 0.5 = no change), Roughness change
#   compare_with_reference.png   the reference (as a guide only) | this layer alone (layout + layer) | the whole recipe from the harness bake
# Use (plain python): python3 -I make_debug_and_compare_sheets.py     (needs full_stack_1254/colour.png and pictures/layer_only_colour_1254.png)
import json
import os
import subprocess

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SLATE_LAYERS = os.path.abspath(os.path.join(HERE, '..', '..'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(SLATE_LAYERS, 'recipe', 'slate_recipe.py')
OUT = os.path.join(SLATE_LAYERS, 'debug_views', 'colour_and_fade')
os.makedirs(OUT, exist_ok=True)
views = {'full': {}, 'mask': {'debug_view': 'colour_and_fade.mask'}, 'colour': {'debug_view': 'colour_and_fade.colour'},
         'height': {'debug_view': 'colour_and_fade.height', 'debug_scale': 2}, 'roughness': {'debug_view': 'colour_and_fade.roughness'}}
folder = os.path.join(HERE, 'dev_debug')
subprocess.run(BLENDER + [os.path.join(HERE, '..', 'bake_tools.py'), '--', RECIPE, folder, '768', '4', json.dumps(views), '{}', 'Colour'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
labels = {'full': 'whole recipe (all layers that exist)', 'colour': 'COLOUR AND FADE colour alone', 'mask': 'fade strength (Mask)',
          'height': 'tone relief (Height; grey 0.5 = none, 2x stretch)', 'roughness': 'roughness change (grey 0.5 = none)'}
tiles = []
for name in ('full', 'colour', 'mask', 'height', 'roughness'):
    image = cv2.imread(os.path.join(folder, f'{name}_colour.png'))
    cv2.imwrite(os.path.join(OUT, f'{name}_768.png'), image)
    bar = np.full((26, image.shape[1], 3), 240, np.uint8)
    cv2.putText(bar, labels[name], (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    tiles.append(np.vstack([bar, image]))
tiles.append(np.full_like(tiles[0], 255))
cv2.imwrite(os.path.join(OUT, 'colour_and_fade_debug_views.png'), np.vstack([np.hstack(tiles[0:3]), np.hstack(tiles[3:6])]))


def label(image, text):
    image = cv2.resize(image, (627, 627), interpolation=cv2.INTER_AREA)
    bar = np.full((30, 627, 3), 245, np.uint8)
    cv2.putText(bar, text, (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)
    return np.vstack([bar, image])


reference = cv2.imread(os.path.join(SLATE_LAYERS, '..', '..', 'reference', 'slate', 'colour.png'))
cv2.imwrite(os.path.join(HERE, 'compare_with_reference.png'), np.hstack([
    label(reference, 'reference (a guide only)'), label(cv2.imread(os.path.join(HERE, 'pictures', 'layer_only_colour_1254.png')), 'COLOUR AND FADE alone (layout + this layer)'),
    label(cv2.imread(os.path.join(HERE, 'full_stack_1254', 'colour.png')), 'whole recipe, harness bake (other layers as built so far)')]))
import shutil
shutil.rmtree(folder, ignore_errors=True)
print('wrote debug views and comparison')

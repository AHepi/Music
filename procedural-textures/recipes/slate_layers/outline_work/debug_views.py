# What this does (plain words): bakes the OUTLINE AND SHADOW layer ALONE (its own Mask, Colour, Height and Roughness as pictures through the debug
# views of the recipe) and the finished recipe, and joins them into one labelled sheet. Also makes "what the layer paints" by laying its Colour over
# flat mid-grey with its Mask (so the colour is only seen where the layer paints), and the layer's mask over the finished picture.
# Use (plain python):  python3 -I debug_views.py [SIZE] [assemble]     ('assemble' = do not bake again, only redraw the sheet)      Output: ../debug_views/outline_and_shadow/ (single pictures and outline_and_shadow_debug_views.png)
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 768
OUT = os.path.abspath(os.path.join(HERE, '..', 'debug_views', 'outline_and_shadow'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
BAKE_TOOLS = os.path.join(HERE, '..', 'tests', 'bake_tools.py')
os.makedirs(OUT, exist_ok=True)
VIEWS = {'full': {}, 'off': {'outline_and_shadow.amount': 0.0},
         'mask': {'debug_view': 'outline_and_shadow.mask'}, 'colour': {'debug_view': 'outline_and_shadow.colour'},
         'height': {'debug_view': 'outline_and_shadow.height'}, 'roughness': {'debug_view': 'outline_and_shadow.roughness'}}


def label(image, text):
    image = image.copy()
    if text:
        cv2.rectangle(image, (0, 0), (image.shape[1], 40), (245, 245, 245), -1)
        cv2.putText(image, text, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 1, cv2.LINE_AA)
    return image


def main():
    if 'assemble' not in sys.argv:          # 'assemble' = only join the pictures that are already baked
        bake()
    sheet()


def bake():
    subprocess.run(BLENDER + [BAKE_TOOLS, '--', RECIPE, OUT, str(SIZE), '4', json.dumps(VIEWS), '{}', 'Colour,Height'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def sheet():
    read = lambda n: cv2.imread(os.path.join(OUT, n + '_colour.png'))
    full, off, mask, colour, height, rough = [read(n) for n in ('full', 'off', 'mask', 'colour', 'height', 'roughness')]
    alpha = mask.astype(np.float32) / 255.0
    painted = (np.full_like(colour, 128, dtype=np.float32) * (1 - alpha) + colour.astype(np.float32) * alpha).astype(np.uint8)
    over_full = (full.astype(np.float32) * 0.45 + np.stack([np.zeros_like(alpha[..., 0]), alpha[..., 0] * 255, np.zeros_like(alpha[..., 0])], axis=-1) * 0.55).astype(np.uint8)
    cv2.imwrite(os.path.join(OUT, 'layer_painted_over_grey.png'), painted)
    row1 = np.hstack([label(full, 'finished (layer on)'), label(off, 'layer OFF (Amount 0)'), label(over_full, 'mask (green) over finished')])
    row2 = np.hstack([label(mask, 'Mask'), label(colour, 'Colour (as the layer outputs it)'), label(painted, 'Colour x Mask over grey')])
    row3 = np.hstack([label(height, 'Height change (grey 0.5 = none; shown x5)'), label(rough, 'Roughness change (grey 0.5 = none; x2)'), label(np.zeros_like(full) + 40, '')])
    cv2.imwrite(os.path.join(OUT, 'outline_and_shadow_debug_views.png'), np.vstack([row1, row2, row3]))
    print('wrote', OUT)


if __name__ == '__main__':
    main()

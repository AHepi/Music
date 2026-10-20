# What this does (plain words): makes the before/after pictures of the OUTLINE AND SHADOW layer: the same recipe with the layer switched off
# (Amount 0) and on (default), (1) as the whole tile at SIZE dots (colour, side by side) and (2) as three zoomed windows (colour, and the finished
# height map beside it). Run with plain Python (it starts Blender itself).
# Use:  python3 -I before_after.py [SIZE] [WINDOW_PIXELS] [assemble]       Output: ../tests/outline_before_after/
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 1254
WINDOW_PIXELS = int(sys.argv[2]) if len(sys.argv) > 2 else 500
OUT = os.path.abspath(os.path.join(HERE, '..', 'tests', 'outline_before_after'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
os.makedirs(OUT, exist_ok=True)
OFF = {'outline_and_shadow.amount': 0.0}


def label(image, text):
    image = image.copy()
    cv2.rectangle(image, (0, 0), (image.shape[1], 34), (245, 245, 245), -1)
    cv2.putText(image, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 1, cv2.LINE_AA)
    return image


def height_picture(path):
    raw = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535.0
    raw = raw if raw.ndim == 2 else raw[..., 0]
    return cv2.cvtColor((np.clip(raw / 0.8, 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)


def main():
    assemble_only = 'assemble' in sys.argv          # 'assemble' = do not bake again, only redraw the sheets from the saved pictures
    if SIZE > 0 and not assemble_only:
        jobs = {'before': {'params': OFF}, 'after': {'params': {}}}
        subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, OUT, str(SIZE), '0.5,0.5,1.0', json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if SIZE > 0:
        a, b = [cv2.imread(os.path.join(OUT, f'{n}_colour.png')) for n in ('before', 'after')]
        cv2.imwrite(os.path.join(OUT, 'whole_tile_before_after.png'), np.hstack([label(a, 'OUTLINE AND SHADOW off'), label(b, 'OUTLINE AND SHADOW on (defaults)')]))
    windows = {'window_a': '0.30,0.62,0.30', 'window_b': '0.72,0.30,0.30', 'window_c': '0.45,0.90,0.30'}
    for name, window in windows.items():
        jobs = {'before': {'params': OFF}, 'after': {'params': {}}, 'before_h': {'params': OFF, 'channel': 'Height'}, 'after_h': {'params': {}, 'channel': 'Height'}}
        folder = os.path.join(OUT, name)
        if not assemble_only:
            subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, folder, str(WINDOW_PIXELS), window, json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        a, b = cv2.imread(os.path.join(folder, 'before_colour.png')), cv2.imread(os.path.join(folder, 'after_colour.png'))
        ha, hb = height_picture(os.path.join(folder, 'before_h_height.png')), height_picture(os.path.join(folder, 'after_h_height.png'))
        top = np.hstack([label(a, 'layer off'), label(b, 'layer on')])
        bottom = np.hstack([label(ha, 'height, layer off'), label(hb, 'height, layer on')])
        cv2.imwrite(os.path.join(OUT, name + '_before_after.png'), np.vstack([top, bottom]))
    print('wrote', OUT)


if __name__ == '__main__':
    main()

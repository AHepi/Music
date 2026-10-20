# What this does (plain words): makes the big area pictures smaller once all measurements are done, to keep this folder under 150 MB:
# colour pictures become JPEG (quality 92), 16-bit height pictures become 8-bit PNG (the exact "which source dot" pictures and the debug pictures
# stay as they are because they are small), the bulky board-colour debug picture and the plain test renders are deleted.
# The measurement scripts can read the shrunk files again, except that the exact pictures are needed for the reuse count (they are kept).
# To redo a measurement that needs a big original picture, bake it again with tools/run_jobs.py and tests/jobs_final_all.json.
import os

import cv2
import numpy as np
from PIL import Image

BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


def colour_to_jpeg(folder):
    p = os.path.join(folder, 'colour.png')
    if os.path.exists(p):
        Image.open(p).convert('RGB').save(os.path.join(folder, 'colour.jpg'), quality=92)
        os.remove(p)


def height_to_8bit(folder):
    p = os.path.join(folder, 'height.png')
    if os.path.exists(p):
        a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
        if a.dtype == np.uint16:
            a = a[..., 0] if a.ndim == 3 else a
            cv2.imwrite(p, np.round(a / 257.0).astype(np.uint8))


for name in ('area_2x2', 'area_4x4', 'tile_repeated_2x2', 'crop_a', 'crop_b', 'crop_c'):
    folder = os.path.join(BASE, 'area', name)
    colour_to_jpeg(folder)
    height_to_8bit(folder)
for name in sorted(os.listdir(os.path.join(BASE, 'area'))):
    if name.startswith('near_copy_'):
        height_to_8bit(os.path.join(BASE, 'area', name))
for path in ('area/debug_boards/colour.png', 'area/debug_flips/colour.png'):
    p = os.path.join(BASE, path)
    if os.path.exists(p) and 'boards' in path:
        os.remove(p)
renders = os.path.join(BASE, 'tests', 'renders')
for root, _, files in os.walk(renders):
    for f in files:
        if f.endswith('.png'):
            os.remove(os.path.join(root, f))
bump = os.path.join(BASE, 'tests', 'cli_check', 'normal_bumpnode.png')
if os.path.exists(bump):
    os.remove(bump)
print('done')

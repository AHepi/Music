# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# Makes two sets of pictures of the MOSS layer with the real recipe (all layers):
#   1. DEBUG VIEWS  (../debug_views/moss/): the layer alone, as pictures: its mask (where it paints), its colour where the mask is 1, its height
#      (0.5 grey = no change, 5 x), its roughness change (0.5 grey = no change, 2 x), plus one sheet that joins them (../debug_views/moss_sheet.png).
#   2. BEFORE / AFTER (../tests/moss/before_after.png and before_after_closeup.png): the finished colour with the moss layer switched off (Amount 0) next to
#      the same picture with the moss layer on, next to the moss mask; and a close-up of the same part of both.
# Use (plain python):  python3 -I make_debug_and_before_after.py [SIZE]      (default 1254; 768 for a quick look)
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 1254
ROOT = os.path.abspath(os.path.join(HERE, '..'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
TOOLS = os.path.join(ROOT, 'tests', 'bake_tools.py')
REAL = os.path.join(HERE, 'frozen', 'recipe', 'slate_recipe.py') if os.environ.get('MOSS_FROZEN') else os.path.join(ROOT, 'recipe', 'slate_recipe.py')      # MOSS_FROZEN=1: use the frozen copy of the whole stack
ONLY = os.path.join(HERE, 'moss_only_recipe.py')
DEBUG = os.path.join(ROOT, 'debug_views', 'moss')
TESTS = os.path.join(ROOT, 'tests', 'moss')
os.makedirs(DEBUG, exist_ok=True)
os.makedirs(TESTS, exist_ok=True)


def bake(recipe, folder, views, channels):
    subprocess.run(BLENDER + [TOOLS, '--', recipe, folder, str(SIZE), '4', json.dumps(views), '{}', channels], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def label(image, text):
    banner = np.full((34, image.shape[1], 3), 245, np.uint8)
    cv2.putText(banner, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([banner, image])


work = os.path.join(HERE, 'dev', 'debug_and_before_after')
bake(REAL, work, {'final_on': {}, 'final_off': {'moss.amount': 0.0}, 'moss_mask': {'debug_view': 'moss.mask'}, 'moss_height': {'debug_view': 'moss.height'},
                  'moss_roughness': {'debug_view': 'moss.roughness'}}, 'Colour')
bake(ONLY, os.path.join(work, 'only'), {'moss_only_flat': {'view': 'moss_only'}, 'on_flat_slate': {'view': 'colour'}}, 'Colour')
pics = {}
for name in ('final_on', 'final_off', 'moss_mask', 'moss_height', 'moss_roughness'):
    pics[name] = cv2.imread(os.path.join(work, name + '_colour.png'))
for name in ('moss_only_flat', 'on_flat_slate'):
    pics[name] = cv2.imread(os.path.join(work, 'only', name + '_colour.png'))
cv2.imwrite(os.path.join(DEBUG, 'moss_mask.png'), pics['moss_mask'])
cv2.imwrite(os.path.join(DEBUG, 'moss_colour_where_mask_is_1.png'), pics['moss_only_flat'])
cv2.imwrite(os.path.join(DEBUG, 'moss_height_0p5_is_no_change_x5.png'), pics['moss_height'])
cv2.imwrite(os.path.join(DEBUG, 'moss_roughness_change_0p5_is_none_x2.png'), pics['moss_roughness'])
cv2.imwrite(os.path.join(DEBUG, 'moss_on_flat_slate.png'), pics['on_flat_slate'])
cell = 640
small = {k: cv2.resize(v, (cell, cell), interpolation=cv2.INTER_AREA) for k, v in pics.items()}
sheet = np.vstack([np.hstack([label(small['moss_mask'], 'MASK: where moss paints (white = moss)'), label(small['moss_only_flat'], 'COLOUR: the moss paint where the mask is 1'), label(small['on_flat_slate'], 'moss on a plain flat slate')]),
                   np.hstack([label(small['moss_height'], 'HEIGHT: grey 0.5 = no change, light = raised (x5)'), label(small['moss_roughness'], 'ROUGHNESS change: light = rougher (x2)'), label(small['final_on'], 'finished colour (all layers)')])])
cv2.imwrite(os.path.join(ROOT, 'debug_views', 'moss_sheet.png'), sheet)
# before / after
diff = np.abs(pics['final_on'].astype(np.int16) - pics['final_off'].astype(np.int16)).max(axis=2)
changed = (diff > 2).mean() * 100
panel = np.hstack([label(small['final_off'], 'moss layer OFF (Amount 0)'), label(small['final_on'], f'moss layer ON ({changed:.1f}% of the dots changed)'), label(small['moss_mask'], 'where the moss layer paints (its mask)')])
cv2.imwrite(os.path.join(TESTS, 'before_after.png'), panel)
n = pics['final_on'].shape[0]
y0, y1, x0, x1 = int(n * 0.30), int(n * 0.62), int(n * 0.30), int(n * 0.74)
close = np.hstack([label(cv2.resize(pics['final_off'][y0:y1, x0:x1], None, fx=1.6, fy=1.6, interpolation=cv2.INTER_NEAREST), 'OFF'), label(cv2.resize(pics['final_on'][y0:y1, x0:x1], None, fx=1.6, fy=1.6, interpolation=cv2.INTER_NEAREST), 'ON')])
cv2.imwrite(os.path.join(TESTS, 'before_after_closeup.png'), close)
print('share of dots changed by the moss layer: %.2f %%' % changed)

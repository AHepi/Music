# What this does (plain words): bakes the recipe with recipe.tiles_across = 2 (a 2 x 2 area of NEW content, not a copy of one tile) at 1024 dots (512 dots per
# base tile) and shows it next to the same recipe with the OUTLINE AND SHADOW layer off, so you can look for seams and see that the layer's look per dot is
# the same as in the single tile. Also bakes the layer's own mask for the 2 x 2 area.
# Use (plain python):  python3 -I two_by_two.py       Output: ../tests/outline_two_by_two/two_by_two.png (+ the single pictures)
import json
import os
import subprocess

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'tests', 'outline_two_by_two'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
os.makedirs(OUT, exist_ok=True)
BASE = {'recipe.tiles_across': 2}
jobs = {'on': {'params': BASE}, 'off': {'params': dict(BASE, **{'outline_and_shadow.amount': 0.0})}, 'mask': {'params': dict(BASE, debug_view='outline_and_shadow.mask')}}
subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, OUT, '1024', '0.5,0.5,1.0', json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
on, off, mask = [cv2.imread(os.path.join(OUT, f'{n}_colour.png')) for n in ('on', 'off', 'mask')]
# a tiling of the finished picture (2 x 2 copies of the 2 x 2 area would be 4 x 4 base tiles): shows that the picture's own edges meet without a seam
tiled = np.tile(on, (2, 2, 1))
cv2.imwrite(os.path.join(OUT, 'two_by_two.png'), np.hstack([on, mask]))
cv2.imwrite(os.path.join(OUT, 'two_by_two_off_on.png'), np.hstack([off, on]))
cv2.imwrite(os.path.join(OUT, 'two_by_two_tiled_look_for_seams.png'), cv2.resize(tiled, (1600, 1600), interpolation=cv2.INTER_AREA))
print('wrote', OUT)

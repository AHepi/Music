# What this does (plain words): shows that every size in the OUTLINE AND SHADOW layer is in TILE units, so the look does not depend on the number of
# dots: the same window of the recipe (a quarter-tile wide) is baked at 512, 1254 and 2508 dots per tile and the three pictures are shown at the same
# size side by side (the small ones enlarged with plain nearest-dot enlargement, so you can see the dots). The widths of the black band, the
# outline and the shadow should be the same share of the picture in all three; only the sharpness of the edges differs.
# Use (plain python):  python3 -I resolution_check.py       Output: ../resolution/outline_and_shadow/resolution_512_1254_2508.png and the single pictures
import json
import os
import subprocess

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'resolution', 'outline_and_shadow'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
WINDOW = '0.46,0.555,0.25'
os.makedirs(OUT, exist_ok=True)
SIZES = {512: 128, 1254: 314, 2508: 627}        # dots per tile -> window pixels (0.25 of the tile)
panels = []
for dots_per_tile, pixels in SIZES.items():
    subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, OUT, str(pixels), WINDOW, json.dumps({f'at_{dots_per_tile}': {'params': {}}})], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    image = cv2.imread(os.path.join(OUT, f'at_{dots_per_tile}_colour.png'))
    shown = cv2.resize(image, (627, 627), interpolation=cv2.INTER_NEAREST if pixels < 627 else cv2.INTER_AREA)
    cv2.rectangle(shown, (0, 0), (627, 34), (245, 245, 245), -1)
    cv2.putText(shown, f'{dots_per_tile} dots per tile ({pixels} dots across this window)', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 1, cv2.LINE_AA)
    panels.append(shown)
cv2.imwrite(os.path.join(OUT, 'resolution_512_1254_2508.png'), np.hstack(panels))
print('wrote', OUT)

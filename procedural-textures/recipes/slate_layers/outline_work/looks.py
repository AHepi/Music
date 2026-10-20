# What this does (plain words): shows five "looks" of the OUTLINE AND SHADOW layer in one picture, each made only by changing this layer's own
# settings (everything else stays at the recipe default): the default; a heavy, thick-inked look; a faint clean look; a sunlit look with a bright lip and
# little shadow; and a hand-inked look with wobbly thick outlines. Two windows of the tile are shown for each look (a joint area and a lower area).
# Use (plain python):  python3 -I looks.py       Output: ../controls_sweeps/outline_and_shadow/looks.png and looks.json (the settings of each look)
import json
import os
import subprocess

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'controls_sweeps', 'outline_and_shadow'))
SINGLE = os.path.join(OUT, 'single')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
P = 'outline_and_shadow.'
LOOKS = {
    'default': {},
    'heavy and thick-inked': {P + 'shadow_darkness': 0.9, P + 'shadow_width': 0.045, P + 'band_width': 0.003, P + 'black_drips': 0.02, P + 'joint_width': 0.002, P + 'side_outline_darkness': 0.85},
    'faint and clean': {P + 'shadow_darkness': 0.35, P + 'shadow_width': 0.02, P + 'black_drips': 0.0, P + 'side_outline_darkness': 0.3, P + 'wobble': 0.2, P + 'edge_darkening': 0.15},
    'sunlit: bright lip, little shadow': {P + 'shadow_darkness': 0.2, P + 'shadow_tiers': 2.0, P + 'lip_brightness': 0.7, P + 'lip_width': 0.005, P + 'lip_breakup': 0.2, P + 'black_drips': 0.003},
    'hand-inked': {P + 'wobble': 1.0, P + 'wobble_scale': 40.0, P + 'side_outline_width': 0.004, P + 'side_outline_darkness': 0.9, P + 'shadow_tiers': 2.0, P + 'shadow_drip': 1.0},
}
WINDOWS = {'joints': '0.46,0.555,0.2', 'lower': '0.78,0.2,0.2'}
CELL = 300


def main():
    os.makedirs(SINGLE, exist_ok=True)
    columns = []
    for window_name, window in WINDOWS.items():
        jobs = {f'look_{window_name}_{i}': {'params': params} for i, params in enumerate(LOOKS.values())}
        subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, SINGLE, str(CELL), window, json.dumps(jobs)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    rows = []
    for window_name in WINDOWS:
        tiles = []
        for i, name in enumerate(LOOKS):
            image = cv2.imread(os.path.join(SINGLE, f'look_{window_name}_{i}_colour.png'))
            banner = np.full((30, CELL, 3), 245, np.uint8)
            cv2.putText(banner, name[:36], (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
            tiles.append(np.vstack([banner, image]))
        rows.append(np.hstack(tiles))
    grid = np.vstack(rows)
    header = np.full((40, grid.shape[1], 3), 255, np.uint8)
    cv2.putText(header, 'OUTLINE AND SHADOW: five looks made only with this layer\'s own settings (see looks.json)', (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.imwrite(os.path.join(OUT, 'looks.png'), np.vstack([header, grid]))
    json.dump(LOOKS, open(os.path.join(OUT, 'looks.json'), 'w'), indent=1)
    print('wrote looks.png')


if __name__ == '__main__':
    main()

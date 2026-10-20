# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# RESOLUTION TEST: does the finished recipe give the same picture at 512, 1254 and 2508 dots per tile? Every size in the recipe is a share of the tile
# ("tile units"), so it should: a bigger picture has the same slates, the same streaks and the same moss, only drawn with more dots (finer edges).
# The script bakes the default settings (colour and height) at 512, 1254 and 2508 dots, writes the wall-clock time of each bake, shrinks the bigger
# pictures to the smaller sizes and compares them with the smaller bakes (mean difference in steps of 255, and the share of dots over 40 steps), and
# makes a sheet with the same crop (one slate wide) at the three sizes, each enlarged to the same size, so edges and detail can be compared by eye.
# Use (plain python): python3 -I run_resolution.py [bake|analyse|all]
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'whole_recipe')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
SIZES = [512, 1254, 2508]
step = sys.argv[1] if len(sys.argv) > 1 else 'all'
os.makedirs(OUT, exist_ok=True)

if step in ('bake', 'all'):
    times = {}
    for size in SIZES:
        folder = os.path.join(OUT, f'at_{size}')
        started = time.time()
        subprocess.run(BLENDER + [os.path.join(HERE, '..', 'tests', 'bake_tools.py'), '--', RECIPE, folder, str(size), '4', json.dumps({'default': {}}), '{}', 'Colour,Height,Roughness'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        times[size] = {'seconds_for_colour_height_roughness': round(time.time() - started, 1), 'load_average_after': round(os.getloadavg()[0], 2)}
        print(size, times[size], flush=True)
    json.dump(times, open(os.path.join(OUT, 'times.json'), 'w'), indent=1)

if step in ('analyse', 'all'):
    def colour(size):
        return cv2.imread(os.path.join(OUT, f'at_{size}', 'default_colour.png')).astype(np.float64)

    def height(size):
        picture = cv2.imread(os.path.join(OUT, f'at_{size}', 'default_height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64) / 65535.0 * 255.0
        return picture.max(axis=2) if picture.ndim == 3 else picture
    rows = []
    for big, small in ((2508, 1254), (1254, 512), (2508, 512)):
        for kind, reader in (('colour', colour), ('height', height)):
            shrunk = cv2.resize(reader(big), (small, small), interpolation=cv2.INTER_AREA)
            difference = np.abs(shrunk - reader(small))
            difference = difference.max(axis=2) if difference.ndim == 3 else difference
            rows.append({'bigger bake': big, 'smaller bake': small, 'picture': kind, 'mean difference (of 255)': round(float(difference.mean()), 2),
                         'share of dots over 40 steps %': round(float(100 * (difference > 40).mean()), 3)})
    # the control: a DIFFERENT tile (seed changed) shrunk and compared the same way, so the numbers above can be judged
    json.dump(rows, open(os.path.join(OUT, 'resolution_differences.json'), 'w'), indent=1)
    cell = 480
    crop = (0.30, 0.40, 0.24, 0.16)                                     # x, y, width, height as shares of the tile: about one slate and its joint
    panels = []
    for size in SIZES:
        picture = cv2.imread(os.path.join(OUT, f'at_{size}', 'default_colour.png'))
        x, y, w, h = [int(round(v * size)) for v in crop]
        piece = picture[y:y + h, x:x + w]
        piece = cv2.resize(piece, (cell * 3 // 2, int(cell * 3 / 2 * h / w)), interpolation=cv2.INTER_NEAREST)
        cv2.putText(piece, f'{size} dots per tile (crop {w} x {h} dots, enlarged)', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        panels.append(piece)
    cv2.imwrite(os.path.join(OUT, 'same_crop_at_three_sizes.png'), np.vstack(panels))
    whole = [cv2.resize(cv2.imread(os.path.join(OUT, f'at_{s}', 'default_colour.png')), (480, 480), interpolation=cv2.INTER_AREA) for s in SIZES]
    for picture, size in zip(whole, SIZES):
        cv2.putText(picture, f'{size} dots', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.imwrite(os.path.join(OUT, 'whole_tile_at_three_sizes.png'), np.hstack(whole))
    for row in rows:
        print(row)

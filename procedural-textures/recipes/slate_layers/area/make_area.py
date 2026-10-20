# What this does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# AREA TEST: the setting recipe.tiles_across makes a BIGGER picture of NEW, non-repeating slates with the same look per dot. With tiles_across = 2 the
# picture is 2 x 2 base tiles wide (bake 2508 dots: the same 1254 dots per base tile); with 4 it is 4 x 4 (5016 dots).
# This script bakes the area, then MEASURES three things and shows a picture:
#   1. SEAMS: how big the jump in brightness is across the line where one base tile would end (x = 1254, y = 1254, and the wrap-round edge) compared
#      with a normal jump between neighbouring dots (1.0 = no seam; the reference tile itself has 1.7 to 2.5 because its slates are cut at the edge).
#   2. REPEATS: if the area were four copies of one tile, the picture would equal itself shifted by one base tile. The measure is the correlation of the
#      picture with itself shifted by (1254, 0), (0, 1254), (1254, 1254) dots (1.0 = a copy, about 0 = new content), next to the same measure for a REAL copy
#      (the default tile laid out 2 x 2), and the difference between the four base tiles of the area.
#   3. SAME LOOK PER DOT: each of the four 1254 x 1254 quarters is scored with the project's "same kind of surface" tool (colour group), like the default tile.
# Use (plain python): python3 -I make_area.py [bake|analyse|all] [2|4]
import json
import os
import subprocess
import sys
import time

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
step = sys.argv[1] if len(sys.argv) > 1 else 'all'
TILES = int(sys.argv[2]) if len(sys.argv) > 2 else 2
SIZE = 1254 * TILES
FOLDER = os.path.join(HERE, f'area_{TILES}x{TILES}')
BASE = 1254

if step in ('bake', 'all'):
    started = time.time()
    channels = 'Colour,Height' if TILES == 2 else 'Colour'
    subprocess.run(BLENDER + [os.path.join(HERE, '..', 'tests', 'bake_tools.py'), '--', RECIPE, FOLDER, str(SIZE), '4', json.dumps({'area': {}}),
                              json.dumps({'recipe.tiles_across': TILES}), channels], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    json.dump({'seconds': round(time.time() - started, 1), 'size': SIZE, 'channels': channels, 'load_average_after': round(os.getloadavg()[0], 2)},
              open(os.path.join(FOLDER, 'time.json'), 'w'))


def lightness(path_or_array):
    picture = cv2.imread(path_or_array) if isinstance(path_or_array, str) else path_or_array
    return cv2.cvtColor(picture, cv2.COLOR_BGR2LAB).astype(np.float32)[..., 0] * 100.0 / 255.0


def seam_ratio_at(light, column=None, row=None):
    """jump across the line between column-1 and column (or row-1 and row), divided by the average jump between neighbouring dots (wrap-round for 0)."""
    # (the "typical jump" of the whole picture is worked out once per picture and kept: on a 5016-dot picture working it out for every
    #  column took hours; changed after the restart, the numbers are the same)
    key = (id(light), column is not None)
    if key not in TYPICAL_JUMP:
        TYPICAL_JUMP[key] = np.abs(np.diff(light, axis=1 if column is not None else 0)).mean()
    typical = TYPICAL_JUMP[key]
    if column is not None:
        jump = np.abs(light[:, column % light.shape[1]] - light[:, (column - 1) % light.shape[1]]).mean()
    else:
        jump = np.abs(light[row % light.shape[0], :] - light[(row - 1) % light.shape[0], :]).mean()
    return float(jump / typical)


TYPICAL_JUMP = {}


def shifted_correlation(light, dx, dy):
    a = light - light.mean()
    b = np.roll(a, (dy, dx), axis=(0, 1))
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))


if step in ('analyse', 'all'):
    picture = cv2.imread(os.path.join(FOLDER, 'area_colour.png'))
    light = lightness(picture)
    result = {'tiles_across': TILES, 'size': SIZE}
    result['seam ratio at each base tile line (x)'] = [round(seam_ratio_at(light, column=BASE * k), 2) for k in range(1, TILES)]
    result['seam ratio at each base tile line (y)'] = [round(seam_ratio_at(light, row=BASE * k), 2) for k in range(1, TILES)]
    result['seam ratio at the wrap-round edge (x, y)'] = [round(seam_ratio_at(light, column=0), 2), round(seam_ratio_at(light, row=0), 2)]
    # the seam ratio of EVERY ordinary line, so the base-tile lines can be placed among them (a vertical joint or a row band gives a big ratio by itself)
    columns = np.array([seam_ratio_at(light, column=c) for c in range(1, light.shape[1])])
    rows = np.array([seam_ratio_at(light, row=r) for r in range(1, light.shape[0])])
    result['seam ratio of ALL ordinary columns: median, 90th percentile, 99th percentile'] = [round(float(np.median(columns)), 2), round(float(np.percentile(columns, 90)), 2), round(float(np.percentile(columns, 99)), 2)]
    result['seam ratio of ALL ordinary rows: median, 90th percentile, 99th percentile'] = [round(float(np.median(rows)), 2), round(float(np.percentile(rows, 90)), 2), round(float(np.percentile(rows, 99)), 2)]
    result['share of ordinary columns with a seam ratio BELOW the base-tile line (x), and rows (y) %'] = [
        [round(float(100 * (columns < seam_ratio_at(light, column=BASE * k)).mean()), 1) for k in range(1, TILES)],
        [round(float(100 * (rows < seam_ratio_at(light, row=BASE * k)).mean()), 1) for k in range(1, TILES)]]
    # repeats: correlation with itself shifted by one base tile, for the area and for a real copy
    tile = cv2.imread(os.path.join(HERE, '..', 'outputs', 'default', 'colour.png'))
    copy = np.tile(tile, (TILES, TILES, 1))
    copy_light = lightness(copy)
    shifts = [(BASE, 0), (0, BASE), (BASE, BASE)]
    result['correlation with itself shifted by one base tile (x, y, diagonal): the NEW area'] = [round(shifted_correlation(light, dx, dy), 3) for dx, dy in shifts]
    result['correlation with itself shifted by one base tile: a REAL COPY of the default tile'] = [round(shifted_correlation(copy_light, dx, dy), 3) for dx, dy in shifts]
    # share of dots that are almost the same (less than 2 brightness steps of 100) after a shift by one base tile: a copy gives about 100, new content little
    def near_equal(a):
        return [round(float(100 * (np.abs(a - np.roll(a, (dy, dx), axis=(0, 1))) < 2.0).mean()), 1) for dx, dy in shifts]
    result['share of dots nearly equal to the dot one base tile away (x, y, diagonal %): the NEW area'] = near_equal(light)
    result['share of dots nearly equal to the dot one base tile away (x, y, diagonal %): a REAL COPY'] = near_equal(copy_light)
    # for the background level: correlation at shifts that are not a base tile (by 600, 900 and 1500 dots)
    background = [shifted_correlation(light, dx, dy) for dx, dy in ((600, 0), (900, 300), (1500, 700), (300, 1100))]
    result['correlation at four shifts that are NOT a base tile (the background level)'] = [round(v, 3) for v in background]
    # difference between base tiles
    tiles = {(i, j): light[j * BASE:(j + 1) * BASE, i * BASE:(i + 1) * BASE] for i in range(TILES) for j in range(TILES)}
    result['mean brightness difference between base tile (0,0) and each other base tile'] = {str(k): round(float(np.abs(tiles[(0, 0)] - v).mean()), 2) for k, v in tiles.items() if k != (0, 0)}
    # same look per dot: score each 1254 quarter with the same-kind tool (colour group), max 4 quarters (for 4 x 4 only the first 2 x 2)
    scores = {}
    for (i, j) in [(0, 0), (1, 0), (0, 1), (1, 1)]:
        quarter = picture[j * BASE:(j + 1) * BASE, i * BASE:(i + 1) * BASE]
        path = os.path.join(FOLDER, f'quarter_{i}_{j}.png')
        cv2.imwrite(path, quarter)
        out = subprocess.run(['bash', os.path.join(PROC, 'recipes', 'slate_layers', 'integration', 'score_colour.sh'), path], capture_output=True, text=True).stdout.split()
        scores[f'quarter ({i},{j})'] = float(out[2])
        os.remove(path)
    result['same-kind colour group of each 1254 x 1254 quarter (the default tile scores 0.70)'] = scores
    json.dump(result, open(os.path.join(FOLDER, 'area_measures.json'), 'w'), indent=1)
    # pictures
    show = 1254
    small = cv2.resize(picture, (show, show), interpolation=cv2.INTER_AREA)
    cv2.imwrite(os.path.join(FOLDER, 'area_overview.png'), small)
    copy_small = cv2.resize(copy, (show, show), interpolation=cv2.INTER_AREA)
    for image, text in ((small, f'NEW content: tiles_across {TILES}'), (copy_small, 'for comparison: the default tile copied')):
        cv2.putText(image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
    cv2.imwrite(os.path.join(FOLDER, 'new_area_against_copied_tile.jpg'), np.hstack([small, copy_small]), [cv2.IMWRITE_JPEG_QUALITY, 90])   # JPEG since the restart (disk)
    print(json.dumps(result, indent=1))

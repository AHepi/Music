# What this does (plain words): measures the LAYOUT the recipe makes and lists the numbers next to the character numbers that were
# measured ONCE on the reference picture (they are a guide for the default settings, never copied piece by piece). It bakes exact
# (16-bit) pictures of five layout numbers through the recipe's debug_view and reads them back:
#   how many slates, their widths (median, smallest, largest, spread of the log-width), row heights, the share of dots that are joint,
#   the thickness of the dark band between rows and the width of the joints between slates in a row.
# The reference numbers come from recipes/slate/04 Recipe (analysis of the first build): 48 slates; width median 200, 134..402,
# log spread 0.217; row body 146 dots (spread 6.4); band between rows 10.6 dots; joints between slates 3.9 dots (spread 1.6); 7 % joint dots.
# Use (plain python):  python3 -I layout_statistics.py [SIZE] [FOLDER] [EXTRA_PARAMETERS_AS_JSON]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 1254
FOLDER = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'layout_stats')
EXTRA = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
SCALES = {'piece_width': 5.0, 'piece_height': 8.0}      # the recipe's default debug scales (the picture holds value x scale)


def bake():
    views = {name: {'debug_view': f'bundle.{name}'} for name in ('gap_mask', 'piece_id', 'piece_width', 'piece_height', 'local_y')}
    subprocess.run(BLENDER + [os.path.join(HERE, 'bake_tools.py'), '--', RECIPE, FOLDER, str(SIZE), '4', json.dumps(views), json.dumps(EXTRA), 'Height'],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read(name):
    image = cv2.imread(os.path.join(FOLDER, f'{name}_height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)[..., 0] / 65535.0
    return image / SCALES.get(name, 1.0)


def runs(mask_line):
    """lengths of runs of True in a 1-D boolean array (no wrap)."""
    padded = np.concatenate([[0], mask_line.astype(np.int8), [0]])
    change = np.diff(padded)
    starts, ends = np.where(change == 1)[0], np.where(change == -1)[0]
    return ends - starts


def statistics(gap, piece_id, width, height, local_y):
    result = {}
    result['joint share of dots %'] = round(100 * float((gap > 0.5).mean()), 2)
    ids = np.round(piece_id * 65535).astype(int)
    interior = cv2.erode((gap < 0.001).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0      # dots well inside a slate (edges blend the numbers)
    values, counts = np.unique(ids[interior], return_counts=True)
    unique = values[counts > 30]                         # one id per slate (a stray blended value covers only a few dots)
    result['number of slates'] = int(len(unique))
    widths, heights = [], []
    for value in unique:
        where = (ids == value) & interior
        widths.append(float(np.median(width[where])) * SIZE)          # dots at this size; at 1254 dots per tile these are the reference's dots
        heights.append(float(np.median(height[where])) * SIZE)
    widths, heights = np.array(widths), np.array(heights)
    result['slate width median / smallest / largest (dots)'] = [round(float(np.median(widths)), 1), round(float(widths.min()), 1), round(float(widths.max()), 1)]
    result['slate width log spread'] = round(float(np.log(widths).std()), 3)
    result['slate (row body) height mean / spread (dots)'] = [round(float(heights.mean()), 1), round(float(heights.std()), 1)]
    # band between rows: vertical runs of joint dots longer than 3 that touch a "local_y just at the end of a slate" zone: use runs > 3 dots in columns
    band, side = [], []
    mask = gap > 0.5
    for x in range(0, SIZE, 3):
        r = runs(mask[:, x])
        band += [v for v in r if 3 <= v <= 40]          # longer runs are the vertical joints, not the band
    for y in range(0, SIZE, 3):
        line = mask[y]
        middle = (local_y[y] > 0.3) & (local_y[y] < 0.7)
        # horizontal runs inside the middle third of a slate row: the joints between slates
        r_all = runs(line & middle)
        side += [v for v in r_all if v >= 1]
    result['band between rows: thickness mean / spread (dots)'] = [round(float(np.mean(band)), 1), round(float(np.std(band)), 1)]
    result['joint between slates (middle of the slate height): width mean / spread (dots)'] = [round(float(np.mean(side)), 1), round(float(np.std(side)), 1)]
    return result


if __name__ == '__main__':
    bake()
    stats = statistics(read('gap_mask'), read('piece_id'), read('piece_width'), read('piece_height'), read('local_y'))
    # the same run-length measure on the reference's darkest dots (analysis only; nothing is copied from it)
    ref = cv2.cvtColor(cv2.imread(os.path.join(HERE, '..', '..', '..', 'reference', 'slate', 'colour.png')), cv2.COLOR_BGR2GRAY)
    ref_mask = ref < 22
    ref_band = [v for x in range(0, ref.shape[1], 3) for v in runs(ref_mask[:, x]) if 3 <= v <= 40]
    reference_by_runs = {'joint share of dots %': round(100 * float(ref_mask.mean()), 2),
                         'band between rows: thickness mean / spread (dots)': [round(float(np.mean(ref_band)), 1), round(float(np.std(ref_band)), 1)]}
    reference = {'joint share of dots %': 7.0, 'number of slates': 48, 'slate width median / smallest / largest (dots)': [200, 134, 402],
                 'slate width log spread': 0.217, 'slate (row body) height mean / spread (dots)': [146, 6.4],
                 'band between rows: thickness mean / spread (dots)': [10.6, 0.5], 'joint between slates (middle of the slate height): width mean / spread (dots)': [3.9, 1.6]}
    lines = ['| measure | the recipe (default settings) | the reference: first-build analysis | the reference: same run-length measure on its darkest dots |', '|---|---|---|---|']
    for key in reference:
        lines.append(f'| {key} | {stats[key]} | {reference[key]} | {reference_by_runs.get(key, "")} |')
    text = '\n'.join(lines)
    with open(os.path.join(FOLDER, 'layout_statistics.md'), 'w') as handle:
        handle.write(text + '\n')
    print(text)

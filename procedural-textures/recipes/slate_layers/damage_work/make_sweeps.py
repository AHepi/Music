# What this does (plain words): makes the "what does this setting do" pictures for the DAMAGE layer. For each main control it draws the SAME
# zoomed window of the slate recipe five times with only that control changed (everything else stays at its default), and joins the five
# pictures into one labelled row; rows are stacked into a few strips. Run with plain Python (it starts Blender for you).
# Use:  python3 -I make_sweeps.py [PIXELS] [ONLY_STRIP_PREFIX] [WINDOW 'cx,cy,width'] [FILE_NAME_SUFFIX]      (default 400 dots for the 0.4 x 0.4 tile window = 1000 dots per tile)
# Output: ../controls_sweeps/damage/strip_1_edge_flakes.png, strip_2_cracks_scratches_pits.png, strip_3_corners_notches_colours_amount.png, strip_4_where_and_how_big.png
#         plus the single pictures in ../controls_sweeps/damage/single/ and sweeps.json (what each picture is).
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'controls_sweeps', 'damage'))
SINGLE = os.path.join(OUT, 'single')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
PIXELS = int(sys.argv[1]) if len(sys.argv) > 1 else 400
ONLY = sys.argv[2] if len(sys.argv) > 2 else None          # e.g. 'strip_4' to make only that strip
STRIP_WINDOWS = {'strip_2_cracks_scratches_pits': '0.15,0.39,0.22'}          # strips whose details are small get a closer window
WINDOW = sys.argv[3] if len(sys.argv) > 3 else '0.2,0.354,0.4'     # centre x, centre y, width of the window, in tile units (y counts from the bottom)
SUFFIX = sys.argv[4] if len(sys.argv) > 4 else ''                   # added to the strip file names, e.g. '_close'

# (strip file name, title, [(row label, setting name, values, extra settings for the whole row, shown labels or None)])
STRIPS = [
    ('strip_1_edge_flakes', 'DAMAGE: flaked edges (the middle picture of each row is the default setting)', [
        ('Chip Amount', 'damage.chip_amount', [0.0, 0.25, 0.45, 0.7, 1.0], {}, None),
        ('Chip Depth', 'damage.chip_depth', [0.008, 0.015, 0.025, 0.04, 0.07], {}, None),
        ('Chip Frequency', 'damage.chip_frequency', [20, 40, 62, 110, 200], {}, None),
        ('Chip Breakup', 'damage.chip_breakup', [0.0, 0.3, 0.6, 1.2, 2.0], {}, None),
        ('Chip Clustering', 'damage.chip_clustering', [0.0, 0.4, 0.8, 1.5, 3.0], {}, None),
    ]),
    ('strip_2_cracks_scratches_pits', 'DAMAGE: cracks, scratches and pits (closer window; the crack rows use Crack Amount 1 so that every slate has a crack)', [
        ('Crack Amount', 'damage.crack_amount', [0.0, 0.2, 0.35, 0.7, 1.0], {}, None),
        ('Crack Length', 'damage.crack_length', [0.02, 0.05, 0.07, 0.11, 0.16], {'damage.crack_amount': 1.0}, None),
        ('Crack Width', 'damage.crack_width', [0.001, 0.002, 0.0028, 0.005, 0.009], {'damage.crack_amount': 1.0}, None),
        ('Crack Across Share', 'damage.crack_across_share', [0.0, 0.25, 0.5, 0.75, 1.0], {'damage.crack_amount': 1.0}, None),
        ('Scratch Amount', 'damage.scratch_amount', [0.0, 0.1, 0.18, 0.5, 1.0], {}, None),
        ('Pit Amount', 'damage.pit_amount', [0.0, 0.06, 0.15, 0.3, 0.5], {}, None),
    ]),
    ('strip_3_corners_notches_colours_amount', 'DAMAGE: corner breaks, notches, colours and the overall Amount', [
        ('Corner Break Amount', 'damage.corner_break_amount', [0.0, 0.08, 0.3, 0.6, 1.0], {}, None),
        ('Notch Amount', 'damage.notch_amount', [0.0, 0.3, 0.6, 0.8, 1.0], {}, None),
        ('Amount (overall)', 'damage.amount', [0.0, 0.25, 0.5, 0.75, 1.0], {}, None),
        ('Colours (light / tan / dark)', 'damage.colours', [0, 1, 2, 3, 4], {}, ['default', 'bleached pale', 'rust tan', 'grey lichen', 'dark brown']),
    ]),
    ('strip_4_where_and_how_big', 'DAMAGE: where it gathers and how big the small things are', [
        ('Side Share', 'damage.side_share', [0.0, 0.06, 0.12, 0.5, 1.0], {}, None),
        ('Corner Gain', 'damage.corner_gain', [0.0, 0.5, 1.0, 2.0, 4.0], {}, None),
        ('Slate Variation', 'damage.slate_variation', [0.0, 0.3, 0.6, 0.85, 1.0], {}, None),
        ('Pit Size (Pit Amount 0.15)', 'damage.pit_size', [0.001, 0.002, 0.0034, 0.0045, 0.005], {'damage.pit_amount': 0.15}, None),
    ]),
]
COLOUR_SETS = [
    {},
    {'damage.break_colour': '#9a9588', 'damage.break_colour_light': '#b4b2ab', 'damage.break_colour_dark': '#6f6b62'},
    {'damage.break_colour': '#8a6a4a', 'damage.break_colour_light': '#a08565', 'damage.break_colour_dark': '#5e4330'},
    {'damage.break_colour': '#6f7569', 'damage.break_colour_light': '#8c9187', 'damage.break_colour_dark': '#4d5249'},
    {'damage.break_colour': '#5a4f43', 'damage.break_colour_light': '#7c6f5d', 'damage.break_colour_dark': '#3a322a'},
]


def fmt(value):
    return ('%g' % value) if isinstance(value, float) else str(value)


def main():
    os.makedirs(SINGLE, exist_ok=True)
    manifest = {}
    for strip_name, title, rows in STRIPS:
        if ONLY and not strip_name.startswith(ONLY):
            continue
        jobs, layout = {}, []
        for row_index, (label, setting, values, extra, shown) in enumerate(rows):
            names = []
            for column, value in enumerate(values):
                params = dict(extra)
                if setting == 'damage.colours':
                    params.update(COLOUR_SETS[value])
                else:
                    params[setting] = value
                name = f'{strip_name}{SUFFIX}_r{row_index}_c{column}'
                jobs[name] = {'params': params, 'channel': 'Colour'}
                names.append(name)
            layout.append((label, setting, values, shown, names))
        subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, SINGLE, str(PIXELS), (STRIP_WINDOWS.get(strip_name, WINDOW) if len(sys.argv) <= 3 else WINDOW), json.dumps(jobs)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        cell = 320
        grid_rows = []
        for label, setting, values, shown, names in layout:
            tiles = []
            for column, name in enumerate(names):
                image = cv2.resize(cv2.imread(os.path.join(SINGLE, name + '_colour.png')), (cell, cell), interpolation=cv2.INTER_AREA)
                text = shown[column] if shown else f'{label} = {fmt(values[column])}'
                banner = np.full((30, cell, 3), 245, np.uint8)
                cv2.putText(banner, text[:36], (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
                tiles.append(np.vstack([banner, image]))
            grid_rows.append(np.hstack(tiles))
            manifest[strip_name + SUFFIX + ':' + label] = {'setting': setting, 'values': values, 'files': [n + '_colour.png' for n in names]}
        grid = np.vstack(grid_rows)
        header = np.full((40, grid.shape[1], 3), 255, np.uint8)
        cv2.putText(header, title[:150], (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.imwrite(os.path.join(OUT, strip_name + SUFFIX + '.png'), np.vstack([header, grid]))
        print('wrote', strip_name)
    path = os.path.join(OUT, 'sweeps.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(manifest)
    json.dump(old, open(path, 'w'), indent=1)


if __name__ == '__main__':
    main()

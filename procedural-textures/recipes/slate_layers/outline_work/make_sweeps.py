# What this does (plain words): makes the "what does this setting do" pictures for the OUTLINE AND SHADOW layer. For each main control it draws the SAME
# zoomed window of the whole slate recipe five times with only that control changed (everything else stays at its default; the default value is
# marked) and joins the five pictures into one labelled row; the rows are stacked into a few strips. The relief strip shows the height map instead
# of the colour. Run with plain Python (it starts Blender itself).
# Use:  python3 -I make_sweeps.py [ONLY_STRIP_PREFIX]          e.g. strip_2 to make only the shadow strip
# Output: ../controls_sweeps/outline_and_shadow/strip_1_joints_and_outlines.png, strip_2_shadow_band.png, strip_3_lip_edges_and_amount.png,
#         strip_4_relief_height.png, the single pictures in .../single/ and sweeps.json (what each picture is).
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, '..', 'controls_sweeps', 'outline_and_shadow'))
SINGLE = os.path.join(OUT, 'single')
BLENDER = ['/home/user/work/blender-app/blender-5.2.2-linux-x64/blender', '-b', '--disable-autoexec', '-t', '2', '--python']
RECIPE = os.path.join(HERE, '..', 'recipe', 'slate_recipe.py')
ONLY = sys.argv[1] if len(sys.argv) > 1 else None
P = 'outline_and_shadow.'
CELL = 320                       # picture size of one cell, in dots
# strip file name -> (title, window 'cx,cy,width' in tile units (cy counts from the BOTTOM), channel, rows)
# a row = (label, setting, values, default value (marked), extra settings for the whole row)
STRIPS = [
    ('strip_1_joints_and_outlines', 'OUTLINE AND SHADOW: black joints and thin outlines (the picture marked * is the default)', '0.46,0.555,0.16', 'Colour', [
        ('Joint Width', P + 'joint_width', [0.0, 0.0004, 0.0008, 0.002, 0.004], 0.0008, {}),
        ('Band Width', P + 'band_width', [0.0, 0.0004, 0.0012, 0.003, 0.006], 0.0004, {}),
        ('Side Outline Width', P + 'side_outline_width', [0.0, 0.001, 0.002, 0.004, 0.007], 0.002, {}),
        ('Side Outline Darkness', P + 'side_outline_darkness', [0.0, 0.3, 0.6, 0.85, 1.0], 0.6, {}),
        ('Wobble', P + 'wobble', [0.0, 0.25, 0.5, 0.8, 1.0], 0.5, {}),
        ('Wobble Scale', P + 'wobble_scale', [20.0, 50.0, 90.0, 200.0, 400.0], 90.0, {}),
    ]),
    ('strip_2_shadow_band', 'OUTLINE AND SHADOW: the shadow band under the black joint (the picture marked * is the default)', '0.46,0.555,0.16', 'Colour', [
        ('Shadow Width', P + 'shadow_width', [0.0, 0.015, 0.03, 0.045, 0.06], 0.03, {}),
        ('Shadow Darkness', P + 'shadow_darkness', [0.0, 0.35, 0.7, 0.85, 1.0], 0.7, {}),
        ('Shadow Tiers', P + 'shadow_tiers', [0.0, 1.0, 2.0, 4.0, 8.0], 4.0, {}),
        ('Shadow Drip', P + 'shadow_drip', [0.0, 0.25, 0.5, 0.8, 1.0], 0.5, {}),
        ('Black Drips', P + 'black_drips', [0.0, 0.004, 0.009, 0.015, 0.03], 0.009, {}),
    ]),
    ('strip_3_lip_edges_and_amount', 'OUTLINE AND SHADOW: the lip, the edge darkening, slate to slate variation and the overall Amount (* = default)', '0.46,0.555,0.16', 'Colour', [
        ('Lip Brightness', P + 'lip_brightness', [0.0, 0.12, 0.25, 0.5, 1.0], 0.25, {}),
        ('Lip Width', P + 'lip_width', [0.0, 0.0015, 0.003, 0.006, 0.012], 0.003, {}),
        ('Lip Breakup', P + 'lip_breakup', [0.0, 0.2, 0.4, 0.7, 1.0], 0.4, {}),
        ('Edge Darkening', P + 'edge_darkening', [0.0, 0.15, 0.3, 0.6, 1.0], 0.3, {}),
        ('Slate Variation', P + 'slate_variation', [0.0, 0.25, 0.5, 0.75, 1.0], 0.5, {}),
        ('Amount (overall)', P + 'amount', [0.0, 0.25, 0.5, 0.75, 1.0], 1.0, {}),
    ]),
    ('strip_4_relief_height', 'OUTLINE AND SHADOW: the relief it adds, seen in the finished HEIGHT map (grey: dark = low; * = default)', '0.46,0.555,0.16', 'Height', [
        ('Shadow Height', P + 'shadow_height', [0.0, 0.06, 0.12, 0.25, 0.5], 0.12, {}),
        ('Lip Height', P + 'lip_height', [0.0, 0.02, 0.04, 0.12, 0.3], 0.04, {}),
        ('Outline Height', P + 'outline_height', [0.0, 0.025, 0.05, 0.12, 0.3], 0.05, {}),
    ]),
]


def fmt(value):
    return '%g' % value


def read_cell(path, channel):
    if channel == 'Height':
        raw = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535.0
        raw = raw if raw.ndim == 2 else raw[..., 0]
        grey = np.clip(raw / 0.8, 0, 1) * 255                       # the finished height 0..0.8 shown as grey 0..255
        return cv2.cvtColor(grey.astype(np.uint8), cv2.COLOR_GRAY2BGR)
    return cv2.imread(path)


def main():
    os.makedirs(SINGLE, exist_ok=True)
    manifest = {}
    for strip_name, title, window, channel, rows in STRIPS:
        if ONLY and not strip_name.startswith(ONLY):
            continue
        jobs, layout = {}, []
        for row_index, (label, setting, values, default, extra) in enumerate(rows):
            names = []
            for column, value in enumerate(values):
                params = dict(extra)
                params[setting] = value
                name = f'{strip_name}_r{row_index}_c{column}'
                jobs[name] = {'params': params, 'channel': channel}
                names.append(name)
            layout.append((label, setting, values, default, names))
        subprocess.run(BLENDER + [os.path.join(HERE, 'window_render.py'), '--', RECIPE, SINGLE, str(CELL), window, json.dumps(jobs)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        grid_rows = []
        for label, setting, values, default, names in layout:
            tiles = []
            for column, name in enumerate(names):
                image = read_cell(os.path.join(SINGLE, f'{name}_{channel.lower()}.png'), channel)
                mark = ' *' if abs(values[column] - default) < 1e-12 else ''
                banner = np.full((30, CELL, 3), 245 if not mark else 215, np.uint8)
                cv2.putText(banner, f'{label} = {fmt(values[column])}{mark}'[:38], (6, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
                tiles.append(np.vstack([banner, image]))
            grid_rows.append(np.hstack(tiles))
            manifest[strip_name + ':' + label] = {'setting': setting, 'values': values, 'default': default, 'files': [n + f'_{channel.lower()}.png' for n in names]}
        grid = np.vstack(grid_rows)
        header = np.full((40, grid.shape[1], 3), 255, np.uint8)
        cv2.putText(header, title[:150], (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.imwrite(os.path.join(OUT, strip_name + '.png'), np.vstack([header, grid]))
        print('wrote', strip_name)
    path = os.path.join(OUT, 'sweeps.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(manifest)
    json.dump(old, open(path, 'w'), indent=1)


if __name__ == '__main__':
    main()

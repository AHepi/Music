# What this does: draws "06 Overview - all six surfaces.png", one row per surface and five columns:
#   the reference | the best traced class L | the small class S | one new tile from a sampled description | the transfer surface.
# It only reads pictures that the six builds already made (paths in SURFACES below) and writes two pictures into
# cookbook/pictures/: the full overview (PNG) and a smaller copy (JPG, meant to stay under 600 KB).
# The numbers printed under each picture are copied from each build's final_report.json (the file and key are named next to them).
# Run with: python3 -I make_overview.py   (plain Python with numpy and cv2; no Blender)
import json
import os

import cv2
import numpy as np

PROC_WORK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
RECIPES = os.path.join(PROC_WORK, 'recipes')
REFERENCE = os.path.join(PROC_WORK, 'reference')
PICTURES = os.path.join(PROC_WORK, 'cookbook', 'pictures')

CELL_SIZE = 236          # dots per picture in the full overview
GAP = 8                  # white gap between pictures
LABEL_WIDTH = 120        # left column with the surface name
HEADER_HEIGHT = 34       # top row with the column names
CAPTION_HEIGHT = 34      # two short lines under each picture

COLUMN_NAMES = ['reference', 'best traced L', 'small S', 'one new tile', 'transfer surface']

# For each surface: the five pictures (relative to recipes/<surface>/ unless they start with 'REF') and two caption lines each.
# Caption numbers: classes and variation blocks of recipes/<surface>/final_report.json; KB = 1024 bytes (as lib/description_audit.py counts).
SURFACES = [
    ('brick', [
        ('REF/brick/colour.png', 'given', ''),
        ('outputs/final_L/colour.png', 'L 497 KB, tier layout', 'SSIM 0.673 (traced)'),
        ('outputs/final_S/colour.png', 'S 7.8 KB, tier layout', 'SSIM 0.532 (fitted)'),
        ('variations/tile_11/colour.png', 'seed 11, 9.3 KB', 'same-kind 0.725'),
        ('transfer/cobble_1/colour.png', 'cobblestones', 'judged by eye'),
    ]),
    ('slate', [
        ('REF/slate/colour.png', 'given', ''),
        ('outputs/L_trace_fine/colour.png', 'L 442 KB, tier close', 'SSIM 0.836 (traced)'),
        ('outputs/S2_stamps_grain/colour.png', 'S2 6.5 KB, tier none', 'SSIM 0.569 (rules)'),
        ('variations/var_101/colour.png', 'seed 101, 6.6 KB', 'same-kind 0.725'),
        ('transfer/out_cedar_1/colour.png', 'cedar shingles', 'judged by eye'),
    ]),
    ('wood', [
        ('REF/wood/colour.png', 'given', ''),
        ('outputs/ladder_L3_trace_480kw/colour.png', 'L3 462 KB, tier layout', 'SSIM 0.725 (traced)'),
        ('outputs/ladder_S1_layout_paint_grain/colour.png', 'S1 6.2 KB, tier none', 'SSIM 0.220 (rules)'),
        ('variations/sample_101/colour.png', 'seed 101, 4.3 KB', 'same-kind 0.619'),
        ('transfer/deck_boards_seed1/colour.png', 'silver deck boards', 'judged by eye'),
    ]),
    ('metal', [
        ('REF/metal/colour.png', 'given', ''),
        ('outputs/L/colour.png', 'L 404 KB, tier close', 'SSIM 0.756 (traced)'),
        ('outputs/S/colour.png', 'S 6.2 KB, tier none', 'SSIM 0.479 (rules)'),
        ('variations/seed_1/colour.png', 'seed 1, 4.9 KB', 'same-kind 0.578'),
        ('transfer/hull_plates/colour.png', 'ship hull plates', 'judged by eye'),
    ]),
    ('mud', [
        ('REF/mud/colour.png', 'given', ''),
        ('outputs/L_final_traced_ground_plus_corrections/colour.png', 'L 491 KB, tier layout', 'SSIM 0.698 (traced)'),
        ('outputs/S_layout_ruts_clods/colour.png', 'S 7.2 KB, tier none', 'SSIM 0.367 (rules)'),
        ('variations/tile_101/colour.png', 'seed 101, 112 KB (!)', 'same-kind 0.407'),
        ('transfer/snow/colour.png', 'snowy track', 'judged by eye'),
    ]),
    ('gravel', [
        ('REF/gravel/colour.png', 'given', ''),
        ('outputs/L_a100_s8/colour.png', 'L 426 KB, tier layout', 'SSIM 0.666 (traced)'),
        ('outputs/S_v4/colour.png', 'S 2.3 KB, tier none', 'SSIM 0.213 (rules)'),
        ('variations/out/sample_01/colour.png', 'sample 1, 2.4 KB', 'same-kind 0.372'),
        ('transfer/out/pebbles_1254/colour.png', 'pebbles on sand', 'judged by eye'),
    ]),
]


def picture_path(surface_name, relative_path):
    if relative_path.startswith('REF/'):
        return os.path.join(REFERENCE, relative_path[4:])
    return os.path.join(RECIPES, surface_name, relative_path)


def load_square(path, size):
    picture = cv2.imread(path, cv2.IMREAD_COLOR)
    if picture is None:
        raise FileNotFoundError(path)
    height, width = picture.shape[:2]
    side = min(height, width)                      # all are square already; keep the middle square if not
    top, left = (height - side) // 2, (width - side) // 2
    picture = picture[top:top + side, left:left + side]
    return cv2.resize(picture, (size, size), interpolation=cv2.INTER_AREA), (width, height)


def put_text(canvas, text, x, y, scale, thickness=1, colour=(30, 30, 30)):
    cv2.putText(canvas, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, colour, thickness, cv2.LINE_AA)


def draw_overview(cell_size):
    scale_factor = cell_size / CELL_SIZE
    gap = max(4, int(round(GAP * scale_factor)))
    label_width = int(round(LABEL_WIDTH * scale_factor))
    header_height = int(round(HEADER_HEIGHT * scale_factor))
    caption_height = int(round(CAPTION_HEIGHT * scale_factor))
    text_scale = 0.42 * scale_factor
    columns, rows = len(COLUMN_NAMES), len(SURFACES)
    width = label_width + columns * (cell_size + gap) + gap
    height = header_height + rows * (cell_size + caption_height + gap) + gap
    canvas = np.full((height, width, 3), 255, dtype=np.uint8)
    for column_index, name in enumerate(COLUMN_NAMES):
        x = label_width + gap + column_index * (cell_size + gap)
        put_text(canvas, name, x + 4, header_height - int(10 * scale_factor), 0.55 * scale_factor, 1 if scale_factor < 0.8 else 2)
    used = []
    for row_index, (surface_name, cells) in enumerate(SURFACES):
        y = header_height + row_index * (cell_size + caption_height + gap)
        put_text(canvas, surface_name, int(8 * scale_factor), y + cell_size // 2, 0.75 * scale_factor, 1 if scale_factor < 0.8 else 2)
        for column_index, (relative_path, line_one, line_two) in enumerate(cells):
            x = label_width + gap + column_index * (cell_size + gap)
            path = picture_path(surface_name, relative_path)
            picture, original_size = load_square(path, cell_size)
            canvas[y:y + cell_size, x:x + cell_size] = picture
            put_text(canvas, line_one, x + 2, y + cell_size + int(14 * scale_factor), text_scale)
            put_text(canvas, line_two, x + 2, y + cell_size + int(29 * scale_factor), text_scale)
            used.append({'surface': surface_name, 'column': COLUMN_NAMES[column_index],
                         'file': os.path.relpath(path, PROC_WORK), 'original_size': original_size})
    return canvas, used


def main():
    os.makedirs(PICTURES, exist_ok=True)
    full, used = draw_overview(CELL_SIZE)
    full_path = os.path.join(PICTURES, '06 Overview - all six surfaces.png')
    cv2.imwrite(full_path, full, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    small, _ = draw_overview(170)
    small_path = os.path.join(PICTURES, '06 Overview - all six surfaces - small.jpg')
    cv2.imwrite(small_path, small, [cv2.IMWRITE_JPEG_QUALITY, 82])
    report = {'full_picture': os.path.relpath(full_path, PROC_WORK), 'full_size': [int(full.shape[1]), int(full.shape[0])],
              'full_bytes': os.path.getsize(full_path), 'small_picture': os.path.relpath(small_path, PROC_WORK),
              'small_size': [int(small.shape[1]), int(small.shape[0])], 'small_bytes': os.path.getsize(small_path),
              'pictures_used': used}
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'overview_files_used.json'), 'w') as handle:
        json.dump(report, handle, indent=1)
    print(json.dumps({key: value for key, value in report.items() if key != 'pictures_used'}, indent=1))


if __name__ == '__main__':
    main()

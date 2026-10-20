# What this does (plain words): reads the pictures that verify_run.py baked for one surface (verify/work/SURFACE/t1_plain_colour.png and so on)
# and answers: does the tile repeat exactly? If it does, the picture slid by half a tile (shifted) must equal the plain picture moved by
# half its size (rolled); numbers are in dots out of 255 (colour) or 65535 (height). A CONTROL is shown beside it: the plain picture
# against the shifted one WITHOUT moving it, which must be very different (otherwise the test could not tell anything).
# For two tiles across it also shows how different the left and right halves of the plain picture are (a copy of one tile would give 0).
# Use: python3 -I half_tile_analyse.py SURFACE [SURFACE ...]   (prints one block per surface and writes work/SURFACE/half_tile_result.json)
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise FileNotFoundError(path)
    top = 65535.0 if image.dtype == np.uint16 else 255.0       # 16 bit height pictures versus 8 bit colour pictures
    if image.ndim == 3:
        image = image[..., :3].astype(np.float64)
    else:
        image = image.astype(np.float64)[..., None]
    return image / top           # 0..1


def measure(a, b, scale):
    difference = np.abs(a - b)
    biggest = difference.max(axis=-1)
    # where do the big differences sit? A seam shows as big differences packed along the picture's middle lines (where the old tile edge went)
    # and along the picture edges; strips 4 dots either side of those lines cover only about 3 percent of the area.
    rows, columns = np.indices(biggest.shape)
    near = (np.abs(rows - biggest.shape[0] // 2) <= 4) | (np.abs(columns - biggest.shape[1] // 2) <= 4) | \
           (rows <= 4) | (columns <= 4) | (rows >= biggest.shape[0] - 5) | (columns >= biggest.shape[1] - 5)
    big = biggest * scale > 40
    in_strips = float(big[near].sum() / max(big.sum(), 1) * 100)
    return {'big_differences_inside_the_seam_strips_percent (strips cover %.1f percent of the picture)' % (near.mean() * 100): round(in_strips, 1),
            'mean_difference': round(float(difference.mean() * scale), 3),
            'share_of_dots_over_40_of_255': round(float((biggest * scale > 40).mean() * 100), 3),
            'largest_difference': round(float(biggest.max() * scale), 2)}


for surface in sys.argv[1:]:
    folder = os.path.join(HERE, 'work', surface)
    result = {'surface': surface}
    for channel, scale in (('colour', 255.0), ('height', 255.0)):
        plain_path = os.path.join(folder, f't1_plain_{channel}.png')
        if not os.path.exists(plain_path):
            continue
        plain = load(plain_path)
        shifted = load(os.path.join(folder, f't1_shifted_{channel}.png'))
        plain, shifted = plain * 255.0, shifted * 255.0           # every picture is judged on a 0..255 scale
        half_y, half_x = plain.shape[0] // 2, plain.shape[1] // 2
        rolled = np.roll(np.roll(plain, half_y, axis=0), half_x, axis=1)
        result[f'one_tile_{channel}_shifted_vs_rolled'] = measure(shifted, rolled, 1.0)
        result[f'one_tile_{channel}_CONTROL_shifted_vs_plain_not_moved'] = measure(shifted, plain, 1.0)
    if os.path.exists(os.path.join(folder, 't2_plain_colour.png')):
        plain = load(os.path.join(folder, 't2_plain_colour.png')) * 255.0
        shifted = load(os.path.join(folder, 't2_shifted_colour.png')) * 255.0
        half_y, half_x = plain.shape[0] // 2, plain.shape[1] // 2
        rolled = np.roll(np.roll(plain, half_y, axis=0), half_x, axis=1)
        result['two_tiles_colour_shifted_vs_rolled'] = measure(shifted, rolled, 1.0)
        result['two_tiles_colour_CONTROL_shifted_vs_plain_not_moved'] = measure(shifted, plain, 1.0)
        result['two_tiles_colour_left_half_vs_right_half (0 would mean the area is a copy of one tile)'] = measure(plain[:, :half_x], plain[:, half_x:], 1.0)
        result['two_tiles_colour_top_half_vs_bottom_half'] = measure(plain[:half_y], plain[half_y:], 1.0)
    with open(os.path.join(folder, 'half_tile_result.json'), 'w') as handle:
        json.dump(result, handle, indent=1)
    print(json.dumps(result, indent=1))

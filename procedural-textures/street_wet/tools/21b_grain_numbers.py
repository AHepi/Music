# What this does (plain Python, no Blender): measures how grainy ("gritty": white speckle) a kind of surface is in one or more pictures drawn from the MAIN camera
# (540 x 960), and how bright it is. "Grain" = the average difference between a dot and the average of its four neighbours, over the dots of that surface (found with the
# material-number picture of the same camera, work/r04/main_id.png). The dry Cycles road has grain 0.0035, a dry EEVEE road is near 0.007; the checker's EEVEE wet road was 0.029.
# You may name a part of the picture (left third of the road: "left", middle "middle", right "right", or all of it: "all"), and the lowest picture rows to ignore.
# Run: python3 -I tools/21b_grain_numbers.py SURFACE PART PICTURE [PICTURE ...]       e.g.  python3 -I tools/21b_grain_numbers.py street_setts left work/r21/*.png
#   SURFACE: street_setts | pavement_flags | kerb+gutter | walls    PART: left | middle | right | all
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ids = json.load(open(f'{ROOT}/work/r04/material_ids.json'))
id_map = np.asarray(Image.open(f'{ROOT}/work/r04/main_id.png').convert('RGB'))[..., 0].astype(int)
GROUPS = {'street_setts': ['street_setts'], 'pavement_flags': ['pavement_flags'], 'kerb+gutter': ['kerb_stone', 'channel_stones'],
          'walls': ['cottage_brick_door_left', 'cottage_brick_door_right', 'cottage_stone_door_left', 'cottage_stone_door_right']}


def part_mask(surface_mask, part):
    """Split the surface's dots into thirds from left to right (by where the surface is, row by row)."""
    if part == 'all':
        return surface_mask
    result = np.zeros_like(surface_mask)
    for row in range(surface_mask.shape[0]):
        cols = np.flatnonzero(surface_mask[row])
        if len(cols) < 6:
            continue
        third = len(cols) // 3
        chosen = {'left': cols[:third], 'middle': cols[third:2 * third], 'right': cols[2 * third:]}[part]
        result[row, chosen] = True
    return result


def measure(path, surface, part):
    array = np.asarray(Image.open(path).convert('RGB')).astype(float) / 255
    grey = 0.2126 * array[..., 0] + 0.7152 * array[..., 1] + 0.0722 * array[..., 2]
    base = np.isin(id_map, [ids[n] for n in GROUPS[surface]])
    mask = part_mask(base, part)
    inner = mask & np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
    # dots that were not drawn (a border render leaves the rest black) are ignored
    drawn = grey > 0.0
    inner &= drawn & np.roll(drawn, 1, 0) & np.roll(drawn, -1, 0) & np.roll(drawn, 1, 1) & np.roll(drawn, -1, 1)
    if inner.sum() < 50:
        return None
    blur = (np.roll(grey, 1, 0) + np.roll(grey, -1, 0) + np.roll(grey, 1, 1) + np.roll(grey, -1, 1)) / 4
    difference = np.abs(grey - blur)[inner]
    return dict(dots=int(inner.sum()), brightness=float(grey[inner].mean()), grain=float(difference.mean()), speckles=float((difference > 0.15).mean()))


if __name__ == '__main__':
    surface, part, pictures = sys.argv[1], sys.argv[2], sys.argv[3:]
    print(f'{surface} / {part}')
    for path in pictures:
        row = measure(path, surface, part)
        name = os.path.relpath(path, ROOT)
        print(f'  {name:60s} ' + ('too few dots drawn' if row is None else f"dots {row['dots']:6d}  brightness {row['brightness']:.3f}  grain {row['grain']:.4f}  speckles over 0.15: {row['speckles'] * 100:5.2f}%"))

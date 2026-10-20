# What this does (plain Python, no Blender): how grainy (sparkly) are the pavement flags, the road setts and the kerb/gutter stones in an EEVEE picture, compared with the Cycles wet picture and
# the dry one? "Grain" = the average difference between a dot and the average of its four neighbours (higher = more sparkle), over the dots of that surface (found with the material-number
# picture of the same camera). Run: python3 -I tools/12b_eevee_noise.py PICTURE.png [PICTURE.png ...]
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ids = json.load(open(f'{ROOT}/work/r04/material_ids.json'))
id_map = np.asarray(Image.open(f'{ROOT}/work/r04/main_id.png').convert('RGB'))[..., 0].astype(int)
GROUPS = {'pavement flags': ['pavement_flags'], 'road setts': ['street_setts'], 'kerb + gutter': ['kerb_stone', 'channel_stones']}


def grain(path, names):
    grey = np.asarray(Image.open(path).convert('L')).astype(float) / 255
    mask = np.isin(id_map, [ids[n] for n in names])
    blur = (np.roll(grey, 1, 0) + np.roll(grey, -1, 0) + np.roll(grey, 1, 1) + np.roll(grey, -1, 1)) / 4
    inner = mask & np.roll(mask, 1, 0) & np.roll(mask, -1, 0) & np.roll(mask, 1, 1) & np.roll(mask, -1, 1)
    bright = (np.abs(grey - blur) > 0.15)[inner].mean()
    return float(np.abs(grey - blur)[inner].mean()), float(bright)


print(f"{'picture':48s} " + ' | '.join(f'{g:>26s}' for g in GROUPS))
for path in sys.argv[1:]:
    row = [grain(path, names) for names in GROUPS.values()]
    print(f'{os.path.relpath(path, ROOT):48s} ' + ' | '.join(f'grain {g:.4f}, speckles {s * 100:5.2f}%' for g, s in row))

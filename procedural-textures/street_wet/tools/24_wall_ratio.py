# What this does (plain Python, no Blender): checks the WALLS the way the checker did. From a DRY and a WET picture of the same camera (the close wall camera "wall_lamp", 640 x 480,
# or the main camera 540 x 960) it works out, for every dot of a cottage wall, how bright the wet picture is as a share of the dry one, and makes a picture of it:
# blue = darker wet, red = lighter wet, grey = the same. Prints the average ratio of the wall, the share of wall dots darker than 0.9 and than 0.75 of dry, and the average in
# bands from the foot of the wall upward (the lowest eighth of the wall's rows, the next, ...). The checker's aim: the wall average under 1.0 and a clear blue band at the foot
# (at least a quarter darker, ratio 0.75 or less).
# Wall dots are found with the material-number picture of the same camera (work/r04/<camera>_id.png and material_ids.json, made in round 1: geometry has not changed).
# Run: python3 -I tools/24_wall_ratio.py CAMERA DRY.png WET.png OUT.jpg [ROW_FROM ROW_TO]      CAMERA: wall_lamp | main
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
camera, dry_path, wet_path, out_path = sys.argv[1:5]
ids = json.load(open(f'{ROOT}/work/r04/material_ids.json'))
id_map = np.asarray(Image.open(f'{ROOT}/work/r04/{camera}_id.png').convert('RGB'))[..., 0].astype(int)
walls = np.isin(id_map, [ids[n] for n in ('cottage_brick_door_left', 'cottage_brick_door_right', 'cottage_stone_door_left', 'cottage_stone_door_right') if n in ids])
dry_rgb = np.asarray(Image.open(dry_path).convert('RGB')).astype(float) / 255
wet_rgb = np.asarray(Image.open(wet_path).convert('RGB')).astype(float) / 255
luma = lambda a: 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]   # noqa: E731
dry, wet = luma(dry_rgb), luma(wet_rgb)
usable = walls & (dry > 0.02)
ratio = np.where(usable, wet / np.maximum(dry, 1e-4), 1.0)
print(f'{camera}: wall dots {int(walls.sum())}, usable (dry brightness over 0.02) {int(usable.sum())}')
print(f'  wall brightness dry {dry[walls].mean():.3f}  wet {wet[walls].mean():.3f}  mean wet/dry (brightness-weighted) {wet[walls].mean() / dry[walls].mean():.2f}')
print(f'  mean of per-dot ratios {ratio[usable].mean():.2f}, median {np.median(ratio[usable]):.2f}; share darker than 0.9: {(ratio[usable] < 0.9).mean() * 100:.0f}%, darker than 0.75: {(ratio[usable] < 0.75).mean() * 100:.0f}%')
rows = np.flatnonzero(walls.any(axis=1))
if len(sys.argv) > 6:
    rows = np.arange(int(sys.argv[5]), int(sys.argv[6]))
bands = np.array_split(rows[::-1], 8)       # from the bottom of the wall rows upward
print('  by band from the foot upward (brightness-weighted wet/dry):', end=' ')
for band in bands:
    m = np.zeros_like(walls)
    m[band] = walls[band]
    print(f'{wet[m].mean() / dry[m].mean():.2f}' if m.sum() > 20 and dry[m].mean() > 0 else 'n/a', end='  ')
print()
# picture: dry | wet | ratio
blue_red = np.zeros_like(dry_rgb)
t = np.clip((ratio - 1.0) / 0.6, -1, 1)            # ratio 0.4 .. 1.6  ->  -1 .. 1
blue_red[..., 0] = np.where(t > 0, 0.5 + 0.5 * t, 0.5 + 0.5 * t * 0.0)
blue_red[..., 2] = np.where(t < 0, 0.5 - 0.5 * t, 0.5)
blue_red[..., 1] = 0.5 - 0.45 * np.abs(t)
grey = np.stack([0.5 * np.ones_like(dry)] * 3, axis=-1)
blue_red = np.where(usable[..., None], blue_red, 0.07 * np.ones_like(blue_red))
h, w = dry.shape
canvas = Image.new('RGB', (3 * w + 16, h + 26), (18, 18, 20))
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
for i, (arr, label) in enumerate(((dry_rgb, 'dry'), (wet_rgb, 'wet'), (blue_red, 'wet / dry on the walls: blue darker, red lighter, grey same'))):
    canvas.paste(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)), (i * (w + 8), 26))
    draw.text((i * (w + 8) + 4, 4), label, fill=(230, 230, 230), font=font)
canvas.save(out_path, quality=88)

# What this does: reads the mask pictures made by 03_wet_street_test.py (--only masks --puddle_list ...) and the material-number picture, and says how
# much of the ROAD the puddles cover at each puddle amount, and how wet the walls are; also writes a sheet of the masks (red = wet, green = puddle, blue = streak).
# Plain Python (python3 -I). Run from the study folder: python3 -I tools/04_puddle_coverage.py FOLDER_OF_MASKS OUTPUT_SHEET.png 0.0,0.3,0.55,0.8
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

folder, sheet_path, values = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
numbers = json.load(open('work/ids/street_main_numbers.json'))['numbers']
ids = np.array(Image.open('work/ids/street_main_ids.png'))[..., 0]
road = ids == numbers['street_setts']
walls = (ids == numbers['cottage_brick']) | (ids == numbers['cottage_stone'])
font = ImageFont.load_default(size=14)
tiles, rows = [], {}
for value in values:
    masks = np.array(Image.open(f'{folder}/main_masks_p{value}.png').convert('RGB')).astype(float) / 255
    rows[value] = dict(road_puddle_percent=round(float((masks[..., 1][road] > 0.5).mean() * 100), 1), road_any_water_percent=round(float((masks[..., 1][road] > 0.05).mean() * 100), 1),
                       road_wet_mean=round(float(masks[..., 0][road].mean()), 2), walls_wet_mean=round(float(masks[..., 0][walls].mean()), 2))
    print(value, rows[value])
    tiles.append((value, Image.fromarray((masks * 255).astype(np.uint8))))
w, h = 270, 480
sheet = Image.new('RGB', (len(tiles) * (w + 6), h + 22), (245, 245, 245))
draw = ImageDraw.Draw(sheet)
for i, (value, tile) in enumerate(tiles):
    sheet.paste(tile.resize((w, h), Image.NEAREST), (i * (w + 6), 22))
    draw.text((i * (w + 6) + 3, 3), f'Puddles = {value}', fill=(0, 0, 0), font=font)
sheet.save(sheet_path)
json.dump(rows, open(sheet_path.replace('.png', '.json'), 'w'), indent=1)

# What this does: lays the per-prop pictures from render_contact_sheet.py out as one labelled
# contact sheet (name, real size and triangle count under each).
#
# Run: python3 -I make_sheet.py PICTURE_FOLDER OUT.png [--library FOLDER]
#   (--library: another prop library's folder, holding its index.json; the pit village's by default)

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'assets', 'models', 'pit-village', 'props', 'index.json')

arguments = sys.argv[1:]
if '--library' in arguments:
    at = arguments.index('--library')
    INDEX = os.path.join(arguments[at + 1], 'index.json')
    del arguments[at:at + 2]
folder, out = arguments[0], arguments[1]
with open(INDEX) as f: index = json.load(f)
cell, label = 420, 54
columns = 6
rows = (len(index) + columns - 1) // columns
sheet = Image.new('RGB', (columns * cell, rows * (cell + label)), (24, 24, 26))
draw = ImageDraw.Draw(sheet)
bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
for i, entry in enumerate(index):
    name = entry['file'][:-4]
    x, y = (i % columns) * cell, (i // columns) * (cell + label)
    path = os.path.join(folder, f'{name}.png')
    if os.path.exists(path):
        sheet.paste(Image.open(path).convert('RGB').resize((cell, cell)), (x, y))
    size = entry['size_metres']
    draw.text((x + 8, y + cell + 6), name, font=bold, fill=(236, 230, 214))
    draw.text((x + 8, y + cell + 29), f"{size['width_x']} x {size['depth']} x {size['height']} m   {entry['triangles']:,} tris",
              font=small, fill=(170, 170, 170))
sheet.save(out)
print('sheet', out, sheet.size)

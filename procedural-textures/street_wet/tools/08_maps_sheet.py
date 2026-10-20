# What this does (plain Python, no Blender): one sheet that shows the baked maps. Top: the ground atlas (road, gutter, kerb tops and pavements seen from above, one picture for the whole
# street, 48 dots a metre) -- a 12 m stretch (y = 4 to 16 m, the middle of the main camera's view) of each map, side by side, then the whole 84 m of the colour and puddle maps small.
# Bottom: the front of a stone cottage and of a brick cottage (the wall maps, 200 dots a metre). Every grey map is shown as it is stored: black = 0, white = 1.
# Run: python3 -I tools/08_maps_sheet.py MAPS_FOLDER OUT.jpg
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

maps, out = sys.argv[1], sys.argv[2]
BOLD = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 20)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
report = json.load(open(os.path.join(maps, 'bake_report.json')))
PPM = report['ground_atlas']['dots_per_metre']
H = report['ground_atlas']['height']
ground = [('colour', 'jpg', 'wet colour', 'base colour'), ('roughness', 'png', 'roughness', 'green of the metal-roughness picture'),
          ('coat', 'png', 'clear coat strength', 'red of the clear coat picture'), ('coat_roughness', 'png', 'clear coat roughness', 'green of the clear coat picture'),
          ('specularity', 'png', 'specularity', 'alpha of the specular picture'), ('normal', 'png', 'wet normal', 'checking only, not in the glb'),
          ('puddles', 'png', 'puddle mask', 'checking only'), ('wet', 'png', 'wet mask', 'checking only')]
SCALE = 0.62
crop_top, crop_bottom = int((72 - 16) * PPM), int((72 - 4) * PPM)
tiles = []
for key, ext, label, note in ground:
    image = Image.open(os.path.join(maps, f'ground_{key}.{ext}')).convert('RGB')
    crop = image.crop((0, crop_top, image.width, crop_bottom))
    tiles.append((crop.resize((int(crop.width * SCALE), int(crop.height * SCALE)), Image.LANCZOS), label, note, image))
cell_w = tiles[0][0].width + 10
wall = [('colour', 'jpg', 'wet colour'), ('roughness', 'png', 'roughness'), ('coat', 'png', 'clear coat'), ('coat_roughness', 'png', 'clear coat roughness'),
        ('specularity', 'png', 'specularity'), ('wet', 'png', 'wet mask')]
WSCALE = 0.30
wall_rows = []
for key, title in (('wall_stone_door_left', 'stone cottage front (layout: door left)'), ('wall_brick_door_left', 'brick cottage front (layout: door left)')):
    row = []
    for channel, ext, label in wall:
        image = Image.open(os.path.join(maps, f'{key}_{channel}.{ext}')).convert('RGB')
        row.append((image.resize((int(image.width * WSCALE), int(image.height * WSCALE)), Image.LANCZOS), label))
    wall_rows.append((title, row))
width = max(len(tiles) * cell_w + 10, len(wall) * (wall_rows[0][1][0][0].width + 10) * 1 + 10)
overview_w = 2 * 80
height = 60 + tiles[0][0].height + 70 + 40 + (wall_rows[0][1][0][0].height + 50) * 2 + 20
sheet = Image.new('RGB', (width + overview_w + 20, height), (18, 18, 20))
draw = ImageDraw.Draw(sheet)
draw.text((10, 8), f"Baked maps, wet state (wetness {report['wetness']}, puddles {report['puddles']}). Ground atlas: 12 m of the street (y = 4 to 16 m) at 48 dots a metre; wall fronts at 200 dots a metre.", font=BOLD, fill=(235, 235, 235))
x = 10
for tile, label, note, full in tiles:
    sheet.paste(tile, (x, 60))
    draw.text((x, 34), label, font=BOLD, fill=(240, 220, 160))
    draw.text((x, 60 + tile.height + 4), note, font=SMALL, fill=(190, 190, 195))
    x += cell_w
# the whole street, colour and puddle mask, small, on the right
for index, (key, ext) in enumerate((('colour', 'jpg'), ('puddles', 'png'))):
    image = Image.open(os.path.join(maps, f'ground_{key}.{ext}')).convert('RGB')
    small = image.resize((70, int(image.height * 70 / image.width)), Image.LANCZOS)
    small = small.crop((0, 0, 70, min(small.height, 640)))
    sheet.paste(small, (width + 20 + index * 80, 60))
draw.text((width + 20, 34), 'whole street', font=BOLD, fill=(240, 220, 160))
draw.text((width + 20, 60 + 650), 'colour | puddles (top = y 72 m)', font=SMALL, fill=(190, 190, 195))
y = 60 + tiles[0][0].height + 60
for title, row in wall_rows:
    draw.text((10, y), title, font=BOLD, fill=(240, 220, 160))
    x = 10
    for image, label in row:
        sheet.paste(image, (x, y + 28))
        draw.text((x, y + 28 + image.height + 2), label, font=SMALL, fill=(190, 190, 195))
        x += image.width + 10
    y += row[0][0].height + 60
sheet = sheet.crop((0, 0, sheet.width, min(sheet.height, y + 10)))
sheet.save(out, quality=88)
print('wrote', out, sheet.size, os.path.getsize(out) // 1024, 'KB')

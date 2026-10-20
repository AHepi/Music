# What this does: turns the material-number pictures (01_material_map.py + 01b_count_materials.py) into one readable picture: the three camera
# views side by side, each material grouped (road, pavement, walls, roofs, sky ...) and painted its group's colour, with a table of the share of the
# frame per group. Also writes work/group_shares.json (the same table as numbers).
# Plain Python (run with python3 -I). Run from the study folder:  python3 -I tools/01c_false_colour_picture.py
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFont

GROUPS = [
    ('road setts (cobbles)', ['street_setts'], (230, 60, 60)),
    ('pavement flags, kerbs, channel stones', ['pavement_flags', 'kerb_stone', 'channel_stones', 'channel plain stone'], (240, 150, 60)),
    ('walls: brick and rubble stone', ['cottage_brick', 'cottage_stone', 'colliery_brick', 'plaster_dark'], (70, 120, 220)),
    ('dressed stone (sills, steps, lintels)', ['dressed_stone', 'dark_dressed_stone'], (130, 190, 255)),
    ('roofs: slate, ridge, chimney pots', ['roof_slate', 'ridge_clay', 'chimney_pot_clay', 'chimney_pot_sooted'], (60, 170, 90)),
    ('metal: lamp posts, gutters, headframe, wheels', ['cast_iron', 'headframe_steel', 'wheel_iron', 'wire_rope', 'brass'], (170, 90, 200)),
    ('colliery yard, spoil heap, moor (ground)', ['colliery_yard', 'spoil_heap', 'moor'], (150, 110, 60)),
    ('sky dome', ['sky_dome_glow'], (40, 40, 40)),
    ('windows, doors, paint, fascia', ['window_dark_0', 'window_dark_1', 'window_dark_2', 'window_lit_glow_0', 'window_lit_glow_1', 'window_lit_glow_2',
        'engine_window_glow', 'lamp_glass_glow', 'interior_dark', 'fascia_board', 'paint_black', 'paint_bottle_green', 'paint_brown', 'paint_cream',
        'paint_maroon', 'paint_navy', 'boarded_blue', 'boarded_green'], (240, 220, 80)),
]
PROPS_COLOUR = (250, 80, 200)   # every other material: the props and signs added for the shots
VIEWS = [('street_main', 'street.blend main camera'), ('lockout', 'lockout plate camera'), ('notice-corner', 'notice-corner plate camera')]
folder = 'work/ids'
group_of = {}
for index, (label, names, colour) in enumerate(GROUPS):
    for name in names:
        group_of[name] = index
tables, tiles = {}, []
for key, title in VIEWS:
    numbers = json.load(open(f'{folder}/{key}_numbers.json'))['numbers']
    picture = np.array(Image.open(f'{folder}/{key}_ids.png'))[..., 0]
    out = np.zeros(picture.shape + (3,), dtype=np.uint8)
    share = {label: 0.0 for label, _, _ in GROUPS}
    share['props and signs (all other materials)'] = 0.0
    total = picture.size
    for name, number in numbers.items():
        mask = picture == number
        if name in group_of:
            label, _, colour = GROUPS[group_of[name]]
        else:
            label, colour = 'props and signs (all other materials)', PROPS_COLOUR
        out[mask] = colour
        share[label] += mask.sum() / total
    tables[key] = {k: round(v * 100, 2) for k, v in share.items()}
    tiles.append((title, Image.fromarray(out)))
json.dump(tables, open('work/group_shares.json', 'w'), indent=1)
font = ImageFont.load_default(size=15)
small = ImageFont.load_default(size=13)
tile_w, tile_h = 360, 640
legend_w = 330
sheet = Image.new('RGB', (legend_w + 3 * tile_w + 40, tile_h + 70), (245, 245, 245))
draw = ImageDraw.Draw(sheet)
for column, (title, tile) in enumerate(tiles):
    sheet.paste(tile.resize((tile_w, tile_h), Image.NEAREST), (legend_w + 10 + column * (tile_w + 10), 50))
    draw.text((legend_w + 10 + column * (tile_w + 10), 28), title, fill=(0, 0, 0), font=font)
y = 28
draw.text((10, 6), 'False colour: one colour per kind of surface', fill=(0, 0, 0), font=font)
for label, _, colour in GROUPS + [('props and signs (all other materials)', [], PROPS_COLOUR)]:
    draw.rectangle([10, y + 30, 28, y + 46], fill=colour)
    values = [tables[key][label] for key, _ in VIEWS]
    draw.text((34, y + 29), label[:44], fill=(0, 0, 0), font=small)
    draw.text((34, y + 44), 'share of frame: ' + '  /  '.join(f'{v:.1f}%' for v in values), fill=(60, 60, 60), font=small)
    y += 56
draw.text((10, tile_h + 52), 'shares are: main camera / lockout plate / notice-corner plate', fill=(0, 0, 0), font=small)
sheet.convert('RGB').save('pictures/01 Street false colour - what fills the frame.jpg', quality=88)
for key, _ in VIEWS:
    print(key, tables[key])

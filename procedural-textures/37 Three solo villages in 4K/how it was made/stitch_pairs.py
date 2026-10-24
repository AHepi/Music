# What this file does: takes the 4K pictures of the three solo-built villages and puts them two side by
# side for every view and every pairing (Sonnet alone with Opus's second pass, Opus's first pass with its
# second pass, Sonnet alone with Opus's first pass), with plain labels, at full 4K size per side.
# Run: python3 stitch_pairs.py RENDERS_FOLDER PAIRS_FOLDER
import os
import sys
from PIL import Image, ImageDraw, ImageFont

renders, pairs_folder = sys.argv[1], sys.argv[2]
os.makedirs(pairs_folder, exist_ok=True)
villages = {'sonnet': 'Sonnet alone', 'opus1': 'Opus alone, first pass', 'opus2': 'Opus alone, second pass'}
pairings = [('sonnet', 'opus2'), ('opus1', 'opus2'), ('sonnet', 'opus1')]
views = [
    ('01_village_from_above', 'Whole village from above'), ('02_road_at_eye_level', 'Road at eye level'),
    ('03_stable_close', 'Stable close'), ('04_cottage_close', 'Cottage close'),
    ('05_road_surface_closeup', 'Road surface close-up'), ('06_second_cottage', 'A second cottage'),
    ('07_props_close', 'Props close'), ('08_stable_stalls', 'Into the empty stable stalls'),
    ('09_puddle_ground_level', 'Puddle at ground level'), ('10_road_into_forest', 'Road into the forest'),
    ('11_village_low_drone', 'Village from a low drone height'),
]
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 64)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 52)
except OSError:
    font = small = ImageFont.load_default()
width, height, header, gap = 3840, 2560, 120, 24
made, missing = 0, []
for number, (view, view_label) in enumerate(views, 1):
    for left, right in pairings:
        paths = [os.path.join(renders, f'{village}_{view}.jpg') for village in (left, right)]
        if not all(os.path.exists(p) for p in paths):
            missing.append(f'{view} {left}-{right}')
            continue
        sheet = Image.new('RGB', (width * 2 + gap, height + header), (20, 20, 20))
        draw = ImageDraw.Draw(sheet)
        for side, (village, path) in enumerate(zip((left, right), paths)):
            with Image.open(path) as picture:
                sheet.paste(picture.convert('RGB').resize((width, height)), (side * (width + gap), header))
            draw.text((side * (width + gap) + 30, 26), f'{villages[village]}  ·  {view_label}', fill=(240, 235, 220), font=font)
        name = f'{number:02d} {view_label} - {villages[left]} (left) vs {villages[right]} (right).jpg'
        sheet.save(os.path.join(pairs_folder, name), quality=90)
        made += 1
print('pairs made', made, 'missing', missing)

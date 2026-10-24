"""What this does: lays the filmed stills of pages 3 to 5 out at about phone size (each 330 x 587, the size a
1080 x 1920 frame shows at on a phone held upright), in numbered sheets of twelve (two rows of six), each still
with its chapter time and its note wrapped under it, so every moment can be judged the way a viewer sees it.
Use: python3 -I phone_groups.py STILLS_FOLDER NOTES.json OUT_FOLDER [PER_SHEET=12] [COLUMNS=6] [WIDTH=330]
  writes OUT_FOLDER/group-01.jpg, group-02.jpg ...
"""
import glob
import json
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

folder, notes, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
per_sheet = int(sys.argv[4]) if len(sys.argv) > 4 else 12
columns = int(sys.argv[5]) if len(sys.argv) > 5 else 6
width = int(sys.argv[6]) if len(sys.argv) > 6 else 330
os.makedirs(out, exist_ok=True)
files = sorted(glob.glob(os.path.join(folder, 'still-*.jpg')), key=lambda f: float(os.path.basename(f)[6:-4]))
height, label = width * 16 // 9, 50
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
for g in range(0, len(files), per_sheet):
    group = files[g:g + per_sheet]
    rows = (len(group) + columns - 1) // columns
    sheet = Image.new('RGB', (columns * (width + 8) + 8, rows * (height + label + 8) + 8), (24, 24, 26))
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(group):
        x, y = 8 + (i % columns) * (width + 8), 8 + (i // columns) * (height + label + 8)
        sheet.paste(Image.open(path).convert('RGB').resize((width, height), Image.LANCZOS), (x, y))
        moment = os.path.basename(path)[6:-4]
        for k, line in enumerate(textwrap.wrap(f'{moment} s  {notes.get(moment, "")}', width=width // 8)[:2]):
            draw.text((x + 4, y + height + 5 + k * 19), line, fill=(230, 230, 230), font=font)
    name = os.path.join(out, f'group-{g // per_sheet + 1:02d}.jpg')
    sheet.save(name, quality=88)
    print(name, len(group), 'stills', os.path.basename(group[0])[6:-4], 'to', os.path.basename(group[-1])[6:-4], 's')

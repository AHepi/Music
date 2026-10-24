"""What this does: lays filmed stills side by side at about phone size (each 330 x 587 by default), each with its
chapter time and its note wrapped onto two lines under it, so a page's moments can be judged the way a viewer sees
them (sheet.py, with the notes wrapped so long ones don't run into the next still).
Use: python3 -I sheet_wrapped.py STILLS_FOLDER OUT.jpg NOTES.json [COLUMNS=6] [WIDTH=330]
"""
import glob
import json
import os
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

folder, out, notes = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
columns = int(sys.argv[4]) if len(sys.argv) > 4 else 6
width = int(sys.argv[5]) if len(sys.argv) > 5 else 330
files = sorted(glob.glob(os.path.join(folder, 'still-*.jpg')), key=lambda f: float(os.path.basename(f)[6:-4]))
height, label = width * 16 // 9, 50
rows = (len(files) + columns - 1) // columns
sheet = Image.new('RGB', (columns * (width + 8) + 8, rows * (height + label + 8) + 8), (24, 24, 26))
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
for i, path in enumerate(files):
    x, y = 8 + (i % columns) * (width + 8), 8 + (i // columns) * (height + label + 8)
    sheet.paste(Image.open(path).convert('RGB').resize((width, height), Image.LANCZOS), (x, y))
    moment = os.path.basename(path)[6:-4]
    lines = textwrap.wrap(f'{moment} s  {notes.get(moment, "")}', width=width // 8)[:2]
    for k, line in enumerate(lines):
        draw.text((x + 4, y + height + 5 + k * 19), line, fill=(230, 230, 230), font=font)
sheet.save(out, quality=88)
print(out, len(files), 'stills')

"""What this does: lays stills drawn by render-paper-film.mjs --stills side by side at about phone size (each 360 x 640,
the size a 1080 x 1920 frame shows at on a phone held upright), each with its moment and a note under it, so the
pages' moments can be judged the way a viewer sees them.
Use: python3 -I sheet.py STILLS_FOLDER OUT.jpg [COLUMNS=6] [WIDTH=360] [NOTES.json: {"57.93": "slide starts", ...}]
"""
import glob
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

folder, out = sys.argv[1], sys.argv[2]
columns = int(sys.argv[3]) if len(sys.argv) > 3 else 6
width = int(sys.argv[4]) if len(sys.argv) > 4 else 360
notes = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else {}
files = sorted(glob.glob(os.path.join(folder, 'still-*.jpg')), key=lambda f: float(os.path.basename(f)[6:-4]))
height = width * 16 // 9
rows = (len(files) + columns - 1) // columns
sheet = Image.new('RGB', (columns * (width + 8) + 8, rows * (height + 34) + 8), (24, 24, 26))
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
except OSError:
    font = ImageFont.load_default()
for i, path in enumerate(files):
    x, y = 8 + (i % columns) * (width + 8), 8 + (i // columns) * (height + 34)
    sheet.paste(Image.open(path).convert('RGB').resize((width, height), Image.LANCZOS), (x, y))
    moment = os.path.basename(path)[6:-4]
    draw.text((x + 4, y + height + 8), f'{moment} s  {notes.get(moment, "")}', fill=(230, 230, 230), font=font)
sheet.save(out, quality=90)
print(out, len(files), 'stills')

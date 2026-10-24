"""What this does: lays the stills drawn by render-paper-film.mjs --stills side by side, small, each with its moment
written under it, so a page's moments can be looked at in one picture.
Use: python3 -I contact_sheet.py STILLS_FOLDER OUT.jpg [COLUMNS=6] [WIDTH=300]
"""
import glob
import os
import sys

from PIL import Image, ImageDraw

folder, out = sys.argv[1], sys.argv[2]
columns = int(sys.argv[3]) if len(sys.argv) > 3 else 6
width = int(sys.argv[4]) if len(sys.argv) > 4 else 300
files = sorted(glob.glob(os.path.join(folder, 'still-*.jpg')), key=lambda f: float(os.path.basename(f)[6:-4]))
height = width * 16 // 9
rows = (len(files) + columns - 1) // columns
sheet = Image.new('RGB', (columns * (width + 8) + 8, rows * (height + 30) + 8), (24, 24, 26))
draw = ImageDraw.Draw(sheet)
for i, path in enumerate(files):
    x, y = 8 + (i % columns) * (width + 8), 8 + (i // columns) * (height + 30)
    sheet.paste(Image.open(path).convert('RGB').resize((width, height)), (x, y))
    draw.text((x + 4, y + height + 6), os.path.basename(path)[6:-4] + ' s', fill=(230, 230, 230))
sheet.save(out, quality=90)
print(out, len(files), 'stills')

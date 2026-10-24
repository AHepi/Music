"""What this does: lays several stills side by side on one contact sheet, each labelled with its
time, so a page can be checked at a glance. Use: python3 -I sheet.py OUT.jpg COLUMNS STILL [STILL ...]"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont
out, columns, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
w, h = 432, 768
rows = (len(files) + columns - 1) // columns
sheet = Image.new("RGB", (w * columns, h * rows), (20, 20, 20))
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
for i, f in enumerate(files):
    im = Image.open(f).convert("RGB").resize((w, h))
    d = ImageDraw.Draw(im)
    d.text((8, 6), os.path.basename(f).replace("still-", "").replace(".jpg", " s"), fill=(255, 255, 0), font=font)
    sheet.paste(im, ((i % columns) * w, (i // columns) * h))
sheet.save(out, quality=86)

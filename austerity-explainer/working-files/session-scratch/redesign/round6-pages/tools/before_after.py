# What this does: lays round 5's stills (top row) over round 6's stills of the same moments (bottom row), each
# labelled with its moment and a short note, at a chosen width, into one sheet for the report.
# Use: python3 -I before_after.py OUT.jpg WIDTH_EACH BEFORE_FOLDER AFTER_FOLDER "SECONDS:note" ...
#   (each still is BEFORE_FOLDER/still-SECONDS.jpg and AFTER_FOLDER/still-SECONDS.jpg; SECONDS with two decimals)
import os
import sys

from PIL import Image, ImageDraw

out, width, before, after, moments = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5:]
height = round(width * 1920 / 1080)
label = 22
sheet = Image.new('RGB', (width * len(moments), 2 * (height + label)), (20, 20, 20))
draw = ImageDraw.Draw(sheet)
for i, moment in enumerate(moments):
    seconds, _, note = moment.partition(':')
    for row, (folder, name) in enumerate(((before, 'round 5'), (after, 'round 6'))):
        path = os.path.join(folder, f'still-{float(seconds):.2f}.jpg')
        y = row * (height + label)
        draw.text((i * width + 4, y + 4), f'{name} {float(seconds):.2f} s {note}', fill=(255, 255, 255))
        if os.path.exists(path):
            sheet.paste(Image.open(path).convert('RGB').resize((width, height)), (i * width, y + label))
sheet.save(out, quality=88)

# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# A small helper for the study's picture sheets (plain Python): puts pictures side by side with a title line and a note line over each, writes a JPEG.
# Use as a library:  from b08_sheets import sheet;  sheet(path, [(title, note, image_path_or_array, crop_box_or_None), ...], columns=3, cell_width=540, heading='...')
# crop_box = (x0, y0, x1, y1) in the picture's own dots; the crop is scaled to cell_width. Nothing else.
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BOLD = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
SMALL = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)


def sheet(path, cells, columns=3, cell_width=540, heading=None, gap=8, quality=88):
    tiles = []
    for title, note, source, box in cells:
        image = Image.open(source).convert('RGB') if isinstance(source, str) else Image.fromarray(np.asarray(source))
        if box:
            image = image.crop(box)
        scale = cell_width / image.width
        tiles.append((title, note, image.resize((cell_width, max(1, int(image.height * scale))), Image.LANCZOS)))
    rows = [tiles[i:i + columns] for i in range(0, len(tiles), columns)]
    head = 34 if heading else 0
    row_heights = [max(t[2].height for t in row) + 44 for row in rows]
    sheet_image = Image.new('RGB', (columns * cell_width + (columns + 1) * gap, head + sum(row_heights) + gap), (18, 18, 20))
    draw = ImageDraw.Draw(sheet_image)
    if heading:
        draw.text((gap, 7), heading, font=BOLD, fill=(235, 235, 235))
    y = head
    for row, row_height in zip(rows, row_heights):
        for column, (title, note, image) in enumerate(row):
            x = gap + column * (cell_width + gap)
            draw.text((x + 2, y + 1), title, font=BOLD, fill=(240, 220, 160))
            draw.text((x + 2, y + 24), note, font=SMALL, fill=(190, 190, 195))
            sheet_image.paste(image, (x, y + 44))
        y += row_height
    sheet_image.save(path, quality=quality)
    print('wrote', path, sheet_image.size, os.path.getsize(path) // 1024, 'KB')

# What this does: lays the check pictures from draw_works_views.py out as one labelled contact sheet, and
# beside it the same pictures at a phone's size (each frame 200 pixels wide, about how big the film looks
# held in a hand), for judging at a glance whether the two factories are told apart. Under each picture: what
# it shows, and (when draw_works_views.py measured them) how much of each chimney shows over what stands in
# front of it.
#
# Run: python3 -I make_works_sheet.py PICTURE_FOLDER OUT.png [view names in order ...]

import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def wrapped(draw, text, font, width):
    """Split text into lines that fit the width."""
    lines, line = [], ''
    for word in text.split():
        trial = f'{line} {word}'.strip()
        if draw.textlength(trial, font=font) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line] if line else lines


def main():
    folder, out = sys.argv[1], sys.argv[2]
    with open(os.path.join(folder, 'views.json')) as f:
        views = json.load(f)
    measured = {}
    if os.path.exists(os.path.join(folder, 'measured.json')):
        with open(os.path.join(folder, 'measured.json')) as f:
            measured = json.load(f)
    order = sys.argv[3:] or list(views)
    cell_width, cell_height, label = 405, 720, 150
    columns = 4
    rows = (len(order) + columns - 1) // columns
    phone_width = 200
    phone_height = phone_width * 16 // 9
    sheet = Image.new('RGB', (columns * (cell_width + 12) + 40 + len(order) * 0 + 4 * (phone_width + 10),
                              rows * (cell_height + label) + 60), (24, 24, 26))
    draw = ImageDraw.Draw(sheet)
    bold, small = ImageFont.truetype(BOLD, 17), ImageFont.truetype(FONT, 13)
    for index, name in enumerate(order):
        x = (index % columns) * (cell_width + 12) + 12
        y = (index // columns) * (cell_height + label) + 12
        sheet.paste(Image.open(os.path.join(folder, f'{name}.png')).convert('RGB').resize((cell_width, cell_height)), (x, y))
        draw.text((x + 4, y + cell_height + 6), name, font=bold, fill=(236, 230, 214))
        lines = wrapped(draw, views[name], small, cell_width - 8)
        for chimney, facts in measured.get(name, {}).items():
            lines += wrapped(draw, f'{chimney}: {facts}', small, cell_width - 8)
        for k, line in enumerate(lines[:7]):
            draw.text((x + 4, y + cell_height + 30 + k * 16), line, font=small, fill=(180, 180, 180))
    # the phone-size column: the lane views at the size a phone shows them
    phone_x = columns * (cell_width + 12) + 30
    draw.text((phone_x, 12), 'at phone size', font=bold, fill=(236, 230, 214))
    phone_views = [name for name in ('w3', 'w1', 'w2', 'w3-working', 'no-1-front', 'no-2-front') if name in order]
    for k, name in enumerate(phone_views):
        px = phone_x + (k % 4) * (phone_width + 10)
        py = 40 + (k // 4) * (phone_height + 30)
        sheet.paste(Image.open(os.path.join(folder, f'{name}.png')).convert('RGB').resize((phone_width, phone_height), Image.LANCZOS), (px, py))
        draw.text((px, py + phone_height + 4), name, font=small, fill=(180, 180, 180))
    sheet.save(out)
    print('sheet', out, sheet.size)


if __name__ == '__main__':
    main()

"""What this does: lays stills side by side on one contact sheet, in rows, each labelled with its
time (or file name), so a page or a whole film can be checked at a glance.

Use: python3 -I contact_sheet.py OUTPUT.jpg COLUMNS STILL_OR_FOLDER [STILL_OR_FOLDER ...]
  - a folder adds every still-*.jpg / still-*.png in it (as made by render-paper-film.mjs --stills);
  - stills are sorted by their time when their names say it (still-12.50.jpg), else kept in order.
Look at single stills at full size too: a small sheet hides cut-off edges and faint mistakes.
"""

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CELL_WIDTH, CELL_HEIGHT = 432, 768   # each still shrunk to this (9:16)


def any_font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf",
                 "C:/Windows/Fonts/arialbd.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def time_in_name(path):
    match = re.search(r"(\d+(?:\.\d+)?)", path.stem.replace("still-", ""))
    return float(match.group(1)) if match else None


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    output, columns = sys.argv[1], int(sys.argv[2])
    stills = []
    for item in sys.argv[3:]:
        path = Path(item)
        if path.is_dir():
            found = sorted(list(path.glob("still-*.jpg")) + list(path.glob("still-*.png")),
                           key=lambda p: time_in_name(p) or 0)
            stills.extend(found)
        else:
            stills.append(path)
    if not stills:
        sys.exit("no stills found")
    rows = (len(stills) + columns - 1) // columns
    sheet = Image.new("RGB", (CELL_WIDTH * columns, CELL_HEIGHT * rows), (20, 20, 20))
    font = any_font(22)
    for i, still in enumerate(stills):
        picture = Image.open(still).convert("RGB").resize((CELL_WIDTH, CELL_HEIGHT))
        seconds = time_in_name(still)
        label = f"{seconds:.2f} s" if seconds is not None and still.stem.startswith("still-") else still.stem
        ImageDraw.Draw(picture).text((8, 6), label, fill=(255, 255, 0), font=font)
        sheet.paste(picture, ((i % columns) * CELL_WIDTH, (i // columns) * CELL_HEIGHT))
    sheet.save(output, quality=86)
    print(f"{output}: {len(stills)} stills, {columns} across")


main()

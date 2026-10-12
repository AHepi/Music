"""What this does: makes one picture showing every painted figure or object cut out by its mask,
laid over bright magenta. Anything the background remover dropped (a missing lectern, a faint
island, a see-through heap) shows at once as magenta where paint should be.

Use: python3 -I contact_sheet_masks.py PAINTINGS_FOLDER OUTPUT.jpg [PICTURE_NAME ...]
PAINTINGS_FOLDER holds the paintings (name.jpg or name.png) and masks/name-mask.png.
Name pictures at the end (for example 201-politician) to show only those.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CELL = 420
COLUMNS = 4


def any_font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main():
    folder, output, wanted = Path(sys.argv[1]), sys.argv[2], set(sys.argv[3:])
    font = any_font(20)
    tiles = []
    for mask_path in sorted((folder / "masks").glob("*-mask.png")):
        name = mask_path.name[:-len("-mask.png")]
        if wanted and name not in wanted:
            continue
        picture_path = next((p for p in (folder / f"{name}.jpg", folder / f"{name}.png") if p.exists()), None)
        if picture_path is None:
            continue
        picture = Image.open(picture_path).convert("RGB")
        mask = Image.open(mask_path).convert("L").resize(picture.size)
        cut = Image.new("RGB", picture.size, (255, 0, 255))
        cut.paste(picture, (0, 0), mask)
        cut.thumbnail((CELL, CELL - 26))
        tile = Image.new("RGB", (CELL, CELL), (40, 40, 40))
        tile.paste(cut, ((CELL - cut.width) // 2, 26))
        ImageDraw.Draw(tile).text((6, 2), name, fill="white", font=font)
        tiles.append(tile)
    if not tiles:
        raise SystemExit("no paintings with masks found")
    rows = (len(tiles) + COLUMNS - 1) // COLUMNS
    sheet = Image.new("RGB", (COLUMNS * CELL, rows * CELL), (20, 20, 20))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % COLUMNS) * CELL, (i // COLUMNS) * CELL))
    sheet.save(output, quality=88)
    print(f"{len(tiles)} cut-outs on {output}")


if __name__ == "__main__":
    main()

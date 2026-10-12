"""What this does: makes one picture showing finished paper pieces over a mid-grey page colour, so
the off-white paper margins, printed labels and cut edges can be checked at a glance.

Use: python3 -I contact_sheet_pieces.py PIECES_FOLDER OUTPUT.jpg [PIECE_NAME ...]
With no names, every piece in the folder's pieces.json is shown (pages, the full backgrounds, are skipped).
"""

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CELL = 400
COLUMNS = 5


def any_font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main():
    folder, output = Path(sys.argv[1]), sys.argv[2]
    names = sys.argv[3:]
    if not names:
        info = json.loads((folder / "pieces.json").read_text())
        names = [name for name, piece in info.items() if piece["kind"] == "piece"]
    font = any_font(18)
    tiles = []
    for name in names:
        piece = Image.open(folder / f"{name}.png").convert("RGBA")
        piece.thumbnail((CELL - 10, CELL - 34))
        tile = Image.new("RGBA", (CELL, CELL), (58, 72, 80, 255))
        tile.alpha_composite(piece, ((CELL - piece.width) // 2, 28))
        ImageDraw.Draw(tile).text((6, 4), name, fill="white", font=font)
        tiles.append(tile)
    rows = (len(tiles) + COLUMNS - 1) // COLUMNS
    sheet = Image.new("RGB", (COLUMNS * CELL, rows * CELL), (20, 20, 20))
    for i, tile in enumerate(tiles):
        sheet.paste(tile.convert("RGB"), ((i % COLUMNS) * CELL, (i // COLUMNS) * CELL))
    sheet.save(output, quality=88)
    print(f"{len(tiles)} pieces on {output}")


if __name__ == "__main__":
    main()

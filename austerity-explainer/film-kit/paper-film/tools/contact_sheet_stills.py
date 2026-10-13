"""What this does: lays single frames side by side, each labelled with its time, to check many
moments of a scene at once (made by render-paper-film.mjs SCENE FOLDER --stills t1 t2 ...).

Use: python3 -I contact_sheet_stills.py STILLS_FOLDER OUTPUT.jpg [WIDTH_OF_EACH, default 300]
Look at single stills at full size too: small sheets hide cut-off edges and faint mistakes.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def any_font(size):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/Library/Fonts/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main():
    folder, output = Path(sys.argv[1]), sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    files = sorted(folder.glob("still-*.jpg"), key=lambda p: float(p.stem.split("-", 1)[1]))
    height = int(width * 1920 / 1080)
    font = any_font(22)
    sheet = Image.new("RGB", (width * len(files), height + 30), (25, 25, 25))
    for i, file in enumerate(files):
        sheet.paste(Image.open(file).resize((width, height)), (i * width, 30))
        ImageDraw.Draw(sheet).text((i * width + 6, 3), file.stem.split("-", 1)[1] + " s", fill="white", font=font)
    sheet.save(output, quality=90)
    print(f"{len(files)} stills on {output}")


if __name__ == "__main__":
    main()

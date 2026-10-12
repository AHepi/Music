"""What this does: makes a film's cover picture (the still apps show before it plays) from one
frame: a soft dark wash at the bottom, a small amber kicker line ("CHAPTER 2"), a thin amber rule,
a big title in two or three lines, and a small source line.

Use: python3 -I make_cover.py FRAME.jpg OUTPUT.jpg --kicker "CHAPTER 2" --title "WHAT REALLY|CAUSES INFLATION"
         [--source "Source: Clara E. Mattei, The Capital Order (2022)"] [--top 1385] [--font-folder FOLDER]
  - "|" splits the title into lines; --top is where the kicker sits (pixels from the top of 1920);
  - fonts: Inter 600/800 from the film kit (film/node_modules/@fontsource/inter/files), else DejaVu.
Pick a frame with an empty lower part (a table, a floor, sky) so the title sits on calm ground.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AMBER, PAPER, MUTED = (232, 163, 61), (242, 237, 227), (200, 196, 188)


def font(folder, weight, size):
    for path in (Path(folder) / f"inter-latin-{weight}-normal.woff2" if folder else None,
                 Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
        if path and path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("frame"); parser.add_argument("output")
    parser.add_argument("--kicker", default=""); parser.add_argument("--title", required=True)
    parser.add_argument("--source", default=""); parser.add_argument("--top", type=int, default=1385)
    parser.add_argument("--font-folder", default=str(here.parent / "node_modules/@fontsource/inter/files"))
    a = parser.parse_args()
    picture = Image.open(a.frame).convert("RGB")
    width, height = picture.size
    wash = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(wash)
    start = a.top - 125
    for y in range(height):
        draw.line([(0, y), (width, y)], fill=0 if y < start else min(170, int((y - start) / 260 * 170)))
    picture = Image.composite(Image.new("RGB", (width, height), (8, 10, 12)), picture, wash)
    draw = ImageDraw.Draw(picture)

    def centred(text, typeface, y, colour, spacing=0):
        widths = [draw.textlength(c, font=typeface) for c in text]
        x = (width - sum(widths) - spacing * (len(text) - 1)) / 2
        for c, w in zip(text, widths):
            draw.text((x, y), c, font=typeface, fill=colour)
            x += w + spacing

    big, small, tiny = font(a.font_folder, 800, 104), font(a.font_folder, 600, 38), font(a.font_folder, 500, 28)
    y = a.top
    if a.kicker:
        centred(a.kicker, small, y, AMBER, spacing=8)
        draw.rectangle([(width / 2 - 70, y + 59), (width / 2 + 70, y + 63)], fill=AMBER)
        y += 95
    lines = a.title.split("|")
    for i, line in enumerate(lines):
        centred(line, big, y + i * 116, PAPER)
    if a.source:
        centred(a.source, tiny, y + len(lines) * 116 + 34, MUTED)
    picture.save(a.output, quality=92)
    print(a.output)


main()

# What this does: lays the checkout's pictures out as one phone-size sheet, for judging at a glance against the standard
# the user kept (the notice corner, log 32): each frame 300 pixels wide, about how big the film looks held in a hand,
# side by side and labelled underneath. The first picture is the notice corner's film frame; then the checkout's plate,
# and the film stage's stills of the checkout (the slide's start at the plate spot, the composed frame at its end, and the
# weights check at the end: orange where the plate is shone onto the set, blue where a surface wears its own picture,
# green where the behind picture shows).
#
# Run: python3 -I make_checkout_sheet.py OUT.jpg PICTURE "LABEL" PICTURE "LABEL" ...

import sys

from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
WIDTH = 300                     # each frame, pixels: about a phone held in a hand
HEIGHT = round(WIDTH * 16 / 9)
GAP = 16
LABEL_HEIGHT = 74


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
    out, rest = sys.argv[1], sys.argv[2:]
    pairs = list(zip(rest[0::2], rest[1::2]))
    sheet = Image.new('RGB', (GAP + len(pairs) * (WIDTH + GAP), GAP + HEIGHT + LABEL_HEIGHT + GAP), (24, 24, 26))
    draw = ImageDraw.Draw(sheet)
    font, bold = ImageFont.truetype(FONT, 14), ImageFont.truetype(BOLD, 15)
    for i, (path, label) in enumerate(pairs):
        picture = Image.open(path).convert('RGB')
        # the frame's own shape is 9:16; a picture of another shape (a plate is 1536 x 2730) is fitted to it
        picture = picture.resize((WIDTH, HEIGHT), Image.LANCZOS)
        x = GAP + i * (WIDTH + GAP)
        sheet.paste(picture, (x, GAP))
        title, _, more = label.partition(': ')
        y = GAP + HEIGHT + 6
        draw.text((x, y), title, font=bold, fill=(235, 235, 235))
        for line in wrapped(draw, more, font, WIDTH)[:3]:
            y += 18
            draw.text((x, y), line, font=font, fill=(190, 190, 190))
    sheet.save(out, quality=90)
    print('make_checkout_sheet: wrote', out, sheet.size)


if __name__ == '__main__':
    main()

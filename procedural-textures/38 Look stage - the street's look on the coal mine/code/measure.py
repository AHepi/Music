"""
What this file does:
Reads the reference pictures in style/reference and prints the main colours of each one,
so the style bible can quote real colour values instead of guesses.
It also splits each picture into "warm light" and "cool shadow" shares.

Run it from the kit folder:  python3 style/sample_palette.py
"""

import colorsys
from pathlib import Path

from PIL import Image

REFERENCE_FOLDER = Path(__file__).parent / "reference"
COLOURS_PER_PICTURE = 8


def main_colours(picture, how_many):
    """Return the picture's main colours as (hex, share_of_picture) pairs, biggest share first."""
    small = picture.convert("RGB").resize((200, 356))
    quantised = small.quantize(colors=how_many, method=Image.Quantize.MEDIANCUT)
    palette = quantised.getpalette()[: how_many * 3]
    counts = sorted(quantised.getcolors(), reverse=True)
    total = sum(count for count, _ in counts)
    result = []
    for count, index in counts:
        red, green, blue = palette[index * 3 : index * 3 + 3]
        result.append(("#%02x%02x%02x" % (red, green, blue), count / total))
    return result


def warm_cool_split(picture):
    """Share of pixels that are warm (amber/orange/red hues) versus cool (blue/teal hues)."""
    small = picture.convert("RGB").resize((200, 356))
    warm = cool = grey = 0
    for red, green, blue in small.getdata():
        hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
        if saturation < 0.12:
            grey += 1
        elif hue < 0.17 or hue > 0.9:
            warm += 1
        elif 0.45 < hue < 0.72:
            cool += 1
        else:
            grey += 1
    total = warm + cool + grey
    return warm / total, cool / total, grey / total


def average_brightness(picture):
    grey_picture = picture.convert("L").resize((200, 356))
    values = list(grey_picture.getdata())
    return sum(values) / len(values) / 255


def light_accent_colour(picture):
    """Average colour of the brightest warm pixels: the lamps, brass and lit windows."""
    small = picture.convert("RGB").resize((200, 356))
    warm_bright = []
    for red, green, blue in small.getdata():
        hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
        if lightness > 0.55 and saturation > 0.3 and (hue < 0.17 or hue > 0.9):
            warm_bright.append((red, green, blue))
    if not warm_bright:
        return None, 0
    count = len(warm_bright)
    red = sum(p[0] for p in warm_bright) // count
    green = sum(p[1] for p in warm_bright) // count
    blue = sum(p[2] for p in warm_bright) // count
    return "#%02x%02x%02x" % (red, green, blue), count / (200 * 356)


if __name__ == "__main__":
    for path in sorted(REFERENCE_FOLDER.glob("*.jpg")):
        picture = Image.open(path)
        print(f"\n{path.name}  size {picture.size[0]}x{picture.size[1]}")
        print(f"  average brightness: {average_brightness(picture):.2f} (0 = black, 1 = white)")
        warm, cool, grey = warm_cool_split(picture)
        print(f"  warm {warm:.0%}   cool {cool:.0%}   grey/other {grey:.0%}")
        accent, accent_share = light_accent_colour(picture)
        print(f"  light accent colour: {accent} (covers {accent_share:.1%} of the picture)")
        print("  main colours (share of picture):")
        for hex_value, share in main_colours(picture, COLOURS_PER_PICTURE):
            print(f"    {hex_value}  {share:.0%}")

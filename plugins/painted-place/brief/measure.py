"""
What this file does:
Measures a picture against the look's bands (see "The look.md" beside this file): brightness, the warm and cool shares of
the frame, and how much of the frame the warm light covers. Prints a table and, with --json, writes the
numbers and a verdict per band to a file.

    python3 measure.py PICTURE [PICTURE ...] [--json OUT.json]

Needs Pillow only. A shuffled copy of a reference scores exactly the same as the original (the measures
ignore where things are), so this is a check on colour and light, never on shapes.
"""

import argparse
import colorsys
import json
import sys
from pathlib import Path

from PIL import Image

# the bands hold every reference picture; the desert mine (3 November 2026) widened the top of the warm share and the warm light
BANDS = {
    'brightness': (0.14, 0.35),
    'warm_share': (0.15, 0.36),
    'cool_share': (0.30, 0.60),
    'warm_light_coverage': (0.004, 0.045),
}

SAMPLE_SIZE = (200, 356)  # the picture is shrunk to this many dots before measuring


def _pixels(picture):
    small = picture.convert('RGB').resize(SAMPLE_SIZE)
    if hasattr(small, 'get_flattened_data'):
        return list(small.get_flattened_data())
    return list(small.getdata())


def measure(picture):
    """Return the four measures of one picture as a dictionary of numbers between 0 and 1."""
    pixels = _pixels(picture)
    total = len(pixels)
    warm = cool = bright_warm = 0
    brightness_sum = 0.0
    for red, green, blue in pixels:
        hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
        brightness_sum += (0.299 * red + 0.587 * green + 0.114 * blue) / 255
        is_warm_hue = hue < 0.17 or hue > 0.9
        if saturation >= 0.12:
            if is_warm_hue:
                warm += 1
            elif 0.45 < hue < 0.72:
                cool += 1
        if lightness > 0.55 and saturation > 0.3 and is_warm_hue:
            bright_warm += 1
    return {
        'brightness': brightness_sum / total,
        'warm_share': warm / total,
        'cool_share': cool / total,
        'warm_light_coverage': bright_warm / total,
    }


def verdicts(numbers):
    """For each measure: 'inside', 'low' or 'high' against the band."""
    result = {}
    for name, (low, high) in BANDS.items():
        value = numbers[name]
        result[name] = 'inside' if low <= value <= high else ('low' if value < low else 'high')
    return result


def dial_for(name, verdict):
    """What usually moves a measure back into its band, in your own scene's terms (the camera's exposure, your lights,
    your sky)."""
    if verdict == 'inside':
        return ''
    advice = {
        ('brightness', 'low'): 'raise the exposure (scene.view_settings.exposure, try +0.4) or strengthen your lamps',
        ('brightness', 'high'): 'lower the exposure (scene.view_settings.exposure, try -0.4)',
        ('warm_share', 'low'): 'more warm light: stronger lamps and lit windows, or more of them in the frame',
        ('warm_share', 'high'): 'less warm light: weaker lamps or fewer lit windows',
        ('cool_share', 'low'): 'the blue is drowned: weaker or fewer warm lights, or more blue from the sky and its fill light',
        ('cool_share', 'high'): 'the picture is all blue: more warm lights in the frame, or a higher exposure',
        ('warm_light_coverage', 'low'): 'the lamps light nothing: lamps nearer the camera or brighter, or a higher exposure',
        ('warm_light_coverage', 'high'): 'blown-out pools of light: weaker lamps, or a lower exposure',
    }
    return advice.get((name, verdict), '')


def main(argv):
    parser = argparse.ArgumentParser(description='Measure pictures against the look\'s bands.')
    parser.add_argument('pictures', nargs='+')
    parser.add_argument('--json', help='write the numbers and verdicts here')
    args = parser.parse_args(argv)
    report = {}
    print(f"{'picture':44s} {'bright':>7s} {'warm':>6s} {'cool':>6s} {'light':>7s}   verdict")
    for path in args.pictures:
        numbers = measure(Image.open(path))
        judged = verdicts(numbers)
        outside = [f"{name} {verdict}" for name, verdict in judged.items() if verdict != 'inside']
        print(f"{Path(path).name[:44]:44s} {numbers['brightness']:7.2f} {numbers['warm_share']:6.0%} "
              f"{numbers['cool_share']:6.0%} {numbers['warm_light_coverage']:7.1%}   {'inside every band' if not outside else '; '.join(outside)}")
        for name, verdict in judged.items():
            dial = dial_for(name, verdict)
            if dial:
                print(f"    {name}: {dial}")
        report[path] = {'numbers': numbers, 'verdicts': judged,
                        'dials': {n: dial_for(n, v) for n, v in judged.items() if v != 'inside'}}
    if args.json:
        Path(args.json).write_text(json.dumps({'bands': BANDS, 'pictures': report}, indent=2))
        print(f"written {args.json}")


if __name__ == '__main__':
    main(sys.argv[1:])

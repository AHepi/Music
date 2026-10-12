# What this does: calms the colour of a cut-out piece so it sits with the others. It scales the colour
# strength (saturation), softens the contrast a little and lifts the darkest shadows, keeping the
# piece's see-through edge exactly as it was. Use it when one painted figure looks louder than the
# rest (chapter 2: the politician's face was about 1.7 times as colourful as the other people).
#
# Use: python3 -I tone_piece.py IN.png OUT.png [--saturation 0.62] [--contrast 0.9] [--lift 0.03]
#      python3 -I tone_piece.py --measure A.png B.png ...   prints each piece's average colour
#                                                           strength and brightness (0-255)
# A piece made of several layers (a face, a jaw and a mouth that move) must get the same settings on
# every layer so they still match.

import sys
from PIL import Image, ImageStat, ImageEnhance


def measure(path):
    picture = Image.open(path).convert('RGBA')
    solid = picture.split()[3].point(lambda v: 255 if v > 200 else 0)
    hue_saturation_value = picture.convert('RGB').convert('HSV')
    stats = ImageStat.Stat(hue_saturation_value, mask=solid)
    return round(stats.mean[1]), round(stats.mean[2])


def tone(in_path, out_path, saturation=0.62, contrast=0.9, lift=0.03):
    picture = Image.open(in_path).convert('RGBA')
    see_through = picture.split()[3]
    colour = picture.convert('RGB')
    colour = ImageEnhance.Color(colour).enhance(saturation)
    colour = ImageEnhance.Contrast(colour).enhance(contrast)
    # lift the shadows: out = lift + (1 - lift) * in
    colour = colour.point(lambda v: round(255 * lift + (1 - lift) * v))
    colour.putalpha(see_through)
    colour.save(out_path)


if __name__ == '__main__':
    arguments = sys.argv[1:]
    if arguments and arguments[0] == '--measure':
        for path in arguments[1:]:
            strength, brightness = measure(path)
            print(f'{path}: colour strength {strength}, brightness {brightness}')
        sys.exit(0)
    if len(arguments) < 2:
        print(__doc__ if __doc__ else 'Use: tone_piece.py IN.png OUT.png [--saturation 0.62] [--contrast 0.9] [--lift 0.03]')
        sys.exit(1)
    settings = {'saturation': 0.62, 'contrast': 0.9, 'lift': 0.03}
    rest = arguments[2:]
    for i in range(0, len(rest) - 1, 2):
        settings[rest[i].lstrip('-')] = float(rest[i + 1])
    tone(arguments[0], arguments[1], **settings)
    print(f'{arguments[1]}: colour strength and brightness now {measure(arguments[1])}')

# What this does: paints the pictures that chapter 2's checkout wears ("34 Plan - chapter 2 full redesign", part 1
# "B. The checkout"), with Pillow and numpy (no Blender needed), into the checkout's textures folder:
#   bill.png                 the newspaper bill: an invented paper's name, THE EVENING LAMP, in a dark band at the top, then
#                            NEW MONEY: / PRICES WILL / GO UP in big black poster letters (about 0.1 m tall) on newsprint
#   bread-bag.png            a white paper bread bag printed BREAD in brown, between two thin brown bands
#   milk-label.png           the sleeve round a plastic milk bottle: MILK in dark slate on white, a grey band above and below
#   butter-wrapper.png       a parchment butter wrapper printed BUTTER in dark brown, a border round it
#   cheese-label.png         the cream label on a block of cheese in clear film: CHEESE in dark brown
#   checkout-sign.png        the hanging sign: CHECKOUT in white on dark charcoal grey (no lane number)
#   petrol-fascia.png        the petrol station canopy's fascia across the road: PETROL · DIESEL in white on mid grey
#                            (no brand, no prices)
#   belt-rubber.jpg          the checkout belt: black rubber with fine ribs along its length, worn shiny in the middle
#   counter-laminate.jpg     the counter's front panels: warm light grey laminate with a faint speckle
#   bag-canvas.jpg           the reusable bags: a plain grey-brown woven cloth, no print
#   newsprint.jpg            the folded papers in the bill stand's tray: grey newsprint with columns of print too small
#                            to read (bars, no letters)
#   packs.jpg                shop goods seen from afar (the aisles' ends): pack fronts in muted colours, bars for print
# and lettering-sizes.json: for each lettered picture, its words, the font, its size in metres and where its capitals'
# ink starts and ends (fractions of the picture from its top left), so assemble_checkout.py can give letter heights
# measured from the pictures rather than typed in.
#
# The lettering rules (plan 34, part 1): real lettering, whole words, no figure (digit) anywhere, no logos, brands or
# chain colours (no supermarket green, red or yellow), no large flat areas of a party's colour: greys, white, cream,
# brown. The newspaper's name is invented and was searched first (round 5 of log 34): no New Zealand paper or business
# called "The Evening Lamp" was found; it avoids every real paper's word the plan lists (Herald, Times, Post, Press, Star).
# NAME below changes it in one place.
#
# Fonts (see fonts/00 Fonts - where to get them.md): Anton (the bill's words), Oswald (the grocery labels), Inter
# (CHECKOUT, PETROL · DIESEL) and Liberation Serif Bold (the paper's name, BREAD).
#
# Run: python3 -I paint_checkout_pictures.py OUT_FOLDER --fonts FONT_FOLDER
#      (OUT_FOLDER is normally assets/models/inflation-chapter-2-newcomers/checkout/textures; build_checkout.sh runs it)

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NAME = 'THE EVENING LAMP'                                 # the invented newspaper (searched: see above)
BILL_LINES = ('NEW MONEY:', 'PRICES WILL', 'GO UP')       # plan 34: "NEW MONEY: PRICES WILL GO UP"
BILL_SIZE = (0.62, 0.72)                                  # metres, width and height
BILL_CAPS = 0.10                                          # the big words' capital height, metres (about 56 pixels on the
                                                          # film's frame at the composed spot, 2.95 m away)
PIXELS_PER_METRE = {'bill': 1800, 'label': 3000, 'sign': 1000, 'fascia': 220}
SYSTEM_FONTS = {'Inter Display Black': '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf',
                'Inter Bold': '/usr/share/fonts/opentype/inter/Inter-Bold.otf',
                'Liberation Serif Bold': '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'}

LETTERING = {}


# ------------------------------------------------------------------------------------------------- helpers

def noise(height, width, seed, smoothness=2.2, smallest=2.0):
    """Cloudy noise between 0 and 1 (the same as the pit village painter's)."""
    rng = np.random.default_rng(seed)
    spectrum = np.fft.fft2(rng.standard_normal((height, width)))
    fy = np.fft.fftfreq(height)[:, None] * height
    fx = np.fft.fftfreq(width)[None, :] * width
    radius = np.sqrt(fx * fx + fy * fy)
    radius[0, 0] = 1
    spectrum *= 1 / radius ** (smoothness / 2)
    spectrum[radius < smallest] *= 0.3
    field = np.real(np.fft.ifft2(spectrum))
    field -= field.min()
    return field / field.max()


def font(fonts, name, size):
    """A font by its name: a system font (SYSTEM_FONTS) or a file in the fonts folder. Oswald is a variable font: Bold."""
    if name in SYSTEM_FONTS:
        return ImageFont.truetype(SYSTEM_FONTS[name], size)
    if name == 'Oswald Bold':
        typeface = ImageFont.truetype(os.path.join(fonts, 'Oswald[wght].ttf'), size)
        typeface.set_variation_by_name('Bold')
        return typeface
    if name == 'Oswald SemiBold':
        typeface = ImageFont.truetype(os.path.join(fonts, 'Oswald[wght].ttf'), size)
        typeface.set_variation_by_name('SemiBold')
        return typeface
    return ImageFont.truetype(os.path.join(fonts, {'Anton': 'Anton-Regular.ttf'}[name]), size)


def cap_height(typeface):
    """The height of a capital H in pixels at this font's size, and how far below the drawing point its top is."""
    left, top, right, bottom = typeface.getbbox('H')
    return bottom - top, top


def font_for_caps(fonts, name, caps_pixels):
    """The font whose capitals are caps_pixels tall."""
    probe = font(fonts, name, 1000)
    height, _ = cap_height(probe)
    return font(fonts, name, max(6, int(round(1000 * caps_pixels / height))))


def write_line(draw, mask, text, typeface, centre_x, caps_top, fill, spacing=0.0, squeeze=1.0, picture=None):
    """Writes one line with its capitals' tops at caps_top, centred on centre_x, into the picture (fill) and into the
    lettering mask. squeeze < 1 narrows the letters (drawn wide, then scaled across). Returns the ink's box."""
    height, top_offset = cap_height(typeface)
    advances = [typeface.getlength(c) + spacing * height for c in text]
    width = sum(advances) - spacing * height
    canvas = Image.new('L', (int(math.ceil(width)) + 8, int(typeface.size * 1.4)), 0)
    pen = ImageDraw.Draw(canvas)
    x = 4.0
    for letter, advance in zip(text, advances):
        pen.text((x, 0), letter, font=typeface, fill=255)
        x += advance
    if squeeze != 1.0:
        canvas = canvas.resize((max(1, int(round(canvas.width * squeeze))), canvas.height), Image.LANCZOS)
    left = int(round(centre_x - canvas.width / 2))
    top = int(round(caps_top - top_offset))
    ink = Image.new('L', mask.size, 0)
    ink.paste(canvas, (left, top))
    mask.paste(Image.composite(Image.new('L', mask.size, 255), mask, ink))
    if picture is not None:
        picture.paste(Image.new('RGB', picture.size, fill), (0, 0), ink)
    box = ink.getbbox()
    return box


def ink_box(mask):
    """Where a lettering mask has ink: (left, top, right, bottom) as fractions of the picture."""
    array = np.asarray(mask, np.float32) / 255
    rows = np.nonzero(array.max(axis=1) > 0.5)[0]
    columns = np.nonzero(array.max(axis=0) > 0.5)[0]
    height, width = array.shape
    return [round(columns[0] / width, 4), round(rows[0] / height, 4), round((columns[-1] + 1) / width, 4), round((rows[-1] + 1) / height, 4)]


def record(file_name, words, font_name, size_metres, mask, lines=None):
    """Notes a lettered picture's words, font, size and where its ink is (lettering-sizes.json)."""
    entry = {'words': words, 'font': font_name, 'size_metres': [round(v, 4) for v in size_metres], 'ink_box': ink_box(mask)}
    if lines:
        entry['lines'] = lines
    LETTERING[file_name] = entry


def paper(width, height, base, seed, grain=0.035, blotch=0.04):
    """A sheet of paper: a base colour with fine grain and soft blotches."""
    fine = noise(height, width, seed, 1.0, 1)
    soft = noise(height, width, seed + 1, 2.6, 2)
    array = np.ones((height, width, 3), np.float32) * np.array(base, np.float32)[None, None, :] / 255
    array *= (1 - grain / 2 + grain * fine)[..., None]
    array *= (1 - blotch / 2 + blotch * soft)[..., None]
    return array


def to_picture(array):
    return Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8))


def printed(picture, mask, colour, spread=0.6, seed=0, wear=0.0):
    """Ink on paper: the mask softened a touch (ink spreads into newsprint), a little uneven, laid over the picture."""
    soft = mask.filter(ImageFilter.GaussianBlur(spread))
    coverage = np.asarray(soft, np.float32)[..., None] / 255
    if wear:
        uneven = noise(mask.height, mask.width, seed, 1.2, 1)[..., None]
        coverage = coverage * (1 - wear * np.clip(uneven - 0.55, 0, 1) * 2)
    base = np.asarray(picture, np.float32) / 255
    ink = np.array(colour, np.float32)[None, None, :] / 255
    return to_picture(base * (1 - coverage) + ink * base ** 0.15 * coverage)


# ------------------------------------------------------------------------------------------------- the pictures

def bill(folder, fonts):
    """The newspaper bill, with the paper's name in a dark band at the top and the three lines of big words."""
    ppm = PIXELS_PER_METRE['bill']
    width, height = int(BILL_SIZE[0] * ppm), int(BILL_SIZE[1] * ppm)
    picture = to_picture(paper(width, height, (236, 233, 224), seed=11, grain=0.05, blotch=0.06))
    draw = ImageDraw.Draw(picture)
    # the paper's name: white serif capitals in a near-black band, with a thin rule under the band
    band_top, band_bottom = int(0.02 * ppm), int(0.112 * ppm)
    # the band a dark cool charcoal (a near-black slate, no party's colour), the rule under it the same
    draw.rectangle((int(0.02 * ppm), band_top, width - int(0.02 * ppm), band_bottom), fill=(30, 33, 40))
    draw.rectangle((int(0.02 * ppm), band_bottom + int(0.008 * ppm), width - int(0.02 * ppm), band_bottom + int(0.011 * ppm)), fill=(30, 33, 40))
    name_mask = Image.new('L', (width, height), 0)
    name_font = font_for_caps(fonts, 'Liberation Serif Bold', 0.036 * ppm)
    while name_font.getlength(NAME) * 1.1 > width - 0.08 * ppm:
        name_font = font(fonts, 'Liberation Serif Bold', name_font.size - 2)
    name_caps, _ = cap_height(name_font)
    write_line(draw, name_mask, NAME, name_font, width / 2, (band_top + band_bottom) / 2 - name_caps / 2, (238, 234, 222),
               spacing=0.08, picture=picture)
    # the big words: Anton, black, centred, each line's capitals BILL_CAPS tall
    words_mask = Image.new('L', (width, height), 0)
    big = font_for_caps(fonts, 'Anton', BILL_CAPS * ppm)
    lines = []
    pitch = 0.135
    for i, line in enumerate(BILL_LINES):
        caps_top = (0.16 + i * pitch) * ppm
        box = write_line(draw, words_mask, line, big, width / 2, caps_top, (0, 0, 0))
        lines.append({'text': line, 'caps_top_metres': round(caps_top / ppm, 4), 'caps_bottom_metres': round((caps_top + BILL_CAPS * ppm) / ppm, 4),
                      'width_metres': round((box[2] - box[0]) / ppm, 4)})
        if box[0] < 0.015 * ppm or box[2] > width - 0.015 * ppm:
            raise SystemExit(f'paint_checkout_pictures: the bill line "{line}" is wider than the bill')
    picture = printed(picture, words_mask, (16, 15, 15), spread=0.9, seed=12, wear=0.25)
    # a soft fold across the middle and a little dirt toward the bottom, as a bill that has been handled
    array = np.asarray(picture, np.float32) / 255
    rows = np.arange(height)[:, None]
    fold = np.exp(-((rows - 0.58 * height) ** 2) / (2 * (0.004 * ppm) ** 2)) * 0.06
    dirt = (rows / height) ** 3 * 0.08 * noise(height, width, 13, 2.4, 2)
    array = array * (1 - fold - dirt)[..., None]
    picture = to_picture(array)
    picture.save(os.path.join(folder, 'bill.png'))
    record('bill.png', f'{NAME} / ' + ' / '.join(BILL_LINES), 'Anton (the words), Liberation Serif Bold (the name)', BILL_SIZE, words_mask,
           lines=lines + [{'text': NAME, 'caps_metres': round(name_caps / ppm, 4)}])
    return picture


def label(folder, fonts, file_name, size_metres, background, words, ink, font_name, caps_metres, bands=None, border=None, seed=0,
          squeeze=1.0, spacing=0.04, grain=0.03, word_at=0.5):
    """A printed label or wrapper: one word, centred across, its middle word_at of the way down (0.5: the middle), on a
    plain background with bands or a border."""
    ppm = PIXELS_PER_METRE['label']
    width, height = int(size_metres[0] * ppm), int(size_metres[1] * ppm)
    picture = to_picture(paper(width, height, background, seed, grain=grain, blotch=0.03))
    draw = ImageDraw.Draw(picture)
    for top, bottom, colour in bands or []:
        draw.rectangle((0, int(top * height), width, int(bottom * height)), fill=colour)
    if border:
        inset, thickness, colour = border
        for k in range(int(thickness * ppm)):
            draw.rectangle((int(inset * ppm) + k, int(inset * ppm) + k, width - int(inset * ppm) - k, height - int(inset * ppm) - k), outline=colour)
    # the word's capitals caps_metres tall, or smaller if the word would not fit inside 86% of the label's width
    while True:
        mask = Image.new('L', (width, height), 0)
        typeface = font_for_caps(fonts, font_name, caps_metres * ppm)
        box = write_line(draw, mask, words, typeface, width / 2, height * word_at - caps_metres * ppm / 2, ink, spacing=spacing, squeeze=squeeze)
        if box[2] - box[0] <= 0.86 * width or caps_metres < 0.01:
            break
        caps_metres *= 0.94
    picture = printed(picture, mask, ink, spread=0.5, seed=seed + 1, wear=0.1)
    picture.save(os.path.join(folder, file_name))
    record(file_name, words, font_name, size_metres, mask)


def sign(folder, fonts, file_name, size_metres, background, words, ink, font_name, caps_metres, ppm, seed=0, spacing=0.08, frame=None):
    """A painted sign panel: words in one colour on a plain painted ground, a little uneven."""
    width, height = int(size_metres[0] * ppm), int(size_metres[1] * ppm)
    ground = paper(width, height, background, seed, grain=0.025, blotch=0.05)
    picture = to_picture(ground)
    draw = ImageDraw.Draw(picture)
    if frame:
        thickness, colour = frame
        for k in range(max(1, int(thickness * ppm))):
            draw.rectangle((k, k, width - 1 - k, height - 1 - k), outline=colour)
    mask = Image.new('L', (width, height), 0)
    typeface = font_for_caps(fonts, font_name, caps_metres * ppm)
    write_line(draw, mask, words, typeface, width / 2, height / 2 - caps_metres * ppm / 2, ink, spacing=spacing)
    picture = printed(picture, mask, ink, spread=0.4, seed=seed + 1)
    picture.save(os.path.join(folder, file_name))
    record(file_name, words, font_name, size_metres, mask)


def belt_rubber(folder):
    """Black rubber with fine ribs along the belt (the picture's up), worn a little smoother and shinier in the middle."""
    width, height = 512, 1024        # 0.5 m across, 1 m along
    across = np.arange(width)[None, :]
    ribs = 0.5 + 0.5 * np.cos(across / width * 0.5 / 0.004 * 2 * math.pi)     # a rib every 4 mm
    wear = np.exp(-((across - width / 2) ** 2) / (2 * (width * 0.22) ** 2))
    grime = noise(height, width, 31, 2.0, 2)
    value = 0.18 + 0.03 * ribs * (1 - 0.6 * wear) + 0.04 * grime     # dark grey rubber, worn (black rubber reads dark grey under light)
    array = np.repeat(value[..., None], 3, axis=2) * np.array([1.0, 1.0, 1.04])
    to_picture(array).save(os.path.join(folder, 'belt-rubber.jpg'), quality=92)


def counter_laminate(folder):
    width = height = 1024            # 1 m square
    speck = (noise(height, width, 41, 0.4, 1) > 0.78).astype(np.float32) * 0.05
    cloud = noise(height, width, 42, 2.4, 2)
    array = np.ones((height, width, 3), np.float32) * np.array([0.56, 0.55, 0.53])
    array *= (0.95 + 0.07 * cloud - speck)[..., None]
    to_picture(array).save(os.path.join(folder, 'counter-laminate.jpg'), quality=92)


def bag_canvas(folder):
    width = height = 512             # 0.25 m square: a thread about 0.8 mm
    x = np.arange(width)[None, :]
    y = np.arange(height)[:, None]
    weave = 0.5 + 0.25 * np.sin(x / 1.6 * math.pi) * np.sign(np.sin(y / 1.6 * math.pi)) + 0.25 * np.sin(y / 1.6 * math.pi)
    cloud = noise(height, width, 51, 2.2, 2)
    value = 0.60 + 0.07 * weave + 0.06 * cloud
    array = np.repeat(value[..., None], 3, axis=2) * np.array([1.0, 0.98, 0.93])
    to_picture(array).save(os.path.join(folder, 'bag-canvas.jpg'), quality=92)


def newsprint(folder):
    """A folded paper's front: grey newsprint with columns of print as fine grey bars (too small to read: no letters)."""
    width, height = 600, 400         # 0.3 x 0.2 m
    array = paper(width, height, (214, 211, 202), 61, grain=0.06, blotch=0.06)
    picture = to_picture(array)
    draw = ImageDraw.Draw(picture)
    rng = np.random.default_rng(62)
    draw.rectangle((16, 14, width - 16, 52), fill=(40, 40, 42))          # the paper's name band, as on the bill (no letters at this size)
    draw.rectangle((16, 66, width - 16, 104), fill=(70, 70, 72))         # a headline, as a dark bar
    for column in range(4):
        left = 16 + column * (width - 32) / 4
        for row in range(int((height - 130) / 9)):
            length = (width - 32) / 4 - 14 - (rng.random() * 30 if rng.random() < 0.2 else 0)
            draw.rectangle((left, 120 + row * 9, left + length, 120 + row * 9 + 3), fill=(120, 119, 116))
    picture.filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(folder, 'newsprint.jpg'), quality=90)


def packs(folder):
    """Shop goods seen from afar, for the packs on the aisles' ends: a grid of pack fronts, each a muted colour with a pale
    panel and a few dark bars where print would be (too small to read: no letters, no brands), 0.6 m square."""
    width = height = 600
    rng = np.random.default_rng(91)
    picture = Image.new('RGB', (width, height), (120, 116, 110))
    draw = ImageDraw.Draw(picture)
    colours = [(132, 120, 104), (96, 104, 112), (150, 142, 128), (88, 80, 74), (120, 112, 96), (104, 96, 90), (140, 134, 126)]
    x = 0
    while x < width:
        w = int(rng.integers(40, 90))
        y = 0
        while y < height:
            h = int(rng.integers(60, 130))
            base = colours[int(rng.integers(0, len(colours)))]
            draw.rectangle((x + 1, y + 1, x + w - 2, y + h - 2), fill=base)
            draw.rectangle((x + 6, y + int(h * 0.25), x + w - 7, y + int(h * 0.6)), fill=tuple(min(255, c + 70) for c in base))
            for k in range(int(rng.integers(1, 4))):
                bar_y = y + int(h * 0.3) + k * 7
                draw.rectangle((x + 10, bar_y, x + 10 + int((w - 22) * rng.uniform(0.4, 1.0)), bar_y + 3), fill=tuple(max(0, c - 60) for c in base))
            y += h
        x += w
    picture.filter(ImageFilter.GaussianBlur(0.7)).save(os.path.join(folder, 'packs.jpg'), quality=90)


def main():
    arguments = sys.argv[1:]
    if not arguments:
        raise SystemExit('Use: python3 -I paint_checkout_pictures.py OUT_FOLDER --fonts FONT_FOLDER')
    folder = os.path.abspath(arguments[0])
    fonts = arguments[arguments.index('--fonts') + 1] if '--fonts' in arguments else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
    os.makedirs(folder, exist_ok=True)
    bill(folder, fonts)
    # groceries (no sizes, no prices, no brands): plain wrappers in neutral colours, the word in a dark ink
    # BREAD near the top of the bag's front, so it shows above the basket's rim when the loaf stands in the basket
    label(folder, fonts, 'bread-bag.png', (0.13, 0.33), (238, 235, 226), 'BREAD', (96, 62, 38), 'Liberation Serif Bold', 0.036,
          bands=[(0.03, 0.04, (150, 112, 78)), (0.17, 0.18, (150, 112, 78))], seed=71, spacing=0.06, word_at=0.105)
    label(folder, fonts, 'milk-label.png', (0.44, 0.09), (244, 244, 241), 'MILK', (52, 58, 70), 'Oswald Bold', 0.036,
          bands=[(0.0, 0.12, (128, 132, 138)), (0.88, 1.0, (128, 132, 138))], seed=72, spacing=0.08, grain=0.015)
    label(folder, fonts, 'butter-wrapper.png', (0.13, 0.058), (232, 224, 198), 'BUTTER', (92, 58, 32), 'Oswald Bold', 0.024,
          border=(0.004, 0.0012, (150, 112, 70)), seed=73, spacing=0.06)
    label(folder, fonts, 'cheese-label.png', (0.12, 0.052), (236, 230, 212), 'CHEESE', (74, 50, 34), 'Oswald Bold', 0.024,
          border=(0.003, 0.001, (120, 96, 70)), seed=74, spacing=0.06)
    sign(folder, fonts, 'checkout-sign.png', (1.10, 0.26), (52, 54, 57), 'CHECKOUT', (226, 226, 222), 'Inter Bold', 0.11, PIXELS_PER_METRE['sign'],
         seed=81, frame=(0.012, (88, 90, 94)))
    sign(folder, fonts, 'petrol-fascia.png', (9.0, 0.9), (128, 130, 132), 'PETROL · DIESEL', (240, 240, 236), 'Inter Bold', 0.42,
         PIXELS_PER_METRE['fascia'], seed=82, spacing=0.1)
    belt_rubber(folder)
    counter_laminate(folder)
    bag_canvas(folder)
    newsprint(folder)
    packs(folder)
    for file_name, entry in LETTERING.items():
        if any(c.isdigit() for c in entry['words']):
            raise SystemExit(f'paint_checkout_pictures: {file_name} carries a figure ({entry["words"]}): the plan allows none here')
    with open(os.path.join(folder, 'lettering-sizes.json'), 'w') as handle:
        json.dump({'about': 'What this file is: the checkout\'s lettered pictures (paint_checkout_pictures.py): each one\'s words, font, size in '
                            'metres and where its ink is (left, top, right, bottom, as fractions of the picture from its top left).',
                   'pictures': LETTERING}, handle, indent=1)
    print('paint_checkout_pictures: wrote', ', '.join(sorted(os.listdir(folder))))


if __name__ == '__main__':
    main()

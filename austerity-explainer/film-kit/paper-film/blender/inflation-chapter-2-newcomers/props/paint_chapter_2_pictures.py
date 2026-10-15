# What this does: paints the pictures that chapter 2's scripted props wear, with Pillow and numpy (no
# Blender needed), for build_chapter_2_props.py. So far the Works' ("34 Plan - chapter 2 full
# redesign", part 1 A and part 3):
#   gate-board-no-1.jpg, gate-board-no-2.jpg   "No. 1" / "No. 2" in cream sign-writer's lettering on
#                                               near-black paint over planks, lightly weathered
#   bank-sign.jpg                               "BANK" in gilt on near-black, for the hanging sign
#   brass-plate.jpg                             "BANK" engraved and blacked in on a brushed brass plate
#   drum-stencil-petrol.png, drum-stencil-diesel.png
#                                               off-white stencilled "PETROL" / "DIESEL" (see-through
#                                               round the letters), laid round a steel drum
#   crate-stencil.png                           black stencilled "THIS WAY UP" under two arrows
#   wages-envelope-front.jpg, wages-envelope-back.jpg
#                                               a brown pay envelope printed "WAGES", and its flap side
# The lettering rules (plan, part 1): real lettering on every sign, no figure (digit) except "No. 1" and
# "No. 2", no logos, brands, flags, or party, chain or bank colours (the bank's sign is plain gilt on
# near-black).
#
# It uses the pit village painter's helpers (paint_prop_pictures.py: noise, fonts, centred lines,
# Poly Haven surfaces) and the same free fonts, which are not kept in the repository (see
# pit-village/props/fonts/00 Fonts - where to get them.md); the stencils use DejaVu Sans Bold.
#
# Run: python3 -I paint_chapter_2_pictures.py PICTURE_FOLDER --downloads DOWNLOAD_FOLDER --fonts FONT_FOLDER
#      (DOWNLOAD_FOLDER holds surfaces/weathered_planks from download_poly_haven.py --choices chapter_2_choices.py)

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'pit-village', 'props'))
import paint_prop_pictures as painter  # noqa: E402
from paint_prop_pictures import as_array, as_picture, centred_text, fitted_font, noise, surface  # noqa: E402

CREAM = (228, 216, 180)
NEAR_BLACK = (24, 23, 21)


def blurred(mask_array, radius):
    """A 0..1 array softened by a Gaussian blur of `radius` pixels."""
    picture = Image.fromarray((np.clip(mask_array, 0, 1) * 255).astype(np.uint8))
    return np.asarray(picture.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255


def weather_paint(paint, wood, planks, seed, chip_threshold=0.70, dirt_strength=0.35):
    """The weather on a painted board: paint chipped off to the timber (more along the plank joints),
    dark joints between planks, a little fading, dirt and rain runs from the bottom, and soot speckle.
    paint and wood are float arrays (height, width, 3)."""
    height, width = paint.shape[:2]
    seam = np.zeros((height, width), np.float32)
    for index in range(1, planks):
        y = int(height * index / planks)
        seam[max(0, y - 4):y + 4, :] = 1
    seam = blurred(seam, 2.5)
    coarse = noise(height, width, seed, 2.0, 3)
    fine = noise(height, width, seed + 1, 1.0, 1)
    chipped = ((coarse * 0.65 + fine * 0.35) > chip_threshold).astype(np.float32)
    edge_wear = np.zeros((height, width), np.float32)
    for index in range(0, planks + 1):
        y = int(height * index / planks)
        edge_wear += np.exp(-((np.arange(height) - y) ** 2) / (2 * 10 ** 2))[:, None]
    chipped = np.clip(chipped + ((fine > 0.62) * edge_wear * 0.8), 0, 1)
    chipped = blurred(chipped, 1.0)[..., None]
    out = paint * (1 - chipped) + wood * chipped
    fade = noise(height, width, seed + 2, 2.6, 2)[..., None]
    out = out * (0.9 + 0.1 * fade) + np.array([0.5, 0.48, 0.44]) * 0.06 * (1 - np.linspace(0, 1, height)[:, None, None])
    runs = noise(height, width // 4, seed + 3, 1.4, 1)
    streak = np.asarray(Image.fromarray((runs[:max(2, height // 16)] * 255).astype(np.uint8)).resize((width, height), Image.BICUBIC), np.float32) / 255
    dirt = np.clip((np.linspace(0, 1, height)[:, None] ** 2) * 0.5 + streak * 0.2, 0, 1)[..., None]
    out = out * (1 - dirt * dirt_strength) + np.array([0.1, 0.09, 0.08]) * dirt * dirt_strength
    out = out * (1 - seam[..., None] * 0.75)
    speck = (noise(height, width, seed + 4, 0.6, 1) > 0.8)[..., None]
    return out * (1 - speck * 0.2)


# ------------------------------------------------------------------------------ the gate boards

def gate_board(folder, words, file_name, seed, width=2048, height=878, planks=4):
    """A works' gate board (1.4 x 0.6 m): cream sign-writer's lettering with a dark drop shade, inside a
    cream lined border, on near-black paint over four planks."""
    wood = as_array(surface('weathered_planks', (width, height)))
    wood = wood * 0.5 + np.array([0.30, 0.28, 0.25]) * 0.5
    paint = Image.new('RGB', (width, height), NEAR_BLACK)
    draw = ImageDraw.Draw(paint)
    inset = 44
    draw.rounded_rectangle((inset, inset, width - inset, height - inset), radius=40, outline=CREAM, width=12)
    draw.rounded_rectangle((inset + 24, inset + 24, width - inset - 24, height - inset - 24), radius=26, outline=(150, 140, 112), width=3)
    typeface = fitted_font('Ultra-Regular.ttf', 560, words, width * 0.74, spacing=14)
    top, bottom = typeface.getbbox('No')[1], typeface.getbbox('No')[3]
    y = (height - (bottom - top)) / 2 - top - 6
    centred_text(draw, y, words, typeface, CREAM, width, shadow=(74, 62, 44), shadow_offset=(12, 14), spacing=14)
    out = weather_paint(as_array(paint), wood, planks, seed, chip_threshold=0.72)
    as_picture(out).save(os.path.join(folder, file_name), quality=92)
    print('painted', file_name, f'(letters {bottom - top} of {height} pixels high)')


# -------------------------------------------------------------------------------------- the bank

def bank_sign(folder, width=2048, height=1024):
    """The bank's hanging sign (1.2 x 0.6 m, both faces): "BANK" in gilt with a dark shade and a gilt
    lined border with small corner diamonds, on near-black; kept well, so only lightly weathered."""
    ground = np.ones((height, width, 3), np.float32) * np.array([0.10, 0.09, 0.085])
    ground = ground * (0.92 + 0.08 * noise(height, width, 61, 2.2, 2)[..., None])
    gilt = Image.new('L', (width, height), 0)
    shade = Image.new('L', (width, height), 0)
    draw_gilt, draw_shade = ImageDraw.Draw(gilt), ImageDraw.Draw(shade)
    inset = 54
    draw_gilt.rectangle((inset, inset, width - inset, height - inset), outline=255, width=10)
    draw_gilt.rectangle((inset + 26, inset + 26, width - inset - 26, height - inset - 26), outline=255, width=3)
    for corner_x, corner_y in ((inset + 70, inset + 70), (width - inset - 70, inset + 70), (inset + 70, height - inset - 70), (width - inset - 70, height - inset - 70)):
        draw_gilt.polygon([(corner_x, corner_y - 18), (corner_x + 18, corner_y), (corner_x, corner_y + 18), (corner_x - 18, corner_y)], fill=255)
    typeface = fitted_font('AbrilFatface-Regular.ttf', 600, 'BANK', width * 0.70, spacing=30)
    top, bottom = typeface.getbbox('BANK')[1], typeface.getbbox('BANK')[3]
    y = (height - (bottom - top)) / 2 - top
    centred_text(draw_shade, y + 12, 'BANK', typeface, 255, width, spacing=30)
    centred_text(draw_gilt, y, 'BANK', typeface, 255, width, spacing=30)
    gilt_array = np.asarray(gilt, np.float32)[..., None] / 255
    shade_array = blurred(np.asarray(shade, np.float32) / 255, 2)[..., None] * (1 - gilt_array)
    # gold leaf: brighter towards the top of each letter, with a fine burnished sparkle
    rows = np.linspace(0, 1, height)[:, None, None]
    gold = np.array([0.90, 0.72, 0.38]) * (1.05 - 0.35 * rows) * (0.9 + 0.1 * noise(height, width, 62, 0.8, 1)[..., None])
    out = ground * (1 - shade_array * 0.85) + np.array([0.24, 0.15, 0.06]) * shade_array * 0.85
    out = out * (1 - gilt_array) + gold * gilt_array
    dirt = (rows ** 3) * (0.5 + 0.5 * noise(height, width, 63, 1.8, 2)[..., None])
    out = out * (1 - 0.18 * dirt)
    as_picture(out).save(os.path.join(folder, 'bank-sign.jpg'), quality=92)
    print('painted bank-sign.jpg', f'(letters {bottom - top} of {height} pixels high)')


def brass_plate(folder, width=1024, height=455):
    """The bank's brass door plate (0.45 x 0.2 m): brushed brass, polished in the middle and tarnished
    toward the edges, "BANK" engraved and filled with black wax inside an engraved border."""
    rng = np.random.default_rng(71)
    streaks = rng.standard_normal((height, 1)) * 0.5 + rng.standard_normal((height, width)) * 0.15
    streaks = np.asarray(Image.fromarray(((streaks - streaks.min()) / (np.ptp(streaks)) * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(6)), np.float32) / 255
    brass = np.array([0.74, 0.56, 0.28]) * (0.85 + 0.3 * streaks[..., None])
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    middle = np.exp(-(((xs / width - 0.5) * 2.2) ** 2 + ((ys / height - 0.5) * 2.6) ** 2))[..., None]
    brass = brass * (0.78 + 0.32 * middle)
    tarnish = np.clip((1 - middle) * (0.4 + 0.6 * noise(height, width, 72, 1.6, 2)[..., None]), 0, 1)
    brass = brass * (1 - 0.35 * tarnish) + np.array([0.22, 0.20, 0.12]) * 0.35 * tarnish
    engraving = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(engraving)
    draw.rectangle((64, 64, width - 64, height - 64), outline=255, width=5)   # inside the four screws
    typeface = fitted_font('OldStandard-Bold.ttf', 300, 'BANK', width * 0.66, spacing=24)
    top, bottom = typeface.getbbox('BANK')[1], typeface.getbbox('BANK')[3]
    centred_text(draw, (height - (bottom - top)) / 2 - top, 'BANK', typeface, 255, width, spacing=24)
    cut = np.asarray(engraving, np.float32)[..., None] / 255
    # the engraving's lower edge catches the light: a thin bright line just below each cut
    lit_edge = np.clip(np.roll(cut, 2, axis=0) - cut, 0, 1)
    out = brass * (1 - cut) + np.array([0.06, 0.05, 0.04]) * cut
    out = out + lit_edge * 0.18
    as_picture(out).save(os.path.join(folder, 'brass-plate.jpg'), quality=92)
    print('painted brass-plate.jpg', f'(letters {bottom - top} of {height} pixels high)')


# -------------------------------------------------------------------------------------- stencils

# where each letter's stencil bridges go, as fractions of its width: a gap cut through the whole
# letter top to bottom (stem from bowl in P, R, B, D and E; the middle of O, Q and A), as stencil
# letters have so that the middles of closed letters don't fall out of the stencil plate
BRIDGES = {'P': (0.30,), 'R': (0.30,), 'B': (0.30,), 'D': (0.30,), 'E': (0.30,), 'O': (0.5,), 'Q': (0.5,), 'A': (0.5,)}


def stencil_mask(words, size, height_fraction=0.8, squeeze=0.80, spacing=0.10, typeface_file='DejaVuSans-Bold.ttf', widest=0.92):
    """A 0..1 mask of stencilled block capitals filling `size` (width, height): the line is drawn,
    squeezed sideways to look condensed, and cut by stencil bridges; it takes up at most `widest` of
    the width."""
    width, height = size
    letter_height = int(height * height_fraction)
    typeface_path = os.path.join(painter.FONTS, typeface_file)
    if not os.path.exists(typeface_path):   # DejaVu comes with most Linux systems
        typeface_path = os.path.join('/usr/share/fonts/truetype/dejavu', typeface_file)
    typeface = ImageFont.truetype(typeface_path, int(letter_height / 0.73))
    advances = [typeface.getlength(letter) for letter in words]
    gap = spacing * letter_height
    wide_width = int(sum(advances) + gap * (len(words) - 1)) + 40
    wide = Image.new('L', (wide_width, height), 0)
    draw = ImageDraw.Draw(wide)
    cap_top = typeface.getbbox('H')[1]
    y = (height - letter_height) / 2 - cap_top
    x = 20
    bridge_width = max(3, int(letter_height * 0.055))
    for letter, advance in zip(words, advances):
        draw.text((x, y), letter, font=typeface, fill=255)
        box = typeface.getbbox(letter)
        for fraction in BRIDGES.get(letter, ()):
            bridge_x = x + box[0] + (box[2] - box[0]) * fraction
            draw.rectangle((bridge_x - bridge_width / 2, 0, bridge_x + bridge_width / 2, height), fill=0)
        x += advance + gap
    squeezed = wide.resize((max(1, int(wide_width * squeeze)), height), Image.LANCZOS)
    if squeezed.width > width * widest:   # still too wide: shrink the whole line to fit
        scale = width * widest / squeezed.width
        squeezed = squeezed.resize((int(squeezed.width * scale), int(height * scale)), Image.LANCZOS)
    canvas = Image.new('L', (width, height), 0)
    canvas.paste(squeezed, ((width - squeezed.width) // 2, (height - squeezed.height) // 2))
    return np.asarray(canvas, np.float32) / 255


def sprayed(mask, seed, colour, overspray=0.12, wear=0.15):
    """Stencil paint from a mask: soft sprayed edges, a faint overspray haze round the letters, the paint
    worn thin in patches. Returns an RGBA picture (see-through where there is no paint)."""
    height, width = mask.shape
    soft = blurred(mask, 1.6)
    haze = blurred(mask, 9) * overspray * (noise(height, width, seed, 0.5, 1) > 0.55)
    worn = 1 - wear * np.clip((noise(height, width, seed + 1, 1.6, 2) - 0.5) * 3, 0, 1)
    alpha = np.clip(soft * worn + haze, 0, 1)
    rgb = np.ones((height, width, 3), np.float32) * np.array(colour) / 255
    rgb = rgb * (0.92 + 0.08 * noise(height, width, seed + 2, 1.2, 1)[..., None])
    picture = as_picture(rgb).convert('RGBA')
    picture.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
    return picture


def drum_stencil(folder, words, file_name, seed, size=(2048, 668)):
    """Off-white stencilled block capitals for the side of a steel drum: the picture is laid round
    120 degrees of the drum and 0.20 m of its height (see build_chapter_2_props.py); the word takes
    up the middle 90 degrees or less, so its ends don't turn too far away from a camera in front."""
    mask = stencil_mask(words, size, height_fraction=0.66, squeeze=0.74, spacing=0.12, widest=0.75)
    sprayed(mask, seed, (226, 220, 202)).save(os.path.join(folder, file_name))
    print('painted', file_name)


def arrow(draw, centre_x, top, bottom, width, fill):
    """An upward arrow: a shaft and a triangular head."""
    head_bottom = top + (bottom - top) * 0.45
    draw.polygon([(centre_x, top), (centre_x + width / 2, head_bottom), (centre_x - width / 2, head_bottom)], fill=fill)
    draw.rectangle((centre_x - width * 0.17, head_bottom - 2, centre_x + width * 0.17, bottom), fill=fill)


def crate_stencil(folder, size=(1600, 645)):
    """Black stencilled "THIS WAY UP" under two upward arrows, for a packing crate's side (the picture
    covers 0.62 x 0.25 m)."""
    width, height = size
    words_band = int(height * 0.48)
    words = stencil_mask('THIS WAY UP', (width, words_band), height_fraction=0.72, squeeze=0.82, spacing=0.10)
    mask = np.zeros((height, width), np.float32)
    mask[height - words_band - int(height * 0.04):height - int(height * 0.04)] = words
    arrows = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(arrows)
    for centre_x in (width * 0.30, width * 0.70):
        arrow(draw, centre_x, height * 0.05, height * 0.44, height * 0.30, 255)
    # a stencil bridge across each arrow, where its head meets its shaft
    for centre_x in (width * 0.30, width * 0.70):
        draw.rectangle((centre_x - height * 0.2, height * 0.05 + (height * 0.39) * 0.45 - 4, centre_x + height * 0.2, height * 0.05 + (height * 0.39) * 0.45 + 6), fill=0)
    mask = np.maximum(mask, np.asarray(arrows, np.float32) / 255)
    sprayed(mask, 81, (26, 23, 20), overspray=0.08, wear=0.2).save(os.path.join(folder, 'crate-stencil.png'))
    print('painted crate-stencil.png')


# -------------------------------------------------------------------------------- pay envelope

def manila_paper(size, seed):
    """Brown manila paper: an even buff with fine fibres, slight mottling and handled, darker edges."""
    width, height = size
    paper = np.ones((height, width, 3), np.float32) * np.array([0.76, 0.62, 0.41])
    paper = paper * (0.93 + 0.07 * noise(height, width, seed, 2.2, 2)[..., None])
    fibres = noise(height, width, seed + 1, 0.3, 1)
    paper = paper * (0.96 + 0.06 * fibres[..., None])
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    edge = np.minimum(np.minimum(xs, width - xs), np.minimum(ys, height - ys))
    handled = np.exp(-edge / 30.0)[..., None]
    return paper * (1 - 0.22 * handled)


def wages_envelope(folder, size=(1024, 683)):
    """The pay envelope (0.114 x 0.076 m): "WAGES" printed large in heavy black letters inside a printed
    rule on the front; the back shows the gummed flap."""
    width, height = size
    front = manila_paper(size, 91)
    ink = Image.new('L', size, 0)
    draw = ImageDraw.Draw(ink)
    draw.rectangle((30, 30, width - 30, height - 30), outline=255, width=5)
    # as big and heavy as the envelope allows: even so, at real size it can only be read from close by
    typeface = fitted_font('AlfaSlabOne-Regular.ttf', 360, 'WAGES', width * 0.86, spacing=6)
    top, bottom = typeface.getbbox('WAGES')[1], typeface.getbbox('WAGES')[3]
    centred_text(draw, (height - (bottom - top)) / 2 - top, 'WAGES', typeface, 255, width, spacing=6)
    printed = np.asarray(ink, np.float32)[..., None] / 255 * (0.85 + 0.15 * noise(height, width, 92, 1.0, 1)[..., None])
    front = front * (1 - printed) + np.array([0.09, 0.07, 0.06]) * printed
    as_picture(front).save(os.path.join(folder, 'wages-envelope-front.jpg'), quality=92)
    back = manila_paper(size, 93)
    flap = Image.new('L', size, 0)
    ImageDraw.Draw(flap).polygon([(0, 0), (width, 0), (width * 0.5, height * 0.62)], fill=255)
    flap_array = np.asarray(flap, np.float32)[..., None] / 255
    edge = np.clip(blurred(flap_array[..., 0], 3) - blurred(flap_array[..., 0], 0.5), 0, 1)[..., None]
    back = back * (1 - 0.08 * flap_array) * (1 - 0.6 * edge)
    as_picture(back).save(os.path.join(folder, 'wages-envelope-back.jpg'), quality=92)
    print('painted wages-envelope-front.jpg and wages-envelope-back.jpg', f'(letters {bottom - top} of {height} pixels high)')


if __name__ == '__main__':
    arguments = sys.argv[1:]
    for name, setting in (('--downloads', 'DOWNLOADS'), ('--fonts', 'FONTS')):
        if name in arguments:
            at = arguments.index(name)
            setattr(painter, setting, os.path.abspath(arguments[at + 1]))
            del arguments[at:at + 2]
    folder = arguments[0]
    os.makedirs(folder, exist_ok=True)
    gate_board(folder, 'No. 1', 'gate-board-no-1.jpg', seed=51)
    gate_board(folder, 'No. 2', 'gate-board-no-2.jpg', seed=55)
    bank_sign(folder)
    brass_plate(folder)
    drum_stencil(folder, 'PETROL', 'drum-stencil-petrol.png', seed=101)
    drum_stencil(folder, 'DIESEL', 'drum-stencil-diesel.png', seed=105)
    crate_stencil(folder)
    wages_envelope(folder)
    print('pictures written to', folder)

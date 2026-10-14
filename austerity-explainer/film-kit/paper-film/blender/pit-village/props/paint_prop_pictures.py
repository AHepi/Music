# What this does: paints the pictures that the scripted props wear, with Pillow and numpy (no
# Blender needed): the painted colliery name board, the printed lock-out notice on weathered paper
# (with torn corners cut out in its transparency), hessian sack cloth with faded stencilled
# coal-merchant marks, and the brass wire gauze of a miner's safety lamp.
#
# Everything named here is invented: the colliery, the company, the coal merchant and the people.
#
# Run: python3 -I paint_prop_pictures.py PICTURE_FOLDER
#      (needs the Poly Haven plank and rock textures already downloaded by download_poly_haven.py)

import math
import os
import tempfile
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
# the Poly Haven downloads (download_poly_haven.py); set PIT_VILLAGE_SCRATCH to choose the folder
DOWNLOADS = os.path.join(os.environ.get('PIT_VILLAGE_SCRATCH', os.path.join(tempfile.gettempdir(), 'pit-village-props')), 'downloads')

COLLIERY = 'ABBOTSCLOUGH'
COMPANY = 'ABBOTSCLOUGH COAL & IRON COMPANY, LIMITED'


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def noise(height, width, seed, smoothness=2.2, smallest=2.0):
    """Cloudy noise between 0 and 1 (tiles, but we only use it once per picture)."""
    rng = np.random.default_rng(seed)
    spectrum = np.fft.fft2(rng.standard_normal((height, width)))
    fy = np.fft.fftfreq(height)[:, None] * height
    fx = np.fft.fftfreq(width)[None, :] * width
    radius = np.sqrt(fx * fx + fy * fy); radius[0, 0] = 1
    spectrum *= 1 / radius ** (smoothness / 2)
    spectrum[radius < smallest] *= 0.3
    field = np.real(np.fft.ifft2(spectrum))
    field -= field.min()
    return field / field.max()


def fitted_font(name, size, text, max_width, spacing=0):
    """The font at `size`, or smaller if the line (with its letter spacing) would be wider than max_width."""
    typeface = font(name, size)
    while size > 8 and sum(typeface.getlength(c) + spacing for c in text) - spacing > max_width:
        size -= 2; typeface = font(name, size)
    return typeface


def as_array(picture):
    return np.asarray(picture.convert('RGB'), dtype=np.float32) / 255


def as_picture(array):
    return Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8))


def surface(asset_id, size):
    """A Poly Haven surface colour picture, resized (width, height) by repeating it."""
    tile = Image.open(os.path.join(DOWNLOADS, 'surfaces', asset_id, 'Diffuse.jpg')).convert('RGB')
    out = Image.new('RGB', size)
    for x in range(0, size[0], tile.width):
        for y in range(0, size[1], tile.height):
            out.paste(tile, (x, y))
    return out


def centred_text(draw, y, text, typeface, fill, width, shadow=None, shadow_offset=(0, 0), spacing=0):
    """Write a line centred across `width` at height y; with letter spacing; optional block shadow
    (the sign-writer's shading: the letter repeated many times down and to the right)."""
    letters = list(text)
    advances = [typeface.getlength(c) + spacing for c in letters]
    total = sum(advances) - spacing
    x = (width - total) / 2
    positions = []
    for letter, advance in zip(letters, advances):
        positions.append((x, letter)); x += advance
    if shadow is not None:
        steps = max(abs(shadow_offset[0]), abs(shadow_offset[1]))
        for step in range(1, steps + 1):
            dx = shadow_offset[0] * step / steps; dy = shadow_offset[1] * step / steps
            for px, letter in positions:
                draw.text((px + dx, y + dy), letter, font=typeface, fill=shadow)
    for px, letter in positions:
        draw.text((px, y), letter, font=typeface, fill=fill)
    return total


# --------------------------------------------------------------------------- colliery name board

def colliery_board(folder, width=2048, height=1024, planks=6):
    """Dark green painted planks, cream lettering shaded in deep red, a cream border with rounded
    corners; then the weather: chipped paint showing grey wood, dirt, fading and rain runs."""
    wood = as_array(surface('weathered_planks', (width, height)).rotate(0))
    wood = wood * 0.55 + np.array([0.30, 0.28, 0.25]) * 0.45  # bleached grey timber under the paint
    paint = Image.new('RGB', (width, height), (32, 58, 44))
    draw = ImageDraw.Draw(paint)
    # border: a cream line with a thin red inner line, inset from the edge
    inset = 46
    draw.rounded_rectangle((inset, inset, width - inset, height - inset), radius=60, outline=(226, 212, 172), width=14)
    draw.rounded_rectangle((inset + 26, inset + 26, width - inset - 26, height - inset - 26), radius=44, outline=(140, 38, 30), width=5)
    big = fitted_font('Ultra-Regular.ttf', 250, COLLIERY, width * 0.84, spacing=6)
    centred_text(draw, 100, COLLIERY, big, (232, 218, 176), width, shadow=(120, 30, 24), shadow_offset=(12, 14), spacing=6)
    centred_text(draw, 380, 'COLLIERY', font('Ultra-Regular.ttf', 250), (232, 218, 176), width, shadow=(120, 30, 24), shadow_offset=(12, 14), spacing=34)
    # thin rules with a diamond either side of the small line
    small = fitted_font('OldStandard-Bold.ttf', 76, COMPANY, width * 0.74, spacing=3)
    line_y = 720
    text_width = centred_text(draw, line_y, COMPANY, small, (226, 212, 172), width, spacing=3)
    middle_y = line_y + 50
    for side in (-1, 1):
        start = width / 2 + side * (text_width / 2 + 30); end = width / 2 + side * (width / 2 - 140)
        draw.line((start, middle_y, end, middle_y), fill=(226, 212, 172), width=5)
    centred_text(draw, 840, 'No. 2  PIT', font('OldStandard-Bold.ttf', 70), (226, 212, 172), width, spacing=8)
    paint = as_array(paint)
    # plank seams: the paint stops at each joint and the joint is dark
    seam = np.zeros((height, width), np.float32)
    for i in range(1, planks):
        y = int(height * i / planks)
        seam[max(0, y - 5):y + 5, :] = 1
    seam = np.asarray(Image.fromarray((seam * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    # chips: where coarse noise and fine noise both run high, the paint has flaked off
    coarse = noise(height, width, 11, 2.0, 3)
    fine = noise(height, width, 12, 1.0, 1)
    chipped = ((coarse * 0.65 + fine * 0.35) > 0.62).astype(np.float32)
    # more flaking along the plank edges, where water sits
    edge_wear = np.zeros((height, width), np.float32)
    for i in range(0, planks + 1):
        y = int(height * i / planks)
        band = np.exp(-((np.arange(height) - y) ** 2) / (2 * 14 ** 2))
        edge_wear += band[:, None]
    chipped = np.clip(chipped + ((fine > 0.55) * edge_wear * 0.9), 0, 1)
    chipped = np.asarray(Image.fromarray((chipped * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255
    out = paint * (1 - chipped) + wood * chipped
    # fade towards the top (sun), dirt and rain runs towards the bottom
    fade = noise(height, width, 13, 2.6, 2)[..., None]
    out = out * (0.86 + 0.14 * fade) + np.array([0.55, 0.52, 0.46]) * 0.10 * (1 - np.linspace(0, 1, height)[:, None, None])
    runs = noise(height, width // 4, 14, 1.4, 1)
    # stretch narrow noise tall, so it reads as vertical runs of rain water
    streak = np.asarray(Image.fromarray((runs[:height // 16] * 255).astype(np.uint8)).resize((width, height), Image.BICUBIC), np.float32) / 255
    dirt = np.clip((np.linspace(0, 1, height)[:, None] ** 2) * 0.5 + streak * 0.25, 0, 1)[..., None]
    out = out * (1 - dirt * 0.45) + np.array([0.12, 0.10, 0.08]) * dirt * 0.45
    out = out * (1 - seam[..., None] * 0.8)
    # soot from the pithead: a fine dark speckle
    speck = (noise(height, width, 15, 0.6, 1) > 0.78)[..., None]
    out = out * (1 - speck * 0.25)
    picture = as_picture(out)
    picture.save(os.path.join(folder, 'colliery-board.jpg'), quality=92)
    return picture


# ------------------------------------------------------------------------------- printed notice

NOTICE_LINES = [
    # (text, font, size, extra letter spacing, gap after)
    (COMPANY.replace(', LIMITED', ', LTD.'), 'OldStandard-Bold.ttf', 50, 2, 26),
    ('NOTICE', 'AbrilFatface-Regular.ttf', 270, 18, 10),
    ('TO ALL WORKMEN', 'OldStandard-Bold.ttf', 84, 8, 30),
    ('The present Contracts of Service will terminate on', 'OldStandard-Regular.ttf', 46, 0, 6),
    ('FRIDAY, 30th APRIL, 1926,', 'OldStandard-Bold.ttf', 74, 2, 6),
    ('and these', 'OldStandard-Italic.ttf', 46, 0, 4),
    ('PITS WILL BE CLOSED', 'AlfaSlabOne-Regular.ttf', 112, 2, 6),
    ('from SATURDAY, 1st MAY, 1926,', 'OldStandard-Bold.ttf', 70, 1, 6),
    ('until the Workmen are prepared to accept the', 'OldStandard-Regular.ttf', 46, 0, 4),
    ('NEW TERMS', 'AlfaSlabOne-Regular.ttf', 112, 6, 6),
    ('now offered by the Owners, copies of which may be', 'OldStandard-Regular.ttf', 46, 0, 2),
    ('seen at the Colliery Office.', 'OldStandard-Regular.ttf', 46, 0, 24),
    ('All Workmen must remove their Tools from the Pit', 'OldStandard-Regular.ttf', 46, 0, 2),
    ('on or before Friday, 30th April.', 'OldStandard-Regular.ttf', 46, 0, 40),
    ('By Order,', 'OldStandard-Italic.ttf', 50, 0, 6),
    ('T. H. WARBRECK, Agent.', 'OldStandard-Bold.ttf', 60, 3, 22),
    ('Colliery Office, Abbotsclough, 16th April, 1926.', 'OldStandard-Italic.ttf', 40, 0, 26),
    ('J. SOWERBY & SON, PRINTERS, ABBOTSCLOUGH.', 'OldStandard-Regular.ttf', 26, 2, 0),
]


def torn_outline(width, height, rng):
    """The paper's outline: straight-ish edges with small nicks, and two corners torn away."""
    def wobble(count, amount):
        return rng.normal(0, amount, count)
    points = []
    steps = 60
    # top edge, left to right, with the top-right corner torn off diagonally
    for i in range(steps + 1):
        x = width * i / steps
        points.append((x, 12 + abs(wobble(1, 3)[0])))
    tear = [(width - 190, 10), (width - 150, 60), (width - 120, 48), (width - 80, 120), (width - 50, 110), (width - 12, 210)]
    points = [p for p in points if p[0] < width - 190] + tear
    for i in range(steps + 1):
        points.append((width - 12 - abs(wobble(1, 3)[0]), 210 + (height - 230) * i / steps))
    # bottom-left corner torn with a ragged curve
    for i in range(steps + 1):
        x = width - 12 - (width - 260) * i / steps
        points.append((x, height - 14 - abs(wobble(1, 3)[0])))
    ragged = [(260 - 240 * i / 11 + rng.normal(0, 8), height - 14 - 250 * (i / 11) ** 1.6 + rng.normal(0, 8)) for i in range(12)]
    points += ragged
    for i in range(steps + 1):
        points.append((12 + abs(wobble(1, 3)[0]), height - 270 - (height - 290) * i / steps))
    return points


def notice(folder, width=1462, height=2048):
    rng = np.random.default_rng(21)
    # paper: cream, yellowed and foxed, stained from paste and rain
    base = np.ones((height, width, 3), np.float32) * np.array([0.90, 0.85, 0.72])
    cloud = noise(height, width, 22, 2.4, 2)[..., None]
    base = base * (0.90 + 0.10 * cloud)
    yellow = noise(height, width, 23, 2.8, 2)[..., None]
    base = base * (1 - 0.18 * yellow ** 2 * np.array([0.2, 0.5, 1.0]))
    # print the type in a separate layer so the ink can be uneven
    ink = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(ink)
    y = 130
    for text, typeface_name, size, spacing, gap in NOTICE_LINES:
        typeface = fitted_font(typeface_name, size, text, width - 260, spacing)
        top, bottom = typeface.getbbox('Hg')[1], typeface.getbbox('Hg')[3]
        centred_text(draw, y - top, text, typeface, 255, width, spacing=spacing)
        y += (bottom - top) + 18 + gap
        if text == 'NOTICE':
            draw.line((width * 0.18, y - 2, width * 0.82, y - 2), fill=255, width=6)
            draw.line((width * 0.18, y + 8, width * 0.82, y + 8), fill=255, width=2)
            y += 30
    print(f'notice text ends at {y} of {height} pixels')
    # a printer's border
    draw.rectangle((70, 70, width - 70, height - 70), outline=255, width=8)
    draw.rectangle((88, 88, width - 88, height - 88), outline=255, width=2)
    ink = np.asarray(ink, np.float32) / 255
    unevenness = 0.78 + 0.22 * noise(height, width, 24, 1.2, 1)
    ink = ink * unevenness
    black = np.array([0.08, 0.07, 0.07])
    paper = base * (1 - ink[..., None]) + black * ink[..., None]
    # creases from folding: two soft lines
    for x in (width // 2 + 7,):
        crease = np.exp(-((np.arange(width) - x) ** 2) / (2 * 4 ** 2))[None, :, None]
        paper = paper * (1 - 0.10 * crease)
    crease = np.exp(-((np.arange(height) - height * 0.34) ** 2) / (2 * 4 ** 2))[:, None, None]
    paper = paper * (1 - 0.08 * crease)
    # rain runs and grime from the bottom up, brown water stains
    stain = noise(height, width, 25, 2.0, 3)
    rings = ((stain > 0.66) & (stain < 0.69)).astype(np.float32)
    paper = paper * (1 - 0.20 * rings[..., None] * np.array([0.3, 0.6, 1.0]))
    paper = paper * (1 - 0.12 * (stain > 0.69)[..., None] * np.array([0.2, 0.5, 1.0]))
    grime = (np.linspace(0, 1, height) ** 3)[:, None, None] * (0.6 + 0.4 * noise(height, width, 26, 1.8, 2)[..., None])
    paper = paper * (1 - 0.30 * grime)
    # paste wrinkles: faint diagonal shading
    wrinkle = noise(height // 8, width // 8, 27, 1.6, 1)
    wrinkle = np.asarray(Image.fromarray((wrinkle * 255).astype(np.uint8)).resize((width, height), Image.BICUBIC), np.float32) / 255
    paper = paper * (0.95 + 0.07 * wrinkle[..., None])
    # foxing: small brown spots, denser near the edges
    spots = noise(height, width, 28, 0.4, 1)
    edge_distance = np.minimum.outer(np.minimum(np.arange(height), height - np.arange(height)), np.minimum(np.arange(width), width - np.arange(width)))
    near_edge = np.exp(-edge_distance / 260.0)
    foxing = np.clip((spots - (0.80 - 0.10 * near_edge)) * 8, 0, 1)
    paper = paper * (1 - 0.35 * foxing[..., None] * np.array([0.25, 0.55, 1.0]))
    # rust runs from the four tacks that hold it up
    for tack_x, tack_y in ((150, 150), (width - 240, 260), (width - 150, height - 150), (330, height - 170)):
        rows = np.arange(height)[:, None]; cols = np.arange(width)[None, :]
        run = np.exp(-((cols - tack_x) ** 2) / (2 * 9 ** 2)) * np.clip(1 - (rows - tack_y) / 260.0, 0, 1) * (rows >= tack_y - 10)
        blot = np.exp(-((cols - tack_x) ** 2 + (rows - tack_y) ** 2) / (2 * 22 ** 2))
        rust = np.clip(run * 0.6 + blot, 0, 1)[..., None]
        paper = paper * (1 - rust * 0.45) + np.array([0.42, 0.22, 0.10]) * rust * 0.30
    # a scuffed patch where the top layer of paper has rubbed away, and a water tide-mark
    scuff = np.clip((noise(height, width, 29, 2.2, 3) - 0.78) * 6, 0, 1)
    paper = paper * (1 - scuff[..., None] * 0.25) + np.array([0.85, 0.80, 0.68]) * scuff[..., None] * 0.25
    # cut out the outline (torn corners) as transparency; darken the torn edge a little
    mask = Image.new('L', (width, height), 0)
    ImageDraw.Draw(mask).polygon(torn_outline(width, height, rng), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.0))
    edge = np.asarray(mask.filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
    paper = paper * (0.80 + 0.20 * edge[..., None])
    picture = as_picture(paper).convert('RGBA')
    picture.putalpha(mask)
    picture.save(os.path.join(folder, 'notice.png'))
    return picture


# --------------------------------------------------------------------------------------- sacks

def hessian(folder, size=1024, marks=None, name='sack-plain', seed=31):
    """Woven jute: over-under threads, uneven thread thickness, coal dust ground in; optionally a
    faded stencilled merchant's mark (lines of text) in the middle of the picture."""
    rng = np.random.default_rng(seed)
    threads = 64  # threads across the picture (about 5 per cm on a 1.3 m wrap)
    u = np.linspace(0, threads * 2 * math.pi, size, endpoint=False)
    warp = 0.5 + 0.5 * np.cos(u)[None, :]
    weft = 0.5 + 0.5 * np.cos(u)[:, None]
    checker = (np.floor(u / (2 * math.pi))[None, :] + np.floor(u / (2 * math.pi))[:, None]) % 2
    weave = np.where(checker > 0, warp * 0.8 + 0.2, weft * 0.8 + 0.2)
    thickness = noise(size, size, seed + 1, 1.0, 1)
    colour = np.array([0.50, 0.40, 0.27])
    cloth = colour * (0.55 + 0.45 * weave[..., None]) * (0.85 + 0.25 * thickness[..., None])
    dust = noise(size, size, seed + 2, 2.2, 2)[..., None]
    cloth = cloth * (1 - 0.55 * dust) + np.array([0.06, 0.06, 0.06]) * 0.3 * dust
    if marks:
        stencil = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(stencil)
        y = size * 0.30
        for text, typeface_name, text_size in marks:
            typeface = font(typeface_name, text_size)
            centred_text(draw, y, text, typeface, 255, size, spacing=6)
            y += text_size * 1.15
        # stencil bridges: thin gaps cut through the letters
        stencil_array = np.asarray(stencil, np.float32) / 255
        bridges = (np.sin(np.arange(size) / size * 2 * math.pi * 70) > 0.93)[None, :]
        stencil_array = stencil_array * (1 - bridges * 0.9)
        faded = stencil_array * (0.6 + 0.4 * noise(size, size, seed + 3, 1.4, 1)) * (0.6 + 0.4 * weave)
        cloth = cloth * (1 - faded[..., None] * 0.88)
    as_picture(cloth).save(os.path.join(folder, f'{name}.jpg'), quality=90)
    # the weave as a normal map (glTF / OpenGL: green points up the picture), so threads catch light
    height_field = weave * 0.7 + thickness * 0.3
    du = (np.roll(height_field, -1, axis=1) - np.roll(height_field, 1, axis=1)) / 2
    dv = (np.roll(height_field, 1, axis=0) - np.roll(height_field, -1, axis=0)) / 2
    normal = np.stack([-du * 3, -dv * 3, np.ones_like(du)], axis=2)
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    as_picture(normal * 0.5 + 0.5).save(os.path.join(folder, 'sack-normal.png'))


# ---------------------------------------------------------------------------------------- gauze

def gauze(folder, size=512, holes=40):
    """Brass wire gauze (28 meshes to the inch in a real Davy lamp): wires as alpha, the rest clear."""
    u = np.linspace(0, holes * 2 * math.pi, size, endpoint=False)
    wire_across = (np.cos(u) > 0.35)[None, :]
    wire_down = (np.cos(u) > 0.35)[:, None]
    wire = (wire_across | wire_down).astype(np.float32)
    colour = np.ones((size, size, 3), np.float32) * np.array([0.46, 0.40, 0.30])  # tarnished, sooty brass wire
    colour *= (0.7 + 0.3 * noise(size, size, 41, 1.6, 1)[..., None])
    picture = as_picture(colour).convert('RGBA')
    # mostly see-through: about 55% wire, so from a few metres it reads as a dark smoky sheen with the flame showing
    picture.putalpha(Image.fromarray((wire * 0.75 * 255).astype(np.uint8)))
    picture.save(os.path.join(folder, 'gauze.png'))


if __name__ == '__main__':
    folder = sys.argv[1]
    os.makedirs(folder, exist_ok=True)
    colliery_board(folder)
    notice(folder)
    hessian(folder, name='sack-plain', seed=31)
    hessian(folder, name='sack-marked-merchant', seed=32,
            marks=[('J. HARTWELL', 'AlfaSlabOne-Regular.ttf', 96), ('COAL MERCHANT', 'OldStandard-Bold.ttf', 70),
                   ('ABBOTSCLOUGH', 'OldStandard-Bold.ttf', 70), ('1 CWT.', 'AlfaSlabOne-Regular.ttf', 110)])
    hessian(folder, name='sack-marked-colliery', seed=33,
            marks=[('A. C. & I. Co.', 'AlfaSlabOne-Regular.ttf', 104), ('No. 2 PIT', 'OldStandard-Bold.ttf', 80),
                   ('BEST HOUSE', 'OldStandard-Bold.ttf', 70)])
    gauze(folder)
    print('pictures written to', folder)

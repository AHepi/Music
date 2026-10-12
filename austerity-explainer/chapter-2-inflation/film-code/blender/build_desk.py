# What this does: builds a reviewer's desk in Blender for chapter 2, page 8 ("An independent review of
# the Reserve Bank says..."), where the printed report drops onto it and a rubber stamp comes down
# twice. The viewer called the old bare table "plain and boring"; this desk fills the tall frame
# around the report: a polished wooden desk top with a green leather blotter (the report lands in its
# middle), a brass banker's lamp with a green glass shade, a stack of folders tied with tape, loose
# typed papers (unreadable grey lines, no words), an open ink pad for the stamp, a fountain pen,
# reading glasses, a cup of tea on its saucer, and bookshelves behind (soft with focus).
#
# The model's origin is the middle of the blotter, on its surface (the report lies there). Blender -y
# is towards the camera (three.js +z). Markers: desk_lamp (the bulb), ink_pad.
#
# Run: /home/user/work/blender-env/bin/python build_desk.py OUT.glb [--no-bake]
# (OUT must end in .glb: Blender adds .glb to any other name)

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model_kit as mk  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

arguments = sys.argv[1:]
OUT = arguments[0] if arguments else 'desk.glb'
rng = np.random.default_rng(5)
mk.reset()

# ------------------------------------------------------------------------------------- materials
wood = mk.material('wood', name='desk-wood', roughness=0.35)
leather_picture = Image.new('RGB', (1024, 820), (54, 86, 70))
ink = ImageDraw.Draw(leather_picture)
noise = (rng.random((820, 1024)) * 18).astype(np.uint8)
leather_array = np.array(leather_picture).astype(int) + noise[..., None] - 9
leather_picture = Image.fromarray(np.clip(leather_array, 0, 255).astype(np.uint8))
ink = ImageDraw.Draw(leather_picture)
ink.rectangle([22, 22, 1001, 797], outline=(176, 142, 74), width=5)      # a tooled gold border
ink.rectangle([36, 36, 987, 783], outline=(140, 112, 60), width=2)
leather = mk.material(name='blotter-leather', roughness=0.55, picture=leather_picture)
brass = mk.material(None, name='brass', colour=(0.75, 0.55, 0.25), roughness=0.3, metallic=0.9)
shade_glass = mk.material(None, name='shade-glass', colour=(0.05, 0.32, 0.18), roughness=0.15, metallic=0.1)
bulb = mk.material(None, name='lamp-glow', colour=(1.0, 0.85, 0.6), glow=(1.0, 0.78, 0.5), glow_strength=4.0, roughness=0.3)
manila = mk.material(None, name='manila', colour=(0.72, 0.6, 0.38), roughness=0.85)
paper_edge = mk.material(None, name='paper-edge', colour=(0.88, 0.85, 0.78), roughness=0.9)
tape = mk.material(None, name='red-tape', colour=(0.55, 0.12, 0.1), roughness=0.7)
black = mk.material(None, name='black-lacquer', colour=(0.02, 0.02, 0.025), roughness=0.2, metallic=0.2)
gold = mk.material(None, name='gold', colour=(0.85, 0.65, 0.3), roughness=0.25, metallic=1.0)
china = mk.material(None, name='china', colour=(0.9, 0.9, 0.86), roughness=0.25)
tea = mk.material(None, name='tea', colour=(0.25, 0.12, 0.05), roughness=0.1)
tin = mk.material(None, name='tin', colour=(0.35, 0.36, 0.38), roughness=0.35, metallic=0.8)
ink_red = mk.material(None, name='ink-pad', colour=(0.45, 0.08, 0.07), roughness=0.6)
lens = mk.material(None, name='lens', colour=(0.6, 0.7, 0.75), roughness=0.05, metallic=0.3)


def typed_page(seed, size=(512, 680)):
    """A typed page: rows of grey bars of uneven length (unreadable, no letters)."""
    r = np.random.default_rng(seed)
    page = Image.new('RGB', size, (232, 226, 210))
    draw = ImageDraw.Draw(page)
    y = 70
    while y < size[1] - 60:
        if r.random() < 0.12: y += 22; continue          # a paragraph gap
        x = 56
        end = size[0] - 56 - (r.random() * 160 if r.random() < 0.2 else 0)
        while x < end:
            word = 14 + r.random() * 46
            draw.rectangle([x, y, min(x + word, end), y + 7], fill=(92, 90, 86))
            x += word + 9
        y += 19
    return page


page_a = mk.material(name='typed-page-a', roughness=0.9, picture=typed_page(1))
page_b = mk.material(name='typed-page-b', roughness=0.9, picture=typed_page(2))

# bookshelf spines: rows of muted cloth bindings with a few gold bands (no titles)
spines = Image.new('RGB', (1024, 256), (20, 16, 14))
draw = ImageDraw.Draw(spines)
x = 0
cloth = [(92, 34, 30), (34, 58, 44), (52, 44, 34), (30, 40, 62), (110, 82, 50), (70, 30, 40), (40, 40, 40)]
while x < 1024:
    width = int(18 + rng.random() * 26)
    colour = cloth[int(rng.random() * len(cloth))]
    shade = 0.75 + rng.random() * 0.35
    top = int(rng.random() * 40)
    draw.rectangle([x, top, x + width - 2, 255], fill=tuple(int(c * shade) for c in colour))
    for band in (top + 18, 220):
        if rng.random() < 0.6: draw.rectangle([x + 2, band, x + width - 4, band + 4], fill=(150, 120, 60))
    x += width
books = mk.material(name='book-spines', roughness=0.8, picture=spines)
shelf_wood = mk.material('wood', name='shelf-wood', roughness=0.5)

parts = []
add = lambda p: parts.append(p) or p

# --------------------------------------------------------------------------------------- the desk
TOP_Y = 0.35                                    # the desk top's middle is a little further back than the blotter
add(mk.box('desk-top', (5.0, 4.2, 0.1), at=(0, TOP_Y, -0.058), material=wood, bevel=0.02))
add(mk.box('desk-edge', (5.06, 0.08, 0.06), at=(0, TOP_Y - 2.1, -0.1), material=wood, bevel=0.015))
add(mk.box('desk-front', (4.9, 0.06, 0.8), at=(0, TOP_Y - 2.05, -0.5), material=wood, bevel=0.01))
add(mk.plane('blotter', (2.5, 2.0), at=(0, 0.05, -0.004), material=leather))
add(mk.box('blotter-base', (2.52, 2.02, 0.006), at=(0, 0.05, -0.008), material=mk.material(None, name='blotter-edge', colour=(0.12, 0.1, 0.08), roughness=0.6)))
for side in (-1, 1):   # leather corners
    add(mk.box(f'blotter-end-{side}', (0.16, 2.04, 0.012), at=(side * 1.29, 0.05, -0.002), material=mk.material(None, name='blotter-ends', colour=(0.1, 0.16, 0.13), roughness=0.5), bevel=0.004))

# the banker's lamp, upper left
LX, LY = -0.95, 1.5
add(mk.cylinder('lamp-base', 0.22, 0.06, at=(LX, LY, 0.03), material=brass, sides=32, bevel=0.01))
add(mk.cylinder('lamp-base-top', 0.12, 0.05, at=(LX, LY, 0.085), material=brass, sides=32, radius_top=0.07))
add(mk.cylinder('lamp-stem', 0.022, 0.75, at=(LX, LY, 0.45), material=brass, sides=12))
add(mk.box('lamp-arm', (0.04, 0.04, 0.16), at=(LX, LY - 0.06, 0.82), material=brass, rotate=(math.radians(30), 0, 0)))
shade = add(mk.cylinder('lamp-shade', 0.17, 0.72, at=(LX + 0.05, LY - 0.14, 0.86), material=shade_glass, sides=28, rotate=(0, math.pi / 2, 0)))
for v in shade.data.vertices:          # keep the top half of the cylinder: a half-round shade
    if v.co.x > 0: v.co.x = 0.0
add(mk.cylinder('lamp-bulb', 0.045, 0.3, at=(LX + 0.05, LY - 0.14, 0.82), material=bulb, sides=12, rotate=(0, math.pi / 2, 0)))
for side in (-1, 1):
    add(mk.cylinder(f'shade-cap-{side}', 0.17, 0.012, at=(LX + 0.05 + side * 0.36, LY - 0.14, 0.86), material=brass, sides=28, rotate=(0, math.pi / 2, 0)))
add(mk.cylinder('pull-chain', 0.006, 0.22, at=(LX + 0.3, LY - 0.2, 0.68), material=brass, sides=6))
mk.marker('desk_lamp', (LX + 0.05, LY - 0.14, 0.76))

# the stack of folders, upper right, tied with red tape
FX, FY = 0.95, 1.55
for k in range(4):
    turn = math.radians(rng.uniform(-7, 7))
    z = 0.012 + k * 0.045
    add(mk.box(f'folder-papers-{k}', (0.86, 1.08, 0.03), at=(FX + rng.uniform(-0.03, 0.03), FY + rng.uniform(-0.03, 0.03), z + 0.018), material=paper_edge, rotate=(0, 0, turn)))
    add(mk.box(f'folder-cover-{k}', (0.9, 1.12, 0.008), at=(FX, FY, z + 0.037), material=manila, rotate=(0, 0, turn), bevel=0.002))
add(mk.box('tape-across', (0.95, 0.05, 0.2), at=(FX, FY + 0.12, 0.1), material=tape))
add(mk.box('tape-along', (0.05, 1.16, 0.2), at=(FX - 0.15, FY, 0.1), material=tape))

# loose typed papers, upper middle (one tucked under the report's top edge would clip: keep clear)
add(mk.plane('paper-a', (0.62, 0.82), at=(-0.25, 1.55, 0.004), material=page_a, rotate=(0, 0, math.radians(8))))
add(mk.plane('paper-b', (0.62, 0.82), at=(0.2, 1.62, 0.007), material=page_b, rotate=(0, 0, math.radians(-5))))

# the ink pad, right of the report (lid open)
IX, IY = 0.98, -0.25
add(mk.box('ink-tin', (0.36, 0.26, 0.04), at=(IX, IY, 0.02), material=tin, bevel=0.008))
add(mk.box('ink-felt', (0.31, 0.21, 0.01), at=(IX, IY, 0.041), material=ink_red))
add(mk.box('ink-lid', (0.36, 0.26, 0.02), at=(IX + 0.02, IY + 0.29, 0.012), material=tin, bevel=0.006, rotate=(0, 0, math.radians(6))))
mk.marker('ink_pad', (IX, IY, 0.05))

# the fountain pen, left of the report
pen_turn = math.radians(-58)
along = (math.sin(pen_turn), -math.cos(pen_turn))     # the pen's length direction on the desk
pen_at = lambda d: (-0.95 + d * along[0], -0.35 + d * along[1])
add(mk.cylinder('pen-barrel', 0.022, 0.36, at=(*pen_at(0), 0.023), material=black, sides=16, rotate=(math.pi / 2, 0, pen_turn)))
add(mk.cylinder('pen-cap', 0.024, 0.2, at=(*pen_at(0.26), 0.025), material=black, sides=16, rotate=(math.pi / 2, 0, pen_turn)))
add(mk.cylinder('pen-band', 0.026, 0.02, at=(*pen_at(0.17), 0.025), material=gold, sides=16, rotate=(math.pi / 2, 0, pen_turn)))
add(mk.box('pen-clip', (0.01, 0.12, 0.006), at=(*pen_at(0.3), 0.05), material=gold, rotate=(0, 0, pen_turn)))

# reading glasses, lower left
GX, GY = -0.75, -1.15
for side in (-1, 1):
    add(mk.cylinder(f'lens-{side}', 0.11, 0.008, at=(GX + side * 0.13, GY, 0.012), material=lens, sides=24))
    rim = add(mk.cylinder(f'rim-{side}', 0.12, 0.016, at=(GX + side * 0.13, GY, 0.012), material=black, sides=24, cap=False))
    add(mk.box(f'temple-{side}', (0.012, 0.36, 0.01), at=(GX + side * 0.24, GY + 0.17, 0.01), material=black, rotate=(0, 0, side * 0.12)))
add(mk.box('bridge', (0.05, 0.012, 0.012), at=(GX, GY, 0.03), material=black))

# a cup of tea on its saucer, lower right
CX, CY = 0.85, -1.15
add(mk.cylinder('saucer', 0.22, 0.02, at=(CX, CY, 0.01), material=china, sides=32, radius_top=0.2, bevel=0.005))
add(mk.cylinder('cup', 0.13, 0.16, at=(CX, CY, 0.1), material=china, sides=32, radius_top=0.15, cap=False))
add(mk.cylinder('cup-bottom', 0.13, 0.01, at=(CX, CY, 0.025), material=china, sides=32))
add(mk.cylinder('tea', 0.14, 0.006, at=(CX, CY, 0.155), material=tea, sides=32))
handle = mk.cylinder('cup-handle', 0.05, 0.02, at=(CX + 0.17, CY, 0.1), material=china, sides=16, cap=False, rotate=(math.pi / 2, 0, 0))
add(handle)

# behind the desk: a wall and bookshelves (soft with focus at the top of the frame)
add(mk.box('wall', (8.0, 0.1, 4.0), at=(0, 3.4, 0.6), material=mk.material(None, name='wall-paint', colour=(0.16, 0.2, 0.19), roughness=0.9)))
for row in range(3):
    z = -0.15 + row * 0.62
    add(mk.box(f'shelf-{row}', (6.0, 0.5, 0.05), at=(0, 3.1, z), material=shelf_wood, bevel=0.006))
    add(mk.plane(f'books-{row}', (6.0, 0.52), at=(0, 2.9, z + 0.3), material=books, rotate=(math.pi / 2, 0, 0)))

mk.finish(OUT, bake='--no-bake' not in arguments, bake_skip=('wall', 'books', 'shelf'))

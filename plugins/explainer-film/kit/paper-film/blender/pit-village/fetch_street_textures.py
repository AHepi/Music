# What this does: downloads the free (CC0) Poly Haven surface pictures that the pit village street
# set wears (brick, stone, cobbled setts, flagstones, slate, plaster, painted planks, rusty iron,
# spoil-heap rubble, a muddy yard), and also paints the few pictures that are made here rather than
# downloaded: lace-curtained windows (lit and dark), the gas-lamp glass, and the dusk sky.
#
# For each Poly Haven texture it keeps the colour picture and the normal map (OpenGL / glTF
# convention). Big colour pictures (brick, stone, setts, slate) are 2k; everything else is 1k.
# Pictures are re-saved as JPEG quality 86 to keep the .glb small.
#
# Run (outside Blender, needs numpy and Pillow; uses curl so the machine's proxy settings apply):
#   python3 -I fetch_street_textures.py KIT/assets/models/pit-village/textures
# It skips files that are already there, so running it again is cheap.

import io
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUTPUT_FOLDER = sys.argv[1] if len(sys.argv) > 1 else 'textures'

# name: resolution of the colour picture (normal maps are always 1k)
POLY_HAVEN_TEXTURES = {
    'red_brick': '2k',               # cottage brick (Durham-style dark red brick, darkened with soot)
    'stone_brick_wall_001': '2k',    # cottage rubble sandstone (the other side of the street)
    'square_cobblestone': '2k',      # the street's granite setts
    'roof_slates_03': '2k',          # Welsh slate roofs
    'castle_brick_02_red': '1k',     # engine house, heapstead and chimney brick
    'large_grey_tiles': '1k',        # pavement flagstones
    'large_sandstone_blocks': '1k',  # kerb stones and the gutter channel
    'rock_surface': '1k',            # dressed sandstone: sills, lintels, steps, plinths, copings
    'grey_plaster_02': '1k',         # painted surfaces (doors, frames), clay pots, ridge tiles
    'green_rough_planks': '1k',      # painted boarded doors and gates
    'blue_painted_planks': '1k',     # painted boarded doors (heapstead)
    'distressed_painted_planks': '1k',  # fascia boards and the engine house doors
    'rusty_metal_02': '1k',          # cast iron (lamps, gutters, downpipes) and the headframe steel
    'rocks_ground_02': '1k',         # the spoil heap (darkened to near black)
    'muddy_tracks': '1k',            # the colliery yard and the land around
}


def curl_json(url):
    return json.loads(subprocess.check_output(['curl', '-sS', '--fail', url]))


def curl_picture(url):
    data = subprocess.check_output(['curl', '-sS', '--fail', url])
    return Image.open(io.BytesIO(data)).convert('RGB')


def fetch_poly_haven():
    for name, resolution in POLY_HAVEN_TEXTURES.items():
        colour_path = os.path.join(OUTPUT_FOLDER, f'{name}_colour.jpg')
        normal_path = os.path.join(OUTPUT_FOLDER, f'{name}_normal.jpg')
        if os.path.exists(colour_path) and os.path.exists(normal_path):
            continue
        files = curl_json(f'https://api.polyhaven.com/files/{name}')
        curl_picture(files['Diffuse'][resolution]['jpg']['url']).save(colour_path, quality=86)
        curl_picture(files['nor_gl']['1k']['jpg']['url']).save(normal_path, quality=92)
        print('downloaded', name)


# ------------------------------------------------------------------------- painted here

def lace_curtain_window(lit, seed, width=384, height=640):
    """One sash window's view: net-lace curtains (a fine mesh with rows of flower motifs, a
    scalloped hem, soft vertical folds), parted in the middle and tied back, a roller blind half
    down at the top, and behind them the room: warm lamplight when lit, near darkness when not.
    Returns (colour picture, glow picture or None)."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:height, 0:width].astype(float)
    u, v = xs / width, ys / height                       # v = 0 at the top
    # the room behind: lit = warm lamplight with a brighter pool from a lamp low on one side
    lamp_x = 0.3 + 0.4 * rng.random()
    if lit:
        room = np.array([1.0, 0.62, 0.28]) * (0.55 + 0.45 * np.exp(-(((u - lamp_x) * 2.2) ** 2 + ((v - 0.7) * 2.5) ** 2)))[..., None]
        # a dark picture frame and a mantel shelf on the far wall, so the room is not empty light
        frame = (np.abs(u - (1 - lamp_x)) < 0.12) & (np.abs(v - 0.42) < 0.08)
        inner = (np.abs(u - (1 - lamp_x)) < 0.095) & (np.abs(v - 0.42) < 0.06)
        room = np.where((frame & ~inner)[..., None], room * 0.35, room)
        room = np.where(inner[..., None], room * 0.75, room)
        shelf = (np.abs(v - 0.62) < 0.012)
        room = np.where(shelf[..., None], room * 0.4, room)
    else:
        room = np.array([0.035, 0.04, 0.05]) * (0.8 + 0.4 * (1 - v))[..., None]
    # the curtain: two halves meeting at the top and swept aside lower down (tied back)
    tie_height = 0.62 + 0.06 * rng.random()
    gap_half = np.where(v < tie_height, 0.02 + 0.28 * (v / tie_height) ** 1.6, 0.30 - 0.2 * (v - tie_height) / (1 - tie_height))
    in_curtain = np.abs(u - 0.5) > gap_half
    # net mesh: a fine diamond grid
    mesh = ((np.sin((xs + ys) * 0.9) > 0.55) | (np.sin((xs - ys) * 0.9) > 0.55)).astype(float)
    # rows of flower motifs: rosettes on a staggered grid
    cell = 48.0
    row = np.floor(ys / cell)
    cx = (xs + (row % 2) * cell / 2) % cell - cell / 2
    cy = ys % cell - cell / 2
    radius = np.sqrt(cx * cx + cy * cy)
    angle = np.arctan2(cy, cx)
    petals = (radius < 14 + 5 * np.cos(angle * 6)) & (radius > 4)
    centre = radius < 3
    stems = (np.abs(cx) < 1.2) & (cy > 10) & (cy < 24)
    motif = (petals | centre | stems).astype(float)
    # scalloped hem and a border band near the bottom of each half
    hem_line = 0.96 - 0.012 * (1 + np.cos(xs / 16 * math.pi))
    below_hem = v > hem_line
    border = (v > 0.88) & (v < 0.9)
    density = np.clip(0.35 * mesh + 0.75 * motif + 0.9 * border, 0, 1)
    # soft vertical folds
    folds = 0.75 + 0.25 * np.sin(xs / width * math.pi * 14 + 2 * np.sin(ys / 90))
    curtain_white = np.array([0.93, 0.9, 0.82])
    curtain = curtain_white * (density * folds)[..., None]
    covered = in_curtain & ~below_hem
    if lit:
        # lamplight shines through the lace: the threads glow warm, the holes show the room
        through = room * (1 - 0.55 * density[..., None]) + np.array([1.0, 0.8, 0.55]) * 0.55 * (density * folds)[..., None]
        picture = np.where(covered[..., None], through, room)
    else:
        # a dark room: the lace catches the last daylight, grey-white over the darkness
        picture = np.where(covered[..., None], room + 0.32 * curtain, room)
    # a roller blind half-way down the top pane: a cream holland blind with a lace edge and a ring pull
    blind_bottom = 0.12 + 0.12 * rng.random()
    blind = v < blind_bottom
    blind_colour = np.array([0.86, 0.78, 0.6]) * (0.45 if not lit else 0.9) * (0.92 + 0.08 * np.sin(ys * 0.6))[..., None]
    picture = np.where(blind[..., None], blind_colour, picture)
    lace_edge = (v >= blind_bottom) & (v < blind_bottom + 0.018) & (np.sin(xs * 0.5) > -0.2)
    picture = np.where(lace_edge[..., None], picture * 0.4 + 0.5 * curtain_white * (0.9 if lit else 0.4), picture)
    ring = (np.abs(np.sqrt((u - 0.5) ** 2 * 16 + (v - blind_bottom - 0.035) ** 2 * 50) - 0.05) < 0.012)
    picture = np.where(ring[..., None], picture * 0.3, picture)
    # a cold reflection of the sky across the glass when unlit
    if not lit:
        streak = np.clip(1 - np.abs(u - v * 0.5 - 0.15) * 7, 0, 1) * 0.06
        picture = picture + streak[..., None] * np.array([0.6, 0.75, 0.9])
    picture = np.clip(picture, 0, 1)
    colour = Image.fromarray((picture * 255).astype(np.uint8), 'RGB')
    glow = colour if lit else None
    return colour, glow


def lamp_glass(width=128, height=192):
    """The glass of a gas lantern: bright gas mantle low in the middle, warm glow fading upwards,
    a slight yellow tint, and the shadow lines of the inner wire frame."""
    ys, xs = np.mgrid[0:height, 0:width].astype(float)
    u, v = xs / width, ys / height
    mantle = np.exp(-(((u - 0.5) * 5) ** 2 + ((v - 0.62) * 4) ** 2))
    glow = 0.45 + 0.55 * mantle
    picture = np.array([1.0, 0.78, 0.45]) * glow[..., None]
    wire = (np.abs(u - 0.5) < 0.012) & (v > 0.7)
    picture = np.where(wire[..., None], picture * 0.5, picture)
    return Image.fromarray((np.clip(picture, 0, 1) * 255).astype(np.uint8), 'RGB')


def dusk_sky(width=1024, height=512):
    """A cool dusk sky for the inside of the sky dome: deep slate blue overhead, teal-grey in the
    middle, a thin band of dull amber at the horizon, with soft long clouds. v = 0 is the top of
    the picture (the zenith); v = 0.5 is the horizon; below that it stays dark."""
    rng = np.random.default_rng(3)
    ys, xs = np.mgrid[0:height, 0:width].astype(float)
    elevation = 1 - ys / (height / 2)          # 1 at the zenith, 0 at the horizon, negative below
    top = np.array([0.10, 0.14, 0.20])
    middle = np.array([0.26, 0.36, 0.40])
    horizon = np.array([0.70, 0.52, 0.32])
    e = np.clip(elevation, 0, 1)[..., None]
    sky = np.where(e > 0.25, middle + (top - middle) * ((e - 0.25) / 0.75) ** 0.8, horizon + (middle - horizon) * (e / 0.25) ** 0.7)
    # long soft clouds (tileable sideways noise, stretched)
    noise = np.zeros((height, width))
    for scale, weight in ((64, 0.6), (24, 0.3), (8, 0.1)):
        small = rng.random((max(2, height // scale), max(2, width // (scale * 3))))
        layer = np.array(Image.fromarray((small * 255).astype(np.uint8)).resize((width, height), Image.BICUBIC)) / 255
        noise += layer * weight
    clouds = np.clip((noise - 0.5) * 3, 0, 1) * np.clip(elevation * 3, 0, 1) * (elevation < 0.9)
    sky = sky * (1 - 0.35 * clouds[..., None]) + np.array([0.08, 0.09, 0.11]) * 0.35 * clouds[..., None]
    below = elevation < 0
    sky = np.where(below[..., None], np.array([0.06, 0.06, 0.07]), sky)
    return Image.fromarray((np.clip(sky, 0, 1) * 255).astype(np.uint8), 'RGB').filter(ImageFilter.GaussianBlur(1.5))


def paint_pictures():
    for index in range(3):
        colour, glow = lace_curtain_window(lit=True, seed=10 + index)
        colour.save(os.path.join(OUTPUT_FOLDER, f'window_lit_{index}.jpg'), quality=88)
        colour, glow = lace_curtain_window(lit=False, seed=20 + index)
        colour.save(os.path.join(OUTPUT_FOLDER, f'window_dark_{index}.jpg'), quality=88)
    lamp_glass().save(os.path.join(OUTPUT_FOLDER, 'lamp_glass.jpg'), quality=90)
    dusk_sky().save(os.path.join(OUTPUT_FOLDER, 'dusk_sky.jpg'), quality=90)


if __name__ == '__main__':
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    fetch_poly_haven()
    paint_pictures()
    print('textures ready in', OUTPUT_FOLDER)

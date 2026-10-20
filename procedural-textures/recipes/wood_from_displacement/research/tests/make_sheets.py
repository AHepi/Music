# What this does: puts the test pictures from tests/renders/ side by side with plain text labels, and saves them as JPEG pictures in
# research/pictures/ for the guide. Nothing is measured here.
# Run with:  python3 -I make_sheets.py      (PIL only)
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REN = os.path.join(HERE, 'renders')
PIC = os.path.join(os.path.dirname(HERE), 'pictures')
PROC = 'proc-work/'
FONT = ImageFont.load_default(size=17)
SMALL = ImageFont.load_default(size=14)


def get(name, size):
    path = name if os.path.isabs(name) else os.path.join(REN, name)
    image = Image.open(path).convert('RGB')
    return image.resize((size, size), Image.LANCZOS)


def sheet(out_name, items, size=420, columns=None, title=None, gap=8):
    """items: list of (file name, label). Saves a labelled contact sheet as JPEG."""
    columns = columns or len(items)
    rows = (len(items) + columns - 1) // columns
    head = 34 if title else 0
    label_h = 24
    width = columns * size + (columns + 1) * gap
    height = head + rows * (size + label_h) + (rows + 1) * gap
    canvas = Image.new('RGB', (width, height), (24, 24, 24))
    draw = ImageDraw.Draw(canvas)
    if title:
        draw.text((gap, 8), title, fill=(255, 255, 255), font=FONT)
    for index, (name, label) in enumerate(items):
        col, row = index % columns, index // columns
        x = gap + col * (size + gap)
        y = head + gap + row * (size + label_h + gap)
        canvas.paste(get(name, size), (x, y + label_h))
        draw.text((x + 2, y + 3), label, fill=(255, 230, 120), font=SMALL)
    canvas.save(os.path.join(PIC, out_name), quality=84)
    print('saved', out_name, canvas.size)


SRC_H = PROC + 'reference/wood/height_as_uploaded.png'
SRC_C = PROC + 'reference/wood/colour.png'

sheet('A1_pieces_tile_512.jpg', [
    ('plain_repeat_1x1_height.png', 'the source map as it is (height)'),
    ('pieces_rows_only_1x1_height.png', 'pieces: rows only (shift + flip)'),
    ('pieces_full_1x1_height.png', 'pieces: full (free random start)'),
    ('pieces_curated_1x1_height.png', 'pieces: knots rationed'),
    ('pieces_curated_1x1_colour.png', 'same, colour map (same windows)')], size=330, columns=5,
    title='Per-piece random sampling, default tile (5 rows, 3 boards per row), 512 dots')

sheet('A2_area_4x4_pieces.jpg', [
    ('plain_repeat_4x4_colour.png', 'plain repeat of the source, 4 x 4 tiles'),
    ('pieces_full_b2_4x4_colour.png', 'pieces, free random start, 2 boards per row'),
    ('pieces_curated_b2_4x4_colour.png', 'pieces, knots rationed, 2 boards per row')], size=500, columns=3,
    title='Big area, 4 x 4 tiles (random numbers from the global board number, so nothing repeats on purpose)')

sheet('B1_hex_and_voronoi.jpg', [
    (SRC_H, 'the source map (height)'),
    ('hex_hard_1x1_height.png', 'hex: hard patches'),
    ('hex_linear_1x1_height.png', 'hex: plain 3-copy blend'),
    ('hex_variance_1x1_height.png', 'hex: blend + contrast put back'),
    ('hex_gauss_1x1_height.png', 'hex: Gaussian (Heitz-Neyret style)'),
    ('voronoi_patches_1x1_height.png', 'Voronoi patches, random shift')], size=330, columns=6,
    title='Stochastic / hex / Voronoi patch tiling applied to the WHOLE map (rows, gaps and joints are lost)')

sheet('C1_bag_and_wang.jpg', [
    ('bag16_1x1_height.png', 'random tile bag of 16, tile'),
    ('bag16_b2_4x4_height.png', 'bag of 16, 4 x 4 area: same tiles keep coming back'),
    ('wang_naive_1x1_height.png', 'Wang tiles from windows that do not match on their edges')], size=480, columns=3,
    title='Random tile picking (Wang style)')

sheet('D1_stamps.jpg', [
    ('bomb_nostamps_1x1_height.png', 'boards only (no knots, no stains stamped)'),
    ('bomb_1x1_height.png', 'plus stamps: knots + stains (height)'),
    ('bomb_1x1_colour.png', 'plus stamps (colour)'),
    ('bomb_zone_1x1_colour.png', 'stamps found with a repeat zone (colour)')], size=400, columns=4,
    title='Texture bombing of stamps on top of the boards, default tile 512 dots')

sheet('E1_masks_4x4.jpg', [
    ('masks_off_4x4_colour.png', 'boards + stamps, no large masks, 2 per row'),
    ('masks_full_4x4_colour.png', 'plus large soft light/dark drift and blotches, 2 per row'),
    ('masks_b3_4x4_colour.png', 'same, shorter boards (3 per row)')], size=500, columns=3,
    title='Large-scale masks and board length, 4 x 4 tiles')

sheet('F1_colour_versus_palette.jpg', [
    (SRC_C, 'the uploaded colour map'),
    ('masks_full_1x1_colour.png', 'MAIN: colour map sampled with the height'),
    ('palette_1x1_colour.png', 'COMPARISON: colour made from the height only')], size=500, columns=3,
    title='Same arrangement, same tone shifts: colour map versus palette from height')

sheet('G1_new_blender_things.jpg', [
    ('repeat_zone_dots.png', 'shader repeat zone: 9 neighbour cells'),
    ('gn_boards_4x4_colour.png', 'geometry nodes: real board quads, own UV window each'),
    ('gn_boards_4x4_height.png', 'same, height')], size=480, columns=3,
    title='Blender 5.2: repeat zone in a shader, and the geometry-nodes route (4 x 4 area)')

sheet('G2_image_edge_options.jpg', [
    ('edge_repeat_1x1_height.png', 'Extension REPEAT (wraps: seam)'),
    ('edge_extend_1x1_height.png', 'Extension EXTEND (smears edge)'),
    ('edge_mirror_1x1_height.png', 'Extension MIRROR (bounces back)')], size=420, columns=3,
    title='Reading a window that runs past the right and bottom edge of the map (starts at x = y = 800)')

sheet('H1_seam_2x2_tile_mode.jpg', [
    ('plain_repeat_2x2_colour.png', 'plain repeat of the source: seam visible'),
    ('seam_masks_2x2_colour.png', 'whole idea, default tile repeated 2 x 2: no seam')], size=700, columns=2,
    title='Does the default tile repeat without a seam? 2 x 2 tiles of the same tile')

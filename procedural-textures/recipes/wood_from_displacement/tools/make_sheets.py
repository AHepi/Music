# ROUND 1 TOOL (its helper functions are used by tools/make_sheets_round2.py, which makes the round 2 sheets).
# What this does (plain words): puts the finished pictures of the wood-from-maps recipe side by side on labelled sheets (JPEG, for looking at), in sheets/.
#   wood_sheet.jpg  reference | earlier wood recipe (best new tile) | new MAIN | new COMPARISON, with a row of 400 x 400 close-ups below
#   seeds.jpg       three seeds, MAIN (top) and COMPARISON (bottom)
#   maps.jpg        every map of the default tile (colour, height, roughness, normal) and the uploaded ones
#   area_4x4.jpg    the whole 4 x 4 area, shrunk, and area_2x2.jpg the 2 x 2 area
#   area_crops.jpg  full-size crops (one dot = one picture dot) of the 4 x 4 area across tile lines
#   seam_2x2.jpg    the default tile repeated 2 x 2 with the tile lines marked on the edge, and the plain source repeated 2 x 2 for comparison
#   lit.jpg         reference and new, lit by a low raking sun
# Use: python3 -I tools/make_sheets.py [name ...]     (no name = every sheet whose pictures exist)
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, '..'))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
REF = os.path.join(PROC, 'reference', 'wood')
SHEETS = os.path.join(BASE, 'sheets')
os.makedirs(SHEETS, exist_ok=True)


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def open_rgb(path):
    if not os.path.exists(path) and path.endswith('.png') and os.path.exists(path[:-4] + '.jpg'):
        path = path[:-4] + '.jpg'          # big area colour pictures are kept as JPEG after tools/shrink_area_files.py
    im = Image.open(path)
    if im.mode in ('I;16', 'I'):
        a = np.asarray(im).astype(np.float32) / 65535.0
        im = Image.fromarray((a * 255).astype(np.uint8))
    return im.convert('RGB')


def labelled(im, text, size):
    """The picture shrunk to size x size with a label bar on top."""
    im = im.resize((size, size), Image.LANCZOS)
    bar = 34
    out = Image.new('RGB', (size, size + bar), (24, 24, 24))
    out.paste(im, (0, bar))
    ImageDraw.Draw(out).text((8, 5), text, fill=(240, 240, 240), font=font(22))
    return out


def grid(tiles, columns, gap=8, background=(255, 255, 255)):
    w, h = tiles[0].size
    rows = (len(tiles) + columns - 1) // columns
    sheet = Image.new('RGB', (columns * w + (columns - 1) * gap, rows * h + (rows - 1) * gap), background)
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % columns) * (w + gap), (i // columns) * (h + gap)))
    return sheet


def save(sheet, name, max_width=2400):
    if sheet.size[0] > max_width:
        sheet = sheet.resize((max_width, int(sheet.size[1] * max_width / sheet.size[0])), Image.LANCZOS)
    path = os.path.join(SHEETS, name)
    sheet.save(path, quality=88)
    print('wrote', path, sheet.size)


def wood_sheet():
    sources = [('reference (the uploaded colour map)', os.path.join(REF, 'colour.png')),
               ('earlier wood recipe, best new tile', os.path.join(BASE, 'tests', 'earlier_wood_seed105', 'colour.png')),
               ('NEW MAIN (colour map, seed 1)', os.path.join(BASE, 'outputs', 'main_seed1', 'colour.png')),
               ('NEW COMPARISON (colour from height, seed 1)', os.path.join(BASE, 'outputs', 'comparison_seed1', 'colour.png'))]
    if not all(os.path.exists(p) for _, p in sources):
        return
    ims = [(t, open_rgb(p)) for t, p in sources]
    top = grid([labelled(im, t, 480) for t, im in ims], 4)
    crops = []
    for t, im in ims:
        crops.append(labelled(im.crop((420, 230, 820, 630)).resize((400, 400)), 'close-up 400 x 400 dots', 400))
    row = grid(crops, 4, gap=88)
    sheet = Image.new('RGB', (max(top.size[0], row.size[0]), top.size[1] + row.size[1] + 16), (255, 255, 255))
    sheet.paste(top, (0, 0))
    sheet.paste(row, (0, top.size[1] + 16))
    save(sheet, 'wood_sheet.jpg')


def seeds_sheet():
    tiles = []
    for kind, title in (('main', 'MAIN'), ('comparison', 'COMPARISON')):
        for seed in (1, 2, 3):
            p = os.path.join(BASE, 'outputs', f'{kind}_seed{seed}', 'colour.png')
            if os.path.exists(p):
                tiles.append(labelled(open_rgb(p), f'{title}, seed {seed}', 640))
    if tiles:
        save(grid(tiles, 3), 'seeds.jpg')


def maps_sheet():
    d = os.path.join(BASE, 'outputs', 'main_seed1')
    names = [('colour (new)', 'colour.png'), ('height (new)', 'height.png'), ('roughness (new)', 'roughness.png'), ('normal (new, from the height, strength 8)', 'normal.png')]
    tiles = [labelled(open_rgb(os.path.join(d, f)), t, 600) for t, f in names if os.path.exists(os.path.join(d, f))]
    refs = [('colour (uploaded)', 'colour.png'), ('height (uploaded)', 'height_as_uploaded.png'), ('(no uploaded roughness map)', None), ('normal (uploaded, OpenGL)', 'normal.png')]
    for t, f in refs:
        if f is None:
            tiles.append(Image.new('RGB', (600, 634), (200, 200, 200)))
        else:
            tiles.append(labelled(open_rgb(os.path.join(REF, f)), t, 600))
    if len(tiles) == 8:
        save(grid(tiles, 4), 'maps.jpg')


def area_sheets():
    for name, out, size in (('area_4x4', 'area_4x4.jpg', 1600), ('area_2x2', 'area_2x2.jpg', 1600)):
        p = os.path.join(BASE, 'area', name, 'colour.png')
        if os.path.exists(p) or os.path.exists(p[:-4] + '.jpg'):
            im = open_rgb(p).resize((size, size), Image.LANCZOS)
            save(im, out, 1700)


def crops_sheet():
    names = [f for f in sorted(os.listdir(os.path.join(BASE, 'area'))) if f.startswith('crop_')] if os.path.isdir(os.path.join(BASE, 'area')) else []
    tiles = []
    for f in names:
        p = os.path.join(BASE, 'area', f, 'colour.png')
        if os.path.exists(p) or os.path.exists(p[:-4] + '.jpg'):
            im = open_rgb(p).crop((177, 177, 1077, 1077))            # the middle 900 x 900 dots, one dot = one picture dot
            info = json.load(open(os.path.join(BASE, 'area', f, 'job.json')))['params']['window']
            tiles.append(labelled(im, f'{f}: window {info} tiles, 1 dot = 1 dot', 900))
    if tiles:
        save(grid(tiles, 2), 'area_crops.jpg', 1900)


def seam_sheet():
    p = os.path.join(BASE, 'area', 'tile_repeated_2x2', 'colour.png')
    if not os.path.exists(p) and not os.path.exists(p[:-4] + '.jpg'):
        return
    im = open_rgb(p)
    n = im.size[0] // 2
    d = ImageDraw.Draw(im)
    for k in (n,):
        d.line([(k, 0), (k, 40)], fill=(255, 255, 0), width=4)
        d.line([(k, im.size[1] - 40), (k, im.size[1])], fill=(255, 255, 0), width=4)
        d.line([(0, k), (40, k)], fill=(255, 255, 0), width=4)
        d.line([(im.size[0] - 40, k), (im.size[0], k)], fill=(255, 255, 0), width=4)
    src = np.asarray(Image.open(os.path.join(REF, 'colour.png')).convert('RGB'))
    plain = Image.fromarray(np.tile(src, (2, 2, 1)))
    d2 = ImageDraw.Draw(plain)
    for k in (1254,):
        d2.line([(k, 0), (k, 40)], fill=(255, 255, 0), width=4)
        d2.line([(k, plain.size[1] - 40), (k, plain.size[1])], fill=(255, 255, 0), width=4)
        d2.line([(0, k), (40, k)], fill=(255, 255, 0), width=4)
        d2.line([(plain.size[0] - 40, k), (plain.size[0], k)], fill=(255, 255, 0), width=4)
    # close-ups of the tile corner of both (400 x 400 dots around the centre)
    c = n
    new_close = im.crop((c - 200, c - 200, c + 200, c + 200))
    old_close = plain.crop((1254 - 200, 1254 - 200, 1254 + 200, 1254 + 200))
    tiles = [labelled(im, 'NEW default tile repeated 2 x 2 (yellow ticks = tile lines)', 800), labelled(plain, 'the uploaded colour map repeated 2 x 2 (it does not wrap)', 800),
             labelled(new_close, 'new tile: the tile corner, 400 x 400 dots', 800), labelled(old_close, 'uploaded map: the corner, 400 x 400 dots', 800)]
    save(grid(tiles, 2), 'seam_2x2.jpg', 1700)


def lit_sheet():
    d = os.path.join(BASE, 'sheets', 'lit_parts')
    files = [('lit_reference_full.png', 'reference, lit from the upper left'), ('lit_new_full.png', 'new MAIN tile, same light'),
             ('lit_reference_zoom.png', 'reference, close-up'), ('lit_new_zoom.png', 'new MAIN tile, close-up')]
    if not all(os.path.exists(os.path.join(d, f)) for f, _ in files):
        return
    save(grid([labelled(open_rgb(os.path.join(d, f)), t, 900) for f, t in files], 2), 'lit.jpg', 1900)


def sweep_sheets():
    """One row of three pictures per control (values left to right), from variations/sweep_*."""
    sets = [('sweep_boards_per_row.jpg', 'layout.boards_per_row', 'boards_per_row', [2, 3, 4]),
            ('sweep_stains_amount.jpg', 'stains.amount (chance per cell for a stain stamp)', 'stains_amount', [0.0, 0.18, 0.5]),
            ('sweep_joined_share.jpg', 'layout.joined_share (pairs of boards joined into one)', 'joined_share', [0.0, 0.5, 1.0]),
            ('sweep_knot_share.jpg', 'windows.knot_share', 'knot_share', [0.0, 0.12, 0.5]),
            ('sweep_patches.jpg', 'large soft patches (masks.blotch_amount / drift_amount)', 'patches', ['none', 'default', 'strong']),
            ('sweep_rows_zoom_joints.jpg', 'rows_per_tile 4 / 6, windows.zoom 0 / 0.2, joints.width 2 / 9', None, None)]
    for out, title, key, values in sets:
        tiles = []
        if key is None:
            for name, label in (('rows_per_tile_4', 'layout.rows_per_tile = 4'), ('rows_per_tile_6', 'layout.rows_per_tile = 6'), ('zoom_0.0', 'windows.zoom = 0'),
                                ('zoom_0.2', 'windows.zoom = 0.2'), ('joint_width_2.0', 'joints.width = 2'), ('joint_width_9.0', 'joints.width = 9')):
                p = os.path.join(BASE, 'variations', 'sweep_' + name, 'colour.png')
                if os.path.exists(p):
                    tiles.append(labelled(open_rgb(p), label, 640))
            if tiles:
                save(grid(tiles, 3), out, 1950)
            continue
        for v in values:
            p = os.path.join(BASE, 'variations', f'sweep_{key}_{v}', 'colour.png')
            if os.path.exists(p):
                tiles.append(labelled(open_rgb(p), f'{title.split(" (")[0]} = {v}', 640))
        if tiles:
            save(grid(tiles, 3), out, 1950)


if __name__ == '__main__':
    todo = sys.argv[1:] or ['wood', 'seeds', 'maps', 'area', 'crops', 'seam', 'lit', 'sweeps']
    for name in todo:
        {'wood': wood_sheet, 'seeds': seeds_sheet, 'maps': maps_sheet, 'area': area_sheets, 'crops': crops_sheet, 'seam': seam_sheet, 'lit': lit_sheet, 'sweeps': sweep_sheets}[name]()

# What this does (plain words): puts the finished pictures of round 2 of the wood-from-maps recipe side by side on labelled sheets (JPEG, for looking at), in sheets/.
# It uses the picture helpers of tools/make_sheets.py (round 1) and makes:
#   wood_sheet.jpg      reference | round 1 MAIN | round 2 MAIN | round 2 COMPARISON, with a row of 400 x 400 close-ups below
#   before_after.jpg    the 4 x 4 area as one picture: the plain uploaded map repeated | round 1 | round 2 (same size, same shrinking), and a 2 x 2 tile close-up of each
#   seeds.jpg, maps.jpg, area_4x4.jpg, area_2x2.jpg, area_crops.jpg, seam_2x2.jpg, lit.jpg
#   sweep_*.jpg         one row of three pictures per control
#   steps_round2.jpg    how the arrangement changed during round 2 (pictures kept in sheets/development/)
# Use: python3 -I tools/make_sheets_round2.py [name ...]     (no name = every sheet whose pictures exist)
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_sheets as ms  # noqa: E402  (round 1 helpers; nothing runs on import)

BASE, REF, SHEETS = ms.BASE, ms.REF, ms.SHEETS
labelled, grid, save, open_rgb = ms.labelled, ms.grid, ms.save, ms.open_rgb


def exists(path):
    return os.path.exists(path) or (path.endswith('.png') and os.path.exists(path[:-4] + '.jpg'))


def wood_sheet():
    sources = [('reference (the uploaded colour map)', os.path.join(REF, 'colour.png')),
               ('round 1 MAIN (seed 1)', os.path.join(BASE, 'round1', 'pictures', 'tile_main_seed1_colour.jpg')),
               ('round 2 MAIN (colour map, seed 1)', os.path.join(BASE, 'outputs', 'main_seed1', 'colour.png')),
               ('round 2 COMPARISON (colour from height, seed 1)', os.path.join(BASE, 'outputs', 'comparison_seed1', 'colour.png'))]
    if not all(exists(p) for _, p in sources):
        return
    ims = [(t, open_rgb(p)) for t, p in sources]
    top = grid([labelled(im, t, 480) for t, im in ims], 4)
    crops = [labelled(im.crop((420, 230, 820, 630)).resize((400, 400)), 'close-up 400 x 400 dots', 400) for t, im in ims]
    row = grid(crops, 4, gap=88)
    sheet = Image.new('RGB', (max(top.size[0], row.size[0]), top.size[1] + row.size[1] + 16), (255, 255, 255))
    sheet.paste(top, (0, 0))
    sheet.paste(row, (0, top.size[1] + 16))
    save(sheet, 'wood_sheet.jpg')


def before_after():
    new = os.path.join(BASE, 'area', 'area_4x4', 'colour.png')
    old = os.path.join(BASE, 'round1', 'area_4x4', 'colour.jpg')
    if not (exists(new) and exists(old)):
        return
    size = 800
    ref = Image.open(os.path.join(REF, 'colour.png')).convert('RGB').resize((size // 4, size // 4), Image.LANCZOS)
    plain = Image.new('RGB', (size, size))
    for i in range(4):
        for j in range(4):
            plain.paste(ref, (i * size // 4, j * size // 4))
    a_old, a_new = open_rgb(old), open_rgb(new)
    top = grid([labelled(plain, 'the uploaded map repeated 4 x 4 (what to get away from)', size), labelled(a_old.resize((size, size), Image.LANCZOS), 'round 1: 4 x 4 area', size),
                labelled(a_new.resize((size, size), Image.LANCZOS), 'round 2: 4 x 4 area', size)], 3)
    # the same piece (2 x 2 tiles at the top left) at one dot = one dot / 2: round 1 and round 2
    k = 700
    pieces = [labelled(plain.resize((size * 2, size * 2), Image.LANCZOS).crop((0, 0, 1600 // 2, 1600 // 2)).resize((k, k)), 'plain repeat, 2 x 2 tiles', k),
              labelled(a_old.crop((0, 0, a_old.size[0] // 2, a_old.size[0] // 2)).resize((k, k), Image.LANCZOS), 'round 1, 2 x 2 tiles', k),
              labelled(a_new.crop((0, 0, a_new.size[0] // 2, a_new.size[0] // 2)).resize((k, k), Image.LANCZOS), 'round 2, 2 x 2 tiles', k)]
    row = grid(pieces, 3, gap=(top.size[0] - 3 * k) // 2)
    sheet = Image.new('RGB', (top.size[0], top.size[1] + row.size[1] + 12), (255, 255, 255))
    sheet.paste(top, (0, 0))
    sheet.paste(row, (0, top.size[1] + 12))
    save(sheet, 'before_after.jpg', 2400)


def seeds_sheet():
    tiles = []
    for kind, title in (('main', 'MAIN'), ('comparison', 'COMPARISON')):
        for seed in (1, 2, 3):
            p = os.path.join(BASE, 'outputs', f'{kind}_seed{seed}', 'colour.png')
            if exists(p):
                tiles.append(labelled(open_rgb(p), f'{title}, seed {seed}', 640))
    if tiles:
        save(grid(tiles, 3), 'seeds.jpg')


def maps_sheet():
    d = os.path.join(BASE, 'outputs', 'main_seed1')
    names = [('colour (new)', 'colour.png'), ('height (new)', 'height.png'), ('roughness (new)', 'roughness.png'), ('normal (new, from the height, strength 8)', 'normal.png')]
    tiles = [labelled(open_rgb(os.path.join(d, f)), t, 600) for t, f in names if os.path.exists(os.path.join(d, f))]
    refs = [('colour (uploaded)', 'colour.png'), ('height (uploaded)', 'height_as_uploaded.png'), ('(no uploaded roughness map)', None), ('normal (uploaded, OpenGL)', 'normal.png')]
    for t, f in refs:
        tiles.append(Image.new('RGB', (600, 634), (200, 200, 200)) if f is None else labelled(open_rgb(os.path.join(REF, f)), t, 600))
    if len(tiles) == 8:
        save(grid(tiles, 4), 'maps.jpg')


def area_sheets():
    for name, out, size in (('area_4x4', 'area_4x4.jpg', 1600), ('area_2x2', 'area_2x2.jpg', 1600)):
        p = os.path.join(BASE, 'area', name, 'colour.png')
        if exists(p):
            save(open_rgb(p).resize((size, size), Image.LANCZOS), out, 1700)


def crops_sheet():
    names = [f for f in sorted(os.listdir(os.path.join(BASE, 'area'))) if f.startswith('crop_')] if os.path.isdir(os.path.join(BASE, 'area')) else []
    tiles = []
    for f in names:
        p = os.path.join(BASE, 'area', f, 'colour.png')
        if exists(p):
            im = open_rgb(p).crop((177, 177, 1077, 1077))            # the middle 900 x 900 dots, one dot = one picture dot
            info = json.load(open(os.path.join(BASE, 'area', f, 'job.json')))['params']['window']
            tiles.append(labelled(im, f'{f}: window {info} tiles, 1 dot = 1 dot', 900))
    if tiles:
        save(grid(tiles, 2), 'area_crops.jpg', 1900)


def seam_sheet():
    p = os.path.join(BASE, 'area', 'tile_repeated_2x2', 'colour.png')
    if not exists(p):
        return
    im = open_rgb(p)
    n = im.size[0] // 2
    d = ImageDraw.Draw(im)
    d.line([(n, 0), (n, 40)], fill=(255, 255, 0), width=4)
    d.line([(n, im.size[1] - 40), (n, im.size[1])], fill=(255, 255, 0), width=4)
    d.line([(0, n), (40, n)], fill=(255, 255, 0), width=4)
    d.line([(im.size[0] - 40, n), (im.size[0], n)], fill=(255, 255, 0), width=4)
    src = np.asarray(Image.open(os.path.join(REF, 'colour.png')).convert('RGB'))
    plain = Image.fromarray(np.tile(src, (2, 2, 1)))
    d2 = ImageDraw.Draw(plain)
    d2.line([(1254, 0), (1254, 40)], fill=(255, 255, 0), width=4)
    d2.line([(1254, plain.size[1] - 40), (1254, plain.size[1])], fill=(255, 255, 0), width=4)
    d2.line([(0, 1254), (40, 1254)], fill=(255, 255, 0), width=4)
    d2.line([(plain.size[0] - 40, 1254), (plain.size[0], 1254)], fill=(255, 255, 0), width=4)
    c = n
    new_close = im.crop((c - 200, c - 200, c + 200, c + 200))
    old_close = plain.crop((1254 - 200, 1254 - 200, 1254 + 200, 1254 + 200))
    tiles = [labelled(im, 'NEW default tile repeated 2 x 2 (yellow ticks = tile lines)', 800), labelled(plain, 'the uploaded colour map repeated 2 x 2 (it does not wrap)', 800),
             labelled(new_close, 'new tile: the tile corner, 400 x 400 dots (2 x 2 picture shrunk 2x: 200 x 200)', 800), labelled(old_close, 'uploaded map: the corner, 400 x 400 dots', 800)]
    save(grid(tiles, 2), 'seam_2x2.jpg', 1700)


def lit_sheet():
    d = os.path.join(SHEETS, 'lit_parts')
    files = [('lit_reference_full.png', 'reference, lit from the upper left'), ('lit_new_full.png', 'new MAIN tile, same light'),
             ('lit_reference_zoom.png', 'reference, close-up'), ('lit_new_zoom.png', 'new MAIN tile, close-up'),
             ('lit_new_zoom_b.png', 'new MAIN tile, another close-up')]
    files = [(f, t) for f, t in files if os.path.exists(os.path.join(d, f))]
    if len(files) < 4:
        return
    save(grid([labelled(open_rgb(os.path.join(d, f)), t, 900) for f, t in files], 2), 'lit.jpg', 1900)


def sweep_sheets():
    sets = [('sweep_boards_per_row.jpg', 'layout.boards_per_row', 'boards_per_row', [2, 3, 4]),
            ('sweep_step_share.jpg', 'joints.step_share (chance that a joint has a step)', 'step_share', [0, 0.7, 1]),
            ('sweep_landmarks.jpg', 'landmarks (knots, zigzags, splinters)', 'landmarks', ['all_painted_out', 'default', 'all_shown']),
            ('sweep_warp.jpg', 'windows.warp_* and windows.tilt (bending of the windows)', 'warp', ['none', 'default', 'strong']),
            ('sweep_row_height.jpg', 'layout.row_height_variation', 'row_height', [0, 0.2, 0.35])]
    for out, title, key, values in sets:
        tiles = []
        for v in values:
            p = os.path.join(BASE, 'variations', f'sweep_{key}_{v}', 'colour.png')
            if exists(p):
                tiles.append(labelled(open_rgb(p), f'{title.split(" (")[0]} = {v}', 640))
        if tiles:
            save(grid(tiles, 3), out, 1950)


def steps_sheet():
    d = os.path.join(SHEETS, 'development')
    files = [('round 1 (3 boards per row, straight joints)', os.path.join(BASE, 'round1', 'pictures', 'tile_main_seed1_colour.jpg')),
             ('round 2, first try: 2 boards per row, rows differ in height', os.path.join(d, 'step1_first_try.jpg')),
             ('round 2, stepped joints (one step per joint)', os.path.join(d, 'step2_stepped_joints.jpg')),
             ('round 2, final: faint and strong joints, tone per row', os.path.join(BASE, 'outputs', 'main_seed1', 'colour.png'))]
    if not all(os.path.exists(p) or exists(p) for _, p in files):
        return
    save(grid([labelled(open_rgb(p), t, 600) for t, p in files], 4), 'steps_round2.jpg', 2400)


if __name__ == '__main__':
    todo = sys.argv[1:] or ['wood', 'before', 'seeds', 'maps', 'area', 'crops', 'seam', 'lit', 'sweeps', 'steps']
    for name in todo:
        {'wood': wood_sheet, 'before': before_after, 'seeds': seeds_sheet, 'maps': maps_sheet, 'area': area_sheets, 'crops': crops_sheet, 'seam': seam_sheet, 'lit': lit_sheet,
         'sweeps': sweep_sheets, 'steps': steps_sheet}[name]()

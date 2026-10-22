"""Builds the sheets for the person (before / after next to the concept followed). Run with plain python (PIL).
   python3 make_sheets.py FINAL_DIR   (FINAL_DIR holds roof_hero.png, roof_veranda.png, final__cam*.jpg downloaded from the store)"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/'
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/31 Japanese garden character - pictures/'
FIN = sys.argv[1]
R = G + 'character/roof/'
os.makedirs(OUT, exist_ok=True)
F = ImageFont.load_default(size=26)
FS = ImageFont.load_default(size=20)
BG = (36, 34, 40)
FG = (236, 228, 214)

hb = Image.open(G + 'fix/out/final/real_hero.png').convert('RGB')
vb = Image.open(G + 'fix/out/final/real_veranda.png').convert('RGB')
ha = Image.open(FIN + '/roof_hero.png').convert('RGB')
va = Image.open(FIN + '/roof_veranda.png').convert('RGB')
concept = lambda n: Image.open(G + 'character/concept/gen/' + n).convert('RGB')


def crop(im, b):
    return im.crop(b)


def labelled(im, text, w=None):
    if w and im.width != w:
        im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    c = Image.new('RGB', (im.width, im.height + 34), BG)
    c.paste(im, (0, 34))
    ImageDraw.Draw(c).text((8, 4), text, font=FS, fill=FG)
    return c


def sheet(panels_rows, title, path, width=1900, gap=14, note=None, maxkb=395):
    rows = []
    for row in panels_rows:
        h = max(p.height for p in row)
        tw = sum(p.width for p in row) + gap * (len(row) - 1)
        rows.append((row, h, tw))
    W = max(tw for _, _, tw in rows) + 2 * gap
    H = 52 + sum(h for _, h, _ in rows) + gap * (len(rows) + 1) + (44 if note else 0)
    S = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(S)
    d.text((gap, 10), title, font=F, fill=FG)
    y = 52
    for row, h, tw in rows:
        x = gap
        for p in row:
            S.paste(p, (x, y))
            x += p.width + gap
        y += h + gap
    if note:
        d.text((gap, y), note, font=FS, fill=(200, 190, 175))
    if W > width:
        S = S.resize((width, int(H * width / W)), Image.LANCZOS)
    q = 88
    while True:
        S.save(path, quality=q, optimize=True)
        if os.path.getsize(path) <= maxkb * 1000 or q <= 40:
            break
        q -= 4
        if q < 60 and S.width > 1500:
            S = S.resize((int(S.width * 0.92), int(S.height * 0.92)), Image.LANCZOS)
    print(path, S.size, os.path.getsize(path) // 1000, 'KB q', q)


# ---------------------------------------------------------------- 1 roof
roof_box = (360, 192, 1800, 640)
cr = concept('sheet_roof.jpg').crop((440, 170, 2420, 1470))
cr = cr.resize((420, int(cr.height * 420 / cr.width)), Image.LANCZOS)
sheet([[labelled(crop(hb, roof_box), 'BEFORE: the roof as it was (hero camera, 100 percent)'), labelled(cr, 'concept followed: sheet_roof')],
       [labelled(crop(ha, roof_box), 'AFTER: tiles of different tone, slipped, chipped, cracked and missing ones, moss, lichen, drip stains, ridge cap, eave discs')]],
      '31 Roof - tiles with character, same art style', OUT + '31 Roof - roof before and after.jpg',
      note='Detail energy of the roof box 8.0 to 8.9 (limit 10). Value range and saturation unchanged.')

# ---------------------------------------------------------------- 2 walls
wall_box = (1488, 288, 2352, 880)
cam_b = lambda n: Image.open(R + 'previews/r5/before__cam%d.jpg' % n).convert('RGB')
cam_a = lambda n: Image.open(FIN + '/final__cam%d.jpg' % n).convert('RGB')
cp = concept('sw_plaster.jpg').resize((330, 330), Image.LANCZOS)
sheet([[labelled(crop(hb, wall_box), 'BEFORE: wall and cap'), labelled(crop(ha, wall_box), 'AFTER: loss patches, hairline cracks, drip streaks, stone footing, chipped cap'),],
       [labelled(cam_b(3), 'BEFORE (3 m from the wall)', 620), labelled(cam_a(3), 'AFTER (3 m from the wall)', 620), labelled(cp, 'concept: sw_plaster', 330)]],
      '31 Roof - plaster walls and caps', OUT + '31 Roof - walls and caps.jpg',
      note='Wall box detail energy 3.4 to 3.5 (limit 4.7). Loss patches are real dents; cracks are thin dark ribbons.')

# ---------------------------------------------------------------- 3 rocks and lantern
ver_rocks = (1680, 640, 2160, 1200)
ver_lant = (288, 400, 960, 1120)
pond = concept('sheet_pond.jpg').crop((1011, 253, 2338, 960))
pond = pond.resize((520, int(pond.height * 520 / pond.width)), Image.LANCZOS)
lan = concept('sheet_lantern.jpg').crop((240, 80, 1110, 1600))
lan = lan.resize((330, int(lan.height * 330 / lan.width)), Image.LANCZOS)
sheet([[labelled(crop(vb, ver_rocks), 'BEFORE: rocks'), labelled(crop(va, ver_rocks), 'AFTER: one soft moss cap on each'), labelled(pond, 'concept: sheet_pond', 520)],
       [labelled(crop(vb, ver_lant), 'BEFORE: lantern'), labelled(crop(va, ver_lant), 'AFTER: cracks, chipped cap, moss'), labelled(lan, 'concept: sheet_lantern', 330)]],
      '31 Roof - rocks and lantern', OUT + '31 Roof - rocks and lantern.jpg',
      note='Rock box detail energy 3.6 to 3.9 (limit 5.0). The lantern window glow is untouched (same colour and strength).')

# ---------------------------------------------------------------- 4 tile close-up
sheet([[labelled(cam_b(2), 'BEFORE: roof from a ladder', 880), labelled(cam_a(2), 'AFTER: same view', 880)]],
      '31 Roof - tile variety close up', OUT + '31 Roof - tile variety close up.jpg',
      note='Every tile has its own tone; slipped, chipped, cracked and missing tiles; moss in the valleys; pale lichen flecks; a few leaves.')

# ---------------------------------------------------------------- 5 hero and veranda after
h = ha.resize((960, 640), Image.LANCZOS)
v = va.resize((960, 640), Image.LANCZOS)
sheet([[labelled(h, 'hero camera, after'), labelled(v, 'veranda camera, after')]], '31 Roof - the two pictures after the roof builder',
      OUT + '31 Roof - hero and veranda after.jpg', note='512 samples, 2400 x 1600 originals; shown at 40 percent.')

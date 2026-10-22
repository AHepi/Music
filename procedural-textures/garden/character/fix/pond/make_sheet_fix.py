# makes "31 Fix - pond - before and after.jpg": per row: integrated final now | after the pond fix | the concept followed (same view)
import sys, os
from PIL import Image, ImageDraw, ImageFont
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character'
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/31 Japanese garden character - pictures/31 Fix - pond - before and after.jpg'
NOW, AFT, CON = G + '/fix/pond/out/now/', G + '/fix/pond/out/finals/small/', G + '/concept/gen/'
CELL_W = int(sys.argv[1]) if len(sys.argv) > 1 else 580
Q = int(sys.argv[2]) if len(sys.argv) > 2 else 66


def cover(im, aspect, box=None):
    """crop (optionally to `box`, given in the displayed 2000-wide coordinates of the concept images) to `aspect` (w/h) around the centre"""
    w, h = im.size
    if box is not None:
        sx = w / 2000.0
        box = tuple(int(v * sx) for v in box)
        im = im.crop(box)
        w, h = im.size
    if w / h > aspect:
        nw = int(h * aspect); x0 = (w - nw) // 2; im = im.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / aspect); y0 = (h - nh) // 2; im = im.crop((0, y0, w, y0 + nh))
    return im


def L(p):
    return Image.open(p).convert('RGB')


rows = [
    ('Hero view (1200 px wide)', 1.5, L(NOW + 'now_hero_1200.jpg'), L(AFT + 'final_hero_1200.jpg'), L(CON + 'hero_A2_posts_nb2.jpg'), None),
    ('Veranda view (1200 px wide)', 1.5, L(NOW + 'now_veranda_1200.jpg'), L(AFT + 'final_veranda_1200.jpg'), L(CON + 'veranda_V2_nb2.jpg'), None),
    ('Pond seen from the hero camera, 100 percent crop', 1560 / 560.0, L(NOW + 'now_hero_crop_pond.jpg'), L(AFT + 'final_hero_crop_pond.jpg'), L(CON + 'hero_A2_posts_nb2.jpg'), (0, 867, 1300, 1334)),
    ('Pond close-up (camera pond Q1) next to the pond concept sheet', 1.5, L(G + '/final/out/finals/small/close_pond_1600.jpg'), L(AFT + 'close_pond_1200.jpg'), L(CON + 'sheet_pond.jpg'), (100, 90, 1800, 1223)),
    ('Maple, veranda camera, 100 percent crop', 2.0, L(NOW + 'now_veranda_crop_maple.jpg'), L(AFT + 'final_veranda_crop_maple.jpg'), L(CON + 'veranda_V2_nb2.jpg'), (900, 40, 1800, 490)),
    ('Maple, hero camera: the branches in the gaps, 100 percent crop', 1.25, L(NOW + 'now_hero_crop_maple.jpg'), L(AFT + 'final_hero_crop_maple.jpg'), L(CON + 'sheet_trees.jpg'), (20, 100, 1100, 965)),
    ('Pine, hero camera, 100 percent crop', 1.55, L(NOW + 'now_hero_crop_pine.jpg'), L(AFT + 'final_hero_crop_pine.jpg'), L(CON + 'sheet_trees.jpg'), (1190, 70, 1900, 530)),
]
try:
    F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
    FB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 15)
except Exception:
    F = FB = ImageFont.load_default()
gap, lab = 6, 22
W = CELL_W * 3 + gap * 2
panels = []
H = 30
for (title, asp, a, b, c, cbox) in rows:
    ch = int(CELL_W / asp)
    panels.append((title, ch))
    H += lab + ch + gap
sheet = Image.new('RGB', (W, H), (24, 22, 26))
d = ImageDraw.Draw(sheet)
d.text((6, 6), 'Pond fix round: the integrated final now (left), after the fix (middle), the concept it follows (right)', fill=(235, 225, 215), font=FB)
y = 30
for (title, asp, a, b, c, cbox), (_, ch) in zip(rows, panels):
    d.text((6, y + 3), title, fill=(200, 190, 180), font=F)
    y += lab
    for i, (im, bx) in enumerate(((a, None), (b, None), (c, cbox))):
        p = cover(im, asp, bx).resize((CELL_W, ch), Image.LANCZOS)
        sheet.paste(p, (i * (CELL_W + gap), y))
    y += ch + gap
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sheet.save(OUT, quality=Q, optimize=True, progressive=True)
print(sheet.size, os.path.getsize(OUT))

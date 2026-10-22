"""make_sheet_fix.py - builds '31 Fix - wood - before and after.jpg': integrated final now | after the wood fix | the concept we followed, same views."""
import os
from PIL import Image, ImageDraw, ImageFont
B = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
CH = B + 'garden/character/'
FX = CH + 'fix/wood/previews/'
INT = CH + 'final/out/finals/small/'
CON = CH + 'concept/gen/'
OUT = B + '31 Japanese garden character - pictures/31 Fix - wood - before and after.jpg'
CW, CHh = 470, 313
GAP = 8
def font(sz, bold=False):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
def cover(path, box=None):
    im = Image.open(path).convert('RGB')
    if box:
        im = im.crop(box)
    w, h = im.size
    s = max(CW / w, CHh / h)
    im = im.resize((int(w * s + 0.5), int(h * s + 0.5)), Image.LANCZOS)
    x0, y0 = (im.size[0] - CW) // 2, (im.size[1] - CHh) // 2
    return im.crop((x0, y0, x0 + CW, y0 + CHh))
rows = [
    ('Hero view, the bridge', INT + 'final_hero_crop_bridge.jpg', FX + 'rI/small/hero_crop_bridge.jpg', (CON + 'hero_A2_posts_nb2.jpg', (0, 1100, 1700, 1640))),
    ('Close-up from the west bank', INT + 'close_bridge_1600.jpg', FX + 'rI/small/close_bridge_1600.jpg', (CON + 'hero_V3_nb2.jpg', (0, 1270, 1750, 1686))),
    ('From above, at the two turns', FX + 'rJ/int_cam4_top.jpg', FX + 'rI/F__cam4_top.jpg', (CON + 'sheet_bridge.jpg', (200, 620, 2340, 1280))),
    ('One plank close up (knot, peg, grain)', FX + 'rJ/int_cam6_macro.jpg', FX + 'rI/F__cam6_macro.jpg', (CON + 'sheet_plank2.jpg', (1040, 30, 2000, 640))),
    ('Posts and footing stones at the water', FX + 'rJ/int_cam11_posts.jpg', FX + 'rI/F__cam11_posts.jpg', (CON + 'sheet_bridge.jpg', (110, 130, 1900, 470))),
    ('Veranda deck', INT + 'final_veranda_crop_deck.jpg', FX + 'rI/small/veranda_crop_deck.jpg', (CON + 'veranda_B_nb2.jpg', (1500, 780, 2528, 1686))),
    ('Foot of the veranda steps', FX + 'rJ/int_cam10_stepfoot.jpg', FX + 'rI/F__cam10_stepfoot.jpg', None),
]
W = 3 * CW + 4 * GAP
H = 54 + len(rows) * (CHh + 24 + GAP) + GAP
sheet = Image.new('RGB', (W, H), (24, 22, 26))
d = ImageDraw.Draw(sheet)
for i, t in enumerate(('integrated final (before this round)', 'after the wood fix', 'the concept picture we followed')):
    d.text((GAP + i * (CW + GAP), 8), t, fill=(240, 232, 220), font=font(16, True))
d.text((GAP, 30), 'same views, wood only: moss and mould, knots, closed corners, bigger pegs, footing stones', fill=(190, 182, 172), font=font(12))
y = 54
for label, a, b, c in rows:
    d.text((GAP, y + 3), label, fill=(255, 214, 120), font=font(13, True))
    y += 24
    sheet.paste(cover(a), (GAP, y))
    sheet.paste(cover(b), (GAP + CW + GAP, y))
    if c:
        sheet.paste(cover(c[0], c[1]), (GAP + 2 * (CW + GAP), y))
    else:
        d.rectangle((GAP + 2 * (CW + GAP), y, GAP + 2 * (CW + GAP) + CW, y + CHh), outline=(70, 66, 72))
        d.text((GAP + 2 * (CW + GAP) + 14, y + CHh // 2 - 8), 'no concept picture for the steps', fill=(150, 144, 136), font=font(13))
    y += CHh + GAP
q = 80
while True:
    sheet.save(OUT, quality=q, optimize=True)
    sz = os.path.getsize(OUT)
    if sz < 395000 or q <= 40:
        break
    q -= 4
print('saved', OUT, sheet.size, sz, 'quality', q)

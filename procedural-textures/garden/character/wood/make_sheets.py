"""make_sheets.py - the pictures for the person (31 Wood - ...). Plain python3 + PIL. Usage: python3 make_sheets.py PREVIEW_DIR"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
W = os.path.dirname(os.path.abspath(__file__))
P = sys.argv[1] if len(sys.argv) > 1 else os.path.join(W, 'previews', 'r9')
G = os.path.dirname(W)                       # .../garden/character
CONC = os.path.join(G, 'concept', 'gen')
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/31 Japanese garden character - pictures'
os.makedirs(OUT, exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BG = (34, 32, 36)
INK = (236, 228, 216)

def font(sz, bold=False):
    return ImageFont.truetype(FB if bold else FONT, sz)

def fit(im, w=None, h=None):
    if w and not h:
        return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    if h and not w:
        return im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    return im.resize((w, h), Image.LANCZOS)

def label(canvas, xy, text, sz=26, bold=True, fill=INK, bg=None):
    d = ImageDraw.Draw(canvas)
    f = font(sz, bold)
    if bg:
        tw = d.textlength(text, font=f)
        d.rectangle((xy[0] - 6, xy[1] - 4, xy[0] + tw + 10, xy[1] + sz + 8), fill=bg)
    d.text(xy, text, font=f, fill=fill)

def save(img, name, limit=395_000):
    path = os.path.join(OUT, name)
    for q in (88, 84, 80, 76, 72, 68, 64):
        img.save(path, quality=q, optimize=True, progressive=True)
        if os.path.getsize(path) < limit:
            break
    print(name, os.path.getsize(path) // 1024, 'KB q', q, img.size)

def op(name):
    return Image.open(os.path.join(P, name)).convert('RGB')

def old(rel):
    return Image.open(os.path.join(W, 'previews', rel)).convert('RGB')

def concept(name, box):
    return Image.open(os.path.join(CONC, name)).convert('RGB').crop(box)

# ---------------------------------------------------------------- 1. how the bridge is built
def sheet_built():
    plan, side = op('diagram__plan.jpg'), op('diagram__side.jpg')
    wd = 1800
    plan = fit(plan, wd); side = fit(side, wd)
    legend = [('footing stone (on the pond bed)', '#7f8c99'), ('post (14 cm, pairs)', '#e3a636'), ('bearer (cross beam)', '#d9584a'), ('stringer (two per run, three at a turn)', '#4b8fc9'),
              ('plank (laid across)', '#d8c3a0'), ('peg', '#f4f4f4'), ('iron cramp', '#1c1c1c'), ('bank sill', '#9a9a9a')]
    H = 90 + plan.height + side.height + 215
    c = Image.new('RGB', (wd, H), BG)
    label(c, (30, 20), 'The bridge, built from the bottom up', 40)
    c.paste(plan, (0, 90))
    label(c, (30, 100), 'seen from above', 24, fill=(40, 40, 40), bg=(240, 236, 228))
    c.paste(side, (0, 90 + plan.height))
    label(c, (30, 100 + plan.height), 'seen from the south (the pond surface is at the bottom of the red bearers)', 24, fill=(235, 235, 235), bg=(40, 40, 44))
    y = 90 + plan.height + side.height + 16
    d = ImageDraw.Draw(c)
    x = 30
    f = font(22)
    for i, (t, col) in enumerate(legend):
        if i == 4:
            x, y = 30, y + 40
        d.rectangle((x, y + 4, x + 26, y + 30), fill=col, outline=(200, 200, 200))
        d.text((x + 36, y + 2), t, font=f, fill=INK)
        x += 36 + int(d.textlength(t, font=f)) + 34
    d.text((30, y + 52), 'Order: stones, posts, bearers pegged to the posts, stringers, planks across (6 to 14 mm gaps).', font=font(20), fill=(200, 192, 182))
    d.text((30, y + 80), 'At each turn the two runs meet on a mitre line: one diagonal board and iron cramps.', font=font(20), fill=(200, 192, 182))
    save(c, '31 Wood - how the bridge is built.jpg')

# ---------------------------------------------------------------- 2. bridge from the south bank
def sheet_south():
    b = old('r1/before__cam3_south.jpg'); a = op('after__cam3_south.jpg'); cc = concept('sheet_bridge.jpg', (140, 170, 2400, 600))
    cw = 900
    b, a = fit(b, cw), fit(a, cw)
    cc = fit(cc, 1800)
    c = Image.new('RGB', (1800, 60 + b.height + cc.height + 50), BG)
    c.paste(b, (0, 60)); c.paste(a, (900, 60))
    label(c, (20, 14), 'Bridge from the south bank: before (planks on thin sticks)', 26)
    label(c, (920, 14), 'after (stones, posts, bearers, stringers, planks)', 26)
    c.paste(cc, (0, 60 + b.height + 40))
    label(c, (20, 60 + b.height + 6), 'The picture we followed for how it is built (side view of the concept sheet)', 24, bold=False)
    save(c, '31 Wood - bridge from the south bank.jpg')

# ---------------------------------------------------------------- 3. plank close-up
def sheet_plank():
    m = op('after__cam6_macro.jpg'); cp = concept('sheet_plank2.jpg', (1330, 30, 2460, 1160))
    h = 720
    m = fit(m, None, h); cp = fit(cp, None, h)
    top = Image.new('RGB', (m.width + cp.width + 10, h + 60), BG)
    top.paste(m, (0, 60)); top.paste(cp, (m.width + 10, 60))
    label(top, (20, 14), 'Plank close-up in the garden (85 mm lens, dusk sun)', 26)
    label(top, (m.width + 30, 14), 'The concept we followed (round edge, peg, split)', 26)
    save(top, '31 Wood - plank close-up.jpg')

# ---------------------------------------------------------------- 4. deck from the steps
def sheet_deck():
    b = old('r2/before__cam7_deck.jpg'); a = op('after__cam7_deck.jpg'); cc = concept('veranda_A_nbpro.jpg', (1500, 700, 2528, 1690))
    cw = 900
    b, a = fit(b, cw), fit(a, cw)
    ph = 560
    cc = fit(cc, None, ph)
    v1 = fit(old('r2/before__veranda_deck.jpg'), None, ph); v2 = fit(op('after__veranda_deck.jpg'), None, ph)
    tot = cc.width + v1.width + v2.width + 20
    c = Image.new('RGB', (1800, 60 + b.height + 60 + ph), BG)
    c.paste(b, (0, 60)); c.paste(a, (900, 60))
    label(c, (20, 14), 'Veranda deck from the steps: before (flat boards)', 26)
    label(c, (920, 14), 'after (boards on joists, butt joints, nosing, worn band)', 26)
    y2 = 60 + b.height + 60
    x = 0
    for im, t in ((cc, 'concept we followed'), (v1, 'veranda camera, before'), (v2, 'veranda camera, after')):
        k = im.width * 1800 / tot
        im2 = im.resize((int(im.width * 1780 / tot), int(im.height * 1780 / tot)), Image.LANCZOS)
        c.paste(im2, (x, y2 + 0))
        label(c, (x + 10, y2 - 44), t, 24, bold=False)
        x += im2.width + 10
    c = c.crop((0, 0, 1800, y2 + int(ph * 1780 / tot) + 4))
    save(c, '31 Wood - deck from the steps.jpg')

# ---------------------------------------------------------------- 5. hero and veranda crops
def sheet_hero():
    b = old('r1/before__hero_bridge.jpg'); a = op('after__hero_bridge.jpg')
    cc = concept('hero_V3_nb2.jpg', (0, 1120, 1700, 1560))
    wd = 1560
    c = Image.new('RGB', (wd, 50 + b.height + 50 + a.height + 50 + int(cc.height * wd / cc.width)), BG)
    y = 0
    label(c, (20, 10), 'Hero camera, the bridge: before', 26); y = 50
    c.paste(b, (0, y)); y += b.height
    label(c, (20, y + 10), 'after', 26); y += 50
    c.paste(a, (0, y)); y += a.height
    label(c, (20, y + 10), 'Concept picture of the right level of wear (not copied, only the level)', 24, bold=False); y += 50
    c.paste(fit(cc, wd), (0, y))
    c = fit(c, 1400)
    save(c, '31 Wood - hero bridge before and after.jpg')

if __name__ == '__main__':
    sheet_built(); sheet_south(); sheet_plank(); sheet_deck(); sheet_hero()

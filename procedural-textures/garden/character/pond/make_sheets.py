# POND BUILDER: builds the pictures for the person (JPG under 400 KB each) from the small JPG previews. Plain words: before / after / concept side by side.
# usage: python3 -I make_sheets.py   (reads previews/final/*.jpg, writes to the "31 Japanese garden character - pictures" folder)
import os
from PIL import Image, ImageDraw, ImageFont

BASE = "/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/"
D = BASE + "garden/character/pond/"
F = D + "previews/final/"
CONCEPT = BASE + "garden/character/concept/gen/"
OUT = BASE + "31 Japanese garden character - pictures/"
os.makedirs(OUT, exist_ok=True)
FONT = ImageFont.load_default(size=26)
FONT_S = ImageFont.load_default(size=20)
BG = (24, 22, 24)


def load(path, width=None, crop=None):
    im = Image.open(path).convert('RGB')
    if crop:
        W, H = im.size
        im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    if width:
        im = im.resize((width, int(round(im.size[1] * width / im.size[0]))), Image.LANCZOS)
    return im


def labelled(im, text, sub=None):
    pad = 40 if not sub else 66
    out = Image.new('RGB', (im.size[0], im.size[1] + pad), BG)
    out.paste(im, (0, pad))
    d = ImageDraw.Draw(out)
    d.text((10, 6), text, fill=(240, 230, 215), font=FONT)
    if sub:
        d.text((10, 38), sub, fill=(190, 180, 170), font=FONT_S)
    return out


def grid(rows, gap=10, bg=BG):
    """rows: list of lists of images; each row is centred, rows are stacked."""
    W = max(sum(i.size[0] for i in r) + gap * (len(r) - 1) for r in rows)
    H = sum(max(i.size[1] for i in r) for r in rows) + gap * (len(rows) + 1)
    out = Image.new('RGB', (W + 2 * gap, H), bg)
    y = gap
    for r in rows:
        x = gap + (W - (sum(i.size[0] for i in r) + gap * (len(r) - 1))) // 2
        for i in r:
            out.paste(i, (x, y))
            x += i.size[0] + gap
        y += max(i.size[1] for i in r) + gap
    return out


def save(im, name, limit=395000):
    path = OUT + name
    for q in (88, 84, 80, 76, 72, 68, 64, 60):
        im.save(path, quality=q, optimize=True)
        if os.path.getsize(path) <= limit:
            break
    print(name, im.size, os.path.getsize(path), 'q', q)


def sheet_full():
    W = 960
    rows = [[labelled(load(F + 'before_hero_1600.jpg', W), 'BEFORE: hero camera'), labelled(load(F + 'A_hero_1600.jpg', W), 'AFTER: hero camera')],
            [labelled(load(F + 'before_veranda_1600.jpg', W), 'BEFORE: veranda camera'), labelled(load(F + 'A_veranda_1600.jpg', W), 'AFTER: veranda camera')]]
    save(grid(rows), '31 Pond - before and after at the hero and veranda cameras.jpg')


def sheet_pond():
    W = 900
    bef = load(F + 'b_hero_pond.jpg', W); aft = load(F + 'a_hero_pond.jpg', W)
    bv = load(F + 'b_ver_pond.jpg', W); av = load(F + 'a_ver_pond.jpg', W)
    conc = load(CONCEPT + 'sheet_pond.jpg', W, crop=(0.18, 0.28, 0.82, 0.92))
    rows = [[labelled(bef, 'BEFORE: pond, hero camera'), labelled(aft, 'AFTER: pond, hero camera')],
            [labelled(bv, 'BEFORE: pond, veranda camera'), labelled(av, 'AFTER: pond, veranda camera')],
            [labelled(conc, 'CONCEPT FOLLOWED (sheet_pond): clear edge, dark middle, notched pads, pink lilies'),
             labelled(load(F + 'A__cam7.jpg', W), 'AFTER: the south shelf, pebbles, a flat stone under water, iris')]]
    save(grid(rows), '31 Pond - the pond before and after next to the concept.jpg')


def sheet_close():
    W = 900
    items = [('A__cam1.jpg', 'water from the south-east bank: ripples, reflections, iris, algae rim'), ('A__cam3.jpg', 'lily pads with a notch, a flower and a ripple ring'),
             ('A__cam4.jpg', 'ripple rings on open water, a red leaf, pebbles under the surface'), ('A__cam2.jpg', 'straight down: shelf, dark middle, pads, bed stones')]
    ims = [labelled(load(F + a, W), 'AFTER: ' + t) for a, t in items]
    save(grid([ims[:2], ims[2:]]), '31 Pond - water, ripples, lilies and iris up close.jpg')


def sheet_maple():
    W = 760
    rows = [[labelled(load(F + 'b_hero_maple.jpg', W), 'BEFORE: maple, hero camera'), labelled(load(F + 'a_hero_maple.jpg', W), 'AFTER: layered pads, same leaves'),
             labelled(load(CONCEPT + 'sheet_trees.jpg', W, crop=(0.01, 0.07, 0.56, 0.74)), 'CONCEPT FOLLOWED (sheet_trees)')],
            [labelled(load(F + 'b_ver_maple.jpg', W), 'BEFORE: maple, veranda camera'), labelled(load(F + 'a_ver_maple.jpg', W), 'AFTER: bent trunk, branches show between pads'),
             labelled(load(F + 'A__cam5.jpg', W), 'AFTER: from the ground, root flare and branches')]]
    save(grid(rows), '31 Trees - maple before and after next to the concept.jpg')


def sheet_pine():
    W = 900
    rows = [[labelled(load(F + 'b_hero_pine.jpg', W), 'BEFORE: pine, hero camera'), labelled(load(F + 'a_hero_pine.jpg', W), 'AFTER: flat discs with a needle fringe, same shadow')],
            [labelled(load(CONCEPT + 'sheet_trees.jpg', 560, crop=(0.58, 0.05, 0.97, 0.74)), 'CONCEPT FOLLOWED (sheet_trees)'),
             labelled(load(F + 'A__cam6.jpg', W), 'AFTER: the crown from the lawn, plated trunk and arms')]]
    save(grid(rows), '31 Trees - pine before and after next to the concept.jpg')


if __name__ == '__main__':
    import sys
    which = sys.argv[1:] or ['full', 'pond', 'close', 'maple', 'pine']
    for w in which:
        {'full': sheet_full, 'pond': sheet_pond, 'close': sheet_close, 'maple': sheet_maple, 'pine': sheet_pine}[w]()

"""make_sheets_final.py - builds the four pictures for the person from the small JPGs downloaded from the card.
usage: python3 -I make_sheets_final.py DIR_WITH_JPGS OUT_DIR
Needs in DIR: hero_1200.jpg, veranda_1200.jpg, close_bridge.jpg, close_eave.jpg, close_pond.jpg, close_grass.jpg (any size >= 800 wide);
before_hero_1200.jpg and before_veranda_1200.jpg come from final/previews; the concept picture is concept/gen/hero_V3_nb2.jpg.
Every sheet is kept under 400 KB (the quality is lowered until it fits)."""
import sys
import os
from PIL import Image, ImageDraw, ImageFont

D, OUT = sys.argv[1], sys.argv[2]
C = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character'
PREV = C + '/final/previews/'
os.makedirs(OUT, exist_ok=True)
BG = (24, 22, 20)


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def fit(im, w):
    im = im.convert('RGB')
    return im.resize((w, int(round(im.size[1] * w / im.size[0]))), Image.LANCZOS)


def label(sheet, x, y, text, size=22):
    d = ImageDraw.Draw(sheet)
    f = font(size)
    d.text((x + 2, y + 1), text, fill=(0, 0, 0), font=f)
    d.text((x, y), text, fill=(236, 230, 220), font=f)


def save(sheet, name, limit=398000):
    path = os.path.join(OUT, name)
    for q in (88, 85, 82, 80, 78, 76, 74, 72, 70, 66, 62):
        sheet.save(path, quality=q, optimize=True, progressive=True)
        if os.path.getsize(path) <= limit:
            break
    print(name, os.path.getsize(path), 'bytes, quality', q, sheet.size)


def side_by_side(left, right, ll, rl, name, pw=1000):
    a, b = fit(Image.open(left), pw), fit(Image.open(right), pw)
    gap, head = 8, 40
    sheet = Image.new('RGB', (2 * pw + gap, max(a.size[1], b.size[1]) + head), BG)
    sheet.paste(a, (0, head))
    sheet.paste(b, (pw + gap, head))
    label(sheet, 12, 8, ll, 24)
    label(sheet, pw + gap + 12, 8, rl, 24)
    save(sheet, name)


have = lambda n: os.path.exists(os.path.join(D, n))
if have('hero_1200.jpg'):
    side_by_side(PREV + 'before_hero_1200.jpg', os.path.join(D, 'hero_1200.jpg'), 'Before (previous final)', 'After (with character)', '31 Before and after - hero view.jpg')
    side_by_side(C + '/concept/gen/hero_V3_nb2.jpg', os.path.join(D, 'hero_1200.jpg'), 'Concept picture (the target)', 'New garden', '31 New next to the concept - hero view.jpg')
if have('veranda_1200.jpg'):
    side_by_side(PREV + 'before_veranda_1200.jpg', os.path.join(D, 'veranda_1200.jpg'), 'Before (previous final)', 'After (with character)', '31 Before and after - veranda view.jpg')
names = [('close_bridge.jpg', 'Bridge from the bank'), ('close_eave.jpg', 'Roof eave'), ('close_pond.jpg', 'Pond edge'), ('close_grass.jpg', 'Grass and moss by the lantern')]
if all(have(n) for n, _ in names):
    pw, gap, head = 790, 6, 0
    ims = [fit(Image.open(os.path.join(D, n)), pw) for n, _ in names]
    ph = max(i.size[1] for i in ims)
    sheet = Image.new('RGB', (2 * pw + gap, 2 * ph + gap), BG)
    for k, (im, (_, lab)) in enumerate(zip(ims, names)):
        x, y = (k % 2) * (pw + gap), (k // 2) * (ph + gap)
        sheet.paste(im, (x, y))
        label(sheet, x + 12, y + 8, lab, 22)
    save(sheet, '31 Close-ups - bridge, roof, pond edge, grass.jpg')

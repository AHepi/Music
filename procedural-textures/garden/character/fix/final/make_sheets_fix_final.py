"""make_sheets_fix_final.py - builds the sheets for the person from the small JPGs downloaded from the card (all under 400 KB).
usage: python3 -I make_sheets_fix_final.py
Names (as in the brief): 31 Final - hero view / veranda view, 31 Before and after - hero view / veranda view (previous final | first integration | after the
fixes), 31 Final - close-ups, 31 Final - next to the concept - hero view, plus one extra: 31 Final - where the squint test loses points."""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

C = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character'
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/31 Japanese garden character - pictures'
NEW = C + '/fix/final/out/finals/small/'
FIRST = C + '/final/out/finals/small/'
PREV = C + '/final/previews/'
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
    q = 90
    for q in (90, 88, 86, 84, 82, 80, 78, 76, 74, 72, 70, 66, 62, 58):
        sheet.save(path, quality=q, optimize=True, progressive=True)
        if os.path.getsize(path) <= limit:
            break
    print(name, os.path.getsize(path), 'bytes, quality', q, sheet.size)


def row_sheet(rows, labels, name, pw=800, gap=6, head=34):
    """rows = list of lists of image paths (3 per row); labels shown on the first row only"""
    ims = [[fit(Image.open(p), pw) for p in r] for r in rows]
    heights = [max(i.size[1] for i in r) for r in ims]
    W = len(rows[0]) * pw + (len(rows[0]) - 1) * gap
    H = head + sum(heights) + gap * (len(rows) - 1)
    sheet = Image.new('RGB', (W, H), BG)
    y = head
    for r, hh in zip(ims, heights):
        for k, im in enumerate(r):
            sheet.paste(im, (k * (pw + gap), y))
        y += hh + gap
    for k, t in enumerate(labels):
        label(sheet, k * (pw + gap) + 10, 6, t, 22)
    save(sheet, name)


# keep the first integration's own before and after sheets (the new ones use the same names)
for a, b in (('31 Before and after - hero view.jpg', '31 First integration - before and after - hero view.jpg'),
             ('31 Before and after - veranda view.jpg', '31 First integration - before and after - veranda view.jpg')):
    pa, pb = os.path.join(OUT, a), os.path.join(OUT, b)
    if os.path.exists(pa) and not os.path.exists(pb):
        os.rename(pa, pb)
        print('kept the old sheet as', b)

LAB = ['Previous final (before the character round)', 'First integration', 'After the fixes']
if os.path.exists(NEW + 'final_hero_1200.jpg'):
    row_sheet([[PREV + 'before_hero_1200.jpg', FIRST + 'final_hero_1200.jpg', NEW + 'final_hero_1200.jpg'],
               [NEW + 'final_hero_crop_bridge_before.jpg', FIRST + 'final_hero_crop_bridge.jpg', NEW + 'final_hero_crop_bridge.jpg']],
              LAB, '31 Before and after - hero view.jpg')
if os.path.exists(NEW + 'final_veranda_1200.jpg'):
    row_sheet([[PREV + 'before_veranda_1200.jpg', FIRST + 'final_veranda_1200.jpg', NEW + 'final_veranda_1200.jpg']],
              LAB, '31 Before and after - veranda view.jpg', pw=840)
# the new finals alone, 1600 px wide
for src, name in (('w_hero_1600.jpg', '31 Final - hero view.jpg'), ('w_veranda_1600.jpg', '31 Final - veranda view.jpg')):
    if os.path.exists(NEW + src):
        im = Image.open(NEW + src).convert('RGB')
        im = im if im.size[0] == 1600 else fit(im, 1600)
        save(im, name)
# close-ups
names = [('close_bridge_1600.jpg', 'Bridge from the bank'), ('close_eave_1600.jpg', 'Roof eave'), ('close_pond_1600.jpg', 'Pond edge'),
         ('close_grass_1600.jpg', 'Grass and moss by the lantern')]
if all(os.path.exists(NEW + n) for n, _ in names):
    pw, gap = 790, 6
    ims = [fit(Image.open(NEW + n), pw) for n, _ in names]
    ph = max(i.size[1] for i in ims)
    sheet = Image.new('RGB', (2 * pw + gap, 2 * ph + gap), BG)
    for k, (im, (_, lab)) in enumerate(zip(ims, names)):
        x, y = (k % 2) * (pw + gap), (k // 2) * (ph + gap)
        sheet.paste(im, (x, y))
        label(sheet, x + 12, y + 8, lab, 22)
    save(sheet, '31 Final - close-ups.jpg')
# next to the concept
pw, gap, head = 1000, 8, 40
a, b = fit(Image.open(C + '/concept/gen/hero_V3_nb2.jpg'), pw), fit(Image.open(NEW + 'final_hero_1200.jpg'), pw)
sheet = Image.new('RGB', (2 * pw + gap, max(a.size[1], b.size[1]) + head), BG)
sheet.paste(a, (0, head))
sheet.paste(b, (pw + gap, head))
label(sheet, 12, 8, 'Concept picture (the target)', 24)
label(sheet, pw + gap + 12, 8, 'The garden after the fixes', 24)
save(sheet, '31 Final - next to the concept - hero view.jpg')
# squint heat maps (extra)
hh = [NEW + 'heat_hero_vs_previous.jpg', NEW + 'heat_veranda_vs_previous.jpg']
if all(os.path.exists(p) for p in hh):
    pw, gap, head = 800, 6, 34
    a, b = fit(Image.open(hh[0]), pw), fit(Image.open(hh[1]), pw)
    sheet = Image.new('RGB', (2 * pw + gap, max(a.size[1], b.size[1]) + head), BG)
    sheet.paste(a, (0, head))
    sheet.paste(b, (pw + gap, head))
    label(sheet, 10, 6, 'Hero: red = where the squint test loses points (12 px blur)', 20)
    label(sheet, pw + gap + 10, 6, 'Veranda: the same', 20)
    save(sheet, '31 Final - where the squint test loses points.jpg')

"""What this file does (plain words): makes the two pictures for the person (JPG, under 400 KB each) from the plate, the no-kit plate and the lined-up painting:
  '25 Painter test - plate and painting.jpg'  : the whole kit plate and the whole painting side by side, same size;
  '25 Painter test - close-ups.jpg'           : six places, each as plate without the kit | plate with the kit | the painting, all cut from the same box at the same size.
Run: python3 -I tools/make_sheets.py"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import crops
OUT = 'proc-work/25 Street grime, cracks, stains, weeds and moss - pictures/'
F = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', n)
FB = lambda n: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', n)
BG, INK, MUTE = (245, 243, 238), (30, 30, 30), (90, 90, 90)
c = crops.load()

def save_under(img, path, limit=395_000):
    for q in (86, 82, 78, 74, 70, 66, 62, 58):
        img.save(path, quality=q, optimize=True, progressive=True)
        if os.path.getsize(path) < limit:
            return q, os.path.getsize(path)
    return None, os.path.getsize(path)

# ---- sheet 1: whole picture
w = 560; h = int(2730 * w / 1536)
head = 60
s1 = Image.new('RGB', (2 * w + 10, h + head), BG)
d = ImageDraw.Draw(s1)
d.text((6, 4), 'THE PLATE (3D picture with the weathering kit)', font=FB(14), fill=INK)
d.text((6, 24), 'what the painter was sent, 1536 x 2730, wet lockout view', font=F(12), fill=MUTE)
d.text((w + 16, 4), 'THE PAINTING (the painter\'s one repaint)', font=FB(14), fill=INK)
d.text((w + 16, 24), 'returned 1520 x 2702, lined up to the plate (it had moved 1 to 3 dots, no stretch)', font=F(12), fill=MUTE)
d.text((w + 16, 42), 'the grey clouds are the painter\'s own again: the brief said none', font=F(12), fill=(150, 50, 40))
s1.paste(c['kit'].resize((w, h), Image.LANCZOS), (0, head))
s1.paste(c['paint'].resize((w, h), Image.LANCZOS), (w + 10, head))
print('sheet 1', save_under(s1, OUT + '25 Painter test - plate and painting.jpg'), s1.size)

# ---- sheet 2: close-ups
rows = [
 ('1  Weeds and moss, left edge of the road', 'every big green clump is kept, in place, as a painted green daub of the same size', (0, 2420, 300, 2700)),
 ('2  Pale grass tufts under the cart', 'the larger tufts stay as pale painted daubs; the smallest ones are gone', (90, 2030, 290, 2160)),
 ('3  Soot and rust on the fire drum', 'the sooty dark top and the rust streaks run on down; the painter makes the drum greyer and lighter', (990, 1800, 1250, 2060)),
 ('4  Rust and washed patches on the right-hand wall', 'orange rust patches by the windows are kept; the pale washed patches fade into the painted stone', (1180, 1160, 1536, 1420)),
 ('5  Near road: wet film, water marks, joints', 'joints stay dark; the wet film turns into painted pale streaks (the painter paints those anyway: weakest match)', (640, 2520, 1100, 2730)),
 ('6  Cracks: a chipped, sooty sett', 'too fine to test here: the kit\'s cracks are 1 to 2 dots wide; this chip was already in the plate', (110, 2540, 330, 2700)),
]
cw = 300; gap = 6; left = 6
hdr = 44
heights = []
for t, cap, box in rows:
    bw, bh = box[2] - box[0], box[3] - box[1]
    heights.append(int(bh * cw / bw))
total = hdr + sum(heights) + len(rows) * (40 + 8)
s2 = Image.new('RGB', (3 * cw + 2 * gap + 2 * left, total), BG)
d = ImageDraw.Draw(s2)
for i, lab in enumerate(('plate WITHOUT the kit', 'plate WITH the kit', 'the PAINTING')):
    d.text((left + i * (cw + gap) + 4, 6), lab, font=FB(14), fill=INK)
d.text((left + 4, 26), 'same box cut from all three, same size; the painter saw the plate at about half this size', font=F(11), fill=MUTE)
y = hdr
for (t, cap, box), hh in zip(rows, heights):
    d.text((left + 4, y + 2), t, font=FB(13), fill=INK)
    d.text((left + 4, y + 20), cap, font=F(11), fill=MUTE)
    y += 40
    for i, k in enumerate(('base', 'kit', 'paint')):
        s2.paste(c[k].crop(box).resize((cw, hh), Image.LANCZOS), (left + i * (cw + gap), y))
    y += hh + 8
print('sheet 2', save_under(s2, OUT + '25 Painter test - close-ups.jpg'), s2.size)

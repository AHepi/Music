# What this does (plain words): builds the sheets for the person from the old and new full-size pictures: labelled before/after panels (JPG under 400 KB each) written to the pictures folder.
import os
from PIL import Image, ImageDraw, ImageFont
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/'
OLD = G + 'final/renders/'
NEW = G + 'fix/out/final/'
P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/30 Japanese garden - pictures/'
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
FONTB = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
_cache = {}


def img(path):
    if path not in _cache:
        _cache[path] = Image.open(path).convert('RGB')
    return _cache[path]


def save(sheet, name):
    out = P + name
    q = 84
    while True:
        sheet.save(out, quality=q, optimize=True, progressive=True)
        kb = os.path.getsize(out) / 1024
        if kb < 385 or q < 50:
            break
        q -= 3
    print(name, sheet.size, round(kb), 'KB q', q)


def before_after_sheet(name, rows, pw, title_left='Before (first round)', title_right='After the fix round'):
    """rows: [(label, file, box)] ; left = old picture, right = new picture, same box."""
    gap, bar, rowbar = 6, 26, 24
    # panel heights from the box aspect
    heights = []
    for label, f, box in rows:
        w, h = box[2] - box[0], box[3] - box[1]
        heights.append(int(round(pw * h / w)))
    H = bar + sum(h + rowbar + gap for h in heights)
    W = 2 * pw + gap
    sheet = Image.new('RGB', (W, H), (18, 18, 18))
    d = ImageDraw.Draw(sheet)
    d.text((8, 4), title_left, fill=(255, 200, 150), font=FONTB)
    d.text((pw + gap + 8, 4), title_right, fill=(170, 235, 170), font=FONTB)
    y = bar
    for (label, f, box), h in zip(rows, heights):
        d.text((8, y + 3), label, fill=(235, 235, 235), font=FONT)
        y += rowbar
        for k, base in enumerate((OLD, NEW)):
            c = img(base + f).crop(box).resize((pw, h), Image.LANCZOS)
            sheet.paste(c, (k * (pw + gap), y))
        y += h + gap
    save(sheet, name)


# ---- painted look
before_after_sheet('30 Fix - painted look before and after (sun rings, ground, maple).jpg', [
    ('Sky above the veranda: the three round rings round the sun are now unequal straight-edged polygons', 'painted_veranda.png', (200, 0, 2400, 700)),
    ('Ground, lower right of the original view: the brown band with the curved edge is gone, flat straight-edged patches instead', 'painted_hero.png', (1500, 1000, 2400, 1600)),
    ('Maple from the veranda: fewer, bigger leaves; the dark eye-shaped hole is closed', 'painted_veranda.png', (1000, 40, 2100, 760)),
], 800)

# ---- realistic look
before_after_sheet('30 Fix - realistic look before and after (pond, dark corner, pine, grass, shrubs).jpg', [
    ('Pond: the white shards (the glow lamps mirrored in the water) are gone', 'real_hero.png', (400, 950, 1300, 1350)),
    ('Lower left under the bridge: the black hole shows water and pebbles again', 'real_hero.png', (0, 1100, 900, 1600)),
    ('Pine pads: ragged needle sprays instead of flat green slabs', 'real_hero.png', (1500, 250, 2100, 700)),
    ('Grass tufts: green tips, four different shapes and sizes', 'real_hero.png', (1400, 1100, 2100, 1500)),
    ('Veranda view: lantern lichen dots gone, shrub (bottom) with a calm fine texture, a clipped hedge behind hides the hard far edge', 'real_veranda.png', (340, 380, 1000, 1180)),
], 640)

# ---- veranda view, both looks
gap, bar = 6, 26
pw, ph = 800, 533
W, H = 2 * pw + gap, 2 * (ph + bar) + gap
sheet = Image.new('RGB', (W, H), (18, 18, 18))
d = ImageDraw.Draw(sheet)
cells = [('Realistic, before', OLD + 'real_veranda.png'), ('Realistic, after (far hedge hides the hard edge and dark band)', NEW + 'real_veranda.png'),
         ('Painted, before', OLD + 'painted_veranda.png'), ('Painted, after (polygon sun rings, flat ground patches, far hedge)', NEW + 'painted_veranda.png')]
for k, (label, path) in enumerate(cells):
    x, y = (k % 2) * (pw + gap), (k // 2) * (ph + bar + gap)
    sheet.paste(img(path).resize((pw, ph), Image.LANCZOS), (x, y + bar))
    d.text((x + 8, y + 4), label, fill=(240, 240, 240), font=FONT)
save(sheet, '30 Fix - veranda view before and after, both looks.jpg')

# ---- updated side by side (same layout as the first round)
bar, gap = 30, 6
pw, ph = 1000, 667
W, H = 2 * pw + gap, ph + bar
sheet = Image.new('RGB', (W, H), (18, 18, 18))
d = ImageDraw.Draw(sheet)
for k, (label, path) in enumerate([('Realistic look (photographed surfaces, weathering, soft stones)', NEW + 'real_hero.png'),
                                   ('Painted look (flat planes, broad colour passages, no smooth curves)', NEW + 'painted_hero.png')]):
    x = k * (pw + gap)
    sheet.paste(img(path).resize((pw, ph), Image.LANCZOS), (x, bar))
    d.text((x + 8, 5), label, fill=(240, 240, 240), font=FONT)
save(sheet, '30 Side by side - realistic and painted.jpg')

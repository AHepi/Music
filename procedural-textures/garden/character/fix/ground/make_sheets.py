"""GROUND builder: the pictures for the person (sheets). python3 -I make_sheets.py"""
import os
from PIL import Image, ImageDraw, ImageFont
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/'
H = G + 'character/ground/'
C = G + 'character/concept/gen/'
OUT = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/31 Japanese garden character - pictures/'
os.makedirs(OUT, exist_ok=True)
F = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BG = (28, 27, 26)
FG = (232, 226, 214)
M = 12


def font(sz, bold=False):
    return ImageFont.truetype(FB if bold else F, sz)


def fit(im, w, h=None):
    if h is None:
        h = round(im.height * w / im.width)
    return im.resize((w, h), Image.LANCZOS)


def sheet(path, W, rows, title, notes=None, q=86):
    """rows: list of lists of (image, label) with images already sized; each row left-aligned with margin M."""
    y = 52
    heights = []
    for r in rows:
        heights.append(max(im.height for im, _ in r) + 26)
    Hh = y + sum(heights) + M + (24 * len(notes) + 8 if notes else 0)
    cv = Image.new('RGB', (W, Hh), BG)
    d = ImageDraw.Draw(cv)
    d.text((M, 12), title, font=font(24, True), fill=FG)
    for r, hh in zip(rows, heights):
        x = M
        for im, lab in r:
            cv.paste(im, (x, y))
            d.text((x, y + im.height + 4), lab, font=font(15), fill=(190, 184, 170))
            x += im.width + M
        y += hh
    if notes:
        for n in notes:
            d.text((M, y), n, font=font(16), fill=FG)
            y += 24
    quality = q
    while True:
        cv.save(path, quality=quality, optimize=True)
        if os.path.getsize(path) < 395000 or quality < 60:
            break
        quality -= 4
    print(os.path.basename(path), cv.size, os.path.getsize(path), 'q', quality)


def crop_frac(im, x0, y0, x1, y1):
    w, h = im.size
    return im.crop((round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h)))


L = lambda p: Image.open(p).convert('RGB')
cw = (1800 - 4 * M) // 3
# ---------------------------------------------------------------- 1 lawn before and after
b, a = L(H + 'crops/hero_before_full.jpg'), L(H + 'crops/hero_after_full.jpg')
cv3 = L(C + 'hero_V3_nb2.jpg')
blr, alr = L(H + 'crops/hero_before_lr.jpg'), L(H + 'crops/hero_after_lr.jpg')
sheet(OUT + '31 Ground - lawn before and after.jpg', 1800, [
    [(fit(b, cw), 'before: today\'s garden, hero camera'), (fit(a, cw), 'after: tufts in clumps with seed heads, worn path, moss, leaves'), (fit(cv3, cw), 'concept followed (hero_V3, ground only)')],
    [(fit(blr, cw), 'before: lower right lawn, 100 % crop'), (fit(alr, cw), 'after: same crop, same light'), (fit(crop_frac(cv3, 0.55, 0.72, 1.0, 1.0), cw), 'concept, same region')],
], 'Ground: the lawn, before and after (same camera, same dusk light, same art style)',
    ['No normal map and no tuft shape variety before; now 12 tuft shapes, a ragged worn path, a soft ground normal map, moss collars and 90 fallen leaves.'])
# ---------------------------------------------------------------- 2 veranda before and after
vb_, va_ = L(H + 'crops/ver_before_full.jpg'), L(H + 'crops/ver_after_full.jpg')
vc = L(C + 'veranda_V2_nb2.jpg')
vbf, vaf = L(H + 'crops/ver_before_fg.jpg'), L(H + 'crops/ver_after_fg.jpg')
cc = crop_frac(vc, 0.0, 0.72, 0.5, 1.0)
sheet(OUT + '31 Ground - veranda before and after.jpg', 1800, [
    [(fit(vb_, cw), 'before: veranda camera'), (fit(va_, cw), 'after'), (fit(vc, cw), 'concept (veranda_V2, for the mood)')],
    [(fit(vbf, cw), 'before: foreground, 100 % crop'), (fit(vaf, cw), 'after: worn patch with ragged edge, tufts, kerb chips'), (fit(cc, cw), 'concept, same region')],
], 'Ground: the veranda view, before and after')
# ---------------------------------------------------------------- 3 tuft shapes
lL, lR = L(H + 'previews/r18/lineup__lineupL.jpg'), L(H + 'previews/r18/lineup__lineupR.jpg')
bandL, bandR = lL.crop((0, 420, 1600, 1300)), lR.crop((0, 420, 1600, 1300))
sg = L(C + 'sheet_grass.jpg')
circ = sg.crop((1990, 95, 2350, 550))
sheet(OUT + '31 Ground - tuft shapes lineup.jpg', 1800, [
    [(fit(bandL, 1100), 'tuft shapes 1 to 8 (short fan, wide fan, arching, upright, tall arching, seed spike, seed plume, nodding pods)'), (fit(circ, 640), 'concept (sheet_grass): chunky tufts with seed spikes')],
    [(fit(bandR, 1100), 'tuft shapes 9 to 16 (broad leaf, dry straw, clover, red tint, straw-tip variants) and three moss domes'), ]
], 'Ground: the tuft recipes in a row (5 to 9 tapered blades, 6 mm and wider at the base, 12 to 70 cm)',
    ['16 meshes: 12 shapes, olive tips (#5c6c2c), 17 percent straw tips, 9 percent reddish. 28 percent of the tufts have seed heads. About 620 tufts in clumps of 2 to 5.'])
# ---------------------------------------------------------------- 4 worn path and kerb
c3, c4 = L(H + 'previews/r18/final__cam3.jpg'), L(H + 'previews/r18/final__cam4.jpg')
earth = sg.crop((1990, 1130, 2450, 1590))
sheet(OUT + '31 Ground - worn path and kerb.jpg', 1800, [
    [(fit(c3, 888), 'the worn path along the kerb, towards the stepping stones'), (fit(c4, 888), 'the kerb join: dark soil lip, tuft at the joint, moss pad, spilled chips')],
    [(fit(alr, 888), 'hero camera, lower right, 100 %'), (fit(earth, 368, 368), 'concept: bare earth patch with pebbles'), ]
], 'Ground: worn path, soil lip and kerb',
    ['Path: bare reddish earth 0.5 m wide with a ragged grass edge and pebble specks, from a top-down mask (2048 px) and a soft ground normal map.'])
# ---------------------------------------------------------------- 5 moss at the rocks
c5, c2 = L(H + 'previews/r18/final__cam5.jpg'), L(H + 'previews/r18/final__cam2.jpg')
lb, la = L(H + 'crops/hero_before_lantern.jpg'), L(H + 'crops/hero_after_lantern.jpg')
moss = sg.crop((1990, 650, 2450, 1110))
sheet(OUT + '31 Ground - moss cushions at the rocks.jpg', 1800, [
    [(fit(c5, 888), 'moss collar and cap on the gravel rocks (soft domes, light top, dark underside)'), (fit(c2, 888), 'a clump with seed heads at a rock foot, low view')],
    [(fit(lb, 572), 'before: lantern and pond-side stones'), (fit(la, 572), 'after'), (fit(moss, 380, 380), 'concept: moss cushions')]
], 'Ground: moss cushions and collars at the rock feet')

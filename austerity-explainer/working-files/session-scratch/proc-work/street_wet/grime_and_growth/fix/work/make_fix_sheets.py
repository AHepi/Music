# Fix round: the before / after sheets for the person, saved in the pictures folder as "25 Fix - ...jpg" (each under 400 KB).
# before = the integrated plates (integrated/plates/<scene>/final_*_kit.png), after = this round's plates (fix/plates/<scene>/final_*_kit.png); both are the full-size 1536 x 2730 pictures.
import os
import sys
from PIL import Image, ImageDraw, ImageFont

K = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
OUT = K + '25 Street grime, cracks, stains, weeds and moss - pictures/'
BEFORE = K + 'street_wet/grime_and_growth/integrated/plates/'
FIX = K + 'street_wet/grime_and_growth/fix/'
AFTER = FIX + 'plates/'
R5 = K + 'street_wet/grime_and_growth/integrated/work/r5/kit/'
FINAL = FIX + 'rounds/final/'


def font(size=18):
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
    except Exception:
        return ImageFont.load_default()


def im(path):
    return Image.open(path).convert('RGB')


def label(img, text, size=18):
    d = ImageDraw.Draw(img)
    f = font(size)
    w = d.textlength(text, font=f)
    d.rectangle((0, 0, w + 12, size + 10), fill=(0, 0, 0))
    d.text((6, 4), text, fill=(255, 235, 120), font=f)
    return img


def pair(before, after, box=None, scale=1.0, titles=('before', 'after')):
    a, b = im(before), im(after)
    if box:
        a, b = a.crop(box), b.crop(box)
    if scale != 1.0:
        a = a.resize((int(a.width * scale), int(a.height * scale)), Image.LANCZOS)
        b = b.resize((int(b.width * scale), int(b.height * scale)), Image.LANCZOS)
    label(a, titles[0]); label(b, titles[1])
    out = Image.new('RGB', (a.width + b.width + 6, a.height), (255, 255, 255))
    out.paste(a, (0, 0)); out.paste(b, (a.width + 6, 0))
    return out


def stack(rows, gap=8, heading=None):
    width = max(r.width for r in rows)
    h = sum(r.height for r in rows) + gap * (len(rows) - 1) + (34 if heading else 0)
    out = Image.new('RGB', (width, h), (255, 255, 255))
    y = 0
    if heading:
        d = ImageDraw.Draw(out)
        d.text((8, 6), heading, fill=(0, 0, 0), font=font(20))
        y = 34
    for r in rows:
        out.paste(r, (0, y))
        y += r.height + gap
    return out


def save(img, name, limit=395_000):
    path = OUT + name
    for q in (90, 86, 82, 78, 74, 70, 66):
        img.save(path, quality=q, optimize=True)
        if os.path.getsize(path) <= limit:
            break
    while os.path.getsize(path) > limit and img.width > 800:
        img = img.resize((int(img.width * 0.92), int(img.height * 0.92)), Image.LANCZOS)
        img.save(path, quality=78, optimize=True)
    print(name, img.size, os.path.getsize(path) // 1024, 'KB')


def plate(scene, name, kind='kit', root=BEFORE):
    return f'{root}{scene}/{name}_{kind}.png'


def make(which):
    s = 'street'
    if which in ('all', 'plants'):
        rows = [pair(plate(s, 'final_main_A_dry'), plate(s, 'final_main_A_dry', root=AFTER), (1000, 1750, 1536, 2250), 1.0),
                pair(plate(s, 'final_main_A_wet'), plate(s, 'final_main_A_wet', root=AFTER), (1000, 1900, 1536, 2400), 1.0),
                pair(plate(s, 'final_main_A_wet'), plate(s, 'final_main_A_wet', root=AFTER), (0, 1900, 700, 2400), 0.78)]
        save(stack(rows, heading='Weeds and moss: dimmer, duller, none in a puddle (main plate at 100 percent: right road dry, right gutter wet, left kerb wet)'), '25 Fix - plants dimmer and out of the puddles (before and after, 100 percent).jpg')
    if which in ('all', 'walls'):
        rows = [pair(plate(s, 'final_main_A_dry'), plate(s, 'final_main_A_dry', root=AFTER), (0, 600, 520, 1250), 1.0),
                pair(plate(s, 'final_main_A_dry'), plate(s, 'final_main_A_dry', root=AFTER), (0, 1500, 540, 1900), 1.0)]
        save(stack(rows, heading='Left brick terrace: no pale panels, the red keeps its warmth (main plate, dry, 100 percent)'), '25 Fix - left brick terrace keeps its warmth (before and after, 100 percent).jpg')
    if which in ('all', 'steps'):
        rows = [pair(plate(s, 'final_main_A_dry'), plate(s, 'final_main_A_dry', root=AFTER), (1000, 1450, 1536, 1850), 1.0),
                pair(plate(s, 'final_main_A_wet'), plate(s, 'final_main_A_wet', root=AFTER), (1000, 1450, 1536, 1850), 1.0)]
        save(stack(rows, heading='Doorsteps: warm cream instead of blue-white (main plate, right pavement, dry above, wet below)'), '25 Fix - doorsteps warm cream (before and after, 100 percent).jpg')
    if which in ('all', 'road'):
        rows = [pair(plate(s, 'final_main_A_wet'), plate(s, 'final_main_A_wet', root=AFTER), (0, 2150, 1536, 2730), 0.65)]
        c_old, c_new = R5 + 'street/plate_close_road_A_wet.jpg', FINAL + 't22/street/close_A_wet.jpg'
        save(stack(rows, heading='Near road, wet: fewer cracks, no bright arcs, smaller film patches (main plate, bottom rows)'), '25 Fix - near road wet calmer (before and after).jpg')
    if which in ('all', 'view'):
        a = [im(plate(s, n, root=r)) for n in ('final_main_A_wet', 'final_main_A_dry') for r in (BEFORE, AFTER)]
        k = 0.36
        a = [x.resize((int(x.width * k), int(x.height * k)), Image.LANCZOS) for x in a]
        for x, t in zip(a, ('wet before', 'wet after', 'dry before', 'dry after')):
            label(x, t, 14)
        out = Image.new('RGB', (sum(x.width for x in a) + 6 * 3, a[0].height), (255, 255, 255))
        x0 = 0
        for x in a:
            out.paste(x, (x0, 0)); x0 += x.width + 6
        save(out, '25 Fix - street view wet and dry (before and after, half size).jpg')
    if which in ('all', 'lockout'):
        a = [im(plate('lockout', n, root=r)) for n in ('final_lockout_B_wet', 'final_lockout_B_dry') for r in (BEFORE, AFTER)]
        k = 0.36
        a = [x.resize((int(x.width * k), int(x.height * k)), Image.LANCZOS) for x in a]
        for x, t in zip(a, ('wet before', 'wet after', 'dry before', 'dry after')):
            label(x, t, 14)
        out = Image.new('RGB', (sum(x.width for x in a) + 6 * 3, a[0].height), (255, 255, 255))
        x0 = 0
        for x in a:
            out.paste(x, (x0, 0)); x0 += x.width + 6
        save(out, '25 Fix - lockout plate wet and dry (before and after, half size).jpg')


if __name__ == '__main__':
    make(sys.argv[1] if len(sys.argv) > 1 else 'all')

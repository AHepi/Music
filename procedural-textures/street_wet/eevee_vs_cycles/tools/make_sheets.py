# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Makes the side-by-side sheets for the person: EEVEE on the left, Cycles on the right, labelled, with the time of each picture, as JPEG files under 400 KB each.
# Plain Python (Pillow, numpy). Reads the full-size pictures and the seconds files, writes the sheets into the sheets folder (see SHEETS below).
# Use: python3 -I make_sheets.py
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
EVC = os.path.abspath(os.path.join(HERE, '..'))
FINAL = EVC                      # the full-size PNGs live here
SHEETS = 'proc-work/26 EEVEE and Cycles side by side - pictures'
os.makedirs(SHEETS, exist_ok=True)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
BG = (24, 24, 26)
TXT = (235, 235, 235)
DIM = (170, 170, 175)
EE_COL = (120, 190, 255)
CY_COL = (255, 190, 110)
TIMES = json.load(open(EVC + '/results/times.json'))      # {"main_wet_eevee": 3.9, ...}  seconds of the picture (average of the two runs), see collect_times.py
INFO = json.load(open(EVC + '/results/picture_info.json'))   # {"main_wet_eevee": "64 samples", "main_wet_cycles": "512 samples + OptiX denoise"}


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def load(name):
    return Image.open(f'{FINAL}/{name}.png').convert('RGB')


def save_under(img, path, limit=390_000):
    for q in range(92, 40, -2):
        img.save(path, 'JPEG', quality=q, optimize=True, progressive=True, subsampling=0 if q >= 86 else 2)
        if os.path.getsize(path) <= limit:
            return q, os.path.getsize(path)
    return q, os.path.getsize(path)


def label_for(name):
    eng = 'EEVEE' if name.endswith('_eevee') else 'Cycles'
    t = TIMES.get(name)
    return eng, INFO.get(name, ''), (f'{t:.1f} s' if t is not None else '')


def sheet(title, subtitle, names, scale=None, width_each=None, path=None, notes=None, gap=14, crops=None):
    """names = [eevee_name, cycles_name]. width_each = the width each picture is shown at."""
    imgs = [load(n) for n in names]
    if width_each is None:
        width_each = imgs[0].width
    h_each = round(imgs[0].height * width_each / imgs[0].width)
    imgs = [im.resize((width_each, h_each), Image.LANCZOS) if im.width != width_each else im for im in imgs]
    pad = 18
    head = 74 if subtitle else 52
    foot = 62
    W = pad * 2 + width_each * 2 + gap
    H = head + h_each + foot + (22 * len(notes) + 10 if notes else 0)
    canvas = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(canvas)
    d.text((pad, 12), title, font=font(22, True), fill=TXT)
    if subtitle:
        d.text((pad, 44), subtitle, font=font(14), fill=DIM)
    for i, (n, im) in enumerate(zip(names, imgs)):
        x = pad + i * (width_each + gap)
        canvas.paste(im, (x, head))
        eng, info, secs = label_for(n)
        col = EE_COL if eng == 'EEVEE' else CY_COL
        d.text((x, head + h_each + 8), eng, font=font(20, True), fill=col)
        d.text((x + 100, head + h_each + 12), secs and f'drawn in {secs}', font=font(16, True), fill=TXT)
        d.text((x, head + h_each + 36), info, font=font(13), fill=DIM)
    if notes:
        y = head + h_each + foot
        for line in notes:
            d.text((pad, y), line, font=font(13), fill=DIM)
            y += 22
    q, size = save_under(canvas, path)
    print(os.path.basename(path), canvas.size, 'q', q, size // 1024, 'KB')


def crops_sheet(rows, path, title, subtitle, crop_w=380, crop_h=250):
    """rows = [(label, eevee_name, cycles_name, (x0, y0))]: 100 % crops (one picture dot = one sheet dot)."""
    pad, gap, head, lab = 14, 10, 62, 22
    W = pad * 2 + crop_w * 2 + gap
    H = head + len(rows) * (crop_h + lab + 8) + 10
    canvas = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(canvas)
    d.text((pad, 10), title, font=font(20, True), fill=TXT)
    d.text((pad, 38), subtitle, font=font(13), fill=DIM)
    y = head
    cache = {}
    for label, ne, nc, (x0, y0) in rows:
        for i, n in enumerate((ne, nc)):
            if n not in cache:
                cache[n] = load(n)
            im = cache[n].crop((x0, y0, x0 + crop_w, y0 + crop_h))
            canvas.paste(im, (pad + i * (crop_w + gap), y + lab))
        d.text((pad, y + 3), label, font=font(13, True), fill=TXT)
        d.text((pad + crop_w - 52, y + 3), 'EEVEE', font=font(13, True), fill=EE_COL)
        d.text((pad + crop_w + gap + crop_w - 56, y + 3), 'Cycles', font=font(13, True), fill=CY_COL)
        y += crop_h + lab + 8
    q, size = save_under(canvas, path)
    print(os.path.basename(path), canvas.size, 'q', q, size // 1024, 'KB')


if __name__ == '__main__':
    cfg = json.load(open(EVC + '/results/sheet_config.json'))
    S = SHEETS + '/'
    sheet('Main street, wet (1080 x 1920)', 'Same file, camera, lighting, wetness, JOINTS and RUBBISH layers. Only the renderer differs. Shown at 55 %.',
          ['main_wet_eevee', 'main_wet_cycles'], width_each=594, path=S + '26 Main street - wet - EEVEE and Cycles.jpg', notes=cfg['notes_main_wet'])
    sheet('Main street, dry (1080 x 1920)', 'Same layers at wetness 0 (JOINTS and RUBBISH on). Shown at 55 %.',
          ['main_dry_eevee', 'main_dry_cycles'], width_each=594, path=S + '26 Main street - dry - EEVEE and Cycles.jpg', notes=cfg['notes_main_dry'])
    sheet('Main street today (file as it is, no layers) (1080 x 1920)', 'The street exactly as the film file has it, no wetness, JOINTS or RUBBISH. Shown at 55 %.',
          ['main_today_eevee', 'main_today_cycles'], width_each=594, path=S + '26 Main street - today, file as it is - EEVEE and Cycles.jpg', notes=cfg['notes_main_today'])
    sheet('Lockout plate, wet, lighting B (1536 x 2730)', 'Exactly as the final plate (WETNESS, JOINTS, RUBBISH). Shown at 50 % (half size).',
          ['lockout_wet_eevee', 'lockout_wet_cycles'], width_each=768, path=S + '26 Lockout plate - wet - EEVEE and Cycles (half size).jpg', notes=cfg['notes_lockout'])
    sheet('Cottage front close view, wet (1600 x 1200)', 'Stone walls, door, window, pavement, gutter and setts. Shown at 50 %.',
          ['cottage_wet_eevee', 'cottage_wet_cycles'], width_each=800, path=S + '26 Cottage front close view - EEVEE and Cycles.jpg', notes=cfg['notes_cottage'])
    sheet('Extra: brick cottage front close view, wet (1600 x 1200)', 'Left-hand row (photo-scanned brick). Shown at 50 %.',
          ['brick_wet_eevee', 'brick_wet_cycles'], width_each=800, path=S + '26 Extra brick cottage front close view - EEVEE and Cycles.jpg', notes=cfg['notes_brick'])
    crops_sheet([tuple([r[0], r[1], r[2], tuple(r[3])]) for r in cfg['crops']], S + '26 Close-ups at 100 percent - walls, door, setts, gutter.jpg',
                'Close-ups at 100 % (one picture dot = one sheet dot)', 'EEVEE left, Cycles right. Brick and stone walls, door, setts, gutter and puddle, rubbish.')

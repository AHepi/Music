# Integrator step 5: the four sheets for the person (JPG under 400 KB each) in the pictures folder.
#   python3 -I make_sheets.py [which ...]     which = lockout street closeups lightings (default all)
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W = os.path.dirname(os.path.abspath(__file__))
INT = os.path.dirname(W)
PICS = 'proc-work/25 Street grime, cracks, stains, weeds and moss - pictures'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
LIMIT = 395 * 1024


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def load(path):
    a = cv2.imread(path)
    if a is None:
        raise FileNotFoundError(path)
    return cv2.cvtColor(a, cv2.COLOR_BGR2RGB)


def label(img, text, size=22, pad=8, fill=(0, 0, 0), color=(255, 255, 255)):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    f = font(size, True)
    w = d.textlength(text, font=f)
    d.rectangle([0, 0, w + 2 * pad, size + 2 * pad], fill=fill)
    d.text((pad, pad - 2), text, font=f, fill=color)
    return np.array(im)


def save(img, name):
    """Saves a JPG as large as the 400 KB line allows (quality steps down)."""
    os.makedirs(PICS, exist_ok=True)
    path = os.path.join(PICS, name)
    pil = Image.fromarray(img)
    for q in (88, 84, 80, 76, 72, 68, 64, 60, 55, 50):
        pil.save(path, quality=q, optimize=True, progressive=True)
        if os.path.getsize(path) <= LIMIT:
            break
    print(path, os.path.getsize(path) // 1024, 'KB, quality', q, img.shape[1], 'x', img.shape[0])
    return path


def pair_panel(before, after, title_b='before', title_a='after', width=640):
    h = int(before.shape[0] * width / before.shape[1])
    b = cv2.resize(before, (width, h), interpolation=cv2.INTER_AREA)
    a = cv2.resize(after, (width, h), interpolation=cv2.INTER_AREA)
    return np.hstack([label(b, title_b), label(a, title_a)])


def sheet_lockout(plates):
    b = load(os.path.join(plates, 'lockout', 'final_lockout_B_wet_base.png'))
    a = load(os.path.join(plates, 'lockout', 'final_lockout_B_wet_kit.png'))
    img = pair_panel(b, a, 'before: water, joints, litter only', 'after: + grime, cracks, stains, weeds, moss', 700)
    save(img, '25 Before and after - lockout plate wet.jpg')


def sheet_street(plates):
    rows = []
    for state in ('wet', 'dry'):
        b = load(os.path.join(plates, 'street', f'final_main_A_{state}_base.png'))
        a = load(os.path.join(plates, 'street', f'final_main_A_{state}_kit.png'))
        rows.append(pair_panel(b, a, f'before ({state})', f'after ({state})', 520))
    img = np.hstack([rows[0], rows[1]])
    img = np.hstack([rows[0], np.full((rows[0].shape[0], 10, 3), 255, np.uint8), rows[1]])
    save(img, '25 Before and after - street view wet and dry.jpg')


def sheet_closeups(plates, boxes):
    """boxes: list of (scene, picture stem, (x0, y0, x1, y1), caption). 100 percent crops of the plates, before beside after."""
    rows = []
    for scene, stem, box, caption in boxes:
        x0, y0, x1, y1 = box
        b = load(os.path.join(plates, scene, f'{stem}_base.png'))[y0:y1, x0:x1]
        a = load(os.path.join(plates, scene, f'{stem}_kit.png'))[y0:y1, x0:x1]
        row = np.hstack([b, np.full((b.shape[0], 6, 3), 255, np.uint8), a])
        rows.append(label(row, caption, 17))
        rows.append(np.full((6, row.shape[1], 3), 255, np.uint8))
    save(np.vstack(rows), '25 Close-ups at 100 percent.jpg')


def sheet_lightings(round_dir, measures):
    p1 = json.load(open(measures))['p1']['pictures']
    order = []
    for label_, lights in (('main', ['A_dry', 'A_wet', 'A_heavy', 'C_dry', 'C_wet', 'D_dry', 'D_wet', 'E_dry', 'E_wet', 'E_heavy']), ('close', ['A_dry', 'A_wet', 'A_heavy', 'C_wet', 'D_wet', 'E_wet']),
                         ('lockout', ['B_dry', 'B_wet', 'B_heavy', 'C_wet', 'D_wet', 'E_wet'])):
        for l in lights:
            order.append((f'{label_}_{l}', 'street' if label_ != 'lockout' else 'lockout'))
    tw, th = 196, 348
    tiles = []
    for name, scene in order:
        img = load(os.path.join(round_dir, 'kit', scene, name + '.jpg'))
        if img.shape[1] / img.shape[0] > 1:          # the 640 x 480 close pictures: fit into the tile
            h = int(tw * img.shape[0] / img.shape[1])
            small = cv2.resize(img, (tw, h), interpolation=cv2.INTER_AREA)
            canvas = np.zeros((th, tw, 3), np.uint8)
            canvas[(th - h) // 2:(th - h) // 2 + h] = small
        else:
            canvas = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA)
        e = p1.get(name)
        ok = e['passed'] if e else None
        near, mid = (e['near']['contrast'], e['middle']['contrast']) if e else (None, None)
        txt = f'{name.replace("_", " ")}'
        sub = ('PASS' if ok else 'FAIL') + (f' {near:.2f}/{mid:.2f}' if near is not None and mid is not None else '')
        im = Image.fromarray(canvas)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, tw, 34], fill=(0, 0, 0))
        d.text((4, 2), txt, font=font(12, True), fill=(255, 255, 255))
        d.text((4, 17), sub, font=font(12, True), fill=(120, 255, 120) if ok else (255, 110, 110))
        tiles.append(np.array(im))
    cols = 6
    rows_ = []
    for i in range(0, len(tiles), cols):
        chunk = tiles[i:i + cols]
        while len(chunk) < cols:
            chunk.append(np.zeros_like(tiles[0]))
        rows_.append(np.hstack(chunk))
    grid = np.vstack(rows_)
    s = json.load(open(measures))['p1']['summary']
    head = np.full((46, grid.shape[1], 3), 20, np.uint8)
    im = Image.fromarray(head)
    d = ImageDraw.Draw(im)
    d.text((8, 6), f"Sett joints with everything on: {s['official']['passed']} of {s['official']['of']} pictures pass the joint test (before the new parts: 20 of 22).", font=font(13, True), fill=(255, 255, 255))
    d.text((8, 26), f"Numbers = joint contrast near/middle. Failing: {', '.join(s['official']['failing']) or 'none'} (it failed before too). Highest {s['max_near_contrast']:.2f}, limit 0.75.", font=font(13), fill=(210, 210, 210))
    save(np.vstack([np.array(im), grid]), '25 All lightings - joints still pass.jpg')


if __name__ == '__main__':
    which = sys.argv[1:] or ['lockout', 'street', 'closeups', 'lightings']
    plates = os.path.join(INT, 'plates')
    if 'lockout' in which:
        sheet_lockout(plates)
    if 'street' in which:
        sheet_street(plates)
    if 'closeups' in which:
        boxes = json.load(open(os.path.join(W, 'closeup_boxes.json')))
        sheet_closeups(plates, [tuple(b[:2]) + (tuple(b[2]), b[3]) for b in boxes])
    if 'lightings' in which:
        rd = os.path.join(W, os.environ.get('ROUND', 'r3'))
        sheet_lightings(rd, os.path.join(rd, 'measures_kit.json'))

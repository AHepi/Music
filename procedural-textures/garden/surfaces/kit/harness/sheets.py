# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# CONTACT SHEETS for the reports: a grid of labelled pictures (contact_sheet), a before/after pair at 100 % crops (before_after), and a sheet of mask pictures with a colour key
# (mask_sheet). Every sheet is a JPG under 400 KB (the quality steps down until it fits). Plain Python (OpenCV, numpy); nothing here needs Blender.
import os

import cv2
import numpy as np

MAX_BYTES = 400 * 1024


def _read(path):
    a = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if a is None:
        raise FileNotFoundError(path)
    if a.dtype == np.uint16:
        a = (a / 257.0).astype(np.uint8)
    if a.ndim == 2:
        a = cv2.cvtColor(a, cv2.COLOR_GRAY2BGR)
    return a[..., :3]


def _label(image, text, scale=0.45, pad=4):
    (w, h), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
    cv2.rectangle(image, (0, 0), (w + 2 * pad, h + base + 2 * pad), (0, 0, 0), -1)
    cv2.putText(image, text, (pad, h + pad), cv2.FONT_HERSHEY_SIMPLEX, scale, (235, 235, 235), 1, cv2.LINE_AA)
    return image


def save_under_limit(image, path, limit=MAX_BYTES, start=90):
    """JPG at the highest quality (stepping down from `start`) that stays under the limit; shrinks the picture by a tenth at a time if even quality 40 is too big."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    img = image
    while True:
        for q in range(start, 39, -5):
            ok, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, q])
            if ok and len(buf) <= limit:
                with open(path, 'wb') as handle:
                    handle.write(buf.tobytes())
                return len(buf), q, img.shape[1], img.shape[0]
        img = cv2.resize(img, None, fx=0.9, fy=0.9, interpolation=cv2.INTER_AREA)


def contact_sheet(items, out, columns=4, cell_width=320, title=None, background=(24, 24, 24)):
    """items: [(picture path or array, label)]. Pictures are shrunk to cell_width wide, rows as tall as the tallest in the row."""
    cells = []
    for source, label in items:
        a = _read(source) if isinstance(source, str) else source
        k = cell_width / a.shape[1]
        a = cv2.resize(a, (cell_width, max(1, int(round(a.shape[0] * k)))), interpolation=cv2.INTER_AREA).copy()
        cells.append(_label(a, label))
    rows = [cells[i:i + columns] for i in range(0, len(cells), columns)]
    strips = []
    for row in rows:
        h = max(c.shape[0] for c in row)
        strip = np.full((h, columns * cell_width + (columns - 1) * 4, 3), background, np.uint8)
        for i, c in enumerate(row):
            strip[:c.shape[0], i * (cell_width + 4):i * (cell_width + 4) + cell_width] = c
        strips.append(strip)
        strips.append(np.full((4, strip.shape[1], 3), background, np.uint8))
    sheet = np.concatenate(strips[:-1], axis=0)
    if title:
        bar = np.full((26, sheet.shape[1], 3), background, np.uint8)
        cv2.putText(bar, title, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (240, 240, 240), 1, cv2.LINE_AA)
        sheet = np.concatenate([bar, sheet], axis=0)
    return save_under_limit(sheet, out)


def before_after(before, after, out, box=None, size=360, labels=('before', 'after')):
    """Side by side at 100 % (a box (x, y, w, h) cut out of both pictures; the middle of the picture when not given)."""
    a, b = _read(before), _read(after)
    if box is None:
        h, w = a.shape[:2]
        box = ((w - size) // 2, (h - size) // 2, min(size, w), min(size, h))
    x, y, w, h = box
    ca, cb = a[y:y + h, x:x + w].copy(), b[y:y + h, x:x + w].copy()
    return save_under_limit(np.concatenate([_label(ca, labels[0]), _label(cb, labels[1])], axis=1), out)


def mask_sheet(items, out, columns=3, cell_width=360, title=None):
    """items: [(mask picture path, label)]; the mask pictures are shown as they are (R, G, B channels = up to three masks) on a dark ground."""
    return contact_sheet(items, out, columns=columns, cell_width=cell_width, title=title)
